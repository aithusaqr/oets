"""Tests for Makefile L2 invariants — generate_python_protos recipe cleanup."""

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def makefile_text(repo_root: Path) -> str:
    makefile = repo_root / "Makefile"
    assert makefile.is_file(), "Makefile does not exist at repo root"
    return makefile.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def recipe_block(makefile_text: str) -> str:
    """Extract the generate_python_protos recipe block (tab-indented lines only)."""
    pattern = re.compile(
        r"^generate_python_protos\s*:.*\n((?:[ \t]+.*\n?)*)",
        re.MULTILINE,
    )
    m = pattern.search(makefile_text)
    assert m, (
        "Makefile: generate_python_protos recipe block not found; "
        "cannot validate L2 invariants"
    )
    return m.group(1)


def test_recipe_has_no_pythonpath_inline(recipe_block: str):
    """The generate_python_protos recipe must NOT contain an inline PYTHONPATH= assignment.

    The dead-code shell prefix ``PYTHONPATH=$(PYTHONPATH):...&&\\`` was removed in L2.
    Finding it now means the cleanup was reverted.
    """
    assert "PYTHONPATH=" not in recipe_block, (
        "Makefile generate_python_protos recipe still contains an inline "
        "'PYTHONPATH=' assignment — this dead-code shell prefix should have "
        "been removed by L2 (fix/15-makefile-cleanup)."
    )


def test_recipe_touches_generated_python_init(recipe_block: str):
    """The generate_python_protos recipe must contain a 'touch' for the top-level __init__.py.

    L2 added ``touch $(OUT)/__init__.py`` so that generated/python/ itself is
    an importable Python package.  Accept either the variable form $(OUT) or
    the resolved literal path.
    """
    pattern = re.compile(
        r"touch\s+(\$\(OUT\)|generated/python)/__init__\.py"
    )
    assert pattern.search(recipe_block), (
        "Makefile generate_python_protos recipe is missing "
        "'touch $(OUT)/__init__.py' (or equivalent resolved path). "
        "L2 requires this line so that generated/python/ is an importable "
        "Python package."
    )


def test_recipe_no_stray_backslash_before_pythonpath_line(recipe_block: str):
    """The 'rm -rf $(OUT)' line must be a clean one-liner with no trailing backslash.

    In the old (pre-L2) recipe the rm line was part of a multi-line shell
    concatenation joined with '\\'.  L2 broke each shell command onto its own
    tab-indented recipe line, so the rm line must NOT end with a continuation.
    """
    for line in recipe_block.splitlines():
        stripped = line.rstrip()
        if re.search(r"rm\s+-rf\s+\$\(OUT\)", stripped):
            assert not stripped.endswith("\\"), (
                f"Makefile generate_python_protos: the 'rm -rf $(OUT)' recipe line "
                f"still ends with a line-continuation backslash: {stripped!r}. "
                "L2 requires each shell command to be a standalone recipe line."
            )
            return  # found and validated — done
    pytest.fail(
        "Makefile generate_python_protos: expected a recipe line containing "
        "'rm -rf $(OUT)' but none was found."
    )
