"""R2-9: Staleness guard for buf.yaml lint.except and lint.ignore entries.

Ensures every suppressed lint rule is documented with a comment and that
any GitHub issue referenced in that comment is currently OPEN.  A closed
issue means the original tracking work landed but the suppression was never
removed — a silent, stale lie in the config.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ISSUE_REF_RE = re.compile(
    r"(?:(?:zachisit|aithusaqr)/oets)?#(\d+)"
)

# Default repo when a bare #NN reference is found (no org/repo prefix).
_DEFAULT_REPO = "zachisit/oets"

# Closed set of valid STANDARD rule names — imported conceptually from
# test_buf_config.py so this file stays self-contained.
_KNOWN_SUPPRESSIBLE_STANDARD_RULES: frozenset[str] = frozenset(
    {
        "ENUM_ZERO_VALUE_SUFFIX",
        "ENUM_VALUE_PREFIX",
        "PACKAGE_VERSION_SUFFIX",
        "FIELD_LOWER_SNAKE_CASE",
        "MESSAGE_PASCAL_CASE",
        "ENUM_PASCAL_CASE",
        "SERVICE_PASCAL_CASE",
        "RPC_PASCAL_CASE",
        "PACKAGE_LOWER_SNAKE_CASE",
        "IMPORT_NO_WEAK",
        "IMPORT_NO_PUBLIC",
        "ENUM_NO_ALLOW_ALIAS",
        "ONEOF_LOWER_SNAKE_CASE",
        "RPC_REQUEST_STANDARD_NAME",
        "RPC_RESPONSE_STANDARD_NAME",
        "RPC_REQUEST_RESPONSE_UNIQUE",
        "SERVICE_SUFFIX",
        "COMMENT_ENUM",
        "COMMENT_ENUM_VALUE",
        "COMMENT_FIELD",
        "COMMENT_MESSAGE",
        "COMMENT_ONEOF",
        "COMMENT_RPC",
        "COMMENT_SERVICE",
        "PROTOVALIDATE",
        "SYNTAX_SPECIFIED",
        "FIELD_NOT_REQUIRED",
        "PACKAGE_DIRECTORY_MATCH",
        "PACKAGE_SAME_DIRECTORY",
    }
)


def _parse_buf_yaml(repo_root: Path) -> dict:
    path = repo_root / "buf.yaml"
    assert path.is_file(), "buf.yaml not found at repo root"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _buf_yaml_raw_lines(repo_root: Path) -> list[str]:
    """Return the raw lines of buf.yaml (1-indexed as lines[0] = line 1)."""
    path = repo_root / "buf.yaml"
    return path.read_text(encoding="utf-8").splitlines()


def _map_entry_to_preceding_comments(raw_lines: list[str]) -> dict[str, list[str]]:
    """Return {entry_value: [comment_lines]} by scanning raw buf.yaml text.

    For each non-comment, non-blank, non-key line that starts with ``- ``
    (a list item), collect all consecutive comment lines immediately above it
    (ignoring blank lines in between).
    """
    result: dict[str, list[str]] = {}
    for i, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip()
        if not value or value.startswith("#"):
            continue

        # Walk upward, collecting comment lines (skip blank lines).
        comments: list[str] = []
        j = i - 1
        while j >= 0:
            prev = raw_lines[j].strip()
            if prev.startswith("#"):
                comments.insert(0, prev)
                j -= 1
            elif prev == "":
                j -= 1
            else:
                break

        result[value] = comments
    return result


def _extract_issue_refs(comment_lines: list[str]) -> list[tuple[str, int]]:
    """Return list of (repo, issue_number) from comment lines.

    Bare #NN refs default to _DEFAULT_REPO.
    """
    refs: list[tuple[str, int]] = []
    for line in comment_lines:
        for m in _ISSUE_REF_RE.finditer(line):
            full = m.group(0)
            num = int(m.group(1))
            if "/" in full and "#" in full:
                # Extract org/repo portion before the #
                repo_part = full.split("#")[0]
                refs.append((repo_part, num))
            else:
                refs.append((_DEFAULT_REPO, num))
    return refs


def _gh_available() -> bool:
    """Return True if gh is on PATH and authenticated."""
    if shutil.which("gh") is None:
        return False
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _gh_issue_state(repo: str, number: int) -> str | None:
    """Return 'OPEN' or 'CLOSED', or None if the issue doesn't exist / network error."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(number), "--repo", repo, "--json", "state,number"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return data.get("state", "").upper()
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_buf_yaml_parses(repo_root: Path):
    """buf.yaml must be valid YAML with the expected top-level keys."""
    cfg = _parse_buf_yaml(repo_root)
    for key in ("version", "modules", "lint", "breaking"):
        assert key in cfg, f"buf.yaml missing top-level key: {key!r}"


def test_each_except_rule_has_a_comment(repo_root: Path):
    """Every entry in lint.except must be preceded by at least one comment line.

    Undocumented suppressions make it impossible to know why the rule was
    disabled or what issue tracks re-enabling it.
    """
    cfg = _parse_buf_yaml(repo_root)
    except_rules: list[str] = cfg.get("lint", {}).get("except", [])
    if not except_rules:
        pytest.skip("lint.except is empty — nothing to validate")

    raw_lines = _buf_yaml_raw_lines(repo_root)
    entry_comments = _map_entry_to_preceding_comments(raw_lines)

    missing: list[str] = []
    for rule in except_rules:
        comments = entry_comments.get(rule, [])
        if not comments:
            missing.append(rule)

    assert not missing, (
        "The following lint.except entries have no documenting comment immediately "
        f"above them in buf.yaml: {missing!r}. Add a comment explaining why the "
        "rule is suppressed and which issue tracks re-enabling it."
    )


def test_each_referenced_issue_is_open(repo_root: Path):
    """Every GitHub issue referenced in a lint.except or lint.ignore comment must be OPEN.

    A closed issue signals that the tracking work landed but the suppression
    was never removed.  Skip cleanly when gh is unavailable or unauthenticated.
    """
    if not _gh_available():
        pytest.skip("gh not available or not authenticated — skipping network test")

    cfg = _parse_buf_yaml(repo_root)
    raw_lines = _buf_yaml_raw_lines(repo_root)
    entry_comments = _map_entry_to_preceding_comments(raw_lines)

    except_rules: list[str] = cfg.get("lint", {}).get("except", [])
    ignore_entries: list[str] = cfg.get("lint", {}).get("ignore", [])
    all_entries = except_rules + ignore_entries

    failures: list[str] = []
    for entry in all_entries:
        comments = entry_comments.get(entry, [])
        refs = _extract_issue_refs(comments)
        for repo, number in refs:
            state = _gh_issue_state(repo, number)
            if state is None:
                failures.append(
                    f"Entry {entry!r}: could not fetch issue {repo}#{number} "
                    "(does not exist or network error)"
                )
            elif state == "CLOSED":
                failures.append(
                    f"Entry {entry!r}: references CLOSED issue {repo}#{number}. "
                    "Either re-enable the lint rule or update the comment to point "
                    "at an open tracking issue."
                )

    assert not failures, (
        "Stale issue references found in buf.yaml lint suppressions:\n"
        + "\n".join(f"  - {f}" for f in failures)
    )


def test_no_orphan_except_rules(repo_root: Path):
    """Every entry in lint.except must be a known STANDARD rule name.

    A misspelled or non-existent rule name silently suppresses nothing while
    giving false confidence that a violation is covered.
    """
    cfg = _parse_buf_yaml(repo_root)
    except_rules: list[str] = cfg.get("lint", {}).get("except", [])
    if not except_rules:
        pytest.skip("lint.except is empty — nothing to validate")

    unrecognised = [r for r in except_rules if r not in _KNOWN_SUPPRESSIBLE_STANDARD_RULES]
    assert not unrecognised, (
        f"Unrecognised rule(s) in buf.yaml lint.except: {unrecognised!r}. "
        "Either the rule name is misspelled or it must be added to the "
        "_KNOWN_SUPPRESSIBLE_STANDARD_RULES set in this test file."
    )
