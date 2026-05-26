"""R4-1 (#64): Makefile generate_python_protos must invoke `python -m`
(not `python3 -m`) so the venv's interpreter is preferred when activated,
and the inline comment about the protobuf pin must match requirements.txt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def makefile_text(repo_root: Path) -> str:
    return (repo_root / "Makefile").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def recipe_block(makefile_text: str) -> str:
    pattern = re.compile(
        r"^generate_python_protos\s*:.*\n((?:[ \t]+.*\n?)*)",
        re.MULTILINE,
    )
    match = pattern.search(makefile_text)
    assert match, "generate_python_protos recipe block not found in Makefile"
    return match.group(1)


def test_recipe_uses_python_not_python3(recipe_block: str) -> None:
    """The recipe must invoke `python -m grpc_tools.protoc`, not `python3 -m ...`.

    Rationale (#64): bare `python3` resolves to whatever `/usr/bin/python3` (or
    `/opt/homebrew/bin/python3`) points at — typically the system interpreter,
    which does not have grpcio-tools installed. A venv places its `python` shim
    earlier on PATH but not necessarily `python3` (and on macOS Homebrew, the
    venv's `python3` symlink may resolve back to the host interpreter). Using
    `python` makes the recipe Just Work after `source .venv/bin/activate`.
    """
    bare_python3 = re.search(r"^\s+python3\s+-m\s+grpc_tools\.protoc\b", recipe_block, re.MULTILINE)
    assert bare_python3 is None, (
        "Makefile generate_python_protos still uses `python3 -m grpc_tools.protoc`. "
        "Use `python -m grpc_tools.protoc` so an activated venv's interpreter is "
        "preferred. See #64. Offending recipe block:\n" + recipe_block
    )
    python_invocation = re.search(r"^\s+python\s+-m\s+grpc_tools\.protoc\b", recipe_block, re.MULTILINE)
    assert python_invocation is not None, (
        "Makefile generate_python_protos must invoke `python -m grpc_tools.protoc`. "
        "Recipe block:\n" + recipe_block
    )


def test_recipe_comment_matches_actual_protobuf_pin(repo_root: Path, makefile_text: str) -> None:
    """The Makefile comment about the pinned protobuf runtime must match the
    actual pin in requirements.txt (and pyproject.toml).

    The comment near `generate_python_protos:` documents which protobuf
    version is compatible with the gencode produced by grpcio-tools' bundled
    protoc 29.x. Drift between the comment and the real pin is silently
    misleading to a future contributor.
    """
    requirements = (repo_root / "requirements.txt").read_text(encoding="utf-8")
    pin_match = re.search(r"protobuf\s*>=\s*(\d+\.\d+)\s*,\s*<\s*(\d+)", requirements)
    assert pin_match is not None, (
        "Could not parse a `protobuf>=X.Y,<Z` pin from requirements.txt"
    )
    lower, upper = pin_match.group(1), pin_match.group(2)

    pin_phrase = f"protobuf>={lower},<{upper}"
    assert pin_phrase in makefile_text, (
        f"Makefile comment does not reference the actual pin {pin_phrase!r} "
        f"(found in requirements.txt). The Makefile comment is documenting the "
        f"protobuf runtime that the bundled protoc 29.x gencode is compatible "
        f"with; let it match reality."
    )


def test_contributing_md_mentions_venv_activation(repo_root: Path) -> None:
    """CONTRIBUTING.md's regen section must point the contributor at activating
    their venv before running `make generate_python_protos`, since the recipe
    relies on `python` resolving to the venv interpreter.
    """
    contributing = (repo_root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    # Find the regen section
    regen_section = re.search(
        r"###\s+3\..+?Regenerate Python bindings.+?(?=###|\Z)",
        contributing,
        re.DOTALL,
    )
    assert regen_section is not None, (
        "CONTRIBUTING.md does not contain a section about regenerating Python bindings"
    )
    section_text = regen_section.group(0).lower()
    assert "venv" in section_text or "activate" in section_text, (
        "CONTRIBUTING.md regen section does not mention venv activation. "
        "Without `source .venv/bin/activate`, the Makefile's `python -m grpc_tools.protoc` "
        "fails on systems where the global `python` lacks grpcio-tools."
    )
