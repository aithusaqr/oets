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
    """CI's setup-python python-version must satisfy requires-python."""
    data = _load_pyproject()
    spec = data.get("project", {}).get("requires-python", "")
    assert spec, "pyproject.toml [project].requires-python is missing"

    # Extract the floor from requires-python (e.g. ">=3.11" -> (3, 11)).
    floor_match = re.search(r">=\s*3\.(\d+)", spec)
    assert floor_match, (
        f"Cannot parse a >= lower bound from requires-python = '{spec}'"
    )
    floor_minor = int(floor_match.group(1))

    ci_text = _load_ci_yaml_text()
    # Find: python-version: "3.x" or python-version: '3.x'
    ci_match = re.search(r'python-version:\s*["\']3\.(\d+)["\']', ci_text)
    assert ci_match, (
        "Could not find an actions/setup-python python-version field in "
        ".github/workflows/ci.yml"
    )
    ci_minor = int(ci_match.group(1))

    assert ci_minor >= floor_minor, (
        f"CI uses Python 3.{ci_minor} but requires-python = '{spec}' "
        f"demands >=3.{floor_minor}. Update one of them so they agree."
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
