"""R3-6: Verify that the CI workflow uses a Python version matrix.

Guards:
- strategy.matrix structure exists and is a dict
- matrix.python-version is a non-empty list
- setup-python step uses the template expression (not a hard-coded version)
- matrix minimum version matches requires-python floor
- fail-fast is explicitly false
"""

import re
import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci_yaml() -> dict:
    with CI_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_ci_text() -> str:
    return CI_PATH.read_text(encoding="utf-8")


def _load_pyproject() -> dict:
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def test_ci_workflow_has_strategy_matrix():
    """jobs.ci.strategy.matrix must exist and be a dict."""
    workflow = _load_ci_yaml()
    ci_job = workflow.get("jobs", {}).get("ci")
    assert ci_job is not None, (
        "jobs.ci not found in ci.yml — expected a job named 'ci'"
    )
    strategy = ci_job.get("strategy")
    assert strategy is not None, (
        "jobs.ci.strategy is missing from ci.yml — add a strategy block with a matrix"
    )
    matrix = strategy.get("matrix")
    assert isinstance(matrix, dict), (
        f"jobs.ci.strategy.matrix must be a dict; got {type(matrix).__name__!r}"
    )


def test_ci_matrix_lists_python_versions():
    """matrix.python-version must be a non-empty list of version strings."""
    workflow = _load_ci_yaml()
    matrix = workflow["jobs"]["ci"]["strategy"]["matrix"]
    versions = matrix.get("python-version")
    assert isinstance(versions, list), (
        f"matrix.python-version must be a list; got {type(versions).__name__!r}"
    )
    assert len(versions) > 0, (
        "matrix.python-version is an empty list — add at least one Python version"
    )
    for v in versions:
        assert re.match(r"^\d+\.\d+$", str(v)), (
            f"matrix.python-version entry {v!r} is not in 'MAJOR.MINOR' form"
        )


def test_ci_matrix_uses_template_var():
    """The setup-python step must use the matrix template expression, not a hard-coded version."""
    ci_text = _load_ci_text()
    # The with.python-version value must be the template expression.
    assert re.search(
        r"python-version:\s*\$\{\{\s*matrix\.python-version\s*\}\}", ci_text
    ), (
        "setup-python step's python-version is not set to "
        "'${{ matrix.python-version }}' — hard-coded versions defeat the matrix"
    )


def test_ci_matrix_covers_requires_python_floor():
    """The lowest version in the CI matrix must equal the requires-python floor.

    If requires-python = '>=3.11', the matrix must include 3.11 as its minimum
    so that the declared floor is actually exercised in CI.
    """
    data = _load_pyproject()
    spec = data.get("project", {}).get("requires-python", "")
    assert spec, "pyproject.toml [project].requires-python is missing"

    floor_match = re.search(r">=\s*3\.(\d+)", spec)
    assert floor_match, (
        f"Cannot parse a >= lower bound from requires-python = '{spec}'"
    )
    floor_minor = int(floor_match.group(1))

    workflow = _load_ci_yaml()
    versions = workflow["jobs"]["ci"]["strategy"]["matrix"]["python-version"]
    matrix_minors = [int(str(v).split(".")[1]) for v in versions]
    min_matrix_minor = min(matrix_minors)

    assert min_matrix_minor == floor_minor, (
        f"CI matrix minimum is Python 3.{min_matrix_minor} but "
        f"requires-python = '{spec}' declares a floor of 3.{floor_minor}. "
        "The matrix minimum must equal the requires-python floor so the "
        "declared minimum is actually validated in CI."
    )


def test_fail_fast_false():
    """strategy.fail-fast must be explicitly false.

    With fail-fast: false all matrix cells complete even when one fails,
    giving a complete diagnostic picture across all supported Python versions.
    """
    workflow = _load_ci_yaml()
    strategy = workflow["jobs"]["ci"]["strategy"]
    # PyYAML parses 'false' as the Python bool False.
    fail_fast = strategy.get("fail-fast")
    assert fail_fast is not None, (
        "strategy.fail-fast is not set in ci.yml — "
        "add 'fail-fast: false' so all matrix cells always run to completion"
    )
    assert fail_fast is False, (
        f"strategy.fail-fast must be false (bool); got {fail_fast!r}. "
        "Set 'fail-fast: false' so every matrix cell reports its result."
    )
