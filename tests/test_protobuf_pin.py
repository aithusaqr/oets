"""Tests that the protobuf pin is >=5.29,<6 across all dependency files."""

import re
import tomllib
from pathlib import Path

import pytest


_DEP_FILES = ["requirements.txt", "requirements-test.txt"]
_PROTOBUF_LINE_RE = re.compile(r"^protobuf([^#\n]*)", re.MULTILINE)
_VERSION_RE = re.compile(r">=(\d+\.\d+)")


def _protobuf_lower_bound(text: str) -> tuple[int, int] | None:
    """Return the (major, minor) lower bound parsed from a protobuf specifier line, or None."""
    m = _PROTOBUF_LINE_RE.search(text)
    if not m:
        return None
    spec = m.group(1)
    vm = _VERSION_RE.search(spec)
    if not vm:
        return None
    major, minor = vm.group(1).split(".", 1)
    return int(major), int(minor.split(".")[0])


@pytest.mark.parametrize("rel_path", _DEP_FILES)
def test_requirements_protobuf_lower_bound(repo_root: Path, rel_path: str):
    """Each requirements file must pin protobuf to >=5.29 after build-cleanup."""
    path = repo_root / rel_path
    assert path.is_file(), f"{rel_path} not found at repo root"
    text = path.read_text(encoding="utf-8")
    bound = _protobuf_lower_bound(text)
    assert bound is not None, (
        f"{rel_path}: no 'protobuf>=' specifier found — "
        "the build-cleanup PR tightened the lower bound to >=5.29 to match the "
        "gencode emitted by grpc_tools 1.69 (bundled protoc 29.0 / 5.29.x)."
    )
    assert bound >= (5, 29), (
        f"{rel_path}: protobuf lower bound is {bound[0]}.{bound[1]}, expected >=5.29. "
        "The build-cleanup PR bumped this to match the grpc_tools-regenerated gencode."
    )


def test_pyproject_protobuf_lower_bound(repo_root: Path):
    """pyproject.toml [project].dependencies must pin protobuf to >=5.29 after build-cleanup."""
    path = repo_root / "pyproject.toml"
    assert path.is_file(), "pyproject.toml not found at repo root"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps: list[str] = data.get("project", {}).get("dependencies", [])
    proto_dep = next((d for d in deps if d.startswith("protobuf")), None)
    assert proto_dep is not None, (
        "pyproject.toml [project].dependencies has no 'protobuf' entry"
    )
    bound = _protobuf_lower_bound(proto_dep)
    assert bound is not None, (
        f"pyproject.toml: could not parse lower bound from {proto_dep!r}"
    )
    assert bound >= (5, 29), (
        f"pyproject.toml: protobuf lower bound is {bound[0]}.{bound[1]}, expected >=5.29. "
        "The build-cleanup PR bumped this to match the grpc_tools-regenerated gencode."
    )


def test_dep_files_upper_bound_consistent(repo_root: Path):
    """All dependency files must keep the protobuf upper bound at <6."""
    files = _DEP_FILES + ["pyproject.toml"]
    for rel_path in files:
        path = repo_root / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "protobuf" not in text:
            continue
        assert "<6" in text, (
            f"{rel_path}: protobuf specifier is missing '<6' upper bound. "
            "All dep files must agree to stay on the protobuf 5.x series."
        )
