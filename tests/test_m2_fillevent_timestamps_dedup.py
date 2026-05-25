"""
Tests for M2 (#9): FillEvent timestamps field deduplication.

Verifies that EventTimestamp timestamps = 19 has been removed from FillEvent,
that field numbers 15 and 19 are reserved, that the now-unused
common/timestamps.proto import is gone, and that the regenerated pb2 is in sync.
"""

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROTO_PATH = Path(__file__).parents[1] / "common" / "execution" / "fill_event.proto"
GENERATED_ROOT = Path(__file__).parents[1] / "generated" / "python"


def _read_proto() -> str:
    return PROTO_PATH.read_text()


def _extract_message_body(proto_text: str) -> str:
    """Return the text inside the outermost FillEvent { ... } braces."""
    match = re.search(r"message\s+FillEvent\s*\{(.+)\}", proto_text, re.DOTALL)
    assert match, "Could not locate FillEvent { ... } in fill_event.proto"
    return match.group(1)


# ---------------------------------------------------------------------------
# Proto-level tests
# ---------------------------------------------------------------------------


def test_timestamps_field_removed():
    """No top-level field declaration named 'timestamps' should exist in FillEvent."""
    body = _extract_message_body(_read_proto())
    # Match lines like:   EventTimestamp timestamps = 19;
    # We check for a *field declaration* (type + name + = + number), not a reserved string.
    field_decl_pattern = re.compile(
        r"^\s*\w[\w.]*\s+timestamps\s*=\s*\d+", re.MULTILINE
    )
    assert not field_decl_pattern.search(body), (
        "FillEvent still contains a top-level 'timestamps' field declaration. "
        "It should have been removed in M2 (#9)."
    )


def test_field_19_reserved():
    """Field number 19 must appear in a reserved declaration inside FillEvent."""
    body = _extract_message_body(_read_proto())
    # Match: reserved 19; OR reserved 15, 19; OR reserved 19, 20; etc.
    reserved_numbers = re.findall(r"reserved\s+([\d,\s]+);", body)
    all_numbers: list[int] = []
    for group in reserved_numbers:
        all_numbers.extend(int(n.strip()) for n in group.split(",") if n.strip())
    assert 19 in all_numbers, (
        f"Field number 19 not found in any reserved declaration inside FillEvent. "
        f"Found reserved numbers: {all_numbers}"
    )


def test_field_name_timestamps_reserved():
    """The string 'timestamps' must appear in a reserved name declaration inside FillEvent."""
    body = _extract_message_body(_read_proto())
    # Match: reserved "timestamps"; OR reserved "source", "timestamps"; etc.
    reserved_names_raw = re.findall(r'reserved\s+("[\w",\s]+");', body)
    all_names: list[str] = []
    for group in reserved_names_raw:
        all_names.extend(
            n.strip().strip('"') for n in group.split(",") if n.strip()
        )
    assert "timestamps" in all_names, (
        f"Name 'timestamps' not found in any reserved name declaration inside FillEvent. "
        f"Found reserved names: {all_names}"
    )


def test_field_15_still_reserved():
    """Regression: field 15 and name 'source' (L6's work) must still be reserved."""
    body = _extract_message_body(_read_proto())

    reserved_numbers = re.findall(r"reserved\s+([\d,\s]+);", body)
    all_numbers: list[int] = []
    for group in reserved_numbers:
        all_numbers.extend(int(n.strip()) for n in group.split(",") if n.strip())
    assert 15 in all_numbers, (
        f"Field number 15 is no longer reserved — L6's work (#19) has been undone. "
        f"Found reserved numbers: {all_numbers}"
    )

    reserved_names_raw = re.findall(r'reserved\s+("[\w",\s]+");', body)
    all_names: list[str] = []
    for group in reserved_names_raw:
        all_names.extend(
            n.strip().strip('"') for n in group.split(",") if n.strip()
        )
    assert "source" in all_names, (
        f"Name 'source' is no longer reserved — L6's work (#19) has been undone. "
        f"Found reserved names: {all_names}"
    )


def test_envelope_field_still_present():
    """Regression: OetsEventEnvelope envelope must still be at field 1."""
    body = _extract_message_body(_read_proto())
    pattern = re.compile(
        r"^\s*OetsEventEnvelope\s+envelope\s*=\s*1\s*;", re.MULTILINE
    )
    assert pattern.search(body), (
        "OetsEventEnvelope envelope = 1 not found in FillEvent. "
        "The envelope field was accidentally removed or renumbered."
    )


def test_realized_pnl_unchanged():
    """Regression: realized_pnl=16, realized_pnl_asset=17, position_side=18 are unchanged."""
    body = _extract_message_body(_read_proto())

    checks = [
        (r"^\s*int64\s+realized_pnl\s*=\s*16\s*;", "int64 realized_pnl = 16"),
        (r"^\s*string\s+realized_pnl_asset\s*=\s*17\s*;", "string realized_pnl_asset = 17"),
        (r"^\s*PositionSide\s+position_side\s*=\s*18\s*;", "PositionSide position_side = 18"),
    ]
    for pattern_str, description in checks:
        pattern = re.compile(pattern_str, re.MULTILINE)
        assert pattern.search(body), (
            f"Expected field '{description}' not found in FillEvent body. "
            "Fields adjacent to the removed timestamps field may have been renumbered."
        )


def test_unused_timestamps_import_removed():
    """The import for common/timestamps.proto must be absent (no longer needed)."""
    proto_text = _read_proto()
    assert 'import "common/timestamps.proto"' not in proto_text, (
        "The import 'common/timestamps.proto' is still present in fill_event.proto. "
        "It should have been removed when EventTimestamp timestamps = 19 was deleted."
    )


# ---------------------------------------------------------------------------
# Generated pb2 in-sync test
# ---------------------------------------------------------------------------


def test_generated_pb2_in_sync():
    """The regenerated fill_event_pb2.py must reflect all proto changes."""
    sys.path.insert(0, str(GENERATED_ROOT))
    try:
        from common.execution import fill_event_pb2  # noqa: PLC0415
    except ImportError as exc:
        pytest.fail(f"Could not import fill_event_pb2: {exc}")

    descriptor = fill_event_pb2.FillEvent.DESCRIPTOR

    # No field named 'timestamps' or 'source'
    field_names = {f.name for f in descriptor.fields}
    assert "timestamps" not in field_names, (
        f"Descriptor still has a 'timestamps' field. pb2 is out of sync with the proto. "
        f"Fields present: {sorted(field_names)}"
    )
    assert "source" not in field_names, (
        f"Descriptor still has a 'source' field. L6's change is missing from pb2. "
        f"Fields present: {sorted(field_names)}"
    )

    # Field numbers 15 and 19 must not appear
    field_numbers = set(descriptor.fields_by_number.keys())
    assert 19 not in field_numbers, (
        f"Field number 19 is still present in the descriptor. "
        f"pb2 is out of sync with the proto. Field numbers: {sorted(field_numbers)}"
    )
    assert 15 not in field_numbers, (
        f"Field number 15 is still present in the descriptor. "
        f"pb2 is out of sync with the proto. Field numbers: {sorted(field_numbers)}"
    )

    # Key surviving fields at expected numbers
    surviving = {
        "envelope": 1,
        "realized_pnl": 16,
        "position_side": 18,
    }
    for name, expected_number in surviving.items():
        field = descriptor.fields_by_name.get(name)
        assert field is not None, (
            f"Field '{name}' is missing from FillEvent descriptor entirely."
        )
        assert field.number == expected_number, (
            f"Field '{name}' has number {field.number}, expected {expected_number}. "
            "It may have been accidentally renumbered."
        )
