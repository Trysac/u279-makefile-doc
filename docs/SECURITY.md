# Security notes

## Threat model

`makefile-doc` parses text and renders text. It does not execute Makefiles, evaluate variables, expand includes or run shell commands.

**Defended**

- Parsing is pure Python text handling and regular-expression matching; Makefile contents are never passed to `eval`, `exec`, a shell or a subprocess.
- Input size is checked before parsing against `max_bytes`, default 1_000_000 UTF-8 bytes. Larger input raises `MakeDocError` with code `input_too_large`.
- `update_markers` only replaces content strictly between the exact `<!-- makefile-doc:start -->` and `<!-- makefile-doc:end -->` marker lines. A missing marker or an end marker before the start raises `MakeDocError` with code `markers_missing`.
- The CLI reads input as UTF-8, catches `OSError`, `UnicodeDecodeError` and `MakeDocError`, prints errors to stderr and returns documented exit codes.
- No network access, runtime dependencies or credential handling are implemented in the library.

**Not defended**

- The parser does not analyse included makefiles, variable values or command recipes; their security properties are outside this utility.
- There is no line-count, regex-time or total-runtime limit beyond the UTF-8 byte limit; accepted input can be as large as `max_bytes`.
- Markdown output escapes `|` in help text only. It is not HTML sanitisation and does not escape general Markdown or HTML.
- The CLI is not a sandbox: it reads the Makefile path given by the caller and writes the `--update` path given by the caller, subject to the process's own filesystem permissions.

## Publishing

No publishing configuration, credentials or upload code is present in the reviewed source. Release publication is outside the behaviour implemented in this repository.
