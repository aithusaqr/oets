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


def test_changelog_records_v0_1_epic_under_unreleased_or_tagged():
    """Until upstream tags v0.1.0, the epic's changes live under [Unreleased];
    once tagged, they should be hoisted to a dated `## [0.1.0]` section.

    Either layout is acceptable, but ONE of them must record the epic. A
    [Unreleased] heading with no content underneath would be a CHANGELOG that
    silently lost the epic's record — guard against that by requiring at least
    one wire-breaking marker (M4, M6, H2, R2-2) under the active section.
    """
    text = _changelog_text()
    has_unreleased = "## [Unreleased]" in text
    has_010 = "## [0.1.0]" in text
    assert has_unreleased or has_010, (
        "CHANGELOG.md must have either '## [Unreleased]' or '## [0.1.0]' as "
        "the active section for the v0.1 epic"
    )
    # Sanity: the file must contain at least one of the canonical epic markers.
    markers = ["M4", "M6", "H2", "R2-2"]
    assert any(m in text for m in markers), (
        "CHANGELOG.md exists with [Unreleased]/[0.1.0] heading but none of the "
        "canonical epic markers (M4/M6/H2/R2-2). Did the section get emptied?"
    )


def test_changelog_references_epic_pr():
    text = _changelog_text()
    assert "aithusaqr/oets#25" in text, (
        "CHANGELOG.md does not reference the epic PR aithusaqr/oets#25; "
        "the active section must link to the review PR that introduced the changes"
    )


def test_changelog_compare_links_dont_point_at_missing_tag():
    """If the file defines link references for [Unreleased] or [0.1.0], they must
    NOT point at a `releases/tag/v0.1.0` URL until that tag actually exists.

    Before this fix the file declared
        [0.1.0]: https://github.com/aithusaqr/oets/releases/tag/v0.1.0
    which is a 404 because upstream has not tagged the release yet. Either omit
    the link, point it at the epic PR, or only add it after the tag is created.
    """
    text = _changelog_text()
    lines = [
        line for line in text.splitlines()
        if line.startswith("[Unreleased]:") or line.startswith("[0.1.0]:")
    ]
    for line in lines:
        assert "releases/tag/v0.1.0" not in line, (
            f"CHANGELOG.md link points at a tag that does not exist upstream:\n"
            f"  {line}\n"
            f"Either tag v0.1.0 upstream first, or replace the URL with the "
            f"epic PR link (https://github.com/aithusaqr/oets/pull/25)."
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
