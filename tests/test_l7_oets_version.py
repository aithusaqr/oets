"""Tests for L7: oets_version SemVer 2.0.0 constraint.

Covers:
- Proto field documentation (comment block mentions SemVer + canonical regex prefix)
- Python validator: is_valid_oets_version, parse_oets_version, OETS_VERSION_REGEX
- Wire-format regression: field type and number unchanged
"""

import re
import pathlib
import pytest

PROTO_PATH = pathlib.Path(__file__).parent.parent / "common" / "event_envelope.proto"


# ---------------------------------------------------------------------------
# Proto-level tests
# ---------------------------------------------------------------------------

def test_proto_field_has_semver_documentation():
    """The oets_version field must have a comment block mentioning SemVer and the regex."""
    text = PROTO_PATH.read_text()
    # Find the comment block immediately preceding the field declaration.
    # We look for 'oets_version' and then check the surrounding text.
    assert "oets_version" in text, "oets_version field not found in proto"

    # The word "semver" (case-insensitive) must appear in the file
    assert re.search(r"semver", text, re.IGNORECASE), (
        "Expected 'SemVer' in the oets_version comment block"
    )

    # The canonical SemVer regex anchor must appear in the comment
    assert "^(0|[1-9]" in text, (
        "Expected canonical SemVer regex anchor '^(0|[1-9]' in the comment block"
    )


def test_field_number_unchanged():
    """Regression guard: field type and number must remain 'string oets_version = 2'."""
    text = PROTO_PATH.read_text()
    assert re.search(r"\bstring\s+oets_version\s*=\s*2\s*;", text), (
        "oets_version must remain 'string oets_version = 2;' (no wire-format change)"
    )


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

from validation.oets_version import (
    OETS_VERSION_REGEX,
    is_valid_oets_version,
    parse_oets_version,
)


def test_regex_is_compiled():
    assert isinstance(OETS_VERSION_REGEX, re.Pattern)


@pytest.mark.parametrize(
    "version",
    [
        "0.1.0",
        "1.0.0",
        "1.0.0-rc.1",
        "1.0.0+20130313144700",
        "1.0.0-rc.1+build.5",
        "0.0.4",
    ],
)
def test_validator_accepts_known_good(version):
    assert is_valid_oets_version(version), f"Expected {version!r} to be valid"


@pytest.mark.parametrize(
    "version",
    [
        "",                # empty
        "1",              # missing minor and patch
        "1.0",            # missing patch
        "01.0.0",         # leading zero in major
        "1.0.0-",         # trailing hyphen in prerelease
        "1.0.0..",        # extra dots
        "v1.0.0",         # leading 'v'
        "1.0.0.0",        # four segments
    ],
)
def test_validator_rejects_known_bad(version):
    assert not is_valid_oets_version(version), f"Expected {version!r} to be invalid"


def test_parse_returns_components():
    result = parse_oets_version("1.2.3-rc.1+build.5")
    assert result == (1, 2, 3, "rc.1", "build.5")


def test_parse_raises_on_invalid():
    with pytest.raises(ValueError):
        parse_oets_version("not-a-version")
