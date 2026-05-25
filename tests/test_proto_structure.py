"""Baseline structural tests over every .proto file under common/."""

import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _imports_from_text(text: str) -> list[str]:
    """Return the list of quoted paths from all import "..." statements."""
    return re.findall(r'^import\s+"([^"]+)"', text, re.MULTILINE)


def _enum_blocks(text: str) -> list[tuple[str, str]]:
    """Return list of (enum_name, enum_body) pairs parsed from proto text."""
    # Capture enum Name { ... } blocks (non-nested; proto3 top-level enums)
    pattern = re.compile(r'\benum\s+(\w+)\s*\{([^}]*)\}', re.DOTALL)
    return [(m.group(1), m.group(2)) for m in pattern.finditer(text)]


def _has_zero_value_entry(enum_body: str) -> bool:
    """Return True if the enum body contains at least one entry assigned = 0."""
    return bool(re.search(r'\w+\s*=\s*0\s*;', enum_body))


# ---------------------------------------------------------------------------
# Parametrised collection — one test per .proto file
# ---------------------------------------------------------------------------

def pytest_generate_tests(metafunc):
    """Dynamically parametrise tests that accept `proto_path`."""
    if "proto_path" in metafunc.fixturenames:
        repo_root = Path(__file__).parent.parent
        proto_paths = sorted(repo_root.joinpath("common").rglob("*.proto"))
        metafunc.parametrize(
            "proto_path",
            proto_paths,
            ids=[str(p.relative_to(repo_root)) for p in proto_paths],
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_proto_syntax_is_proto3(proto_path: Path):
    """Every .proto file must declare syntax = "proto3";."""
    text = proto_path.read_text(encoding="utf-8")
    if not text.strip():
        pytest.skip(f"{proto_path.name} is empty (stub)")
    assert re.search(r'^syntax\s*=\s*"proto3"\s*;', text, re.MULTILINE), (
        f"{proto_path}: missing or wrong syntax declaration"
    )


def test_proto_package_is_oets_v1(proto_path: Path):
    """Every .proto file must declare package oets.v1;."""
    text = proto_path.read_text(encoding="utf-8")
    if not text.strip():
        pytest.skip(f"{proto_path.name} is empty (stub)")
    assert re.search(r'^package\s+oets\.v1\s*;', text, re.MULTILINE), (
        f"{proto_path}: missing or wrong package declaration"
    )


def test_proto_imports_resolve(proto_path: Path):
    """Every import path in a .proto file must resolve to an existing file.

    Imports under google/protobuf/ are Google well-known types — they are
    not checked in to this repository but are always available at compile
    time via the protoc / grpc_tools include path. We skip resolution checks
    for those prefixes and only verify project-local imports.
    """
    repo_root = Path(__file__).parent.parent
    text = proto_path.read_text(encoding="utf-8")
    if not text.strip():
        pytest.skip(f"{proto_path.name} is empty (stub)")
    imports = _imports_from_text(text)
    # Google well-known types (google/protobuf/...) are resolved by protoc
    # from its built-in include path, not from the repo root — skip them.
    project_imports = [imp for imp in imports if not imp.startswith("google/protobuf/")]
    missing = [imp for imp in project_imports if not (repo_root / imp).is_file()]
    assert not missing, (
        f"{proto_path.relative_to(repo_root)}: unresolvable imports: {missing}"
    )


def test_proto_enums_have_zero_value(proto_path: Path):
    """Every enum in a .proto file must have at least one entry assigned to 0."""
    text = proto_path.read_text(encoding="utf-8")
    if not text.strip():
        pytest.skip(f"{proto_path.name} is empty (stub)")
    enums = _enum_blocks(text)
    if not enums:
        pytest.skip(f"{proto_path.name} contains no enum definitions")
    bad = [name for name, body in enums if not _has_zero_value_entry(body)]
    assert not bad, (
        f"{proto_path}: enums missing a zero-value entry: {bad}. "
        "Proto3 requires the first enum value to be 0."
    )
