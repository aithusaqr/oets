"""
OETS version string validator.

Validates that ``OetsEventEnvelope.oets_version`` conforms to SemVer 2.0.0
as documented in the field comment and at https://semver.org/spec/v2.0.0.html.

Public API
----------
OETS_VERSION_REGEX : re.Pattern
    Compiled SemVer 2.0.0 regex with named capture groups.
is_valid_oets_version(value) -> bool
    Return True if *value* is a valid SemVer 2.0.0 string.
parse_oets_version(value) -> tuple[int, int, int, str | None, str | None]
    Return (major, minor, patch, prerelease, build).
    Raises ValueError if *value* is not valid.

References
----------
Canonical regex sourced from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
Issue: https://github.com/aithusaqr/oets/issues/20
"""

import re

# Official SemVer 2.0.0 regex with named capture groups (from semver.org).
OETS_VERSION_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def is_valid_oets_version(value: str) -> bool:
    """Return True if *value* is a valid SemVer 2.0.0 version string."""
    if not isinstance(value, str):
        return False
    return OETS_VERSION_REGEX.match(value) is not None


def parse_oets_version(value: str) -> tuple:
    """Parse *value* as a SemVer 2.0.0 string.

    Returns
    -------
    tuple[int, int, int, str | None, str | None]
        ``(major, minor, patch, prerelease, build)`` where *prerelease* and
        *build* are ``None`` when absent.

    Raises
    ------
    ValueError
        If *value* does not conform to SemVer 2.0.0.
    """
    m = OETS_VERSION_REGEX.match(value)
    if m is None:
        raise ValueError(
            f"Invalid oets_version {value!r}: must be a SemVer 2.0.0 string "
            "(MAJOR.MINOR.PATCH[-prerelease][+build]). "
            "See https://semver.org/spec/v2.0.0.html"
        )
    return (
        int(m.group("major")),
        int(m.group("minor")),
        int(m.group("patch")),
        m.group("prerelease"),
        m.group("build"),
    )
