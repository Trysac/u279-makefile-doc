# makefile-doc

[![PyPI version](https://img.shields.io/pypi/v/trysac-makefile-doc)](https://pypi.org/project/trysac-makefile-doc/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-makefile-doc)](LICENSE)
[![CI](https://github.com/Trysac/u279-makefile-doc/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u279-makefile-doc/actions/workflows/ci.yml)

Document Makefiles from their ## comments: aligned help output, a Markdown table kept in sync between README markers, sections and a check for undocumented targets

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-makefile-doc
# or
uv add trysac-makefile-doc
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import makefile_doc

# normalize() trims surrounding whitespace and lower-cases the text.
print(makefile_doc.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    makefile_doc.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
