"""Command-line interface for makefile-doc."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import (
    MakeDocError,
    parse_makefile,
    render_help,
    render_markdown,
    undocumented,
    update_markers,
)


def main(argv: list[str] | None = None) -> int:
    """Run the ``makefile-doc`` CLI.

    Returns:
        0 on success, 1 for undocumented targets or missing markers, 2 for usage,
        I/O, or input-too-large errors.
    """
    parser = argparse.ArgumentParser(
        prog="makefile-doc",
        description="Document Makefiles from their ## comments.",
    )
    parser.add_argument("makefile", nargs="?", default="Makefile", help="Path to Makefile")
    parser.add_argument("--markdown", action="store_true", help="Render Markdown table")
    parser.add_argument("--check", action="store_true", help="Print undocumented phony targets")
    parser.add_argument("--update", metavar="FILE", help="Update markers in FILE")
    args = parser.parse_args(argv)

    try:
        text = Path(args.makefile).read_text(encoding="utf-8")
        mf = parse_makefile(text)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except MakeDocError as exc:
        print(exc.code, file=sys.stderr)
        return 2

    if args.check:
        targets = undocumented(mf)
        for name in targets:
            print(f"undocumented: {name}")
        return 1 if targets else 0

    if args.update:
        try:
            document = Path(args.update).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        try:
            updated = update_markers(document, mf)
        except MakeDocError as exc:
            print(exc.code, file=sys.stderr)
            return 1
        try:
            Path(args.update).write_text(updated, encoding="utf-8")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    if args.markdown:
        sys.stdout.write(render_markdown(mf))
    else:
        sys.stdout.write(render_help(mf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
