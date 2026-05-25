"""Tests for Makefile structure — covers L1 (PHONY declaration) already on epic."""

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def makefile_text(repo_root: Path) -> str:
    makefile = repo_root / "Makefile"
    assert makefile.is_file(), "Makefile does not exist at repo root"
    return makefile.read_text(encoding="utf-8")


def test_makefile_exists_and_readable(repo_root: Path):
    """Makefile must exist and be a non-empty regular file."""
    makefile = repo_root / "Makefile"
    assert makefile.is_file(), "Makefile is missing from repo root"
    assert makefile.stat().st_size > 0, "Makefile is empty"


def test_phony_declares_generate_python_protos(makefile_text: str):
    """generate_python_protos must appear in a .PHONY declaration."""
    # .PHONY: may list multiple targets in any order; scan all .PHONY lines.
    phony_targets: list[str] = []
    for line in makefile_text.splitlines():
        m = re.match(r"^\.PHONY\s*:\s*(.+)", line)
        if m:
            phony_targets.extend(m.group(1).split())
    assert "generate_python_protos" in phony_targets, (
        f"generate_python_protos not found in any .PHONY declaration; "
        f"found targets: {phony_targets!r}"
    )


def test_phony_declares_clean_python_protos(makefile_text: str):
    """clean_python_protos must appear in a .PHONY declaration."""
    phony_targets: list[str] = []
    for line in makefile_text.splitlines():
        m = re.match(r"^\.PHONY\s*:\s*(.+)", line)
        if m:
            phony_targets.extend(m.group(1).split())
    assert "clean_python_protos" in phony_targets, (
        f"clean_python_protos not found in any .PHONY declaration; "
        f"found targets: {phony_targets!r}"
    )


def test_generate_python_protos_recipe_exists(makefile_text: str):
    """generate_python_protos must be defined as a recipe block (target line + indented commands)."""
    # Look for the target header line followed by at least one tab-indented recipe line.
    pattern = re.compile(
        r"^generate_python_protos\s*:.*\n(?:[ \t]+\S.*\n?)+",
        re.MULTILINE,
    )
    assert pattern.search(makefile_text), (
        "generate_python_protos is declared .PHONY but has no recipe block"
    )


def test_clean_python_protos_recipe_exists(makefile_text: str):
    """clean_python_protos must be defined as a recipe block (target line + indented commands)."""
    pattern = re.compile(
        r"^clean_python_protos\s*:.*\n(?:[ \t]+\S.*\n?)+",
        re.MULTILINE,
    )
    assert pattern.search(makefile_text), (
        "clean_python_protos is declared .PHONY but has no recipe block"
    )
