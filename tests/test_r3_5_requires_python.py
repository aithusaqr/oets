"""
R3-5: Verify that pyproject.toml's requires-python honestly reflects what the
project actually needs (>=3.11, because tomllib is stdlib only from 3.11).

Catches future drift between the declared minimum and CI's python-version.
"""

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def _load_pyproject() -> dict:
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def _load_ci_yaml_text() -> str:
    return (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()


def test_pyproject_requires_python_311_or_higher():
    """requires-python must declare >=3.11 (tomllib is 3.11+ only)."""
    data = _load_pyproject()
    spec = data.get("project", {}).get("requires-python", "")
    assert spec, "pyproject.toml [project].requires-python is missing"

    # Reject any spec whose lower bound is < 3.11.
    # We look for patterns like >=3.10 or >=3.9 etc.
    too_low = re.search(r">=\s*3\.([0-9]+)", spec)
    if too_low:
        minor = int(too_low.group(1))
        assert minor >= 11, (
            f"requires-python = '{spec}' allows Python 3.{minor}, but "
            "tests/test_buf_config.py and tests/test_r2_7_validation_packaging.py "
            "import tomllib which is only available in Python 3.11+. "
            "Set requires-python = '>=3.11'."
        )

    # Also accept exact pins like ==3.11, ~=3.11, but reject anything <3.11.
    # A simple sanity check: the spec must contain '3.11' or higher.
    version_refs = re.findall(r"3\.(\d+)", spec)
    assert version_refs, (
        f"requires-python = '{spec}' contains no recognisable 3.x version reference"
    )
    lowest = min(int(m) for m in version_refs)
    assert lowest >= 11, (
        f"requires-python = '{spec}' references Python 3.{lowest} which is below "
        "the project's actual minimum of 3.11 (tomllib dependency)."
    )


def test_ci_python_version_matches_requires_python():
    """The minimum Python version in the CI matrix must satisfy requires-python.

    After R3-6 CI uses a strategy matrix; we collect all version entries and
    assert the lowest one matches (or exceeds) the requires-python floor.
    """
    data = _load_pyproject()
    spec = data.get("project", {}).get("requires-python", "")
    assert spec, "pyproject.toml [project].requires-python is missing"

    # Extract the floor from requires-python (e.g. ">=3.11" -> 11).
    floor_match = re.search(r">=\s*3\.(\d+)", spec)
    assert floor_match, (
        f"Cannot parse a >= lower bound from requires-python = '{spec}'"
    )
    floor_minor = int(floor_match.group(1))

    ci_text = _load_ci_yaml_text()
    # Collect all 3.x version entries from the YAML text.  This covers both the
    # old single-version form ("3.11") and new matrix list entries ('3.11').
    ci_versions = re.findall(r'["\']3\.(\d+)["\']', ci_text)
    assert ci_versions, (
        "Could not find any python-version entries in "
        ".github/workflows/ci.yml — expected at least one '3.x' value"
    )

    ci_minors = [int(m) for m in ci_versions]
    min_ci_minor = min(ci_minors)

    assert min_ci_minor >= floor_minor, (
        f"CI matrix minimum is Python 3.{min_ci_minor} but "
        f"requires-python = '{spec}' demands >=3.{floor_minor}. "
        "Update pyproject.toml or the CI matrix so they agree."
    )


def test_tomllib_imported_correctly():
    """
    Every test file that imports tomllib must do so directly (no try/except
    fallback to tomli), because we are committed to Python 3.11+ where tomllib
    is stdlib.
    """
    tests_dir = REPO_ROOT / "tests"
    this_file = Path(__file__).name
    files_with_tomllib = [
        p for p in tests_dir.glob("*.py")
        if p.name != this_file and "tomllib" in p.read_text()
    ]

    assert files_with_tomllib, (
        "Expected at least one test file to import tomllib — did all tests move?"
    )

    for path in files_with_tomllib:
        source = path.read_text()
        # Detect try/except fallback pattern: `import tomllib` inside a try block
        # alongside `import tomli` as fallback.
        has_fallback = bool(
            re.search(r"import\s+tomllib", source)
            and re.search(r"import\s+tomli\b", source)
        )
        assert not has_fallback, (
            f"{path.name} uses a tomllib/tomli fallback import, which implies "
            "support for Python <3.11. The project requires >=3.11; remove the "
            "fallback and import tomllib directly."
        )
