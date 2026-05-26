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
        "QA cycle",
        "Wire-breaking change policy",
        "Code style",
    ]
    missing = [h for h in required_headings if h not in text]
    assert not missing, (
        "CONTRIBUTING.md is missing the following required section headings: "
        + ", ".join(repr(h) for h in missing)
        + ". Each section must appear verbatim in the document."
    )


def test_contributing_mentions_grpc_tools_protoc():
    text = _contributing_text()
    assert "grpc_tools.protoc" in text, (
        "CONTRIBUTING.md does not mention 'grpc_tools.protoc'; "
        "it must warn contributors to use 'python -m grpc_tools.protoc' "
        "instead of bare protoc to stay compatible with the pinned protobuf 5.x runtime"
    )
    # Also check that it warns against bare protoc
    assert "protoc" in text and (
        "NOT use bare" in text or "Do NOT use bare" in text or "not use bare" in text
    ), (
        "CONTRIBUTING.md mentions grpc_tools.protoc but does not warn against "
        "bare 'protoc'; add a clear warning that bare protoc produces gencode 7.x "
        "which is incompatible with the pinned protobuf 5.x runtime"
    )


def test_contributing_mentions_qa_cycle():
    text = _contributing_text()
    # Must explain the 3-iteration cycle
    assert "three" in text.lower() or "3" in text, (
        "CONTRIBUTING.md does not explain the 3-iteration QA cycle; "
        "it must state that the reviewer runs three audit iterations"
    )
    # Must include the N1/N2/N3 notation
    assert "N1/N2/N3" in text, (
        "CONTRIBUTING.md is missing the 'N1/N2/N3' QA result notation; "
        "it must document how QA results are formatted in PR comments "
        "(e.g. '## QA Cycle — N1/N2/N3')"
    )
    # Must mention the 0/0/0 clean-pass criterion
    assert "0/0/0" in text, (
        "CONTRIBUTING.md does not include the '0/0/0' clean-pass criterion; "
        "the QA section must state that the PR ships when three consecutive "
        "iterations are clean (0/0/0)"
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
