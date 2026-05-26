"""R2-2 (#21): Hybrid envelope architecture — event messages carry OetsEventEnvelope;
snapshot/delta messages intentionally do not.

See: https://github.com/zachisit/oets/issues/21
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_GENERATED = str(_REPO_ROOT / "generated" / "python")

# Event messages that MUST carry OetsEventEnvelope at field 1.
_EVENT_PROTOS = [
    ("CashFlowEvent", "common/reconciliation/cash_flow_event.proto"),
    ("SettlementEvent", "common/reconciliation/settlement_event.proto"),
    ("FundingRate", "common/reconciliation/funding_event.proto"),
    ("FundingPayment", "common/reconciliation/funding_event.proto"),
]

# Snapshot/delta messages that must NOT carry OetsEventEnvelope.
_SNAPSHOT_DELTA_PROTOS = [
    ("PositionSnapshot", "common/reconciliation/position_event.proto"),
    ("PositionDelta", "common/reconciliation/position_event.proto"),
    ("BalanceSnapshot", "common/reconciliation/balance_event.proto"),
    ("BalanceDelta", "common/reconciliation/balance_event.proto"),
]

# Files that must document the snapshot/delta exemption.
_SNAPSHOT_DELTA_FILES = [
    "common/reconciliation/position_event.proto",
    "common/reconciliation/balance_event.proto",
]


def _proto_text(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


def _message_body(text: str, message_name: str) -> str:
    """Return the body (between braces) of the first matching top-level message."""
    pattern = r"message\s+" + re.escape(message_name) + r"\s*\{([^}]*)\}"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"Message {message_name!r} not found in proto text")
    return match.group(1)


def _ensure_generated_on_path() -> None:
    if _GENERATED not in sys.path:
        sys.path.insert(0, _GENERATED)


# ---------------------------------------------------------------------------
# 1. Event messages carry OetsEventEnvelope at field 1
# ---------------------------------------------------------------------------

def test_event_messages_carry_envelope():
    """Each of the 4 event messages must declare OetsEventEnvelope envelope = 1."""
    failures = []
    for msg_name, proto_rel in _EVENT_PROTOS:
        text = _proto_text(proto_rel)
        body = _message_body(text, msg_name)
        pattern = r"OetsEventEnvelope\s+envelope\s*=\s*1\s*;"
        if not re.search(pattern, body):
            failures.append(
                f"{proto_rel}::{msg_name} — missing 'OetsEventEnvelope envelope = 1;'"
            )
    assert not failures, (
        "The following event messages are missing OetsEventEnvelope at field 1:\n  "
        + "\n  ".join(failures)
    )


# ---------------------------------------------------------------------------
# 2. Event messages have no duplicate top-level source or timestamps
# ---------------------------------------------------------------------------

def test_event_messages_no_duplicate_source_or_timestamps():
    """Event messages must NOT have top-level 'source' or 'timestamps' fields
    (those are now carried exclusively by envelope.source / envelope.timestamps).
    """
    failures = []
    for msg_name, proto_rel in _EVENT_PROTOS:
        text = _proto_text(proto_rel)
        body = _message_body(text, msg_name)
        # Match live field declarations (not reserved names in reserved stmts).
        # A live field looks like: <Type> source = N; or <Type> timestamps = N;
        for bad_name in ("source", "timestamps"):
            live_pattern = r"\bSourceReference\s+" + bad_name + r"\s*=\s*\d+\s*;"
            if re.search(live_pattern, body):
                failures.append(
                    f"{proto_rel}::{msg_name} — has live top-level 'source' field "
                    f"(should be reserved, not a live field)"
                )
            ts_pattern = r"\bEventTimestamp\s+" + bad_name + r"\s*=\s*\d+\s*;"
            if re.search(ts_pattern, body):
                failures.append(
                    f"{proto_rel}::{msg_name} — has live top-level '{bad_name}' field "
                    f"(should be reserved, not a live field)"
                )
    assert not failures, (
        "The following event messages still have duplicate top-level source/timestamps:\n  "
        + "\n  ".join(failures)
    )


# ---------------------------------------------------------------------------
# 3. Snapshot/delta messages have NO OetsEventEnvelope field
# ---------------------------------------------------------------------------

def test_snapshot_delta_messages_have_no_envelope():
    """Snapshot and delta messages must NOT contain an OetsEventEnvelope field."""
    failures = []
    for msg_name, proto_rel in _SNAPSHOT_DELTA_PROTOS:
        text = _proto_text(proto_rel)
        body = _message_body(text, msg_name)
        if re.search(r"OetsEventEnvelope", body):
            failures.append(
                f"{proto_rel}::{msg_name} — unexpectedly contains OetsEventEnvelope"
            )
    assert not failures, (
        "The following snapshot/delta messages must NOT carry an envelope:\n  "
        + "\n  ".join(failures)
    )


# ---------------------------------------------------------------------------
# 4. Snapshot/delta files document the design rationale
# ---------------------------------------------------------------------------

def test_snapshot_delta_files_document_design():
    """position_event.proto and balance_event.proto must contain a file-level comment
    that mentions both 'snapshot' (or 'delta') AND 'envelope', documenting why these
    messages intentionally do not carry an OetsEventEnvelope.
    """
    failures = []
    for proto_rel in _SNAPSHOT_DELTA_FILES:
        text = _proto_text(proto_rel)
        has_snapshot_or_delta = bool(
            re.search(r"snapshot|delta", text, re.IGNORECASE)
        )
        has_envelope = bool(re.search(r"envelope", text, re.IGNORECASE))
        if not has_snapshot_or_delta:
            failures.append(
                f"{proto_rel} — comment does not mention 'snapshot' or 'delta'"
            )
        if not has_envelope:
            failures.append(
                f"{proto_rel} — comment does not mention 'envelope' (rationale missing)"
            )
    assert not failures, (
        "Design-rationale comments are missing or incomplete in:\n  "
        + "\n  ".join(failures)
    )


# ---------------------------------------------------------------------------
# 5. docs/ARCHITECTURE.md exists and mentions all envelope-bearing messages
# ---------------------------------------------------------------------------

def test_architecture_md_exists():
    """docs/ARCHITECTURE.md must exist and mention all 6 envelope-bearing message names."""
    arch_md = _REPO_ROOT / "docs" / "ARCHITECTURE.md"
    assert arch_md.exists(), (
        f"docs/ARCHITECTURE.md not found at {arch_md}; R2-2 requires this file."
    )
    content = arch_md.read_text(encoding="utf-8")
    envelope_messages = [
        "FillEvent", "OrderEvent", "CashFlowEvent",
        "SettlementEvent", "FundingRate", "FundingPayment",
    ]
    missing = [m for m in envelope_messages if m not in content]
    assert not missing, (
        "docs/ARCHITECTURE.md is missing references to these envelope-bearing messages: "
        + str(missing)
    )


# ---------------------------------------------------------------------------
# 6. pb2 descriptors: field 1 is 'envelope' for each event message
# ---------------------------------------------------------------------------

_EVENT_PB2_CLASSES = [
    ("common.reconciliation.cash_flow_event_pb2", "CashFlowEvent"),
    ("common.reconciliation.settlement_event_pb2", "SettlementEvent"),
    ("common.reconciliation.funding_event_pb2", "FundingRate"),
    ("common.reconciliation.funding_event_pb2", "FundingPayment"),
]


def test_pb2_envelope_descriptors_in_sync():
    """For each event message pb2, field number 1 must be named 'envelope'."""
    _ensure_generated_on_path()
    import importlib

    failures = []
    for module_name, class_name in _EVENT_PB2_CLASSES:
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        descriptor = cls.DESCRIPTOR
        if 1 not in descriptor.fields_by_number:
            failures.append(f"{class_name} — has no field at number 1")
            continue
        field_1 = descriptor.fields_by_number[1]
        if field_1.name != "envelope":
            failures.append(
                f"{class_name} — field 1 is named '{field_1.name}', expected 'envelope'"
            )
    assert not failures, (
        "pb2 descriptor field-1 name is wrong for these event messages:\n  "
        + "\n  ".join(failures)
    )


# ---------------------------------------------------------------------------
# 7. Wire-level roundtrip: SettlementEvent with full envelope
# ---------------------------------------------------------------------------

def test_settlement_event_full_envelope_roundtrip():
    """Serialize a SettlementEvent with a fully-populated envelope plus business fields;
    deserialize and assert all values survive the wire trip.
    """
    _ensure_generated_on_path()
    import importlib

    settlement_pb2 = importlib.import_module(
        "common.reconciliation.settlement_event_pb2"
    )
    envelope_pb2 = importlib.import_module("common.event_envelope_pb2")
    source_pb2 = importlib.import_module("common.source_pb2")
    ts_pb2 = importlib.import_module("common.timestamps_pb2")
    rel_pb2 = importlib.import_module("common.relationships_pb2")

    SettlementEvent = settlement_pb2.SettlementEvent
    SettlementType = settlement_pb2.SettlementType
    OetsEventEnvelope = envelope_pb2.OetsEventEnvelope
    EventType = envelope_pb2.EventType
    SourceReference = source_pb2.SourceReference
    EventTimestamp = ts_pb2.EventTimestamp
    EventRelationship = rel_pb2.EventRelationship

    # EventTimestamp uses google.protobuf.Timestamp sub-messages.
    from google.protobuf import timestamp_pb2
    ts_decision = timestamp_pb2.Timestamp(seconds=1_700_000_000, nanos=0)
    ts_observed = timestamp_pb2.Timestamp(seconds=1_700_000_001, nanos=500_000_000)

    original = SettlementEvent(
        envelope=OetsEventEnvelope(
            event_id="se-rt-001",
            oets_version="0.1.1",
            event_type=EventType.EVENT_TYPE_SETTLEMENT,
            source=SourceReference(
                source_id="drift-ws",
                source_name="drift-websocket",
            ),
            timestamps=EventTimestamp(
                decision_timestamp=ts_decision,
                observed_timestamp=ts_observed,
            ),
            relationships=[
                EventRelationship(
                    related_event_id="cf-123",
                    relationship_type=rel_pb2.RelationshipType.FILLS_ORDER,
                )
            ],
        ),
        venue_id="drift",
        account_id="acct-xyz",
        instrument_id="SOL-PERP",
        settlement_type=SettlementType.SETTLEMENT_TYPE_CASH,
        settlement_price=25_000_000_000,
        quantity_settled=5_000_000_000,
        settlement_amount=125_000_000,
        settlement_asset_id="USDC",
        realized_pnl=62_500_000,
        realized_pnl_asset_id="USDC",
    )
    original.metadata["roundtrip_test"] = "r2-2"
    original.envelope.extensions["schema_hint"] = "settlement-v2"

    wire = original.SerializeToString()
    recovered = SettlementEvent()
    recovered.ParseFromString(wire)

    assert recovered.envelope.event_id == "se-rt-001", (
        f"envelope.event_id mismatch: got '{recovered.envelope.event_id}'"
    )
    assert recovered.envelope.oets_version == "0.1.1", (
        f"envelope.oets_version mismatch: got '{recovered.envelope.oets_version}'"
    )
    assert recovered.envelope.event_type == EventType.EVENT_TYPE_SETTLEMENT, (
        f"envelope.event_type mismatch: got {recovered.envelope.event_type}"
    )
    assert recovered.envelope.source.source_id == "drift-ws", (
        f"envelope.source.source_id mismatch: got '{recovered.envelope.source.source_id}'"
    )
    assert recovered.envelope.timestamps.decision_timestamp.seconds == 1_700_000_000, (
        f"envelope.timestamps.decision_timestamp.seconds mismatch: "
        f"got {recovered.envelope.timestamps.decision_timestamp.seconds}"
    )
    assert len(recovered.envelope.relationships) == 1, (
        f"envelope.relationships count mismatch: got {len(recovered.envelope.relationships)}"
    )
    assert recovered.envelope.relationships[0].related_event_id == "cf-123", (
        f"envelope.relationships[0].related_event_id mismatch: "
        f"got '{recovered.envelope.relationships[0].related_event_id}'"
    )
    assert recovered.envelope.extensions["schema_hint"] == "settlement-v2", (
        "envelope.extensions['schema_hint'] mismatch"
    )

    # Business fields must survive unchanged.
    assert recovered.venue_id == "drift"
    assert recovered.account_id == "acct-xyz"
    assert recovered.instrument_id == "SOL-PERP"
    assert recovered.settlement_type == SettlementType.SETTLEMENT_TYPE_CASH
    assert recovered.settlement_price == 25_000_000_000
    assert recovered.quantity_settled == 5_000_000_000
    assert recovered.settlement_amount == 125_000_000
    assert recovered.settlement_asset_id == "USDC"
    assert recovered.realized_pnl == 62_500_000
    assert recovered.realized_pnl_asset_id == "USDC"
    assert recovered.metadata["roundtrip_test"] == "r2-2"
