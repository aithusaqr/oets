"""R3-2: Verify that the protobuf pin is >=5.29,<6 across all three dependency files
and that the lower bound is consistent with the gencode version in the committed _pb2 files.
"""
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _get_protobuf_line_from_requirements(path: Path) -> str:
    """Return the first line in *path* that begins with 'protobuf'."""
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("protobuf"):
            return stripped
    raise AssertionError(f"No protobuf line found in {path}")


def test_requirements_pins_protobuf_5_29() -> None:
    line = _get_protobuf_line_from_requirements(REPO_ROOT / "requirements.txt")
    assert "5.29" in line, (
        f"requirements.txt protobuf line does not contain '5.29': {line!r}"
    )
    assert "<6" in line, (
        f"requirements.txt protobuf line does not contain upper bound '<6': {line!r}"
    )


def test_requirements_test_pins_protobuf_5_29() -> None:
    line = _get_protobuf_line_from_requirements(REPO_ROOT / "requirements-test.txt")
    assert "5.29" in line, (
        f"requirements-test.txt protobuf line does not contain '5.29': {line!r}"
    )
    assert "<6" in line, (
        f"requirements-test.txt protobuf line does not contain upper bound '<6': {line!r}"
    )


def test_pyproject_pins_protobuf_5_29() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    deps: list[str] = data["project"]["dependencies"]
    protobuf_entries = [d for d in deps if d.startswith("protobuf")]
    assert protobuf_entries, "No protobuf entry found in [project].dependencies in pyproject.toml"
    entry = protobuf_entries[0]
    assert "5.29" in entry, (
        f"pyproject.toml protobuf dependency does not contain '5.29': {entry!r}"
    )
    assert "<6" in entry, (
        f"pyproject.toml protobuf dependency does not contain upper bound '<6': {entry!r}"
    )


def _extract_specifier(raw: str) -> str:
    """Strip the leading 'protobuf' package name and return only the version specifier."""
    return raw.removeprefix("protobuf").strip()


def test_all_three_pins_match() -> None:
    req_spec = _extract_specifier(
        _get_protobuf_line_from_requirements(REPO_ROOT / "requirements.txt")
    )
    req_test_spec = _extract_specifier(
        _get_protobuf_line_from_requirements(REPO_ROOT / "requirements-test.txt")
    )
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    deps: list[str] = data["project"]["dependencies"]
    protobuf_entries = [d for d in deps if d.startswith("protobuf")]
    assert protobuf_entries, "No protobuf entry found in pyproject.toml [project].dependencies"
    pyproject_spec = _extract_specifier(protobuf_entries[0])

    assert req_spec == req_test_spec == pyproject_spec, (
        "Protobuf version specifiers are out of sync across files:\n"
        "  requirements.txt:      protobuf" + req_spec + "\n"
        "  requirements-test.txt: protobuf" + req_test_spec + "\n"
        "  pyproject.toml:        protobuf" + pyproject_spec
    )


def test_pin_matches_pb2_gencode_version() -> None:
    # Locate one _pb2.py to extract the gencode minor version.
    pb2_files = list((REPO_ROOT / "generated" / "python").rglob("*_pb2.py"))
    assert pb2_files, (
        "No _pb2.py files found under generated/python — cannot verify gencode version"
    )
    pb2_source = pb2_files[0].read_text()

    # Match: ValidateProtobufRuntimeVersion(
    #     _runtime_version.Domain.PUBLIC,
    #     5,
    #     29,   <-- minor
    match = re.search(
        r"ValidateProtobufRuntimeVersion\(\s*"
        r"_runtime_version\.Domain\.PUBLIC,\s*"
        r"\d+,\s*"        # major
        r"(\d+),",        # minor (captured)
        pb2_source,
    )
    assert match, (
        "Could not parse ValidateProtobufRuntimeVersion call in "
        + str(pb2_files[0])
    )
    gencode_minor = int(match.group(1))

    # The lower-bound minor in requirements.txt must be <= gencode_minor so that the
    # minimum installable version still satisfies runtime.minor >= gencode.minor.
    req_line = _get_protobuf_line_from_requirements(REPO_ROOT / "requirements.txt")
    lower_match = re.search(r">=5\.(\d+)", req_line)
    assert lower_match, (
        "Could not parse lower-bound minor from requirements.txt protobuf line: "
        + repr(req_line)
    )
    pin_minor = int(lower_match.group(1))

    assert pin_minor <= gencode_minor, (
        "Pin lower bound 5." + str(pin_minor) + " is ABOVE gencode version 5."
        + str(gencode_minor) + " — any installed 5."
        + str(pin_minor) + ".x would be rejected by the pb2 runtime check."
    )
    assert pin_minor >= gencode_minor, (
        "Pin lower bound 5." + str(pin_minor) + " is BELOW gencode version 5."
        + str(gencode_minor) + " — installing protobuf==5."
        + str(pin_minor) + ".x satisfies the pin but will fail the pb2 runtime check."
    )
