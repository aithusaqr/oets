"""Tests that generate_python_protos uses python -m grpc_tools.protoc (not bare protoc)."""

import re
from pathlib import Path

import pytest


def _extract_recipe(makefile_text: str, target: str) -> str:
    """Return the tab-indented recipe block for the given Makefile target."""
    pattern = re.compile(
        rf"^{re.escape(target)}\s*:.*\n((?:[ \t]+.*\n?)*)",
        re.MULTILINE,
    )
    m = pattern.search(makefile_text)
    assert m, f"'{target}' recipe block not found in Makefile"
    return m.group(1)


@pytest.fixture(scope="module")
def makefile_text(repo_root: Path) -> str:
    makefile = repo_root / "Makefile"
    assert makefile.is_file(), "Makefile does not exist at repo root"
    return makefile.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def recipe_block(makefile_text: str) -> str:
    return _extract_recipe(makefile_text, "generate_python_protos")


@pytest.fixture(scope="module")
def clean_recipe_block(makefile_text: str) -> str:
    return _extract_recipe(makefile_text, "clean_python_protos")


def test_recipe_uses_grpc_tools_protoc(recipe_block: str):
    """generate_python_protos must invoke python -m grpc_tools.protoc, not bare protoc."""
    assert "python -m grpc_tools.protoc" in recipe_block, (
        "Makefile generate_python_protos recipe does not call "
        "'python -m grpc_tools.protoc'. "
        "The build-cleanup PR switched generation from bare 'protoc' to the "
        "grpc_tools-bundled compiler so that generation is reproducible from "
        "requirements-test.txt alone, without a separately installed protoc."
    )


def test_recipe_does_not_use_bare_protoc(recipe_block: str):
    """generate_python_protos must NOT invoke bare protoc (only python -m grpc_tools.protoc)."""
    for line in recipe_block.splitlines():
        # Strip the grpc_tools invocation first, then check what's left for bare protoc.
        remainder = line.replace("python -m grpc_tools.protoc", "")
        if re.search(r"(?<![.\w])protoc(?![\w.])", remainder):
            pytest.fail(
                f"Makefile generate_python_protos recipe contains a bare 'protoc' "
                f"invocation: {line.strip()!r}\n"
                "Only 'python -m grpc_tools.protoc' is allowed after the build-cleanup PR."
            )


def test_recipe_has_python_out_flag(recipe_block: str):
    """generate_python_protos must pass --python_out to direct output to $(OUT)."""
    assert "--python_out=" in recipe_block, (
        "Makefile generate_python_protos recipe is missing '--python_out=' flag. "
        "Without it grpc_tools.protoc has nowhere to write the generated files."
    )


def test_recipe_has_include_flag(recipe_block: str):
    """generate_python_protos must pass an -I include path so proto imports resolve."""
    assert re.search(r"-I\s+\S", recipe_block), (
        "Makefile generate_python_protos recipe is missing an '-I <path>' include flag. "
        "Without it cross-proto imports (e.g. 'common/event_envelope.proto') will fail."
    )


def test_clean_removes_out_root(clean_recipe_block: str):
    """clean_python_protos must rm -rf $(OUT), not just $(OUT)/common.

    The prior implementation only removed $(OUT)/common, leaving $(OUT)/__init__.py
    behind on a clean → generate cycle. The build-cleanup PR fixed this to rm -rf $(OUT).
    A revert to $(OUT)/common would silently leave stale files in the tree.
    """
    assert "rm -rf $(OUT)" in clean_recipe_block, (
        "clean_python_protos recipe does not contain 'rm -rf $(OUT)'. "
        "It must remove the entire output directory, not just $(OUT)/common."
    )
    assert "$(OUT)/common" not in clean_recipe_block, (
        "clean_python_protos recipe still references '$(OUT)/common'. "
        "It should rm -rf the full $(OUT) directory."
    )
