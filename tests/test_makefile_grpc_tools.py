"""Tests that generate_python_protos uses python -m grpc_tools.protoc (not bare protoc)."""

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def recipe_block(repo_root: Path) -> str:
    """Extract the generate_python_protos recipe block (tab-indented lines)."""
    makefile = repo_root / "Makefile"
    assert makefile.is_file(), "Makefile does not exist at repo root"
    text = makefile.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^generate_python_protos\s*:.*\n((?:[ \t]+.*\n?)*)",
        re.MULTILINE,
    )
    m = pattern.search(text)
    assert m, "generate_python_protos recipe block not found in Makefile"
    return m.group(1)


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
