"""Parse and document Makefiles from their ``##`` comments.

The parser recognises a practical GNU make subset:

* CRLF is normalised to LF.
* Backslash continuations are joined (line numbers stay at the first physical line).
* Recipe lines (starting with a tab), ``define ... endef`` blocks, ``include`` lines and
  comment-only lines are skipped.
* ``##@ Section`` starts a section.
* Consecutive ``## help`` lines directly above a rule become that rule's help unless the
  rule has its own trailing `` ## help``, which wins.
* Variable assignments are never rules; special targets are not listed, but ``.PHONY:``
  marks its prerequisites as phony.

The rendered outputs come from the same parsed model, which keeps terminal help, a
Markdown table, and an undocumented-target check in sync.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "MakeDocError",
    "Makefile",
    "Target",
    "__version__",
    "parse_makefile",
    "render_help",
    "render_markdown",
    "undocumented",
    "update_markers",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

ErrorCode = Literal["input_too_large", "markers_missing"]


class MakeDocError(Exception):
    """Base error for the library.

    Attributes:
        code: Stable machine-readable error identifier.
    """

    def __init__(self, code: ErrorCode) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Target:
    """A single Makefile target.

    Attributes:
        name: Target name (one entry per name in a multi-target rule).
        help: Human-readable help text; empty when undocumented.
        section: Section name from the nearest preceding ``##@`` marker; empty when none.
        line: First physical line number of the rule (1-based).
        phony: Whether the target was listed as a prerequisite of ``.PHONY``.
    """

    name: str
    help: str
    section: str
    line: int
    phony: bool


@dataclass(frozen=True)
class Makefile:
    """Parsed Makefile model.

    Attributes:
        targets: Targets in file order. A target defined twice keeps the first line and
            the first non-empty help.
    """

    targets: list[Target]


_RULE_RE = re.compile(r"^([^:=#\t][^:=#]*?)(::?)(?!=)(.*)$")
_ASSIGN_RE = re.compile(r"^[^:=#\t][^:=#]*?(?:::=|::=|:=|\?=|\+=|!=|=)")
_TRAILING_HELP_MARKER = " ## "


def parse_makefile(text: str, *, max_bytes: int = 1_000_000) -> Makefile:
    """Parse ``text`` and return a :class:`Makefile`.

    Args:
        text: Makefile contents.
        max_bytes: Maximum accepted UTF-8 size of ``text``. Larger inputs raise
            :class:`MakeDocError` with code ``input_too_large``.

    Raises:
        MakeDocError: If ``text`` is larger than ``max_bytes`` bytes.
    """
    if len(text.encode("utf-8")) > max_bytes:
        raise MakeDocError("input_too_large")

    text = text.replace("\r\n", "\n")
    raw_lines = text.split("\n")
    logical_lines: list[tuple[int, str]] = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        first_line = i + 1
        while line.endswith("\\"):
            line = line[:-1]
            if i + 1 < len(raw_lines):
                i += 1
                line += raw_lines[i]
            else:
                break
        logical_lines.append((first_line, line))
        i += 1

    collected: dict[str, dict[str, str | int]] = {}
    phony_names: set[str] = set()
    current_section = ""
    pending_help: list[str] = []
    in_define = False

    for line_no, line in logical_lines:
        stripped = line.strip()

        if in_define:
            if stripped.startswith("endef") and (len(stripped) == 5 or stripped[5].isspace()):
                in_define = False
            continue

        if stripped.startswith("define") and (len(stripped) == 6 or stripped[6].isspace()):
            in_define = True
            pending_help.clear()
            continue

        if stripped.startswith("include") and (len(stripped) == 7 or stripped[7].isspace()):
            pending_help.clear()
            continue
        if stripped.startswith("-include") and (len(stripped) == 8 or stripped[8].isspace()):
            pending_help.clear()
            continue
        if stripped.startswith("sinclude") and (len(stripped) == 8 or stripped[8].isspace()):
            pending_help.clear()
            continue

        if stripped == "" or stripped.startswith("#"):
            if stripped.startswith("##@"):
                current_section = stripped[3:].strip()
                pending_help.clear()
                continue
            if stripped.startswith("##"):
                pending_help.append(stripped[2:].strip())
                continue
            pending_help.clear()
            continue

        if line.startswith((" ", "\t")):
            pending_help.clear()
            continue

        rule_part = line
        trailing_help = ""
        marker_pos = line.find(_TRAILING_HELP_MARKER)
        if marker_pos != -1:
            rule_part = line[:marker_pos]
            trailing_help = line[marker_pos + len(_TRAILING_HELP_MARKER) :].strip()

        if _ASSIGN_RE.match(rule_part):
            pending_help.clear()
            continue

        match = _RULE_RE.match(rule_part)
        if match is None:
            pending_help.clear()
            continue

        target_names = match.group(1).strip().split()
        if not target_names:
            pending_help.clear()
            continue

        if target_names == [".PHONY"]:
            phony_names.update(match.group(3).split())
            pending_help.clear()
            continue

        help_text = trailing_help
        if not help_text and pending_help:
            help_text = " ".join(pending_help)

        for name in target_names:
            if name.startswith(".") or "%" in name or "$(" in name or "${" in name:
                continue
            existing = collected.get(name)
            if existing is None:
                collected[name] = {
                    "line": line_no,
                    "help": help_text,
                    "section": current_section,
                }
            elif not existing["help"] and help_text:
                existing["help"] = help_text

        pending_help.clear()

    targets = [
        Target(
            name=name,
            help=str(data["help"]),
            section=str(data["section"]),
            line=int(data["line"]),
            phony=name in phony_names,
        )
        for name, data in collected.items()
    ]
    return Makefile(targets=targets)


def _documented_targets(mf: Makefile) -> list[Target]:
    return [t for t in mf.targets if t.help]


def render_help(mf: Makefile) -> str:
    """Render terminal-friendly aligned help.

    Documented targets are grouped by section. When no section markers exist a single
    ``Targets:`` header is used. Undocumented targets are omitted. The output always
    ends with a newline.
    """
    documented = _documented_targets(mf)
    if not documented:
        return ""

    max_width = max(len(t.name) for t in documented)

    groups: dict[str, list[Target]] = {}
    section_order: list[str] = []
    for target in documented:
        section = target.section
        if section not in groups:
            groups[section] = []
            section_order.append(section)
        groups[section].append(target)

    blocks: list[str] = []
    for section in section_order:
        header = "Targets:" if section == "" else f"{section}:"
        lines = [header]
        for target in groups[section]:
            lines.append(f"  {target.name.ljust(max_width)}  {target.help}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks) + "\n"


def render_markdown(mf: Makefile) -> str:
    """Render a Markdown table of documented targets.

    The table always starts with a header row and a separator row. Target names are
    wrapped in backticks and ``|`` in help text is escaped as ``\\|``.
    """
    documented = _documented_targets(mf)
    rows = ["| Target | Description |", "| --- | --- |"]
    for target in documented:
        escaped_help = target.help.replace("|", "\\|")
        rows.append(f"| `{target.name}` | {escaped_help} |")
    return "\n".join(rows) + "\n"


def undocumented(mf: Makefile) -> list[str]:
    """Return sorted names of phony targets without help."""
    return sorted(t.name for t in mf.targets if t.phony and not t.help)


_START_MARKER = "<!-- makefile-doc:start -->"
_END_MARKER = "<!-- makefile-doc:end -->"


def update_markers(document: str, mf: Makefile) -> str:
    """Replace content between marker comments in ``document`` by the Markdown table.

    The replacement is a single newline followed by the rendered table. The marker
    lines themselves are preserved.

    Raises:
        MakeDocError: With code ``markers_missing`` if either marker is absent or the
            end marker precedes the start marker.
    """
    lines = document.splitlines(keepends=True)
    start_idx: int | None = None
    end_idx: int | None = None
    for idx, line in enumerate(lines):
        content = line.rstrip("\r\n")
        if content == _START_MARKER and start_idx is None:
            start_idx = idx
        if content == _END_MARKER and start_idx is not None:
            end_idx = idx
            break
    if start_idx is None or end_idx is None or end_idx <= start_idx:
        raise MakeDocError("markers_missing")

    prefix = "".join(lines[: start_idx + 1])
    suffix = "".join(lines[end_idx:])
    return prefix + "\n" + render_markdown(mf) + suffix
