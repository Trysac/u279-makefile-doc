# Use a single parsed model for terminal help, Markdown, and CI checks

Status: accepted (generated, pending human review)

## Context

Makefile targets are typically documented with ad-hoc awk one-liners that break on multi-target rules, continuations, and double-colon rules. README tables go stale because they are maintained separately.

## Decision

Implement a dedicated parser for a practical GNU make subset and expose one frozen `Makefile` model. The CLI and update-markers feature render from that same model, so terminal help, Markdown tables, and the undocumented-target check can never diverge.

## Consequences

The parser intentionally does not evaluate variables or expand includes; those constructs remain out of scope. This keeps the implementation deterministic and dependency-free, while covering the common documentation patterns used in modern repositories.
