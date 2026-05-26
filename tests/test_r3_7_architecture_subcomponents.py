"""
R3-7 (#49): Tests that verify docs/ARCHITECTURE.md accurately describes
the sub-component layer now that Fee is wired in via R3-1.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ARCH_MD = REPO_ROOT / "docs" / "ARCHITECTURE.md"
COMMON_DIR = REPO_ROOT / "common"


def _read_arch() -> str:
    return ARCH_MD.read_text(encoding="utf-8")


def _parse_subcomponent_table(text: str) -> list[dict]:
    """
    Parse the '## Sub-components currently in the schema' table.

    Returns a list of dicts with keys: name, defined_in, embedded_by_raw.
    """
    section_match = re.search(
        r"## Sub-components currently in the schema\n.*?\n\|.*?\|\n\|[-| ]+\|\n(.*?)(?=\n##|\Z)",
        text,
        re.DOTALL,
    )
    assert section_match, (
        "Could not locate the sub-components table in ARCHITECTURE.md. "
        "Expected a section headed '## Sub-components currently in the schema' "
        "followed by a markdown table."
    )
    table_body = section_match.group(1)
    rows = []
    for line in table_body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip().strip("`") for c in line.split("|") if c.strip()]
        if len(cols) < 3:
            continue
        rows.append(
            {
                "name": cols[0],
                "defined_in": cols[1],
                "embedded_by_raw": cols[2],
            }
        )
    assert rows, "Sub-components table parsed but contained no data rows."
    return rows


# ---------------------------------------------------------------------------
# 1. Section heading exists
# ---------------------------------------------------------------------------


def test_architecture_md_has_subcomponents_section():
    """The doc must contain the new sub-components section heading."""
    text = _read_arch()
    assert "## Sub-components currently in the schema" in text, (
        "ARCHITECTURE.md is missing the '## Sub-components currently in the schema' heading. "
        "R3-7 requires this section to be present."
    )


# ---------------------------------------------------------------------------
# 2. Every 'Defined in' file actually exists
# ---------------------------------------------------------------------------


def test_each_listed_subcomponent_file_exists():
    """Every 'Defined in' path in the table must point to a real .proto file."""
    rows = _parse_subcomponent_table(_read_arch())
    missing = []
    for row in rows:
        proto_path = REPO_ROOT / row["defined_in"]
        if not proto_path.exists():
            missing.append((row["name"], str(proto_path)))

    assert not missing, (
        "The following sub-components list a 'Defined in' file that does not exist:\n"
        + "\n".join(f"  {name}: {path}" for name, path in missing)
    )


# ---------------------------------------------------------------------------
# 3. Each sub-component is actually used as a field type in its listed parents
# ---------------------------------------------------------------------------


def _extract_parent_names(embedded_by_raw: str) -> list[str]:
    """
    Extract parent message names from an 'Embedded by' cell.

    The cell may contain parenthetical qualifications like "(in `source` field)"
    or field details like "(`repeated Fee fees`)"; we want bare CamelCase names.
    """
    # Strip backtick-quoted phrases (field names / annotations)
    cleaned = re.sub(r"`[^`]+`", " ", embedded_by_raw)
    # Extract CamelCase tokens (message names start with uppercase)
    return re.findall(r"\b([A-Z][A-Za-z]+)\b", cleaned)


def test_each_listed_subcomponent_actually_embedded():
    """
    For every (sub-component, parent-message) pair implied by the 'Embedded by'
    column, grep the proto files to confirm the sub-component appears as a field
    type in at least one proto that mentions the parent message.
    """
    rows = _parse_subcomponent_table(_read_arch())
    all_proto_text: dict[Path, str] = {}
    for p in COMMON_DIR.rglob("*.proto"):
        all_proto_text[p] = p.read_text(encoding="utf-8")

    failures = []
    for row in rows:
        name = row["name"]
        parents = _extract_parent_names(row["embedded_by_raw"])
        if not parents:
            continue  # nothing to check

        for parent in parents:
            # Find proto files that define the parent message
            parent_files = [
                path
                for path, text in all_proto_text.items()
                if re.search(r"\bmessage\s+" + re.escape(parent) + r"\b", text)
            ]
            if not parent_files:
                failures.append(
                    f"{name} -> {parent}: no proto file defines 'message {parent}'"
                )
                continue

            # Check that at least one of those files uses the sub-component as a field type
            found = any(
                # matches a field declaration like: `SomeType fieldname = N;`
                re.search(
                    r"\b" + re.escape(name) + r"\b\s+\w+\s*=\s*\d+",
                    all_proto_text[pf],
                )
                for pf in parent_files
            )
            if not found:
                failures.append(
                    f"{name} claimed embedded by {parent}, but no field of type "
                    f"'{name}' found in: "
                    + ", ".join(str(pf.relative_to(REPO_ROOT)) for pf in parent_files)
                )

    assert not failures, (
        "Sub-component embedding claims in ARCHITECTURE.md do not match the proto sources:\n"
        + "\n".join(f"  - {f}" for f in failures)
    )


# ---------------------------------------------------------------------------
# 4. No orphan sub-components (each must appear as a field type outside own file)
# ---------------------------------------------------------------------------


def test_no_orphan_subcomponents_listed():
    """
    Every sub-component in the table must appear as a field type in at least one
    proto file *other than* its own definition file.  This guards against a
    recurrence of the pre-R3-1 orphan state.
    """
    rows = _parse_subcomponent_table(_read_arch())
    all_proto_text: dict[Path, str] = {}
    for p in COMMON_DIR.rglob("*.proto"):
        all_proto_text[p] = p.read_text(encoding="utf-8")

    orphans = []
    for row in rows:
        name = row["name"]
        own_file = REPO_ROOT / row["defined_in"]
        used_outside = any(
            re.search(r"\b" + re.escape(name) + r"\b\s+\w+\s*=\s*\d+", text)
            for path, text in all_proto_text.items()
            if path != own_file
        )
        if not used_outside:
            orphans.append(
                f"{name} (defined in {row['defined_in']}) is not used as a field type "
                "in any other proto file — it is an orphan sub-component."
            )

    assert not orphans, (
        "The following sub-components listed in ARCHITECTURE.md are orphans "
        "(not embedded anywhere outside their own file):\n"
        + "\n".join(f"  - {o}" for o in orphans)
    )


# ---------------------------------------------------------------------------
# 5. Cross-check: envelope table and sub-components table are consistent
# ---------------------------------------------------------------------------

# Messages that carry OetsEventEnvelope according to the top table in the doc
_ENVELOPE_BEARING = {
    "FillEvent",
    "OrderEvent",
    "CashFlowEvent",
    "SettlementEvent",
    "FundingRate",
    "FundingPayment",
}

# Messages that do NOT carry OetsEventEnvelope
_NON_ENVELOPE = {
    "PositionSnapshot",
    "PositionDelta",
    "BalanceSnapshot",
    "BalanceDelta",
    "Fee",
}


def test_architecture_table_envelope_consistent_with_envelope_table():
    """
    The sub-components table's 'OetsEventEnvelope' row must list exactly the
    envelope-bearing messages from the top table, and no non-envelope message.
    """
    rows = _parse_subcomponent_table(_read_arch())
    envelope_row = next(
        (r for r in rows if r["name"] == "OetsEventEnvelope"), None
    )
    assert envelope_row is not None, (
        "OetsEventEnvelope must appear as a row in the sub-components table "
        "(it is itself a sub-component embedded in every event-bearing message)."
    )

    embedded_by_raw = envelope_row["embedded_by_raw"]

    # Every envelope-bearing message should be mentioned in the row
    missing_from_row = [
        m for m in _ENVELOPE_BEARING if m not in embedded_by_raw
    ]
    assert not missing_from_row, (
        "OetsEventEnvelope 'Embedded by' cell is missing these envelope-bearing messages: "
        + ", ".join(missing_from_row)
    )

    # No non-envelope message should appear there
    wrongly_listed = [
        m for m in _NON_ENVELOPE if m in embedded_by_raw
    ]
    assert not wrongly_listed, (
        "OetsEventEnvelope 'Embedded by' cell incorrectly lists these non-envelope messages: "
        + ", ".join(wrongly_listed)
    )

    # The proto files must back up the claim: each envelope-bearing message should
    # have an OetsEventEnvelope field in its proto.
    all_proto_text: dict[Path, str] = {}
    for p in COMMON_DIR.rglob("*.proto"):
        all_proto_text[p] = p.read_text(encoding="utf-8")

    mismatches = []
    for msg in _ENVELOPE_BEARING:
        parent_files = [
            path
            for path, text in all_proto_text.items()
            if re.search(r"\bmessage\s+" + re.escape(msg) + r"\b", text)
        ]
        found = any(
            re.search(r"\bOetsEventEnvelope\b\s+\w+\s*=\s*\d+", all_proto_text[pf])
            for pf in parent_files
        )
        if not found:
            mismatches.append(
                f"{msg} is listed as envelope-bearing in the top table but has no "
                "OetsEventEnvelope field in its proto."
            )

    assert not mismatches, "\n".join(mismatches)
