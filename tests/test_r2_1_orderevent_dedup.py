"""
Tests for R2-1 (#20): OrderEvent.source (field 13) and OrderEvent.timestamps (field 14)
deduplication.

Asserts that:
- The top-level `source` field is removed from OrderEvent.
- The top-level `timestamps` field is removed from OrderEvent.
- Field numbers 13 and 14 and the names "source" and "timestamps" are both reserved.
- The `envelope` field is untouched at number 1 (regression guard).
- `order_intention_type` remains at field 15 (regression guard).
- The now-unused `import "common/source.proto"` and `import "common/timestamps.proto"` are absent.
- The regenerated pb2 descriptor matches the proto changes.

Mirrors the L6 (aithusaqr/oets#19) and M2 (aithusaqr/oets#9) fix on FillEvent.
"""

import re
import sys
import pathlib

import pytest

PROTO_PATH = pathlib.Path(__file__).parent.parent / "common" / "execution" / "order_event.proto"
GENERATED_ROOT = pathlib.Path(__file__).parent.parent / "generated" / "python"


def _proto_text() -> str:
    return PROTO_PATH.read_text()


def _orderevent_body(text: str) -> str:
    """Extract the body of the OrderEvent message (between the outermost braces)."""
    match = re.search(r"message\s+OrderEvent\s*\{(.+)\}", text, re.DOTALL)
    assert match, "Could not locate OrderEvent message body in order_event.proto"
    return match.group(1)


# ---------------------------------------------------------------------------
# Proto-level assertions
# ---------------------------------------------------------------------------


def test_source_field_removed():
    """No top-level field declaration for `source` inside OrderEvent."""
    body = _orderevent_body(_proto_text())
    # A field declaration looks like: <type> source = <number>;
    # Must NOT match the reserved "source"; line or comments.
    field_decl = re.compile(r"^\s*\w[\w.]*\s+source\s*=\s*\d+", re.MULTILINE)
    matches = field_decl.findall(body)
    assert not matches, (
        f"Found unexpected top-level 'source' field declaration(s) in OrderEvent: {matches}"
    )


def test_timestamps_field_removed():
    """No top-level field declaration for `timestamps` inside OrderEvent."""
    body = _orderevent_body(_proto_text())
    field_decl = re.compile(r"^\s*\w[\w.]*\s+timestamps\s*=\s*\d+", re.MULTILINE)
    matches = field_decl.findall(body)
    assert not matches, (
        f"Found unexpected top-level 'timestamps' field declaration(s) in OrderEvent: {matches}"
    )


def test_fields_13_14_reserved():
    """Field numbers 13 and 14 must both appear in reserved declarations in OrderEvent."""
    body = _orderevent_body(_proto_text())
    # Extract all reserved number groups: e.g. "reserved 13, 14;" -> ["13, 14"]
    reserved_groups = re.findall(r"reserved\s+([\d,\s]+);", body)
    all_numbers: list[int] = []
    for group in reserved_groups:
        all_numbers.extend(int(n.strip()) for n in group.split(",") if n.strip())
    assert 13 in all_numbers, (
        f"Field number 13 not found in any reserved declaration inside OrderEvent. "
        f"Found reserved numbers: {all_numbers}"
    )
    assert 14 in all_numbers, (
        f"Field number 14 not found in any reserved declaration inside OrderEvent. "
        f"Found reserved numbers: {all_numbers}"
    )


def test_field_names_source_timestamps_reserved():
    """The names "source" and "timestamps" must both be reserved in OrderEvent."""
    body = _orderevent_body(_proto_text())
    # Extract all reserved name groups: e.g. 'reserved "source", "timestamps";'
    reserved_names_raw = re.findall(r'reserved\s+("[\w",\s]+");', body)
    all_names: list[str] = []
    for group in reserved_names_raw:
        all_names.extend(
            n.strip().strip('"') for n in group.split(",") if n.strip()
        )
    assert "source" in all_names, (
        f"Name 'source' not found in any reserved name declaration inside OrderEvent. "
        f"Found reserved names: {all_names}"
    )
    assert "timestamps" in all_names, (
        f"Name 'timestamps' not found in any reserved name declaration inside OrderEvent. "
        f"Found reserved names: {all_names}"
    )


def test_envelope_field_still_present():
    """OetsEventEnvelope envelope = 1 must remain (regression guard)."""
    body = _orderevent_body(_proto_text())
    assert re.search(r"\benvelope\s*=\s*1\b", body), (
        "envelope field (number 1) appears to have been removed from OrderEvent — "
        "this should NOT have been touched.\n"
        f"OrderEvent body:\n{body}"
    )


def test_order_intention_type_still_at_15():
    """OrderIntentionType order_intention_type = 15 must remain unchanged (regression guard)."""
    body = _orderevent_body(_proto_text())
    pattern = re.compile(
        r"^\s*OrderIntentionType\s+order_intention_type\s*=\s*15\s*;", re.MULTILINE
    )
    assert pattern.search(body), (
        "OrderIntentionType order_intention_type = 15 not found in OrderEvent. "
        "The field was accidentally removed or renumbered — it must stay at 15.\n"
        f"OrderEvent body:\n{body}"
    )


def test_unused_imports_removed():
    """Neither import \"common/timestamps.proto\" nor import \"common/source.proto\" may appear."""
    text = _proto_text()
    assert 'import "common/timestamps.proto"' not in text, (
        "Found 'import \"common/timestamps.proto\"' still present in order_event.proto. "
        "It is unused after EventTimestamp timestamps = 14 was removed and should be deleted."
    )
    assert 'import "common/source.proto"' not in text, (
        "Found 'import \"common/source.proto\"' still present in order_event.proto. "
        "It is unused after SourceReference source = 13 was removed and should be deleted."
    )


# ---------------------------------------------------------------------------
# Generated pb2 descriptor assertions
# ---------------------------------------------------------------------------


def test_generated_pb2_in_sync():
    """The regenerated order_event_pb2 descriptor must reflect all proto changes."""
    gen_root = str(GENERATED_ROOT)
    if gen_root not in sys.path:
        sys.path.insert(0, gen_root)

    try:
        from common.execution import order_event_pb2  # noqa: PLC0415
    except ImportError as exc:
        pytest.fail(f"Could not import order_event_pb2: {exc}")

    descriptor = order_event_pb2.OrderEvent.DESCRIPTOR

    field_names = {f.name for f in descriptor.fields}
    field_numbers = set(descriptor.fields_by_number.keys())

    # `source` must be absent
    assert "source" not in field_names, (
        f"'source' is still present in OrderEvent descriptor fields. "
        f"pb2 is out of sync with the proto. Fields: {sorted(field_names)}"
    )

    # `timestamps` must be absent
    assert "timestamps" not in field_names, (
        f"'timestamps' is still present in OrderEvent descriptor fields. "
        f"pb2 is out of sync with the proto. Fields: {sorted(field_names)}"
    )

    # Field number 13 must not be assigned to any field
    assert 13 not in field_numbers, (
        f"Field number 13 is still in use in OrderEvent descriptor — "
        f"pb2 is out of sync with the proto. Field numbers: {sorted(field_numbers)}"
    )

    # Field number 14 must not be assigned to any field
    assert 14 not in field_numbers, (
        f"Field number 14 is still in use in OrderEvent descriptor — "
        f"pb2 is out of sync with the proto. Field numbers: {sorted(field_numbers)}"
    )

    # `envelope` must be at number 1
    assert "envelope" in field_names, (
        f"'envelope' field is missing from OrderEvent descriptor entirely. "
        f"Fields present: {sorted(field_names)}"
    )
    assert descriptor.fields_by_name["envelope"].number == 1, (
        f"'envelope' field number changed: got {descriptor.fields_by_name['envelope'].number}, "
        "expected 1."
    )

    # `order_intention_type` must be at number 15
    assert "order_intention_type" in field_names, (
        f"'order_intention_type' field is missing from OrderEvent descriptor entirely. "
        f"Fields present: {sorted(field_names)}"
    )
    assert descriptor.fields_by_name["order_intention_type"].number == 15, (
        f"'order_intention_type' field number changed: "
        f"got {descriptor.fields_by_name['order_intention_type'].number}, expected 15."
    )
