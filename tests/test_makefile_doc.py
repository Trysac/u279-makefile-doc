"""Tests for makefile_doc."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from makefile_doc import (
    MakeDocError,
    Makefile,
    Target,
    parse_makefile,
    render_help,
    render_markdown,
    undocumented,
    update_markers,
)
from makefile_doc.__main__ import main


def test_parse_simple_trailing_help() -> None:
    mf = parse_makefile("build: deps ## Build the app\n\tgo build\n")
    assert mf.targets == [
        Target(name="build", help="Build the app", section="", line=1, phony=False)
    ]


def test_parse_preceding_help_joined() -> None:
    mf = parse_makefile("## Run tests\n## with coverage\ntest:\n\tpytest\n")
    assert len(mf.targets) == 1
    target = mf.targets[0]
    assert target.name == "test"
    assert target.help == "Run tests with coverage"
    assert target.line == 3
    assert not target.phony


def test_render_help_no_sections() -> None:
    mf = parse_makefile("build: ## Build\ntest: ## Run tests\n")
    assert render_help(mf) == "Targets:\n  build  Build\n  test   Run tests\n"


def test_render_help_with_sections() -> None:
    mf = parse_makefile("##@ Build\nbuild: ## Build\n##@ Test\ntest: ## Test\n")
    assert render_help(mf) == ("Build:\n  build  Build\n\nTest:\n  test   Test\n")


def test_rule_skipping_and_special_cases() -> None:
    text = """CC := gcc
%.o: %.c
$(BIN): main.c
	recipe line
clean:: ## Clean
a b: ## Both
build: a \\
  b ## Build
"""
    mf = parse_makefile(text)
    names = {t.name: t for t in mf.targets}
    assert set(names) == {"clean", "a", "b", "build"}
    assert names["clean"].help == "Clean"
    assert names["a"].help == "Both"
    assert names["b"].help == "Both"
    assert names["build"].help == "Build"
    # The continued rule starts on its first physical line (line 7 of ``text``),
    # not on the continuation line.
    assert names["build"].line == 7


def test_parse_continuation_rule_is_one_target_on_first_line() -> None:
    mf = parse_makefile("build: a \\\n  b ## Build\n")
    assert mf.targets == [Target(name="build", help="Build", section="", line=1, phony=False)]


def test_phony_markers_and_undocumented() -> None:
    text = ".PHONY: build lint\nbuild: ## Build\nlint:\n"
    mf = parse_makefile(text)
    assert {t.name: t.phony for t in mf.targets} == {"build": True, "lint": True}
    assert undocumented(mf) == ["lint"]


def test_render_markdown_escapes_pipe() -> None:
    mf = parse_makefile("build: ## Build\ntest: ## a | b\n")
    assert render_markdown(mf) == (
        "| Target | Description |\n| --- | --- |\n| `build` | Build |\n| `test` | a \\| b |\n"
    )


def test_cli_check_and_update_markers(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text(".PHONY: build lint\nbuild: ## Build\nlint:\n", encoding="utf-8")
    assert main(["--check", str(makefile)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "undocumented: lint\n"
    assert captured.err == ""

    readme = tmp_path / "README.md"
    readme.write_text(
        "before\n<!-- makefile-doc:start -->\nold\n<!-- makefile-doc:end -->\nafter\n",
        encoding="utf-8",
    )
    assert main(["--update", str(readme), str(makefile)]) == 0
    updated = readme.read_text(encoding="utf-8")
    assert "<!-- makefile-doc:start -->" in updated
    assert "<!-- makefile-doc:end -->" in updated
    assert "| `build` | Build |" in updated
    assert "| `lint` |  |" not in updated  # undocumented omitted


def test_cli_update_markers_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("build: ## Build\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("no markers\n", encoding="utf-8")
    assert main(["--update", str(readme), str(makefile)]) == 1
    captured = capsys.readouterr()
    assert "markers_missing" in captured.err


def test_cli_input_too_large(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("a" * 1_000_001, encoding="utf-8")
    assert main([str(makefile)]) == 2
    captured = capsys.readouterr()
    assert "input_too_large" in captured.err


def test_cli_io_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "missing")]) == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_cli_markdown_and_default(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("build: ## Build\n", encoding="utf-8")
    assert main([str(makefile)]) == 0
    out = capsys.readouterr().out
    assert "Targets:" in out
    assert main(["--markdown", str(makefile)]) == 0
    out = capsys.readouterr().out
    assert "| Target | Description |" in out


def test_edge_cases_crlf_define_order_only_hash_in_help() -> None:
    text = "define mydef\r\necho hi\r\nendef\r\n##@ Build\r\nbuild: a | b ## Build #1\r\n"
    mf = parse_makefile(text)
    assert len(mf.targets) == 1
    assert mf.targets[0].name == "build"
    assert mf.targets[0].help == "Build #1"
    assert mf.targets[0].section == "Build"


def test_duplicate_target_keeps_first_nonempty_help_and_line() -> None:
    text = "build: ## First\nbuild: ## Second\n"
    mf = parse_makefile(text)
    assert len(mf.targets) == 1
    assert mf.targets[0].help == "First"
    assert mf.targets[0].line == 1


def test_update_markers_error_when_end_before_start() -> None:
    doc = "<!-- makefile-doc:end -->\n<!-- makefile-doc:start -->\n"
    with pytest.raises(MakeDocError) as exc_info:
        update_markers(doc, Makefile([]))
    assert exc_info.value.code == "markers_missing"


def test_update_markers_error_when_missing() -> None:
    with pytest.raises(MakeDocError, match="markers_missing"):
        update_markers("no markers", Makefile([]))


def test_parse_too_large_input() -> None:
    with pytest.raises(MakeDocError) as exc_info:
        parse_makefile("x" * 100, max_bytes=50)
    assert exc_info.value.code == "input_too_large"


def test_render_help_empty_input() -> None:
    assert render_help(Makefile([])) == ""


def test_render_help_omits_undocumented() -> None:
    mf = parse_makefile("build: ## Build\nlint:\n")
    assert render_help(mf) == "Targets:\n  build  Build\n"


def test_parse_variable_assignments_never_rules() -> None:
    text = "VAR := value\nVAR2 = value2\nbuild: ## Build\n"
    mf = parse_makefile(text)
    assert [t.name for t in mf.targets] == ["build"]


def test_parse_assignments_with_colons_in_value_are_not_rules() -> None:
    assert parse_makefile("## Doc\nURL = https://example.com\n").targets == []
    assert parse_makefile("VAR ::= x\n").targets == []
    assert parse_makefile("VPATH = src:../include\n").targets == []


def test_cli_non_utf8_input_returns_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_bytes(b"\xff\xfe build: ## B\n")
    assert main([str(makefile)]) == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_parse_skips_include_and_comments() -> None:
    text = "include other.mk\n# plain comment\n## help before variable\nVAR=1\nbuild: ## Build\n"
    mf = parse_makefile(text)
    assert [t.name for t in mf.targets] == ["build"]
    assert mf.targets[0].help == "Build"


def test_parse_multi_target_rule_same_line() -> None:
    mf = parse_makefile("a b: ## Both\n")
    assert len(mf.targets) == 2
    assert mf.targets[0].name == "a"
    assert mf.targets[1].name == "b"
    assert mf.targets[0].help == "Both"
    assert mf.targets[1].help == "Both"
    assert mf.targets[0].line == 1
    assert mf.targets[1].line == 1


def test_parse_special_targets_not_listed_but_phony_marked() -> None:
    text = ".DEFAULT_GOAL := build\n.PHONY: clean\nclean:\n"
    mf = parse_makefile(text)
    assert [t.name for t in mf.targets] == ["clean"]
    assert mf.targets[0].phony is True


def test_parse_phony_after_target() -> None:
    text = "build:\n.PHONY: build\n"
    mf = parse_makefile(text)
    assert mf.targets[0].phony is True


def test_logger_has_null_handler() -> None:
    import makefile_doc

    logger = makefile_doc.logger
    assert any(isinstance(handler, logging.NullHandler) for handler in logger.handlers)
