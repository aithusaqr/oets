"""Tests for R2-10: README.md reflects the v0.1 code-review epic final state."""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, "README.md")
LICENSE_PATH = os.path.join(REPO_ROOT, "LICENSE")


def _readme_text():
    with open(README_PATH, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# 1. Path prefixes correct
# ---------------------------------------------------------------------------

def test_readme_has_correct_paths():
    text = _readme_text()

    correct_paths = [
        "common/event_envelope.proto",
        "common/execution/fill_event.proto",
        "common/reconciliation/balance_event.proto",
    ]
    for path in correct_paths:
        assert path in text, (
            "README.md must contain the correct proto path "
            + repr(path)
            + " but it was not found"
        )

    stale_paths = [
        "oets/common/event_envelope.proto",
        "oets/execution/fill_event.proto",
        "oets/reconciliation/balance_event.proto",
    ]
    for path in stale_paths:
        assert path not in text, (
            "README.md must NOT contain the stale proto path "
            + repr(path)
            + " — fix to actual layout (no oets/ prefix)"
        )


# ---------------------------------------------------------------------------
# 2. All v0.1.1 reconciliation protos listed
# ---------------------------------------------------------------------------

def test_readme_lists_all_v0_1_1_protos():
    text = _readme_text()

    protos = [
        "balance_event.proto",
        "cash_flow_event.proto",
        "fee_event.proto",
        "funding_event.proto",
        "position_event.proto",
        "settlement_event.proto",
    ]
    for proto in protos:
        assert proto in text, (
            "README.md must mention all reconciliation protos; missing: " + repr(proto)
        )


# ---------------------------------------------------------------------------
# 3. Breaking changes section exists with sufficient coverage
# ---------------------------------------------------------------------------

def test_readme_documents_breaking_changes():
    text = _readme_text()

    # Section heading
    assert re.search(r"breaking change", text, re.IGNORECASE), (
        "README.md must contain a section with a heading matching 'breaking change(s)'"
    )

    critical_items = [
        # EventTimestamp → Timestamp
        "Timestamp",
        # Fee.amount int64
        "int64",
        # Fee.fee_type enum
        "FeeType",
        # OrderSide enum shift
        "OrderSide",
        # OetsEventEnvelope on event messages
        "OetsEventEnvelope",
        # EventType rename
        "EVENT_TYPE_CASH_FLOW",
    ]
    found = [item for item in critical_items if item in text]
    assert len(found) >= 6, (
        "README.md breaking-changes section must mention at least 6 critical items; "
        "found "
        + str(len(found))
        + " of "
        + str(len(critical_items))
        + ": "
        + str(found)
    )


# ---------------------------------------------------------------------------
# 4. Getting Started section
# ---------------------------------------------------------------------------

def test_readme_has_getting_started():
    text = _readme_text()

    assert re.search(r"getting started", text, re.IGNORECASE), (
        "README.md must contain a 'Getting Started' section"
    )
    assert "pip install" in text, (
        "README.md Getting Started must include pip install instructions"
    )
    assert "pytest" in text, (
        "README.md Getting Started must mention pytest"
    )


# ---------------------------------------------------------------------------
# 5. Key docs referenced
# ---------------------------------------------------------------------------

def test_readme_references_key_docs():
    text = _readme_text()

    refs = [
        "docs/SCALING.md",
        "docs/ARCHITECTURE.md",
        "validation/",
        "buf.yaml",
    ]
    for ref in refs:
        assert ref in text, (
            "README.md must reference " + repr(ref) + " but it was not found"
        )


# ---------------------------------------------------------------------------
# 6. Relative path links resolve locally
# ---------------------------------------------------------------------------

def test_readme_links_resolve_locally():
    text = _readme_text()

    # Collect paths from markdown links: [label](path) — skip http(s) and anchors
    md_link_paths = re.findall(r"\[(?:[^\]]*)\]\(([^)]+)\)", text)
    relative_links = [
        p for p in md_link_paths
        if not p.startswith("http") and not p.startswith("#")
    ]

    # Collect backtick-wrapped paths in the See Also section that look like
    # file paths (contain a dot or slash, not a shell command)
    see_also_match = re.search(r"## See Also(.+?)(?:\n## |\Z)", text, re.DOTALL)
    backtick_paths = []
    if see_also_match:
        see_also_text = see_also_match.group(1)
        candidates = re.findall(r"`([^`]+)`", see_also_text)
        for candidate in candidates:
            # Only treat as a file path if it looks like one:
            # must contain a slash OR end with a known file extension.
            # Exclude dotted identifiers (e.g. proto field references).
            has_slash = "/" in candidate
            has_file_ext = bool(re.search(r"\.(md|py|yaml|yml|proto|txt)$", candidate))
            if (has_slash or has_file_ext) and " " not in candidate:
                backtick_paths.append(candidate)

    all_paths = relative_links + backtick_paths
    missing = []
    for rel_path in all_paths:
        full_path = os.path.join(REPO_ROOT, rel_path)
        if not os.path.exists(full_path):
            missing.append(rel_path)

    assert not missing, (
        "README.md references the following paths that do not exist in the repo: "
        + str(missing)
    )


# ---------------------------------------------------------------------------
# 7. License section (R3-8)
# ---------------------------------------------------------------------------

def test_readme_has_license_section():
    text = _readme_text()
    assert re.search(r"^## License", text, re.IGNORECASE | re.MULTILINE), (
        "README.md must contain a '## License' section heading"
    )


def test_readme_links_to_license_file():
    text = _readme_text()
    # Accept [LICENSE](LICENSE) or [the LICENSE file](LICENSE) etc.
    assert re.search(r"\[[^\]]+\]\(LICENSE\)", text), (
        "README.md must contain a markdown link to the LICENSE file, "
        "e.g. [LICENSE](LICENSE)"
    )


def test_readme_mentions_apache_2():
    text = _readme_text()
    license_section_match = re.search(
        r"## License\b(.+?)(?:\n## |\Z)", text, re.DOTALL | re.IGNORECASE
    )
    assert license_section_match, (
        "README.md must contain a '## License' section"
    )
    section_text = license_section_match.group(1)
    # Both tokens must appear in the same paragraph (no blank-line gap between them)
    paragraphs = re.split(r"\n\s*\n", section_text)
    found = any(
        "Apache" in para and "2.0" in para
        for para in paragraphs
    )
    assert found, (
        "README.md License section must mention 'Apache' and '2.0' in the same paragraph"
    )


def test_license_file_exists_and_is_apache_2():
    assert os.path.isfile(LICENSE_PATH), (
        "LICENSE file must exist at repo root: " + LICENSE_PATH
    )
    with open(LICENSE_PATH, encoding="utf-8") as fh:
        content = fh.read()
    first_line = content.splitlines()[0].strip()
    assert first_line == "Apache License", (
        "LICENSE first line must be 'Apache License'; got: " + repr(first_line)
    )
    assert "Version 2.0" in content, (
        "LICENSE must contain 'Version 2.0' to confirm it is Apache 2.0"
    )
