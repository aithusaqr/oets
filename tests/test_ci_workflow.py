"""Tests for L4: GitHub Actions CI workflow structure.

Verifies that .github/workflows/ci.yml exists, is valid YAML, and contains
the expected jobs, steps, and action versions.  The workflow itself is NOT
executed — tests are structural only.
"""

from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def workflow_path(repo_root: Path) -> Path:
    """Path to the CI workflow file."""
    return repo_root / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def workflow(workflow_path: Path) -> dict:
    """Parsed contents of ci.yml."""
    assert workflow_path.is_file(), (
        f"CI workflow not found at {workflow_path}. "
        "Expected .github/workflows/ci.yml to exist."
    )
    with workflow_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def all_steps(workflow: dict) -> list[dict]:
    """Flat list of all step dictionaries across all jobs."""
    steps: list[dict] = []
    for job in workflow.get("jobs", {}).values():
        steps.extend(job.get("steps", []))
    return steps


# ---------------------------------------------------------------------------
# Existence and basic structure
# ---------------------------------------------------------------------------


def test_workflow_file_exists(workflow_path: Path):
    """ci.yml must exist at .github/workflows/ci.yml."""
    assert workflow_path.is_file(), (
        f"Expected .github/workflows/ci.yml to exist at {workflow_path}"
    )


def test_workflow_parses_as_valid_yaml(workflow: dict):
    """ci.yml must be valid YAML (fixture already parses it; just assert non-empty)."""
    assert workflow, "ci.yml parsed as empty/null — check the file contents"


# ---------------------------------------------------------------------------
# Trigger rules
# ---------------------------------------------------------------------------


def test_workflow_has_trigger(workflow: dict):
    """Workflow must define at least one trigger (push or pull_request)."""
    on_block = workflow.get("on", workflow.get(True))  # 'on' may parse as True in PyYAML
    assert on_block is not None, "Workflow is missing an 'on:' trigger block"
    has_trigger = (
        isinstance(on_block, dict)
        and bool({"push", "pull_request"} & set(on_block.keys()))
    ) or (
        isinstance(on_block, list)
        and bool({"push", "pull_request"} & set(on_block))
    ) or (
        isinstance(on_block, str)
        and on_block in {"push", "pull_request"}
    )
    assert has_trigger, (
        f"Workflow 'on:' block must include 'push' or 'pull_request'; got {on_block!r}"
    )


# ---------------------------------------------------------------------------
# Step-level assertions
# ---------------------------------------------------------------------------


def test_workflow_uses_checkout_v4_or_newer(all_steps: list[dict]):
    """Workflow must include actions/checkout@v4 (or newer major)."""
    checkout_steps = [
        s for s in all_steps if "checkout" in str(s.get("uses", "")).lower()
    ]
    assert checkout_steps, "No step uses actions/checkout"
    for step in checkout_steps:
        uses = step.get("uses", "")
        # Accept @v4 or any higher major (v5, v10, etc.)
        assert _major_version(uses) >= 4, (
            f"actions/checkout must be pinned to @v4 or newer; got {uses!r}"
        )


def test_workflow_uses_setup_python_v5_or_newer(all_steps: list[dict]):
    """Workflow must include actions/setup-python@v5 (or newer major)."""
    sp_steps = [
        s for s in all_steps if "setup-python" in str(s.get("uses", "")).lower()
    ]
    assert sp_steps, "No step uses actions/setup-python"
    for step in sp_steps:
        uses = step.get("uses", "")
        assert _major_version(uses) >= 5, (
            f"actions/setup-python must be pinned to @v5 or newer; got {uses!r}"
        )


def test_workflow_installs_python_deps_from_both_requirements_files(all_steps: list[dict]):
    """A step must install deps from both requirements.txt and requirements-test.txt."""
    matching = [
        s for s in all_steps
        if "requirements.txt" in str(s.get("run", ""))
        and "requirements-test.txt" in str(s.get("run", ""))
    ]
    assert matching, (
        "No step installs Python deps from both requirements.txt and "
        "requirements-test.txt in a single 'run' command"
    )


def test_workflow_installs_buf(all_steps: list[dict]):
    """A step must use bufbuild/buf-setup-action pinned to a major version."""
    buf_steps = [
        s for s in all_steps if "buf-setup-action" in str(s.get("uses", ""))
    ]
    assert buf_steps, (
        "No step uses bufbuild/buf-setup-action to install buf"
    )
    for step in buf_steps:
        uses = step.get("uses", "")
        assert "@v" in uses, (
            f"bufbuild/buf-setup-action must be pinned to a major version (e.g. @v1); "
            f"got {uses!r}"
        )


def test_workflow_runs_buf_lint(all_steps: list[dict]):
    """A step must run 'buf lint'."""
    lint_steps = [
        s for s in all_steps if "buf lint" in str(s.get("run", ""))
    ]
    assert lint_steps, (
        "No step runs 'buf lint' — add a step with run: buf lint"
    )


def test_workflow_runs_pytest(all_steps: list[dict]):
    """A step must run pytest against the tests/ directory."""
    pytest_steps = [
        s for s in all_steps if "pytest" in str(s.get("run", ""))
    ]
    assert pytest_steps, (
        "No step runs pytest — add a step with run: pytest tests/ -v (or similar)"
    )


def test_workflow_has_pb2_idempotency_check(all_steps: list[dict]):
    """A step must run make generate_python_protos and assert generated/python/ is clean.

    This guards against proto/pb2 drift: if a .proto is edited without regenerating,
    CI fails rather than silently shipping stale gencode.
    """
    regen_steps = [
        s for s in all_steps
        if "make generate_python_protos" in str(s.get("run", ""))
    ]
    assert regen_steps, (
        "No CI step runs 'make generate_python_protos' — "
        "add a step to regenerate and then assert generated/python/ is clean."
    )
    for step in regen_steps:
        run_text = str(step.get("run", ""))
        has_drift_check = "git diff" in run_text or "git status" in run_text
        assert has_drift_check, (
            f"CI step '{step.get('name', '(unnamed)')}' runs make generate_python_protos "
            "but does not follow up with a 'git diff' or 'git status' check to catch drift."
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _major_version(uses: str) -> int:
    """Extract the numeric major version from a 'uses: action@vN' string.

    Returns 0 if no '@vN' suffix is found (caller will fail the assertion).
    """
    if "@v" not in uses:
        return 0
    try:
        return int(uses.split("@v")[-1].split(".")[0])
    except ValueError:
        return 0
