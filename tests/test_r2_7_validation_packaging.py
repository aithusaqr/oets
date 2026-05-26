"""Tests for R2-7 (#26): expose validation/ in pyproject.toml setuptools config."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_pyproject() -> dict:
    """Parse pyproject.toml using tomllib (stdlib in 3.11+) or tomli fallback."""
    try:
        import tomllib  # type: ignore[import]
    except ImportError:
        import tomli as tomllib  # type: ignore[import]
    with open(PYPROJECT_PATH, "rb") as fh:
        return tomllib.load(fh)


# ---------------------------------------------------------------------------
# 1. build-system declared correctly
# ---------------------------------------------------------------------------

def test_pyproject_declares_setuptools_build_system():
    """pyproject.toml must declare setuptools.build_meta as the build backend."""
    data = _load_pyproject()
    assert "build-system" in data, (
        "pyproject.toml is missing a [build-system] table. "
        "PEP 517 build tools need an explicit backend declaration."
    )
    backend = data["build-system"].get("build-backend")
    assert backend == "setuptools.build_meta", (
        "Expected build-backend = 'setuptools.build_meta', got: " + repr(backend)
    )
    requires = data["build-system"].get("requires", [])
    assert any("setuptools" in r for r in requires), (
        "[build-system].requires must list setuptools. Got: " + repr(requires)
    )


# ---------------------------------------------------------------------------
# 2. [tool.setuptools].packages lists validation
# ---------------------------------------------------------------------------

def test_pyproject_declares_setuptools_packages():
    """[tool.setuptools].packages must be a non-empty list containing 'validation'."""
    data = _load_pyproject()
    tool_setuptools = data.get("tool", {}).get("setuptools", {})
    assert "packages" in tool_setuptools, (
        "pyproject.toml is missing [tool.setuptools].packages. "
        "Setuptools auto-discovery cannot find 'validation/' in a multi-directory repo."
    )
    packages = tool_setuptools["packages"]
    assert isinstance(packages, list) and len(packages) > 0, (
        "[tool.setuptools].packages must be a non-empty list, got: " + repr(packages)
    )
    assert "validation" in packages, (
        "'validation' is not listed in [tool.setuptools].packages. "
        "Found: " + repr(packages)
    )


# ---------------------------------------------------------------------------
# 3. validation package is importable at runtime (layout regression guard)
# ---------------------------------------------------------------------------

def test_validation_package_importable():
    """validation.oets_version must be importable and functionally correct."""
    from validation.oets_version import (  # type: ignore[import]
        OETS_VERSION_REGEX,
        is_valid_oets_version,
        parse_oets_version,
    )

    # Basic functional checks — these guard against accidental regressions.
    assert is_valid_oets_version("1.2.3") is True, (
        "is_valid_oets_version('1.2.3') should return True"
    )
    assert is_valid_oets_version("not-a-version") is False, (
        "is_valid_oets_version('not-a-version') should return False"
    )

    parsed = parse_oets_version("2.0.0")
    assert parsed is not None, "parse_oets_version('2.0.0') should not return None"

    import re
    assert isinstance(OETS_VERSION_REGEX, (str, re.Pattern)), (
        "OETS_VERSION_REGEX should be a string or compiled Pattern"
    )


# ---------------------------------------------------------------------------
# 4. Built wheel contains validation/ (proves pip install will work)
# ---------------------------------------------------------------------------

def test_build_artifacts_contain_validation(tmp_path):
    """Building a wheel from the repo must include validation/oets_version.py."""
    # Skip if the `build` package is not installed.
    try:
        import build  # type: ignore[import]  # noqa: F401
    except ImportError:
        pytest.skip(
            "The 'build' package is not installed. "
            "Install it with `pip install build` to enable this test."
        )

    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "wheel build failed.\n"
        "STDOUT:\n" + result.stdout + "\n"
        "STDERR:\n" + result.stderr
    )

    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, (
        "Expected exactly 1 wheel in output dir, found: " + repr([w.name for w in wheels])
    )

    wheel_path = wheels[0]
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()

    validation_files = [n for n in names if n.startswith("validation/")]
    assert len(validation_files) > 0, (
        "Wheel " + wheel_path.name + " contains no files under validation/. "
        "Contents: " + repr(names)
    )
    assert "validation/oets_version.py" in validation_files, (
        "validation/oets_version.py is missing from the wheel. "
        "validation/ contents: " + repr(validation_files)
    )

    # Confirm unwanted directories are absent.
    for unwanted_prefix in ("common/", "generated/"):
        unwanted = [n for n in names if n.startswith(unwanted_prefix)]
        assert len(unwanted) == 0, (
            "Wheel should not contain '" + unwanted_prefix + "' files; "
            "found: " + repr(unwanted)
        )
