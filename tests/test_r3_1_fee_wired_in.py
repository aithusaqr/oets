"""R3-1 (#43): Wire Fee into FillEvent and CashFlowEvent — close orphan-message bug.

Fee was defined in fee_event.proto but never embedded. This test suite verifies
the wiring is in place and that the wire round-trip works correctly.

Covers:
  1. FillEvent proto declares `repeated Fee fees = 12;`
  2. FillEvent reserves field 13 and old names "fee", "fee_asset"
  3. FillEvent declares `int64 total_notional_fee = 14;` (renamed from notional_fee)
  4. CashFlowEvent proto declares `Fee fee = 9;`
  5. CashFlowEvent reserves field 10 and old names "fee_amount", "fee_asset_id"
  6. pb2 descriptor: FillEvent.fees is repeated with message_type Fee
  7. pb2 descriptor: CashFlowEvent.fee has message_type Fee
  8. Round-trip: FillEvent with two fees (trading + protocol) survives serialize/deserialize
  9. Round-trip: CashFlowEvent with embedded Fee survives serialize/deserialize
 10. Regression: Fee appears as a field type in at least 2 proto files outside fee_event.proto
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_FILL_PROTO = _REPO_ROOT / "common" / "execution" / "fill_event.proto"
_CASH_FLOW_PROTO = _REPO_ROOT / "common" / "reconciliation" / "cash_flow_event.proto"
_COMMON_DIR = _REPO_ROOT / "common"
_GENERATED = str(_REPO_ROOT / "generated" / "python")


def _ensure_generated_on_path() -> None:
    if _GENERATED not in sys.path:
        sys.path.insert(0, _GENERATED)


def _message_body(text: str, message_name: str) -> str:
    """Return the body (between the outer braces) of the first matching top-level message."""
    pattern = r"message\s+" + re.escape(message_name) + r"\s*\{([^}]*)\}"
    match = re.search(pattern, text, re.DOTALL)
    assert match is not None, (
        f"Could not locate 'message {message_name} {{ ... }}' in proto text"
    )
    return match.group(1)


# ---------------------------------------------------------------------------
# 1. FillEvent declares repeated Fee fees = 12
# ---------------------------------------------------------------------------

def test_fillevent_has_repeated_fees():
    """fill_event.proto must declare 'repeated Fee fees = 12;' inside FillEvent."""
    text = _FILL_PROTO.read_text(encoding="utf-8")
    body = _message_body(text, "FillEvent")
    match = re.search(r"\brepeated\s+Fee\s+fees\s*=\s*12\s*;", body)
    assert match is not None, (
        "Expected 'repeated Fee fees = 12;' inside FillEvent body, but it was not found. "
        "Body:\n" + body.strip()
    )


# ---------------------------------------------------------------------------
# 2. FillEvent reserves field 13 and old names "fee", "fee_asset"
# ---------------------------------------------------------------------------

def test_fillevent_field_13_reserved():
    """FillEvent must reserve field number 13 and the old names 'fee' and 'fee_asset'."""
    text = _FILL_PROTO.read_text(encoding="utf-8")
    body = _message_body(text, "FillEvent")

    number_reserved = re.search(r"\breserved\b[^;]*\b13\b", body)
    assert number_reserved is not None, (
        "FillEvent must reserve field number 13 (old fee_asset). "
        "No 'reserved ... 13 ...' declaration found in FillEvent body:\n" + body.strip()
    )

    for name in ("fee", "fee_asset"):
        name_reserved = re.search(
            r'\breserved\b[^;]*"' + re.escape(name) + r'"', body
        )
        assert name_reserved is not None, (
            f"FillEvent must reserve old field name \"{name}\". "
            f"No 'reserved ... \"{name}\" ...' found in FillEvent body:\n" + body.strip()
        )


# ---------------------------------------------------------------------------
# 3. FillEvent declares int64 total_notional_fee = 14
# ---------------------------------------------------------------------------

def test_fillevent_total_notional_fee():
    """FillEvent must declare 'int64 total_notional_fee = 14;' (renamed from notional_fee)."""
    text = _FILL_PROTO.read_text(encoding="utf-8")
    body = _message_body(text, "FillEvent")
    match = re.search(r"\bint64\s+total_notional_fee\s*=\s*14\s*;", body)
    assert match is not None, (
        "Expected 'int64 total_notional_fee = 14;' inside FillEvent body. "
        "Body:\n" + body.strip()
    )

    # Old name must be reserved, not live
    old_name_live = re.search(r"\bint64\s+notional_fee\s*=\s*14\s*;", body)
    assert old_name_live is None, (
        "FillEvent still contains live 'int64 notional_fee = 14;' — "
        "R3-1 renamed this to total_notional_fee. Body:\n" + body.strip()
    )


# ---------------------------------------------------------------------------
# 4. CashFlowEvent declares Fee fee = 9
# ---------------------------------------------------------------------------

def test_cashflow_has_fee_field():
    """cash_flow_event.proto must declare 'Fee fee = 9;' inside CashFlowEvent."""
    text = _CASH_FLOW_PROTO.read_text(encoding="utf-8")
    body = _message_body(text, "CashFlowEvent")
    match = re.search(r"\bFee\s+fee\s*=\s*9\s*;", body)
    assert match is not None, (
        "Expected 'Fee fee = 9;' inside CashFlowEvent body, but it was not found. "
        "Body:\n" + body.strip()
    )


# ---------------------------------------------------------------------------
# 5. CashFlowEvent reserves field 10 and old names
# ---------------------------------------------------------------------------

def test_cashflow_field_10_reserved():
    """CashFlowEvent must reserve field number 10 and the old names 'fee_amount', 'fee_asset_id'."""
    text = _CASH_FLOW_PROTO.read_text(encoding="utf-8")
    body = _message_body(text, "CashFlowEvent")

    number_reserved = re.search(r"\breserved\b[^;]*\b10\b", body)
    assert number_reserved is not None, (
        "CashFlowEvent must reserve field number 10 (old fee_asset_id). "
        "No 'reserved ... 10 ...' declaration found in CashFlowEvent body:\n" + body.strip()
    )

    for name in ("fee_amount", "fee_asset_id"):
        name_reserved = re.search(
            r'\breserved\b[^;]*"' + re.escape(name) + r'"', body
        )
        assert name_reserved is not None, (
            f"CashFlowEvent must reserve old field name \"{name}\". "
            f"No 'reserved ... \"{name}\" ...' found in CashFlowEvent body:\n" + body.strip()
        )


# ---------------------------------------------------------------------------
# 6. pb2 descriptor: FillEvent.fees is repeated with message_type Fee
# ---------------------------------------------------------------------------

def test_pb2_fillevent_descriptor():
    """FillEvent pb2 descriptor must expose 'fees' as a repeated Fee message field."""
    _ensure_generated_on_path()
    from common.execution import fill_event_pb2
    from common.reconciliation import fee_event_pb2
    from google.protobuf.descriptor import FieldDescriptor

    descriptor = fill_event_pb2.FillEvent.DESCRIPTOR
    fees_field = descriptor.fields_by_name.get("fees")
    assert fees_field is not None, (
        "FillEvent descriptor has no field named 'fees' — "
        "was fill_event_pb2.py regenerated after the proto change?"
    )
    assert fees_field.label == FieldDescriptor.LABEL_REPEATED, (
        f"FillEvent.fees must be LABEL_REPEATED ({FieldDescriptor.LABEL_REPEATED}), "
        f"got {fees_field.label}"
    )
    assert fees_field.message_type is not None, (
        "FillEvent.fees.message_type is None — expected Fee message type"
    )
    assert fees_field.message_type.full_name == "oets.v1.Fee", (
        f"FillEvent.fees.message_type.full_name should be 'oets.v1.Fee', "
        f"got '{fees_field.message_type.full_name}'"
    )
    assert fees_field.number == 12, (
        f"FillEvent.fees must be at field number 12, got {fees_field.number}"
    )


# ---------------------------------------------------------------------------
# 7. pb2 descriptor: CashFlowEvent.fee has message_type Fee
# ---------------------------------------------------------------------------

def test_pb2_cashflow_descriptor():
    """CashFlowEvent pb2 descriptor must expose 'fee' as a singular Fee message field."""
    _ensure_generated_on_path()
    from common.reconciliation import cash_flow_event_pb2

    descriptor = cash_flow_event_pb2.CashFlowEvent.DESCRIPTOR
    fee_field = descriptor.fields_by_name.get("fee")
    assert fee_field is not None, (
        "CashFlowEvent descriptor has no field named 'fee' — "
        "was cash_flow_event_pb2.py regenerated after the proto change?"
    )
    assert fee_field.message_type is not None, (
        "CashFlowEvent.fee.message_type is None — expected Fee message type"
    )
    assert fee_field.message_type.full_name == "oets.v1.Fee", (
        f"CashFlowEvent.fee.message_type.full_name should be 'oets.v1.Fee', "
        f"got '{fee_field.message_type.full_name}'"
    )
    assert fee_field.number == 9, (
        f"CashFlowEvent.fee must be at field number 9, got {fee_field.number}"
    )


# ---------------------------------------------------------------------------
# 8. Round-trip: FillEvent with two fees
# ---------------------------------------------------------------------------

def test_fillevent_roundtrip_with_two_fees():
    """Construct a FillEvent with a 2-element fees list (trading + protocol),
    serialize to wire format, deserialize, and assert both fees survive intact
    with correct asset/amount/fee_type values.
    """
    _ensure_generated_on_path()
    from common.execution import fill_event_pb2
    from common.reconciliation import fee_event_pb2

    Fee = fee_event_pb2.Fee
    FeeType = fee_event_pb2.FeeType
    FillEvent = fill_event_pb2.FillEvent

    trading_fee = Fee(
        asset="USDC",
        amount=500_000,
        fee_type=FeeType.Value("FEE_TYPE_TRADING"),
    )
    protocol_fee = Fee(
        asset="SOL",
        amount=12_000,
        fee_type=FeeType.Value("FEE_TYPE_PROTOCOL"),
    )

    original = FillEvent(
        fees=[trading_fee, protocol_fee],
        total_notional_fee=512_000,
    )

    wire = original.SerializeToString()
    recovered = FillEvent()
    recovered.ParseFromString(wire)

    assert len(recovered.fees) == 2, (
        f"Expected 2 fees after round-trip, got {len(recovered.fees)}"
    )

    r_trading = recovered.fees[0]
    assert r_trading.asset == "USDC", (
        f"fees[0].asset round-trip failed: expected 'USDC', got '{r_trading.asset}'"
    )
    assert r_trading.amount == 500_000, (
        f"fees[0].amount round-trip failed: expected 500000, got {r_trading.amount}"
    )
    assert r_trading.fee_type == FeeType.Value("FEE_TYPE_TRADING"), (
        f"fees[0].fee_type round-trip failed: expected FEE_TYPE_TRADING, got {r_trading.fee_type}"
    )

    r_protocol = recovered.fees[1]
    assert r_protocol.asset == "SOL", (
        f"fees[1].asset round-trip failed: expected 'SOL', got '{r_protocol.asset}'"
    )
    assert r_protocol.amount == 12_000, (
        f"fees[1].amount round-trip failed: expected 12000, got {r_protocol.amount}"
    )
    assert r_protocol.fee_type == FeeType.Value("FEE_TYPE_PROTOCOL"), (
        f"fees[1].fee_type round-trip failed: expected FEE_TYPE_PROTOCOL, got {r_protocol.fee_type}"
    )

    assert recovered.total_notional_fee == 512_000, (
        f"total_notional_fee round-trip failed: expected 512000, got {recovered.total_notional_fee}"
    )


# ---------------------------------------------------------------------------
# 9. Round-trip: CashFlowEvent with embedded Fee
# ---------------------------------------------------------------------------

def test_cashflow_roundtrip_with_fee():
    """Construct a CashFlowEvent with an embedded Fee, serialize, deserialize,
    and assert the fee fields round-trip correctly.
    """
    _ensure_generated_on_path()
    from common.reconciliation import cash_flow_event_pb2
    from common.reconciliation import fee_event_pb2

    Fee = fee_event_pb2.Fee
    FeeType = fee_event_pb2.FeeType
    CashFlowEvent = cash_flow_event_pb2.CashFlowEvent
    CashFlowType = cash_flow_event_pb2.CashFlowType

    original = CashFlowEvent(
        venue_id="drift",
        account_id="acct-001",
        asset_id="USDC",
        cash_flow_type=CashFlowType.Value("CASH_FLOW_TYPE_TRADING_FEE"),
        amount=-250_000,
        fee=Fee(
            asset="USDC",
            amount=250_000,
            fee_type=FeeType.Value("FEE_TYPE_TRADING"),
        ),
    )

    wire = original.SerializeToString()
    recovered = CashFlowEvent()
    recovered.ParseFromString(wire)

    assert recovered.venue_id == "drift", (
        f"venue_id round-trip failed: expected 'drift', got '{recovered.venue_id}'"
    )
    assert recovered.fee.asset == "USDC", (
        f"fee.asset round-trip failed: expected 'USDC', got '{recovered.fee.asset}'"
    )
    assert recovered.fee.amount == 250_000, (
        f"fee.amount round-trip failed: expected 250000, got {recovered.fee.amount}"
    )
    assert recovered.fee.fee_type == FeeType.Value("FEE_TYPE_TRADING"), (
        f"fee.fee_type round-trip failed: expected FEE_TYPE_TRADING, got {recovered.fee.fee_type}"
    )
    assert recovered.amount == -250_000, (
        f"amount round-trip failed: expected -250000, got {recovered.amount}"
    )


# ---------------------------------------------------------------------------
# 10. Regression: Fee appears as field type in at least 2 files outside fee_event.proto
# ---------------------------------------------------------------------------

def test_fee_no_longer_orphan():
    """Fee must be used as a field type in at least 2 .proto files outside its
    own definition file (fee_event.proto). This is a regression guard on the
    orphan-message bug fixed by R3-1.
    """
    fee_definition_file = "fee_event.proto"
    embedding_files: list[str] = []

    for proto_path in sorted(_COMMON_DIR.rglob("*.proto")):
        if proto_path.name == fee_definition_file:
            continue
        text = proto_path.read_text(encoding="utf-8")
        # Match "Fee " as a field type — e.g. "Fee fee = 9;" or "repeated Fee fees = 12;"
        if re.search(r"\bFee\s+\w+\s*=\s*\d+\s*;", text):
            embedding_files.append(str(proto_path.relative_to(_REPO_ROOT)))

    assert len(embedding_files) >= 2, (
        f"Fee must be embedded as a field type in at least 2 proto files outside "
        f"fee_event.proto (R3-1 fixed the orphan-message bug). "
        f"Currently embedded in: {embedding_files}"
    )
