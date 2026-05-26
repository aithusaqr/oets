"""Tests for R2-6 (#25): cosmetic cleanup — duplicate H3 comments + whitespace nits."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

FUNDING_PROTO = REPO_ROOT / "common" / "reconciliation" / "funding_event.proto"
SETTLEMENT_PROTO = REPO_ROOT / "common" / "reconciliation" / "settlement_event.proto"
BALANCE_PROTO = REPO_ROOT / "common" / "reconciliation" / "balance_event.proto"
FILL_PROTO = REPO_ROOT / "common" / "execution" / "fill_event.proto"

# The 8 .proto files that H3 touched (mirrored from test_h3_scaling_documentation.py).
SCALED_PROTO_FILES = [
    REPO_ROOT / "common" / "execution" / "fill_event.proto",
    REPO_ROOT / "common" / "execution" / "order_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "balance_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "cash_flow_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "fee_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "funding_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "position_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "settlement_event.proto",
]


# ---------------------------------------------------------------------------
# 1. funding_event.proto — duplicate scaling comment consolidated
# ---------------------------------------------------------------------------

def test_funding_event_no_duplicate_scaling_comment():
    """The H3 template phrase must appear at most once in funding_event.proto."""
    assert FUNDING_PROTO.exists(), (
        "funding_event.proto not found at " + str(FUNDING_PROTO)
    )
    content = FUNDING_PROTO.read_text(encoding="utf-8")
    phrase = "Numeric fields in this file follow the OETS int64 scaling convention"
    count = content.count(phrase)
    assert count <= 1, (
        "funding_event.proto contains the H3 template phrase "
        + repr(phrase)
        + " "
        + str(count)
        + " time(s); expected at most 1 after consolidation."
    )


# ---------------------------------------------------------------------------
# 2. settlement_event.proto — duplicate scaling comment consolidated
# ---------------------------------------------------------------------------

def test_settlement_event_no_duplicate_scaling_comment():
    """The H3 template phrase must appear at most once in settlement_event.proto."""
    assert SETTLEMENT_PROTO.exists(), (
        "settlement_event.proto not found at " + str(SETTLEMENT_PROTO)
    )
    content = SETTLEMENT_PROTO.read_text(encoding="utf-8")
    phrase = "Numeric fields in this file follow the OETS int64 scaling convention"
    count = content.count(phrase)
    assert count <= 1, (
        "settlement_event.proto contains the H3 template phrase "
        + repr(phrase)
        + " "
        + str(count)
        + " time(s); expected at most 1 after consolidation."
    )


# ---------------------------------------------------------------------------
# 3. balance_event.proto — exactly one blank line after `package oets.v1;`
# ---------------------------------------------------------------------------

def test_balance_event_no_double_blank_after_package():
    """After `package oets.v1;` there should be exactly one blank line."""
    assert BALANCE_PROTO.exists(), (
        "balance_event.proto not found at " + str(BALANCE_PROTO)
    )
    lines = BALANCE_PROTO.read_text(encoding="utf-8").splitlines()
    pkg_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "package oets.v1;":
            pkg_idx = i
            break
    assert pkg_idx is not None, (
        "balance_event.proto: could not find 'package oets.v1;' line."
    )
    assert pkg_idx + 1 < len(lines), (
        "balance_event.proto: no line after 'package oets.v1;'."
    )
    assert lines[pkg_idx + 1].strip() == "", (
        "balance_event.proto: line immediately after 'package oets.v1;' "
        "should be blank, got: " + repr(lines[pkg_idx + 1])
    )
    assert pkg_idx + 2 < len(lines), (
        "balance_event.proto: no second line after 'package oets.v1;'."
    )
    assert lines[pkg_idx + 2].strip() != "", (
        "balance_event.proto: found a double blank line after 'package oets.v1;'; "
        "collapse to a single blank line."
    )


# ---------------------------------------------------------------------------
# 4. fill_event.proto — no trailing blank line before FillEvent closing brace
# ---------------------------------------------------------------------------

def test_fill_event_no_trailing_blank_in_message():
    """The closing `}` of FillEvent must not be preceded by a blank line."""
    assert FILL_PROTO.exists(), (
        "fill_event.proto not found at " + str(FILL_PROTO)
    )
    lines = FILL_PROTO.read_text(encoding="utf-8").splitlines()
    # Find the last `}` that closes FillEvent (the final `}` in the file).
    closing_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            closing_idx = i
            break
    assert closing_idx is not None, (
        "fill_event.proto: could not find a closing `}` line."
    )
    assert closing_idx > 0, (
        "fill_event.proto: closing `}` is the first line — unexpected structure."
    )
    assert lines[closing_idx - 1].strip() != "", (
        "fill_event.proto: the line immediately before the FillEvent closing `}` "
        "is blank; remove the stray trailing blank line (residue from M2 timestamps removal)."
    )


# ---------------------------------------------------------------------------
# 5. Regression — all H3 files still reference SCALING.md
# ---------------------------------------------------------------------------

def test_each_int64_proto_still_references_scaling_md():
    """Regression: H3's SCALING.md reference must survive the cleanup edits."""
    missing = []
    for proto_path in SCALED_PROTO_FILES:
        if not proto_path.exists():
            missing.append(str(proto_path) + " (file not found)")
            continue
        content = proto_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        found = any(
            line.strip().startswith("//") and "SCALING.md" in line
            for line in lines
        )
        if not found:
            missing.append(proto_path.name)
    assert not missing, (
        "The following proto files no longer have a comment line mentioning "
        "'SCALING.md' — H3 invariant broken by the cleanup: " + ", ".join(missing)
    )
