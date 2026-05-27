"""Tests that the protobuf pin is >=5.29,<6 across all dependency files."""

import re
import tomllib
from pathlib import Path

import pytest


_KNOWN_DEP_FILES = ["requirements.txt", "requirements-test.txt"]
_PROTOBUF_LINE_RE = re.compile(r"^protobuf([^#\n]*)", re.MULTILINE)
_GRPCIO_TOOLS_LINE_RE = re.compile(r"^grpcio-tools([^#\n]*)", re.MULTILINE)
_VERSION_RE = re.compile(r">=(\d+\.\d+)")


def _lower_bound(spec_text: str) -> tuple[int, int] | None:
    """Return the (major, minor) lower bound from a PEP 440 specifier string, or None."""
    m = _VERSION_RE.search(spec_text)
    if not m:
        return None
    major, minor = m.group(1).split(".", 1)
    return int(major), int(minor.split(".")[0])


def _extract_spec(text: str, pkg_re: re.Pattern) -> str | None:
    """Return the full specifier string (everything after the package name) or None."""
    m = pkg_re.search(text)
    return m.group(1).strip() if m else None


@pytest.mark.parametrize("rel_path", _KNOWN_DEP_FILES)
def test_requirements_protobuf_lower_bound(repo_root: Path, rel_path: str):
    """Each requirements file must pin protobuf to >=5.29 after build-cleanup."""
    path = repo_root / rel_path
    assert path.is_file(), f"{rel_path} not found at repo root"
    spec = _extract_spec(path.read_text(encoding="utf-8"), _PROTOBUF_LINE_RE)
    assert spec is not None, (
        f"{rel_path}: no 'protobuf' specifier found — "
        "the build-cleanup PR tightened the lower bound to >=5.29."
    )
    bound = _lower_bound(spec)
    assert bound is not None, f"{rel_path}: cannot parse lower bound from protobuf specifier {spec!r}"
    assert bound >= (5, 29), (
        f"{rel_path}: protobuf lower bound is {bound[0]}.{bound[1]}, expected >=5.29."
    )


def test_pyproject_protobuf_lower_bound(repo_root: Path):
    """pyproject.toml [project].dependencies must pin protobuf to >=5.29 after build-cleanup."""
    path = repo_root / "pyproject.toml"
    assert path.is_file(), "pyproject.toml not found at repo root"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps: list[str] = data.get("project", {}).get("dependencies", [])
    proto_dep = next((d for d in deps if d.startswith("protobuf")), None)
    assert proto_dep is not None, "pyproject.toml [project].dependencies has no 'protobuf' entry"
    bound = _lower_bound(proto_dep)
    assert bound is not None, f"pyproject.toml: cannot parse lower bound from {proto_dep!r}"
    assert bound >= (5, 29), (
        f"pyproject.toml: protobuf lower bound is {bound[0]}.{bound[1]}, expected >=5.29."
    )


def test_protobuf_spec_consistent_across_dep_files(repo_root: Path):
    """protobuf specifier must be identical across pyproject.toml and requirements files.

    A contributor bumping the pin in one file without the others will be caught here.
    """
    specs: dict[str, str] = {}

    # pyproject.toml — extract just the version spec portion
    toml_path = repo_root / "pyproject.toml"
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    deps: list[str] = data.get("project", {}).get("dependencies", [])
    proto_dep = next((d for d in deps if d.startswith("protobuf")), None)
    if proto_dep:
        specs["pyproject.toml"] = proto_dep[len("protobuf"):].strip()

    for rel_path in _KNOWN_DEP_FILES:
        path = repo_root / rel_path
        if path.is_file():
            spec = _extract_spec(path.read_text(encoding="utf-8"), _PROTOBUF_LINE_RE)
            if spec is not None:
                specs[rel_path] = spec

    assert len(specs) >= 2, "Expected protobuf spec in at least two dep files"
    unique = set(specs.values())
    assert len(unique) == 1, (
        f"protobuf specifiers are not consistent across dep files:\n"
        + "\n".join(f"  {f}: protobuf{s}" for f, s in sorted(specs.items()))
    )


def test_dep_files_upper_bound_consistent(repo_root: Path):
    """All known dependency files must keep the protobuf upper bound at <6."""
    _UPPER_BOUND_RE = re.compile(r"<(\d+)")

    def _assert_upper_bound(spec: str, label: str) -> None:
        m = _UPPER_BOUND_RE.search(spec)
        assert m and int(m.group(1)) == 6, (
            f"{label}: protobuf specifier {spec!r} is missing or has wrong '<N' upper bound "
            "(expected '<6'). All dep files must agree to stay on the protobuf 5.x series."
        )

    for rel_path in _KNOWN_DEP_FILES:
        path = repo_root / rel_path
        assert path.is_file(), f"{rel_path} not found at repo root"
        spec = _extract_spec(path.read_text(encoding="utf-8"), _PROTOBUF_LINE_RE)
        assert spec is not None, f"{rel_path}: no 'protobuf' specifier found"
        _assert_upper_bound(spec, rel_path)

    toml_path = repo_root / "pyproject.toml"
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    deps: list[str] = data.get("project", {}).get("dependencies", [])
    proto_dep = next((d for d in deps if d.startswith("protobuf")), None)
    assert proto_dep is not None, "pyproject.toml [project].dependencies has no 'protobuf' entry"
    _assert_upper_bound(proto_dep[len("protobuf"):], "pyproject.toml")


def test_grpcio_tools_not_in_runtime_requirements(repo_root: Path):
    """grpcio-tools must NOT appear in requirements.txt or pyproject.toml dependencies.

    grpcio-tools is a generation-time tool only. If it leaks into the runtime dep
    list, consumers pay a heavy grpcio install (>50 MB) for something only needed
    during proto regeneration.
    """
    for rel_path in ["requirements.txt"]:
        path = repo_root / rel_path
        text = path.read_text(encoding="utf-8")
        assert "grpcio-tools" not in text, (
            f"{rel_path}: 'grpcio-tools' must not appear in runtime dependencies — "
            "it is a generation-time tool and belongs only in requirements-test.txt."
        )

    toml_path = repo_root / "pyproject.toml"
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    deps: list[str] = data.get("project", {}).get("dependencies", [])
    assert not any("grpcio-tools" in d for d in deps), (
        "pyproject.toml [project].dependencies must not include 'grpcio-tools' — "
        "it is a generation-time tool only."
    )


def test_grpcio_tools_lower_bound(repo_root: Path):
    """requirements-test.txt must pin grpcio-tools to >=1.69.

    grpcio-tools 1.69 bundles libprotoc 29.0 (5.29.x) — the version that emits the
    committed gencode. A lower bound of <1.69 allows regeneration with a stale protoc
    that produces 5.28.x gencode, breaking test_pb2_gencode_version_at_least_5_29.
    """
    path = repo_root / "requirements-test.txt"
    assert path.is_file(), "requirements-test.txt not found at repo root"
    spec = _extract_spec(path.read_text(encoding="utf-8"), _GRPCIO_TOOLS_LINE_RE)
    assert spec is not None, "requirements-test.txt: no 'grpcio-tools' specifier found"
    bound = _lower_bound(spec)
    assert bound is not None, f"requirements-test.txt: cannot parse lower bound from grpcio-tools specifier {spec!r}"
    assert bound >= (1, 69), (
        f"requirements-test.txt: grpcio-tools lower bound is {bound[0]}.{bound[1]}, "
        "expected >=1.69 (the version that bundles libprotoc 29.0 / 5.29.x)."
    )
