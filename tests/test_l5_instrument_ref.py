"""Tests for L5 (#18): InstrumentRef must embed only stable identifier fields.

These tests parse common/instrument.proto directly (text-level) and also
interrogate the regenerated _pb2 descriptor to confirm the wire bindings are
in sync with the source proto.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
INSTRUMENT_PROTO = REPO_ROOT / "common" / "instrument.proto"

REMOVED_FIELDS = {
    "price_precision_rounding",
    "size_precision_rounding",
    "lot_size",
    "notional_lot_size",
    "days_to_expiry",
}
RESERVED_NUMBERS = {6, 8, 11, 12, 16}

KEPT_FIELDS = {
    "instrument_id": 1,
    "base_asset": 2,
    "quote_asset": 3,
    "venue_instrument_id": 4,
    "price_precision": 5,
    "size_precision": 7,
    "minimum_size": 9,
    "minimum_notional_size": 10,
    "contract_type": 13,
    "alias": 14,
    "expiry_date": 15,
    "currency": 17,
    "position_currency": 18,
}


def _instrument_ref_body(proto_text: str) -> str:
    """Extract the text inside the InstrumentRef { ... } block."""
    match = re.search(
        r"\bmessage\s+InstrumentRef\s*\{(.*?)\}",
        proto_text,
        re.DOTALL,
    )
    assert match, "Could not locate `message InstrumentRef { ... }` in instrument.proto"
    return match.group(1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_removed_fields_not_present():
    """Removed fields must not appear as field declarations inside InstrumentRef."""
    proto_text = INSTRUMENT_PROTO.read_text(encoding="utf-8")
    body = _instrument_ref_body(proto_text)

    # Match actual field declaration lines: <type> <name> = <number>;
    # Comments and reserved lines are intentionally excluded.
    field_decl_pattern = re.compile(
        r"^\s*\w[\w.]*\s+(\w+)\s*=\s*\d+\s*;",
        re.MULTILINE,
    )
    declared_names = {m.group(1) for m in field_decl_pattern.finditer(body)}

    collisions = REMOVED_FIELDS & declared_names
    assert not collisions, (
        f"These mutable/computed fields must NOT appear as field declarations in "
        f"InstrumentRef, but were found: {sorted(collisions)}"
    )


def test_field_numbers_reserved():
    """The removed field numbers must appear in a `reserved` declaration inside InstrumentRef."""
    proto_text = INSTRUMENT_PROTO.read_text(encoding="utf-8")
    body = _instrument_ref_body(proto_text)

    # Collect all numbers that appear in numeric reserved statements.
    # Supports: reserved 6, 8, 11, 12, 16; (any order, any whitespace)
    found_numbers: set[int] = set()
    for m in re.finditer(r"\breserved\b([^;\"]+);", body):
        for num_str in re.findall(r"\d+", m.group(1)):
            found_numbers.add(int(num_str))

    missing = RESERVED_NUMBERS - found_numbers
    assert not missing, (
        f"Field numbers {sorted(missing)} must be declared `reserved` inside InstrumentRef "
        f"to prevent silent re-use (see #18). Found reserved numbers: {sorted(found_numbers)}"
    )


def test_field_names_reserved():
    """The removed field names must appear in a `reserved \"...\"` declaration inside InstrumentRef."""
    proto_text = INSTRUMENT_PROTO.read_text(encoding="utf-8")
    body = _instrument_ref_body(proto_text)

    # Collect all quoted names from reserved statements.
    found_names: set[str] = set()
    for m in re.finditer(r'\breserved\b([^;]*);', body):
        clause = m.group(1)
        for name in re.findall(r'"(\w+)"', clause):
            found_names.add(name)

    missing = REMOVED_FIELDS - found_names
    assert not missing, (
        f"Field names {sorted(missing)} must be declared `reserved` inside InstrumentRef "
        f"to prevent silent re-use (see #18). Found reserved names: {sorted(found_names)}"
    )


def test_kept_fields_still_present():
    """Stable identifier fields must still be present with their original field numbers."""
    proto_text = INSTRUMENT_PROTO.read_text(encoding="utf-8")
    body = _instrument_ref_body(proto_text)

    # Parse field declarations: <type> <name> = <number>;
    field_decl_pattern = re.compile(
        r"^\s*\w[\w.]*\s+(\w+)\s*=\s*(\d+)\s*;",
        re.MULTILINE,
    )
    declared = {m.group(1): int(m.group(2)) for m in field_decl_pattern.finditer(body)}

    for field_name, expected_num in KEPT_FIELDS.items():
        assert field_name in declared, (
            f"Field `{field_name}` must still be present in InstrumentRef "
            f"but was not found. Declared fields: {list(declared.keys())}"
        )
        actual_num = declared[field_name]
        assert actual_num == expected_num, (
            f"Field `{field_name}` must keep field number {expected_num} "
            f"for wire compatibility, but got {actual_num}"
        )


def test_no_field_number_collision_with_reserved():
    """No live field declaration inside InstrumentRef may use a reserved field number."""
    proto_text = INSTRUMENT_PROTO.read_text(encoding="utf-8")
    body = _instrument_ref_body(proto_text)

    field_decl_pattern = re.compile(
        r"^\s*\w[\w.]*\s+\w+\s*=\s*(\d+)\s*;",
        re.MULTILINE,
    )
    live_numbers = {int(m.group(1)) for m in field_decl_pattern.finditer(body)}

    collisions = live_numbers & RESERVED_NUMBERS
    assert not collisions, (
        f"Field numbers {sorted(collisions)} are declared `reserved` in InstrumentRef "
        f"but are also used by live field declarations — this would be a proto compile error."
    )


def test_generated_pb2_in_sync():
    """The regenerated instrument_pb2 DESCRIPTOR must reflect the pruned field set."""
    generated = str(REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)

    from common import instrument_pb2  # noqa: PLC0415

    descriptor = instrument_pb2.InstrumentRef.DESCRIPTOR

    live_field_names = {f.name for f in descriptor.fields}

    # Removed fields must NOT be present in the descriptor.
    present_but_should_be_gone = REMOVED_FIELDS & live_field_names
    assert not present_but_should_be_gone, (
        f"The regenerated instrument_pb2 still contains these removed fields in the "
        f"InstrumentRef DESCRIPTOR: {sorted(present_but_should_be_gone)}. "
        f"Run `make generate_python_protos` and commit the result."
    )

    # All kept fields must be present.
    for field_name, expected_num in KEPT_FIELDS.items():
        assert field_name in live_field_names, (
            f"Field `{field_name}` is missing from the InstrumentRef DESCRIPTOR in "
            f"instrument_pb2. Expected fields: {sorted(KEPT_FIELDS.keys())}"
        )
        actual_num = descriptor.fields_by_name[field_name].number
        assert actual_num == expected_num, (
            f"Field `{field_name}` has field number {actual_num} in the DESCRIPTOR "
            f"but expected {expected_num}."
        )
