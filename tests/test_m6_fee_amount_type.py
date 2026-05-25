"""
M6 (#13): Fee.amount must be int64, not string.

Covers:
  1. Proto source declares `int64 amount = 2;`
  2. Field number 2 is unchanged (regression)
  3. `string asset = 1;` is unchanged (regression)
  4. `fee_type = 3;` field number is unchanged (H2 #6 converted type to FeeType enum)
  5. FeeType enum is intact (all 7 entries, original numbers)
  6. pb2 descriptor reports TYPE_INT64 for amount, field number 2
  7. Round-trip serialisation with an int64 value works correctly
"""

import re
import sys
import os

import pytest

PROTO_PATH = os.path.join(
    os.path.dirname(__file__), "..", "common", "reconciliation", "fee_event.proto"
)
GENERATED_ROOT = os.path.join(os.path.dirname(__file__), "..", "generated", "python")


def _proto_text():
    with open(PROTO_PATH, "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Proto-source tests
# ---------------------------------------------------------------------------

def test_fee_amount_is_int64():
    """Fee.amount field declaration must use int64, not string."""
    text = _proto_text()
    current_decl = re.search(r"\w+ amount = \d+;", text)
    assert "int64 amount = 2;" in text, (
        "Expected 'int64 amount = 2;' in fee_event.proto but it was not found. "
        "Current amount declaration: " + str(current_decl)
    )


def test_fee_amount_field_number_unchanged():
    """Field number for amount must still be 2 (no renumbering)."""
    text = _proto_text()
    match = re.search(r"\bint64\s+amount\s*=\s*(\d+)\s*;", text)
    assert match is not None, "Could not find 'int64 amount = <number>;' in fee_event.proto"
    assert match.group(1) == "2", (
        f"Fee.amount field number changed: expected 2, got {match.group(1)}"
    )


def test_fee_asset_unchanged():
    """Fee.asset must remain 'string asset = 1;' — M6 must not touch it."""
    text = _proto_text()
    assert "string asset = 1;" in text, (
        "Expected 'string asset = 1;' to remain unchanged in fee_event.proto"
    )


def test_fee_type_field_number_unchanged():
    """Fee.fee_type must still be field number 3 — H2 (#6) converted the type to FeeType enum."""
    text = _proto_text()
    match = re.search(r"\bfee_type\s*=\s*(\d+)\s*;", text)
    assert match is not None, "Could not find 'fee_type = <number>;' in fee_event.proto"
    assert match.group(1) == "3", (
        f"Fee.fee_type field number changed: expected 3, got {match.group(1)}"
    )


def test_fee_type_enum_intact():
    """FeeType enum must retain all 7 original entries with original field numbers."""
    text = _proto_text()
    expected = {
        "FEE_TYPE_UNKNOWN": 0,
        "FEE_TYPE_TRADING": 1,
        "FEE_TYPE_FUNDING": 2,
        "FEE_TYPE_ACCOUNT": 3,
        "FEE_TYPE_BORROW": 4,
        "FEE_TYPE_PROTOCOL": 5,
        "FEE_TYPE_PRIORITY": 6,
    }
    for name, number in expected.items():
        pattern = rf"\b{name}\s*=\s*{number}\s*;"
        assert re.search(pattern, text), (
            f"FeeType enum entry '{name} = {number}' not found in fee_event.proto"
        )


# ---------------------------------------------------------------------------
# pb2 descriptor tests
# ---------------------------------------------------------------------------

def _import_pb2():
    if GENERATED_ROOT not in sys.path:
        sys.path.insert(0, GENERATED_ROOT)
    from common.reconciliation import fee_event_pb2  # noqa: PLC0415
    return fee_event_pb2


def test_pb2_descriptor_amount_is_int64():
    """pb2 descriptor must report TYPE_INT64 for Fee.amount at field number 2."""
    pb2 = _import_pb2()
    from google.protobuf.descriptor import FieldDescriptor

    fee_descriptor = pb2.Fee.DESCRIPTOR
    amount_field = fee_descriptor.fields_by_name.get("amount")
    assert amount_field is not None, "Field 'amount' not found in Fee descriptor"
    assert amount_field.type == FieldDescriptor.TYPE_INT64, (
        f"Expected Fee.amount type to be TYPE_INT64 ({FieldDescriptor.TYPE_INT64}), "
        f"got {amount_field.type}"
    )
    assert amount_field.number == 2, (
        f"Expected Fee.amount field number 2, got {amount_field.number}"
    )


# ---------------------------------------------------------------------------
# Wire round-trip test
# ---------------------------------------------------------------------------

def test_roundtrip_fee_with_int64_amount():
    """Serialise a Fee with an int64 amount, deserialise, and confirm exact value."""
    pb2 = _import_pb2()

    original = pb2.Fee(asset="USDC", amount=1500000)
    serialised = original.SerializeToString()
    recovered = pb2.Fee()
    recovered.ParseFromString(serialised)

    assert recovered.asset == "USDC", (
        f"asset round-trip failed: expected 'USDC', got '{recovered.asset}'"
    )
    assert recovered.amount == 1500000, (
        f"amount round-trip failed: expected 1500000 (int), got {recovered.amount!r}"
    )
    assert isinstance(recovered.amount, int), (
        f"amount must be int after deserialisation, got {type(recovered.amount)}"
    )
