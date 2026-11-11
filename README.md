# makefile-doc

[![CI](https://github.com/Trysac/u279-makefile-doc/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u279-makefile-doc/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/trysac-makefile-doc.svg)](https://pypi.org/project/trysac-makefile-doc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Makefiles are entry points, but their targets are usually discovered by reading the file. The common awk help one-liner breaks on multiple targets, line continuations or double-colon rules, and README target tables go stale. `makefile-doc` parses documented targets once and renders terminal help, a Markdown table and a phony-target check from the same parsed model.

## Installation

```sh
pip install trysac-makefile-doc
```

The import name is `makefile_doc`. The package uses only the Python standard library and requires Python >= 3.10.

## Usage

```python
from makefile_doc import parse_makefile, render_help

mf = parse_makefile("build: ## Build the app\ntest: ## Run tests\n")
print(render_help(mf))
```

## Public API

- `parse_makefile(text: str, *, max_bytes: int = 1_000_000) -> Makefile` parses `##` comments, `##@ Section` markers, rules, continuations and `.PHONY` prerequisites.
- `render_help(mf: Makefile) -> str` returns aligned terminal help for documented targets, grouped by section, omitting undocumented targets, ending with a newline.
- `render_markdown(mf: Makefile) -> str` returns a Markdown table of documented targets; `|` in help text is escaped as `\|`.
- `undocumented(mf: Makefile) -> list[str]` returns sorted names of phony targets without help.
- `update_markers(document: str, mf: Makefile) -> str` replaces the text between `<!-- makefile-doc:start -->` and `<!-- makefile-doc:end -->` with a newline plus the Markdown table.
- `Target` is the frozen dataclass `Target(name: str, help: str, section: str, line: int, phony: bool)`.
- `Makefile` is the frozen dataclass `Makefile(targets: list[Target])`.
- `MakeDocError(code)` carries `code` as `"input_too_large"` or `"markers_missing"`.

Limits and behavior: input size is measured in UTF-8 bytes and defaults to 1_000_000; larger input raises `MakeDocError("input_too_large")`. `update_markers` raises `MakeDocError("markers_missing")` when either marker is absent or the end marker precedes the start marker. The parser normalises CRLF, joins backslash continuations at the first physical line, skips recipes, `define ... endef` blocks, `include` lines and comment-only lines, treats variable assignments as non-rules, skips special targets and names containing `%`, `$(` or `${`, and does not evaluate variables or expand includes. A target defined twice keeps the first line and the first non-empty help.

CLI: `makefile-doc [Makefile] [--markdown] [--check] [--update FILE]`. The Makefile path defaults to `Makefile`. `--check` prints `undocumented: <name>` per target and exits 1 when any exist; `--update FILE` writes the marker replacement. Exit code 0 is success, 1 is undocumented targets or missing markers, 2 is usage, I/O or input-too-large errors.

## Why not the awk help one-liner

The common awk help one-liner does not handle continuations, double-colon and multi-target rules, sections, or README synchronization. This package uses one parser for terminal help, Markdown output and the undocumented-target check.

## Security

See [docs/SECURITY.md](docs/SECURITY.md).
