"""Behavior tests for the public API of makefile_doc."""

from __future__ import annotations

import pytest

import makefile_doc


def test_normalize_trims_and_lowercases() -> None:
    assert makefile_doc.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        makefile_doc.normalize(value)


def test_version_is_semver() -> None:
    parts = makefile_doc.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
