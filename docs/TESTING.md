# Testing

## Running

The tests are pytest functions in `tests/test_makefile_doc.py`:

```sh
python -m pytest tests/test_makefile_doc.py
```

## Policy

The tests exercise the public API (`parse_makefile`, `render_help`, `render_markdown`, `undocumented`, `update_markers`, `MakeDocError`) and the CLI `main`. CLI tests use `tmp_path` and `capsys` and assert return codes, stdout, stderr and written file contents. The tests present do not use network access, wall-clock timing or external tools.

## Tiers

Only one test module is present: `tests/test_makefile_doc.py`. No conformance-tier tests, external-tool tests or CI-only test markers are shown in the provided tests.

## Layout

`tests/test_makefile_doc.py` is the test source file. The provided tree does not show a `tests/conftest.py`.

Covered tests include:

- `test_parse_simple_trailing_help`
- `test_parse_preceding_help_joined`
- `test_render_help_no_sections`
- `test_render_help_with_sections`
- `test_rule_skipping_and_special_cases`
- `test_parse_continuation_rule_is_one_target_on_first_line`
- `test_phony_markers_and_undocumented`
- `test_render_markdown_escapes_pipe`
- `test_cli_check_and_update_markers`
- `test_cli_update_markers_missing`
- `test_cli_input_too_large`
- `test_cli_io_error`
- `test_cli_markdown_and_default`
- `test_edge_cases_crlf_define_order_only_hash_in_help`
- `test_duplicate_target_keeps_first_nonempty_help_and_line`
