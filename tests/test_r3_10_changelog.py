"""R3-10: CHANGELOG.md scaffold tests.

Verifies that CHANGELOG.md exists at the repo root, follows Keep-a-Changelog
format, documents the v0.1 breaking changes, and that README.md links to it.
"""

import re
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


def test_changelog_active_section_has_content():
    """The active section (Unreleased or the most recent tagged version) must
    have at least one entry under one of the Keep-a-Changelog headings. A bare
    `## [Unreleased]` with nothing below it is a CHANGELOG that's silently
    lost track of what shipped.
    """
    text = _changelog_text()
    has_unreleased = "## [Unreleased]" in text
    has_010 = "## [0.1.0]" in text
    assert has_unreleased or has_010, (
        "CHANGELOG.md must have either '## [Unreleased]' or '## [0.1.0]' as "
        "the active section"
    )
    # Active section must contain at least one Keep-a-Changelog subsection
    # with at least one bullet under it.
    has_any_subsection = any(
        re.search(rf"### {kind}\s*\n+\s*[-*]", text)
        for kind in ("Added", "Changed", "Fixed", "Removed", "Deprecated", "Security")
    )
    assert has_any_subsection, (
        "CHANGELOG.md's active section has no entries under any "
        "Added/Changed/Fixed/Removed/Deprecated/Security heading"
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
