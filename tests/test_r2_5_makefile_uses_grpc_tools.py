"""Tests for R2-5 invariants — generate_python_protos uses grpc_tools.protoc."""

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
        "cannot validate R2-5 invariants"
    )
    return m.group(1)


def test_recipe_uses_grpc_tools_protoc(recipe_block: str):
    """The generate_python_protos recipe must invoke grpc_tools.protoc.

    R2-5 switches from bare `protoc` to `python -m grpc_tools.protoc` so that
    the bundled protoc 29.x is used, which produces gencode 5.x compatible with
    the pinned protobuf>=5.29,<6 runtime.
    """
    assert "grpc_tools" in recipe_block, (
        "Makefile generate_python_protos recipe does not invoke grpc_tools.protoc. "
        "R2-5 requires `python -m grpc_tools.protoc` (not bare `protoc`) so that "
        "bundled protoc 29.x produces gencode 5.x matching our pinned runtime. "
        "Found recipe block:\n" + recipe_block
    )


def test_recipe_does_not_use_bare_protoc(recipe_block: str):
    """The generate_python_protos recipe must NOT contain a bare `protoc` invocation.

    A bare `protoc \\` line (system protoc) silently produces gencode 7.x on
    modern systems (protoc 35+), which is incompatible with protobuf>=5.29,<6.
    Only `python -m grpc_tools.protoc` (or similar grpc_tools-prefixed call)
    is allowed.
    """
    # Match lines where `protoc` appears NOT immediately preceded by `grpc_tools.`
    # e.g. catches `\tprotoc \` but not `grpc_tools.protoc`
    bare_protoc_pattern = re.compile(
        r"^\s+(?!.*grpc_tools\.).*\bprotoc\b",
        re.MULTILINE,
    )
    matches = bare_protoc_pattern.findall(recipe_block)
    assert not matches, (
        "Makefile generate_python_protos recipe contains a bare `protoc` invocation "
        "not routed through grpc_tools. This silently produces gencode 7.x on "
        "protoc 35+, breaking the pinned protobuf>=5.29,<6 runtime (see #24). "
        "Offending lines: " + repr(matches)
    )


def test_recipe_comment_mentions_compatibility(makefile_text: str):
    """A comment immediately before generate_python_protos: must document the rationale.

    The block comment should reference grpcio-tools, protoc 35, or gencode so that
    developers understand why bare `protoc` is not used.
    """
    # Extract any comment lines that appear just before the recipe target
    pattern = re.compile(
        r"((?:^#[^\n]*\n)+)^generate_python_protos\s*:",
        re.MULTILINE,
    )
    m = pattern.search(makefile_text)
    assert m, (
        "Makefile: no comment block found immediately before `generate_python_protos:`. "
        "R2-5 requires a leading comment documenting why grpcio-tools is used. "
        "Add a `# Requires: grpcio-tools ...` comment."
    )
    comment_block = m.group(1)
    keywords = ["grpc_tools", "grpcio-tools", "protoc 35", "gencode"]
    assert any(kw in comment_block for kw in keywords), (
        "Makefile comment before generate_python_protos: does not mention any of "
        + str(keywords)
        + ". The comment should explain the grpcio-tools requirement and protoc "
        "compatibility constraint (see #24). Found comment:\n" + comment_block
    )


def test_requirements_test_pins_grpcio_tools():
    """requirements-test.txt must list grpcio-tools.

    grpcio-tools is the dev dependency that provides `python -m grpc_tools.protoc`.
    It was previously added ad-hoc by agents; R2-5 ensures it is pinned so CI
    and fresh dev environments install it reliably.
    """
    req_file = Path(__file__).parent.parent / "requirements-test.txt"
    assert req_file.is_file(), (
        f"requirements-test.txt not found at {req_file}. "
        "This file must exist and list grpcio-tools."
    )
    content = req_file.read_text(encoding="utf-8")
    assert "grpcio-tools" in content, (
        "requirements-test.txt does not list grpcio-tools. "
        "R2-5 requires this entry so that `make generate_python_protos` "
        "works after a fresh `pip install -r requirements-test.txt`. "
        "Add `grpcio-tools>=1.60` (or a tighter bound) to the file."
    )
