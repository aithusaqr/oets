"""R4-3: README's Initial Proto Scope and Project Layout sections must list
every .proto file actually present under common/.

The pre-fix README listed 14 protos but the repo contains 15 (account.proto
was missing). Doc drift like this is easy to introduce when files are added
and easy to miss in review.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def readme_text(repo_root: Path) -> str:
    return (repo_root / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def actual_proto_paths(repo_root: Path) -> list[str]:
    """All .proto file paths under common/, repo-relative, sorted."""
    common_dir = repo_root / "common"
    return sorted(
        str(p.relative_to(repo_root)) for p in common_dir.rglob("*.proto")
    )


def test_initial_proto_scope_lists_every_proto(
    readme_text: str, actual_proto_paths: list[str]
) -> None:
    """The 'Initial Proto Scope' section must mention every .proto under common/.

    The section spans v0.1.0 + v0.1.1 sub-headers. We extract the fenced block
    immediately following the section heading and assert every actual proto
    path appears verbatim.
    """
    section_match = re.search(
        r"##\s+Initial Proto Scope.*?```text\s*\n(.*?)\n```",
        readme_text,
        re.DOTALL,
    )
    assert section_match is not None, (
        "README.md does not contain an '## Initial Proto Scope' section with a "
        "```text fenced block."
    )
    scope_block = section_match.group(1)

    missing = [p for p in actual_proto_paths if p not in scope_block]
    assert not missing, (
        "README.md 'Initial Proto Scope' is missing these .proto files that "
        "exist in the repo:\n  " + "\n  ".join(missing)
        + "\nThe scope listing must enumerate every common/*.proto file. "
        "Add the missing entries under v0.1.0 or v0.1.1 (whichever fits)."
    )


def test_project_layout_lists_every_proto(
    readme_text: str, actual_proto_paths: list[str]
) -> None:
    """The 'Project Layout' section must mention every .proto under common/ by
    filename. The tree uses just basenames; verify each basename appears.

    Catches the same drift as the scope test, but on the layout diagram, so a
    file added without updating the layout will fail here even if the scope
    section happens to be right.
    """
    section_match = re.search(
        r"##\s+Project Layout.*?```\s*\n(.*?)\n```",
        readme_text,
        re.DOTALL,
    )
    assert section_match is not None, (
        "README.md does not contain a '## Project Layout' section with a "
        "```-fenced block."
    )
    layout_block = section_match.group(1)

    missing_basenames = [
        Path(p).name for p in actual_proto_paths if Path(p).name not in layout_block
    ]
    assert not missing_basenames, (
        "README.md 'Project Layout' tree is missing these .proto basenames "
        "that exist in the repo:\n  " + "\n  ".join(missing_basenames)
        + "\nAdd them to the appropriate subtree."
    )
