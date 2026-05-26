"""R3-10: CHANGELOG.md scaffold tests.

Verifies that CHANGELOG.md exists at the repo root, follows Keep-a-Changelog
format, documents the v0.1 breaking changes, and that README.md links to it.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
README = REPO_ROOT / "README.md"


def _changelog_text() -> str:
    return CHANGELOG.read_text(encoding="utf-8")


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_changelog_md_exists():
    assert CHANGELOG.exists(), (
        "CHANGELOG.md not found at repo root "
        + str(CHANGELOG)
        + " — create it following Keep-a-Changelog format"
    )


def test_changelog_has_unreleased_section():
    text = _changelog_text()
    assert "## [Unreleased]" in text, (
        "CHANGELOG.md is missing the '## [Unreleased]' section required by "
        "Keep a Changelog; add it immediately below the file header"
    )


def test_changelog_has_0_1_0_section():
    text = _changelog_text()
    assert "## [0.1.0]" in text, (
        "CHANGELOG.md is missing the '## [0.1.0]' release section; "
        "it must include the date and summary of the v0.1 epic"
    )


def test_changelog_references_epic_pr():
    text = _changelog_text()
    assert "aithusaqr/oets#25" in text, (
        "CHANGELOG.md does not reference the epic PR aithusaqr/oets#25; "
        "the v0.1.0 section must link to the review PR that introduced the changes"
    )


def test_changelog_documents_all_v0_1_breaking_changes():
    text = _changelog_text()
    required_refs = [
        ("M4", "EventTimestamp string→Timestamp (M4)"),
        ("M6", "Fee.amount string→int64 (M6)"),
        ("H2", "Fee.fee_type string→FeeType enum (H2)"),
        ("M3", "OrderSide/TIF/IntentionType sentinel shift (M3)"),
        ("L6", "FillEvent fields 15/19 removed (L6)"),
        ("M2", "FillEvent timestamps deduplication (M2)"),
        ("R2-2", "OetsEventEnvelope replaces top-level event_id (R2-2)"),
    ]
    missing = [description for ref, description in required_refs if ref not in text]
    assert not missing, (
        "CHANGELOG.md is missing breaking-change references: "
        + ", ".join(missing)
    )


def test_changelog_links_to_keep_a_changelog():
    text = _changelog_text()
    assert "keepachangelog.com" in text, (
        "CHANGELOG.md does not reference keepachangelog.com; "
        "add the standard 'The format is based on [Keep a Changelog]' line"
    )


def test_readme_links_to_changelog():
    text = _readme_text()
    assert "CHANGELOG.md" in text, (
        "README.md does not mention CHANGELOG.md; "
        "add a link to it in the 'See Also' section"
    )
