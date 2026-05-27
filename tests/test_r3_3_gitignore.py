"""
R3-3: Verify that build/, *.egg-info/, and dist/ are excluded by .gitignore
and that no build artifacts have accidentally been committed to the repo.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GITIGNORE = REPO_ROOT / ".gitignore"


def test_gitignore_excludes_build_artifacts():
    """Each of build/, *.egg-info/, and dist/ must appear as a line in .gitignore."""
    assert GITIGNORE.exists(), f".gitignore not found at {GITIGNORE}"
    lines = {line.strip() for line in GITIGNORE.read_text().splitlines()}
    missing = []
    for entry in ("build/", "*.egg-info/", "dist/"):
        if entry not in lines:
            missing.append(entry)
    assert not missing, (
        f"These entries are absent from .gitignore: {missing}. "
        f"Add them so wheel-build artifacts cannot slip into the repo."
    )


def test_no_build_artifacts_tracked():
    """No build/, *.egg-info/, or dist/ paths should be tracked by git."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = result.stdout.splitlines()
    offenders = [
        f
        for f in tracked
        if f.startswith("build/")
        or ".egg-info/" in f
        or f.startswith("dist/")
    ]
    assert not offenders, (
        f"These build-artifact paths are tracked by git and must be removed: {offenders}"
    )


def test_no_pyc_files_tracked():
    """No .pyc files should be tracked by git (defensive check)."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = result.stdout.splitlines()
    pyc_files = [f for f in tracked if f.endswith(".pyc")]
    assert not pyc_files, (
        f"These .pyc files are tracked by git and must be removed: {pyc_files}"
    )
