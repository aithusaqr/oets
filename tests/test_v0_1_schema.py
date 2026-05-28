"""Structural tests for v0.1 schema invariants.

Covers: envelope rule, sentinel naming, Fee typing, EventType completeness,
reserved-field hygiene, and snapshot/delta envelope exclusion.
"""

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_COMMON = _REPO_ROOT / "common"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize proto_path over every .proto file under common/."""
    if "proto_path" in metafunc.fixturenames:
        files = sorted(_REPO_ROOT.joinpath("common").rglob("*.proto"))
        metafunc.parametrize("proto_path", files, ids=[p.name for p in files])


# ---------------------------------------------------------------------------
# Known message classifications
# ---------------------------------------------------------------------------

_EVENT_MESSAGES = {
    "FillEvent": "common/execution/fill_event.proto",
    "OrderEvent": "common/execution/order_event.proto",
    "CashFlowEvent": "common/reconciliation/cash_flow_event.proto",
    "SettlementEvent": "common/reconciliation/settlement_event.proto",
}

_SNAPSHOT_DELTA_MESSAGES = {
    "BalanceSnapshot": "common/reconciliation/balance_event.proto",
    "BalanceDelta": "common/reconciliation/balance_event.proto",
    "PositionSnapshot": "common/reconciliation/position_event.proto",
    "PositionDelta": "common/reconciliation/position_event.proto",
}


def _proto_text(rel_path: str) -> str:
    return (_REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _message_body(text: str, message_name: str) -> str | None:
    """Return the body of a top-level message by name, or None."""
    pattern = re.compile(
        rf'\bmessage\s+{re.escape(message_name)}\s*\{{([^{{}}]*)\}}',
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Envelope rule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("msg,rel_path", _EVENT_MESSAGES.items())
def test_event_message_has_envelope_at_field_1(msg: str, rel_path: str):
    """Every event message must carry OetsEventEnvelope envelope = 1."""
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    assert re.search(r'\bOetsEventEnvelope\s+envelope\s*=\s*1\s*;', body), (
        f"{rel_path} '{msg}': missing 'OetsEventEnvelope envelope = 1'. "
        "All event messages must carry the envelope at field 1."
    )


@pytest.mark.parametrize("msg,rel_path", _SNAPSHOT_DELTA_MESSAGES.items())
def test_snapshot_delta_message_has_no_envelope(msg: str, rel_path: str):
    """Snapshot/delta messages must NOT carry OetsEventEnvelope."""
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    assert not re.search(r'\bOetsEventEnvelope\b', body), (
        f"{rel_path} '{msg}': snapshot/delta messages must not carry "
        "OetsEventEnvelope — they manage their own observation-time metadata."
    )


# ---------------------------------------------------------------------------
# Deduplication: event messages must not duplicate envelope routing fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("msg,rel_path", _EVENT_MESSAGES.items())
def test_event_message_no_standalone_source(msg: str, rel_path: str):
    """Event messages must not carry a standalone SourceReference source field.

    source is owned by the envelope; a duplicate field creates two sources
    of truth and silently diverges in consumers.
    """
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    non_reserved = re.sub(r'\breserved\b[^;]+;', '', body)
    assert not re.search(r'\bSourceReference\s+source\b', non_reserved), (
        f"{rel_path} '{msg}': has standalone 'SourceReference source' field. "
        "Remove it — source is already carried by OetsEventEnvelope."
    )


@pytest.mark.parametrize("msg,rel_path", _EVENT_MESSAGES.items())
def test_event_message_no_standalone_timestamps(msg: str, rel_path: str):
    """Event messages must not carry a standalone EventTimestamp timestamps field.

    timestamps is owned by the envelope.
    """
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    non_reserved = re.sub(r'\breserved\b[^;]+;', '', body)
    assert not re.search(r'\bEventTimestamp\s+timestamps\b', non_reserved), (
        f"{rel_path} '{msg}': has standalone 'EventTimestamp timestamps' field. "
        "Remove it — timestamps is already carried by OetsEventEnvelope."
    )


# ---------------------------------------------------------------------------
# Reserved-field hygiene: removed routing fields must be reserved by name
# ---------------------------------------------------------------------------

_SOURCE_BEARING = {
    "FillEvent": "common/execution/fill_event.proto",
    "OrderEvent": "common/execution/order_event.proto",
}

_TIMESTAMPS_BEARING = {
    "FillEvent": "common/execution/fill_event.proto",
    "OrderEvent": "common/execution/order_event.proto",
}


@pytest.mark.parametrize("msg,rel_path", _SOURCE_BEARING.items())
def test_event_message_reserves_source_name(msg: str, rel_path: str):
    """Event messages that removed a source field must reserve the name.

    Reserving the name prevents accidental future reintroduction of a
    standalone source field on a different field number.
    """
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    assert re.search(r'\breserved\b[^;]*"source"', body), (
        f"{rel_path} '{msg}': 'source' field name is not reserved. "
        "Add reserved \"source\"; to prevent accidental reuse."
    )


@pytest.mark.parametrize("msg,rel_path", _TIMESTAMPS_BEARING.items())
def test_event_message_reserves_timestamps_name(msg: str, rel_path: str):
    """Event messages that removed a timestamps field must reserve the name."""
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    assert re.search(r'\breserved\b[^;]*"timestamps"', body), (
        f"{rel_path} '{msg}': 'timestamps' field name is not reserved. "
        "Add reserved \"timestamps\"; to prevent accidental reuse."
    )


def test_cash_flow_event_reserves_routing_field_names():
    """CashFlowEvent must reserve the names of all removed routing fields."""
    rel_path = "common/reconciliation/cash_flow_event.proto"
    body = _message_body(_proto_text(rel_path), "CashFlowEvent")
    assert body is not None, "CashFlowEvent message not found"
    for name in ("source", "timestamp", "related_events", "metadata", "event_id", "fee_amount"):
        assert re.search(rf'\breserved\b[^;]*"{re.escape(name)}"', body), (
            f"{rel_path} 'CashFlowEvent': field name '{name}' is not reserved. "
            "Reserving removed field names prevents silent reuse on future PRs."
        )


# ---------------------------------------------------------------------------
# Enum value assignments: sentinel-shifted enums must have correct values
# ---------------------------------------------------------------------------

def test_order_side_values_are_shifted():
    """OrderSide BUY=1 and SELL=2 after the v0.1 sentinel shift."""
    text = _proto_text("common/execution/order_event.proto")
    assert re.search(r'\bBUY\s*=\s*1\s*;', text), (
        "OrderSide.BUY must be 1 after the v0.1 sentinel shift (was 0)."
    )
    assert re.search(r'\bSELL\s*=\s*2\s*;', text), (
        "OrderSide.SELL must be 2 after the v0.1 sentinel shift (was 1)."
    )


def test_order_tif_values_are_shifted():
    """OrderTimeInForce GOOD_TIL_CANCEL=1 after the v0.1 sentinel shift."""
    text = _proto_text("common/execution/order_event.proto")
    assert re.search(r'\bGOOD_TIL_CANCEL\s*=\s*1\s*;', text), (
        "OrderTimeInForce.GOOD_TIL_CANCEL must be 1 after the v0.1 sentinel shift (was 0)."
    )


def test_order_intention_type_values_are_shifted():
    """OrderIntentionType RESTING=1 after the v0.1 sentinel shift."""
    text = _proto_text("common/execution/order_event.proto")
    assert re.search(r'\bRESTING\s*=\s*1\s*;', text), (
        "OrderIntentionType.RESTING must be 1 after the v0.1 sentinel shift (was 0)."
    )


# ---------------------------------------------------------------------------
# Fee typing
# ---------------------------------------------------------------------------

def test_fee_amount_is_int64():
    """Fee.amount must be int64 (not string) per the int64 scaling convention."""
    text = _proto_text("common/reconciliation/fee_event.proto")
    body = _message_body(text, "Fee")
    assert body is not None, "Fee message not found in fee_event.proto"
    assert re.search(r'\bint64\s+amount\b', body), (
        "Fee.amount must be int64. "
        "String amounts cannot participate in arithmetic and violate the "
        "int64 scaling convention documented in docs/SCALING.md."
    )
    assert not re.search(r'\bstring\s+amount\b', body), (
        "Fee.amount is typed as string — must be int64."
    )


def test_fee_fee_type_uses_enum():
    """Fee.fee_type must use the FeeType enum, not a raw string."""
    text = _proto_text("common/reconciliation/fee_event.proto")
    body = _message_body(text, "Fee")
    assert body is not None, "Fee message not found in fee_event.proto"
    assert re.search(r'\bFeeType\s+fee_type\b', body), (
        "Fee.fee_type must be typed as FeeType (the enum defined in the same file). "
        "A raw string field loses type safety and breaks exhaustive matching."
    )


def test_fill_event_has_fee_sub_message_at_field_12():
    """FillEvent.fee must be typed as Fee at field 12."""
    text = _proto_text("common/execution/fill_event.proto")
    body = _message_body(text, "FillEvent")
    assert body is not None, "FillEvent message not found"
    non_reserved = re.sub(r'\breserved\b[^;]+;', '', body)
    assert re.search(r'\bFee\s+fee\s*=\s*12\s*;', non_reserved), (
        "FillEvent must carry 'Fee fee = 12'. "
        "Field 12 was retyped from int64 to Fee in v0.1; pinning the number prevents drift."
    )


def test_cash_flow_event_has_fee_sub_message_at_field_9():
    """CashFlowEvent.fee must be typed as Fee at field 9."""
    text = _proto_text("common/reconciliation/cash_flow_event.proto")
    body = _message_body(text, "CashFlowEvent")
    assert body is not None, "CashFlowEvent message not found"
    non_reserved = re.sub(r'\breserved\b[^;]+;', '', body)
    assert re.search(r'\bFee\s+fee\s*=\s*9\s*;', non_reserved), (
        "CashFlowEvent must carry 'Fee fee = 9'. "
        "Field 9 replaced int64 fee_amount in v0.1; pinning the number prevents drift."
    )


# ---------------------------------------------------------------------------
# Reserved-field numeric tags: removed field numbers must be reserved
# ---------------------------------------------------------------------------

def test_fill_event_reserved_numbers():
    """FillEvent must reserve field numbers 13, 14 (fee_asset/notional_fee), 15 (source), 19 (timestamps)."""
    text = _proto_text("common/execution/fill_event.proto")
    body = _message_body(text, "FillEvent")
    assert body is not None, "FillEvent message not found"
    for num in (13, 14, 15, 19):
        assert re.search(rf'\breserved\b[^;]*\b{num}\b', body), (
            f"FillEvent does not reserve field number {num}. "
            "Reserving removed field numbers prevents silent wire-format collisions."
        )


def test_order_event_reserved_numbers():
    """OrderEvent must reserve field numbers 13 (source) and 14 (timestamps)."""
    text = _proto_text("common/execution/order_event.proto")
    body = _message_body(text, "OrderEvent")
    assert body is not None, "OrderEvent message not found"
    for num in (13, 14):
        assert re.search(rf'\breserved\b[^;]*\b{num}\b', body), (
            f"OrderEvent does not reserve field number {num}. "
            "Reserving removed field numbers prevents silent wire-format collisions."
        )


# ---------------------------------------------------------------------------
# Sub-components must not carry OetsEventEnvelope
# ---------------------------------------------------------------------------

_SUB_COMPONENTS = {
    "Fee": "common/reconciliation/fee_event.proto",
    "AccountRef": "common/account.proto",
    "InstrumentRef": "common/instrument.proto",
    "ExecutionVenue": "common/execution_venue.proto",
    "EventRelationship": "common/relationships.proto",
    "EventTimestamp": "common/timestamps.proto",
    "SourceReference": "common/source.proto",
}


@pytest.mark.parametrize("msg,rel_path", _SUB_COMPONENTS.items())
def test_sub_component_has_no_envelope(msg: str, rel_path: str):
    """Sub-component messages must NOT carry OetsEventEnvelope.

    Sub-components are embedded inside event or snapshot/delta messages and
    inherit routing context from their parent. Adding an envelope would
    duplicate routing and create two sources of truth.
    """
    body = _message_body(_proto_text(rel_path), msg)
    assert body is not None, f"{rel_path}: message '{msg}' not found"
    assert not re.search(r'\bOetsEventEnvelope\b', body), (
        f"{rel_path} '{msg}': sub-component must not carry OetsEventEnvelope."
    )


# ---------------------------------------------------------------------------
# EventType completeness
# ---------------------------------------------------------------------------

def test_event_type_has_settlement():
    """EventType enum must contain EVENT_TYPE_SETTLEMENT at value 4."""
    text = _proto_text("common/event_envelope.proto")
    assert re.search(r'\bEVENT_TYPE_SETTLEMENT\s*=\s*4\s*;', text), (
        "EventType enum is missing 'EVENT_TYPE_SETTLEMENT = 4'. "
        "SettlementEvent requires this value at 4 to fill the former gap."
    )


def test_event_type_cash_flow_is_value_6():
    """EventType.EVENT_TYPE_CASH_FLOW must be assigned value 6."""
    text = _proto_text("common/event_envelope.proto")
    assert re.search(r'\bEVENT_TYPE_CASH_FLOW\s*=\s*6\s*;', text), (
        "EventType is missing 'EVENT_TYPE_CASH_FLOW = 6'. "
        "This value was fixed in v0.1 alongside the rename from EVENT_TYPE_CASH_FLOW_EVENT."
    )


def test_event_type_no_gap_in_values():
    """EventType enum must not have gaps in its assigned values."""
    text = _proto_text("common/event_envelope.proto")
    pattern = re.compile(r'EVENT_TYPE_\w+\s*=\s*(\d+)\s*;')
    values = sorted(int(m.group(1)) for m in pattern.finditer(text) if m.group(1) != '0')
    assert values == list(range(1, len(values) + 1)), (
        f"EventType enum has gaps in its non-zero values: {values}. "
        "All values should be contiguous starting from 1."
    )


def test_event_type_cash_flow_not_suffixed_event():
    """EventType value for cash flow must be EVENT_TYPE_CASH_FLOW, not EVENT_TYPE_CASH_FLOW_EVENT."""
    text = _proto_text("common/event_envelope.proto")
    assert "EVENT_TYPE_CASH_FLOW_EVENT" not in text, (
        "EventType still uses the old name 'EVENT_TYPE_CASH_FLOW_EVENT'. "
        "It was renamed to 'EVENT_TYPE_CASH_FLOW' for naming consistency."
    )
    assert "EVENT_TYPE_CASH_FLOW" in text, (
        "EventType is missing 'EVENT_TYPE_CASH_FLOW'."
    )


# ---------------------------------------------------------------------------
# Sentinel naming
# ---------------------------------------------------------------------------

_SENTINEL_PATTERN = re.compile(r'\b(\w+)\s*=\s*0\s*;')
_VALID_ZERO_NAME = re.compile(r'UNSPECIFIED$', re.IGNORECASE)


def test_enum_zero_values_follow_sentinel_naming(proto_path: Path):
    """Every enum zero-value entry must end with _UNSPECIFIED.

    Proto3 default-initialises missing fields to the 0 value; a zero-value
    that maps to a real domain value (e.g. BUY = 0) silently corrupts data
    on deserialisation of messages that omitted the field.
    """
    text = proto_path.read_text(encoding="utf-8")
    if not text.strip():
        pytest.skip(f"{proto_path.name} is empty")
    enum_blocks = re.findall(r'\benum\s+\w+\s*\{([^}]*)\}', text, re.DOTALL)
    bad = []
    for block in enum_blocks:
        for m in _SENTINEL_PATTERN.finditer(block):
            name = m.group(1)
            if not _VALID_ZERO_NAME.search(name):
                bad.append(name)
    assert not bad, (
        f"{proto_path.name}: enum zero-value entries with non-UNSPECIFIED names: {bad}. "
        "Zero-value entries must end with _UNSPECIFIED so that the proto3 default "
        "is unambiguously 'not set', not a real domain value."
    )


# ---------------------------------------------------------------------------
# SettlementEvent existence and substantive schema
# ---------------------------------------------------------------------------

def test_settlement_event_message_exists():
    """settlement_event.proto must define a SettlementEvent message."""
    text = _proto_text("common/reconciliation/settlement_event.proto")
    assert "message SettlementEvent" in text, (
        "settlement_event.proto does not define a SettlementEvent message. "
        "The file was previously an empty stub."
    )


def test_settlement_event_has_envelope():
    """SettlementEvent must carry OetsEventEnvelope envelope = 1."""
    text = _proto_text("common/reconciliation/settlement_event.proto")
    body = _message_body(text, "SettlementEvent")
    assert body is not None, "SettlementEvent message not found"
    assert re.search(r'\bOetsEventEnvelope\s+envelope\s*=\s*1\s*;', body), (
        "SettlementEvent is missing 'OetsEventEnvelope envelope = 1'."
    )


def test_settlement_event_has_settlement_type_field():
    """SettlementEvent must carry a SettlementType settlement_type field."""
    text = _proto_text("common/reconciliation/settlement_event.proto")
    body = _message_body(text, "SettlementEvent")
    assert body is not None, "SettlementEvent message not found"
    assert re.search(r'\bSettlementType\s+settlement_type\b', body), (
        "SettlementEvent is missing 'SettlementType settlement_type'. "
        "SettlementEvent was a stub before v0.1; this field is part of its schema."
    )


def test_settlement_event_has_settlement_amount_field():
    """SettlementEvent must carry an int64 settlement_amount field."""
    text = _proto_text("common/reconciliation/settlement_event.proto")
    body = _message_body(text, "SettlementEvent")
    assert body is not None, "SettlementEvent message not found"
    assert re.search(r'\bint64\s+settlement_amount\b', body), (
        "SettlementEvent is missing 'int64 settlement_amount'. "
        "Settlement amounts must use int64 per docs/SCALING.md."
    )


def test_settlement_event_has_settlement_asset_and_mark_price():
    """SettlementEvent must carry settlement_asset and mark_price fields."""
    text = _proto_text("common/reconciliation/settlement_event.proto")
    body = _message_body(text, "SettlementEvent")
    assert body is not None, "SettlementEvent message not found"
    assert re.search(r'\bstring\s+settlement_asset\b', body), (
        "SettlementEvent is missing 'string settlement_asset'."
    )
    assert re.search(r'\bint64\s+mark_price\b', body), (
        "SettlementEvent is missing 'int64 mark_price'. "
        "Mark price must use int64 per docs/SCALING.md."
    )


def test_settlement_type_enum_exists():
    """settlement_event.proto must define a SettlementType enum with an UNSPECIFIED sentinel."""
    text = _proto_text("common/reconciliation/settlement_event.proto")
    assert "enum SettlementType" in text, (
        "settlement_event.proto does not define a SettlementType enum."
    )
    assert "SETTLEMENT_TYPE_UNSPECIFIED" in text, (
        "SettlementType enum is missing SETTLEMENT_TYPE_UNSPECIFIED = 0 sentinel."
    )
