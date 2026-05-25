"""
H2 (#6): Fee.fee_type must use the FeeType enum, not raw string.

Covers:
  1. Proto source declares `FeeType fee_type = 3;` inside Fee message
  2. No `string fee_type` declaration remains in the Fee body
  3. `int64 amount = 2;` is still present (M6 regression guard)
  4. `string asset = 1;` is still present (field regression guard)
  5. FeeType enum is intact (all 7 entries, original numbers)
  6. pb2 descriptor reports TYPE_ENUM for fee_type, full_name == "oets.v1.FeeType", field number 3
  7. Round-trip serialisation with a FeeType enum value preserves the value correctly
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


def _fee_body(text):
    """Extract the body of the Fee message (between the outer braces)."""
    match = re.search(r"\bmessage\s+Fee\s*\{([^}]*)\}", text, re.DOTALL)
    assert match is not None, "Could not locate 'message Fee { ... }' in fee_event.proto"
    return match.group(1)


# ---------------------------------------------------------------------------
# Proto-source tests
# ---------------------------------------------------------------------------

def test_fee_fee_type_is_feetype_enum():
    """Fee.fee_type field declaration must use FeeType enum at field number 3."""
    text = _proto_text()
    body = _fee_body(text)
    match = re.search(r"\bFeeType\s+fee_type\s*=\s*3\s*;", body)
    assert match is not None, (
        "Expected 'FeeType fee_type = 3;' inside Fee message body, but it was not found. "
        "Body: " + body.strip()
    )


def test_fee_fee_type_no_longer_string():
    """Fee.fee_type must NOT be declared as 'string fee_type' anywhere in the Fee body."""
    text = _proto_text()
    body = _fee_body(text)
    string_match = re.search(r"\bstring\s+fee_type\b", body)
    assert string_match is None, (
        "Found 'string fee_type' inside Fee message body — H2 should have converted it to FeeType enum. "
        "Body: " + body.strip()
    )


def test_fee_amount_still_int64():
    """Regression: Fee.amount must still be 'int64 amount = 2;' (M6 work intact)."""
    text = _proto_text()
    body = _fee_body(text)
    match = re.search(r"\bint64\s+amount\s*=\s*2\s*;", body)
    assert match is not None, (
        "Regression: 'int64 amount = 2;' no longer present in Fee message body (M6 change broken). "
        "Body: " + body.strip()
    )


def test_fee_asset_still_string():
    """Regression: Fee.asset must still be 'string asset = 1;'."""
    text = _proto_text()
    body = _fee_body(text)
    match = re.search(r"\bstring\s+asset\s*=\s*1\s*;", body)
    assert match is not None, (
        "Regression: 'string asset = 1;' no longer present in Fee message body. "
        "Body: " + body.strip()
    )


def test_feetype_enum_intact():
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
        entry_match = re.search(pattern, text)
        assert entry_match is not None, (
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


def test_pb2_descriptor_fee_type_is_enum():
    """pb2 descriptor must report TYPE_ENUM for Fee.fee_type with correct enum name and field number 3."""
    pb2 = _import_pb2()
    from google.protobuf.descriptor import FieldDescriptor

    fee_descriptor = pb2.Fee.DESCRIPTOR
    fee_type_field = fee_descriptor.fields_by_name.get("fee_type")
    assert fee_type_field is not None, "Field 'fee_type' not found in Fee descriptor"
    assert fee_type_field.type == FieldDescriptor.TYPE_ENUM, (
        f"Expected Fee.fee_type type to be TYPE_ENUM ({FieldDescriptor.TYPE_ENUM}), "
        f"got {fee_type_field.type}"
    )
    full_name = fee_type_field.enum_type.full_name
    assert full_name == "oets.v1.FeeType", (
        f"Expected Fee.fee_type enum_type.full_name to be 'oets.v1.FeeType', got '{full_name}'"
    )
    assert fee_type_field.number == 3, (
        f"Expected Fee.fee_type field number 3, got {fee_type_field.number}"
    )


# ---------------------------------------------------------------------------
# Wire round-trip test
# ---------------------------------------------------------------------------

def test_roundtrip_fee_with_enum():
    """Serialise a Fee with a FeeType enum value, deserialise, and confirm exact enum value preserved."""
    pb2 = _import_pb2()

    trading_value = pb2.FeeType.Value("FEE_TYPE_TRADING")
    original = pb2.Fee(asset="USDC", amount=100, fee_type=trading_value)
    serialised = original.SerializeToString()
    recovered = pb2.Fee()
    recovered.ParseFromString(serialised)

    assert recovered.asset == "USDC", (
        f"asset round-trip failed: expected 'USDC', got '{recovered.asset}'"
    )
    assert recovered.amount == 100, (
        f"amount round-trip failed: expected 100, got {recovered.amount!r}"
    )
    expected_enum = pb2.FeeType.Value("FEE_TYPE_TRADING")
    assert recovered.fee_type == expected_enum, (
        f"fee_type round-trip failed: expected FEE_TYPE_TRADING ({expected_enum}), "
        f"got {recovered.fee_type!r}"
    )
