# Project record

## Objective

Document Makefiles from their `##` comments: aligned help output, a Markdown table kept in sync between README markers, sections, and a check for undocumented targets.

## Scope

- In scope: parsing the practical GNU make subset implemented in `parse_makefile` (CRLF normalisation, continuations, `##@` sections, `##` help, trailing ` ##` help, `.PHONY`, skipping recipes, `define` blocks, `include` lines and variable assignments).
- In scope: the public library API `parse_makefile`, `render_help`, `render_markdown`, `undocumented`, `update_markers`, `Target`, `Makefile` and `MakeDocError`.
- In scope: the `makefile-doc` CLI with a Makefile path (default `Makefile`), `--markdown`, `--check` and `--update FILE`.
- Out of scope: evaluating make variables, expanding `include` files, BSD make syntax, and documenting variables.
- Out of scope: runtime dependencies; the package uses only the Python standard library.

## Timeline

The specification records no dated events for this project.

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 583737 / 56353 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0795 |

## Factory run u279 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1714 | 14960 | 0 | 3200 | 0.0308 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 8781 | 3093 | 0 | 52864 | 0.0033 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 6435 | 3933 | 0 | 37760 | 0.0034 |
| 2026-11-10 | audit | deepseek-flash | no | 17908 | 24639 | 0 | 293120 | 0.0183 |
| 2026-11-10 | fix-3 | deepseek-flash | no | 7159 | 2535 | 0 | 44416 | 0.0027 |
| 2026-11-10 | docs | deepseek-flash | no | 110124 | 7193 | 0 | 256 | 0.0208 |

Total: $0.0795. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
