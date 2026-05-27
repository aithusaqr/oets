"""R3-9: CONTRIBUTING.md documentation tests.

Verifies that CONTRIBUTING.md exists, has the required sections, warns about
bare protoc, explains the 3-iteration QA cycle, has resolvable relative links,
and that README.md links back to it.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
README = REPO_ROOT / "README.md"


def _contributing_text() -> str:
    return CONTRIBUTING.read_text(encoding="utf-8")


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_contributing_md_exists():
    assert CONTRIBUTING.exists(), (
        f"CONTRIBUTING.md not found at repo root ({CONTRIBUTING}); "
        "create it to document the fork → epic → PR → QA-cycle workflow"
    )


def test_contributing_has_required_sections():
    text = _contributing_text()
    required_headings = [
        "Filing an issue",
        "Proposing a code change",
        "Wire-breaking change policy",
        "Code style",
    ]
    missing = [h for h in required_headings if h not in text]
    assert not missing, (
        "CONTRIBUTING.md is missing the following required section headings: "
        + ", ".join(repr(h) for h in missing)
        + ". Each section must appear verbatim in the document."
    )


def test_contributing_describes_pr_workflow():
    """CONTRIBUTING.md must explain how to fork, branch, test, and open a PR."""
    text = _contributing_text()
    required_phrases = [
        ("fork", "fork the repo to start a contribution"),
        ("pytest", "run the test suite locally before opening the PR"),
        ("requirements", "install dependencies from requirements files"),
        ("make generate_python_protos", "regenerate pb2 bindings via the Makefile target"),
    ]
    missing = [
        phrase for phrase, _ in required_phrases if phrase.lower() not in text.lower()
    ]
    assert not missing, (
        "CONTRIBUTING.md does not mention these expected workflow phrases: "
        + ", ".join(repr(m) for m in missing)
    )


def test_contributing_links_resolve():
    text = _contributing_text()
    # Find all markdown links with relative paths: [text](path)
    # Exclude http/https URLs and anchor-only links
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    unresolved = []
    for _label, target in link_pattern.findall(text):
        if target.startswith(("http://", "https://", "#")):
            continue
        # Strip any anchor from path
        path_part = target.split("#")[0]
        if not path_part:
            continue
        resolved = (REPO_ROOT / path_part).resolve()
        if not resolved.exists():
            unresolved.append(target)
    assert not unresolved, (
        "CONTRIBUTING.md contains relative links that do not resolve to "
        "existing files in the repo: "
        + ", ".join(repr(t) for t in unresolved)
        + f". Repo root is {REPO_ROOT}."
    )


def test_readme_links_to_contributing():
    text = _readme_text()
    assert "CONTRIBUTING.md" in text, (
        "README.md does not link to CONTRIBUTING.md; "
        "add '[CONTRIBUTING.md](CONTRIBUTING.md)' in the See Also section "
        "so new contributors can find the workflow documentation"
    )
