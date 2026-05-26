"""R2-8 (#27): Cross-message envelope invariants.

Three test classes that would have caught R2-1 (OrderEvent duplicate
source/timestamps) and R2-2 (envelope unreachability) if they had existed
earlier:

1. Envelope-dup guard  — every envelope-bearing message must NOT also declare
   top-level SourceReference source or EventTimestamp timestamps fields.
2. End-to-end envelope roundtrip  — full OetsEventEnvelope (all sub-fields)
   wrapped in FillEvent, serialized, deserialized, every field verified.
3. EventType ↔ message mapping coverage  — every non-zero EventType either
   maps to an importable envelope-bearing class or is in UNMAPPED_EVENT_TYPES.

See: https://github.com/zachisit/oets/issues/27
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_GENERATED = str(_REPO_ROOT / "generated" / "python")


def _ensure_generated_on_path() -> None:
    if _GENERATED not in sys.path:
        sys.path.insert(0, _GENERATED)


# ---------------------------------------------------------------------------
# Proto-text helpers (reused across Test 1)
# ---------------------------------------------------------------------------

def _proto_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_message_bodies(text: str) -> list[tuple[str, str]]:
    """Return list of (message_name, body_text) for every top-level message block.

    Uses a simple brace-depth scanner so nested messages are captured correctly
    as part of the outer body (we only need to check that outer body for fields).
    Only truly top-level messages (depth 0 before entering) are returned.
    """
    results: list[tuple[str, str]] = []
    # Find all top-level message declarations.
    for match in re.finditer(r"\bmessage\s+(\w+)\s*\{", text):
        name = match.group(1)
        start = match.end()  # position after the opening brace
        depth = 1
        pos = start
        while pos < len(text) and depth > 0:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        body = text[start : pos - 1]
        results.append((name, body))
    return results


# ---------------------------------------------------------------------------
# Test 1: Cross-message envelope-dup guard
# ---------------------------------------------------------------------------

class TestEnvelopeDupGuard:
    """For every message carrying OetsEventEnvelope, assert it does NOT
    also declare a live top-level SourceReference source or EventTimestamp
    timestamps field.  Catches the class of bug fixed by L6/M2/R2-1/R2-2.
    """

    @pytest.fixture(scope="class")
    def all_proto_files(self) -> list[Path]:
        return sorted((_REPO_ROOT / "common").rglob("*.proto"))

    def _offenders(self, proto_files: list[Path]) -> list[str]:
        """Return a list of human-readable offender strings, empty if clean."""
        offenders: list[str] = []
        for path in proto_files:
            text = _proto_text(path)
            rel = path.relative_to(_REPO_ROOT)
            for msg_name, body in _extract_message_bodies(text):
                # Only check messages that declare an OetsEventEnvelope field.
                if not re.search(r"\bOetsEventEnvelope\b", body):
                    continue
                # Live SourceReference source = N;
                if re.search(r"\bSourceReference\s+source\s*=\s*\d+\s*;", body):
                    offenders.append(
                        f"{rel}::{msg_name} — has live 'SourceReference source' "
                        f"field alongside OetsEventEnvelope"
                    )
                # Live EventTimestamp timestamps = N;
                if re.search(r"\bEventTimestamp\s+timestamps\s*=\s*\d+\s*;", body):
                    offenders.append(
                        f"{rel}::{msg_name} — has live 'EventTimestamp timestamps' "
                        f"field alongside OetsEventEnvelope"
                    )
        return offenders

    def test_no_envelope_bearing_message_has_duplicate_source(
        self, all_proto_files: list[Path]
    ) -> None:
        """No message with OetsEventEnvelope may also declare SourceReference source."""
        offenders = [
            o for o in self._offenders(all_proto_files) if "SourceReference source" in o
        ]
        assert not offenders, (
            "Envelope-bearing messages with duplicate top-level source field "
            "(violates L6/R2-1 fix pattern):\n  " + "\n  ".join(offenders)
        )

    def test_no_envelope_bearing_message_has_duplicate_timestamps(
        self, all_proto_files: list[Path]
    ) -> None:
        """No message with OetsEventEnvelope may also declare EventTimestamp timestamps."""
        offenders = [
            o for o in self._offenders(all_proto_files) if "EventTimestamp timestamps" in o
        ]
        assert not offenders, (
            "Envelope-bearing messages with duplicate top-level timestamps field "
            "(violates M2/R2-1 fix pattern):\n  " + "\n  ".join(offenders)
        )

    @pytest.mark.parametrize(
        "proto_rel, msg_name",
        [
            ("common/execution/fill_event.proto", "FillEvent"),
            ("common/execution/order_event.proto", "OrderEvent"),
            ("common/reconciliation/cash_flow_event.proto", "CashFlowEvent"),
            ("common/reconciliation/settlement_event.proto", "SettlementEvent"),
            ("common/reconciliation/funding_event.proto", "FundingRate"),
            ("common/reconciliation/funding_event.proto", "FundingPayment"),
        ],
    )
    def test_known_envelope_message_has_no_duplicate_fields(
        self, proto_rel: str, msg_name: str
    ) -> None:
        """Parametrized over the 6 known envelope-bearing messages: no dups."""
        text = _proto_text(_REPO_ROOT / proto_rel)
        bodies = {name: body for name, body in _extract_message_bodies(text)}
        assert msg_name in bodies, (
            f"{proto_rel} does not contain message {msg_name!r}"
        )
        body = bodies[msg_name]

        assert not re.search(r"\bSourceReference\s+source\s*=\s*\d+\s*;", body), (
            f"{proto_rel}::{msg_name} — live 'SourceReference source' field found; "
            f"this duplicates OetsEventEnvelope.source (L6/R2-1 regression)"
        )
        assert not re.search(r"\bEventTimestamp\s+timestamps\s*=\s*\d+\s*;", body), (
            f"{proto_rel}::{msg_name} — live 'EventTimestamp timestamps' field found; "
            f"this duplicates OetsEventEnvelope.timestamps (M2/R2-1 regression)"
        )


# ---------------------------------------------------------------------------
# Test 2: End-to-end envelope roundtrip
# ---------------------------------------------------------------------------

class TestEnvelopeRoundtrip:
    """Full OetsEventEnvelope roundtrip via FillEvent: all sub-fields survive
    serialization → deserialization intact.
    """

    @pytest.fixture(scope="class", autouse=True)
    def _path_setup(self):
        _ensure_generated_on_path()

    def _build_original(self):
        from google.protobuf import timestamp_pb2

        fill_pb2 = importlib.import_module("common.execution.fill_event_pb2")
        envelope_pb2 = importlib.import_module("common.event_envelope_pb2")
        source_pb2 = importlib.import_module("common.source_pb2")
        ts_pb2 = importlib.import_module("common.timestamps_pb2")
        rel_pb2 = importlib.import_module("common.relationships_pb2")

        OetsEventEnvelope = envelope_pb2.OetsEventEnvelope
        EventType = envelope_pb2.EventType
        SourceReference = source_pb2.SourceReference
        SourceType = source_pb2.SourceType
        EventTimestamp = ts_pb2.EventTimestamp
        EventRelationship = rel_pb2.EventRelationship
        RelationshipType = rel_pb2.RelationshipType
        FillEvent = fill_pb2.FillEvent

        ts = lambda s, n: timestamp_pb2.Timestamp(seconds=s, nanos=n)

        original = FillEvent(
            envelope=OetsEventEnvelope(
                event_id="fill-roundtrip-001",
                oets_version="0.1.0",
                event_type=EventType.EVENT_TYPE_FILL,
                source=SourceReference(
                    source_id="binance-ws-01",
                    source_type=SourceType.VENUE_WS,
                    source_name="binance-websocket",
                ),
                timestamps=EventTimestamp(
                    decision_timestamp=ts(1_700_000_000, 1),
                    submitted_timestamp=ts(1_700_000_001, 2),
                    event_timestamp=ts(1_700_000_002, 3),
                    ledger_timestamp=ts(1_700_000_003, 4),
                    observed_timestamp=ts(1_700_000_004, 5),
                    valuation_timestamp=ts(1_700_000_005, 6),
                ),
                relationships=[
                    EventRelationship(
                        relationship_type=RelationshipType.FILLS_ORDER,
                        related_event_id="order-abc-123",
                    ),
                    EventRelationship(
                        relationship_type=RelationshipType.FEE_FOR_FILL,
                        related_event_id="fee-xyz-456",
                    ),
                ],
            ),
            account=None,
        )
        original.envelope.extensions["schema_hint"] = "fill-v1"
        original.envelope.extensions["region"] = "us-east-1"
        return original

    def test_envelope_scalar_fields_roundtrip(self) -> None:
        """event_id and oets_version survive serialization."""
        original = self._build_original()
        wire = original.SerializeToString()
        envelope_pb2 = importlib.import_module("common.event_envelope_pb2")
        fill_pb2 = importlib.import_module("common.execution.fill_event_pb2")
        recovered = fill_pb2.FillEvent()
        recovered.ParseFromString(wire)

        assert recovered.envelope.event_id == "fill-roundtrip-001", (
            f"envelope.event_id mismatch: got {recovered.envelope.event_id!r}"
        )
        assert recovered.envelope.oets_version == "0.1.0", (
            f"envelope.oets_version mismatch: got {recovered.envelope.oets_version!r}"
        )
        assert recovered.envelope.event_type == envelope_pb2.EventType.EVENT_TYPE_FILL, (
            f"envelope.event_type mismatch: got {recovered.envelope.event_type!r}"
        )

    def test_envelope_source_roundtrip(self) -> None:
        """All three SourceReference fields survive serialization."""
        original = self._build_original()
        wire = original.SerializeToString()
        fill_pb2 = importlib.import_module("common.execution.fill_event_pb2")
        source_pb2 = importlib.import_module("common.source_pb2")
        recovered = fill_pb2.FillEvent()
        recovered.ParseFromString(wire)

        src = recovered.envelope.source
        assert src.source_id == "binance-ws-01", (
            f"envelope.source.source_id mismatch: got {src.source_id!r}"
        )
        assert src.source_type == source_pb2.SourceType.VENUE_WS, (
            f"envelope.source.source_type mismatch: got {src.source_type!r}"
        )
        assert src.source_name == "binance-websocket", (
            f"envelope.source.source_name mismatch: got {src.source_name!r}"
        )

    @pytest.mark.parametrize(
        "field_name, expected_seconds, expected_nanos",
        [
            ("decision_timestamp", 1_700_000_000, 1),
            ("submitted_timestamp", 1_700_000_001, 2),
            ("event_timestamp", 1_700_000_002, 3),
            ("ledger_timestamp", 1_700_000_003, 4),
            ("observed_timestamp", 1_700_000_004, 5),
            ("valuation_timestamp", 1_700_000_005, 6),
        ],
    )
    def test_envelope_all_six_timestamps_roundtrip(
        self, field_name: str, expected_seconds: int, expected_nanos: int
    ) -> None:
        """Each of the 6 EventTimestamp sub-fields survives serialization."""
        original = self._build_original()
        wire = original.SerializeToString()
        fill_pb2 = importlib.import_module("common.execution.fill_event_pb2")
        recovered = fill_pb2.FillEvent()
        recovered.ParseFromString(wire)

        ts_msg = getattr(recovered.envelope.timestamps, field_name)
        assert ts_msg.seconds == expected_seconds, (
            f"envelope.timestamps.{field_name}.seconds: "
            f"expected {expected_seconds}, got {ts_msg.seconds}"
        )
        assert ts_msg.nanos == expected_nanos, (
            f"envelope.timestamps.{field_name}.nanos: "
            f"expected {expected_nanos}, got {ts_msg.nanos}"
        )

    def test_envelope_relationships_roundtrip(self) -> None:
        """Both EventRelationship entries survive serialization intact."""
        original = self._build_original()
        wire = original.SerializeToString()
        fill_pb2 = importlib.import_module("common.execution.fill_event_pb2")
        rel_pb2 = importlib.import_module("common.relationships_pb2")
        recovered = fill_pb2.FillEvent()
        recovered.ParseFromString(wire)

        rels = list(recovered.envelope.relationships)
        assert len(rels) == 2, (
            f"envelope.relationships count: expected 2, got {len(rels)}"
        )
        assert rels[0].related_event_id == "order-abc-123", (
            f"relationships[0].related_event_id: got {rels[0].related_event_id!r}"
        )
        assert rels[0].relationship_type == rel_pb2.RelationshipType.FILLS_ORDER, (
            f"relationships[0].relationship_type: got {rels[0].relationship_type!r}"
        )
        assert rels[1].related_event_id == "fee-xyz-456", (
            f"relationships[1].related_event_id: got {rels[1].related_event_id!r}"
        )
        assert rels[1].relationship_type == rel_pb2.RelationshipType.FEE_FOR_FILL, (
            f"relationships[1].relationship_type: got {rels[1].relationship_type!r}"
        )

    def test_envelope_extensions_roundtrip(self) -> None:
        """Both extensions map entries survive serialization intact."""
        original = self._build_original()
        wire = original.SerializeToString()
        fill_pb2 = importlib.import_module("common.execution.fill_event_pb2")
        recovered = fill_pb2.FillEvent()
        recovered.ParseFromString(wire)

        exts = recovered.envelope.extensions
        assert exts["schema_hint"] == "fill-v1", (
            f"envelope.extensions['schema_hint']: got {exts.get('schema_hint')!r}"
        )
        assert exts["region"] == "us-east-1", (
            f"envelope.extensions['region']: got {exts.get('region')!r}"
        )
        assert len(exts) == 2, (
            f"envelope.extensions count: expected 2, got {len(exts)}"
        )


# ---------------------------------------------------------------------------
# Test 3: EventType ↔ concrete message mapping coverage
# ---------------------------------------------------------------------------

# Every non-zero EventType that HAS an envelope-bearing message.
_EVENT_TYPE_TO_MESSAGE: dict[int, tuple[str, str]] = {
    # EventType.EVENT_TYPE_FILL
    1: ("common.execution.fill_event_pb2", "FillEvent"),
    # EventType.EVENT_TYPE_ORDER
    2: ("common.execution.order_event_pb2", "OrderEvent"),
    # EventType.EVENT_TYPE_SETTLEMENT
    4: ("common.reconciliation.settlement_event_pb2", "SettlementEvent"),
    # EventType.EVENT_TYPE_CASH_FLOW
    6: ("common.reconciliation.cash_flow_event_pb2", "CashFlowEvent"),
    # EventType.EVENT_TYPE_FUNDING_RATE  — R3-4 (#46): was EVENT_TYPE_FUNDING; wire-compat rename
    7: ("common.reconciliation.funding_event_pb2", "FundingRate"),
    # EventType.EVENT_TYPE_FUNDING_PAYMENT  — R3-4 (#46): new value for the account-level payment event
    8: ("common.reconciliation.funding_event_pb2", "FundingPayment"),
}

# Non-zero EventType values that deliberately have NO envelope-bearing message.
# These correspond to snapshot/delta state messages only, not event messages.
# Tracked in: https://github.com/zachisit/oets/issues/38
#   EVENT_TYPE_POSITION = 3  — only PositionSnapshot/PositionDelta exist (no envelope)
#   EVENT_TYPE_BALANCE  = 5  — only BalanceSnapshot/BalanceDelta exist (no envelope)
_UNMAPPED_EVENT_TYPES: frozenset[int] = frozenset({3, 5})


class TestEventTypeMappingCoverage:
    """Every non-zero EventType either maps to an envelope-bearing message class
    or is explicitly acknowledged in _UNMAPPED_EVENT_TYPES.
    """

    @pytest.fixture(scope="class", autouse=True)
    def _path_setup(self):
        _ensure_generated_on_path()

    @pytest.fixture(scope="class")
    def event_type_enum(self):
        _ensure_generated_on_path()
        envelope_pb2 = importlib.import_module("common.event_envelope_pb2")
        return envelope_pb2.EventType

    # --- 3a: mapped types resolve to importable envelope-bearing classes ---

    @pytest.mark.parametrize(
        "event_type_value, module_name, class_name",
        [
            (value, mod, cls)
            for value, (mod, cls) in sorted(_EVENT_TYPE_TO_MESSAGE.items())
        ],
    )
    def test_mapped_event_type_class_is_importable(
        self,
        event_type_value: int,
        module_name: str,
        class_name: str,
        event_type_enum,
    ) -> None:
        """The mapped module exists and the class is accessible."""
        try:
            mod = importlib.import_module(module_name)
        except ImportError as exc:
            pytest.fail(
                f"EventType value {event_type_value}: cannot import {module_name!r}: {exc}"
            )
        assert hasattr(mod, class_name), (
            f"EventType value {event_type_value}: {module_name} has no attribute "
            f"{class_name!r}"
        )

    @pytest.mark.parametrize(
        "event_type_value, module_name, class_name",
        [
            (value, mod, cls)
            for value, (mod, cls) in sorted(_EVENT_TYPE_TO_MESSAGE.items())
        ],
    )
    def test_mapped_event_type_class_has_envelope_field(
        self,
        event_type_value: int,
        module_name: str,
        class_name: str,
        event_type_enum,
    ) -> None:
        """The mapped message class has an 'envelope' field of type OetsEventEnvelope."""
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        descriptor = cls.DESCRIPTOR

        assert "envelope" in descriptor.fields_by_name, (
            f"EventType value {event_type_value}: {class_name}.DESCRIPTOR has no "
            f"field named 'envelope'"
        )
        envelope_field = descriptor.fields_by_name["envelope"]
        assert envelope_field.message_type is not None, (
            f"EventType value {event_type_value}: {class_name}.envelope is not a "
            f"message-type field"
        )
        assert envelope_field.message_type.name == "OetsEventEnvelope", (
            f"EventType value {event_type_value}: {class_name}.envelope message type "
            f"is {envelope_field.message_type.name!r}, expected 'OetsEventEnvelope'"
        )

    # --- 3b: every non-zero EventType value is accounted for ---

    def test_all_nonzero_event_types_are_mapped_or_acknowledged(
        self, event_type_enum
    ) -> None:
        """Every non-zero EventType value appears either in _EVENT_TYPE_TO_MESSAGE
        or in _UNMAPPED_EVENT_TYPES.  An unlisted value means a new enum entry was
        added without updating this test.
        """
        all_nonzero = {
            val
            for name, val in event_type_enum.items()
            if val != 0
        }
        mapped = set(_EVENT_TYPE_TO_MESSAGE.keys())
        unmapped = _UNMAPPED_EVENT_TYPES
        uncovered = all_nonzero - mapped - unmapped
        assert not uncovered, (
            "The following non-zero EventType values are neither in "
            "_EVENT_TYPE_TO_MESSAGE nor in _UNMAPPED_EVENT_TYPES — update "
            "one of those dicts in this test file:\n  "
            + "\n  ".join(
                f"value={v} ({event_type_enum.Name(v)})" for v in sorted(uncovered)
            )
        )

    def test_unmapped_event_types_have_no_envelope_bearing_message(
        self, event_type_enum
    ) -> None:
        """Sanity-check: none of the unmapped types accidentally have an
        envelope-bearing message that we missed.  Searches generated/python for
        any top-level class whose descriptor has an 'envelope' field whose name
        matches the EventType name stem (POSITION / BALANCE).
        """
        _ensure_generated_on_path()
        # Stems we expect NOT to find as envelope-bearing message names.
        unmapped_stems = {
            event_type_enum.Name(v).replace("EVENT_TYPE_", "").title().replace("_", "")
            for v in _UNMAPPED_EVENT_TYPES
        }
        # e.g. "Position", "Balance"

        envelope_pb2 = importlib.import_module("common.event_envelope_pb2")
        OetsEventEnvelope = envelope_pb2.OetsEventEnvelope

        # Scan all pb2 modules under generated/python.
        generated_root = _REPO_ROOT / "generated" / "python"
        suspicious: list[str] = []
        for pb2_file in generated_root.rglob("*_pb2.py"):
            rel_parts = pb2_file.relative_to(generated_root).with_suffix("").parts
            module_name = ".".join(rel_parts)
            try:
                mod = importlib.import_module(module_name)
            except Exception:
                continue
            for attr_name in dir(mod):
                for stem in unmapped_stems:
                    if stem in attr_name:
                        obj = getattr(mod, attr_name, None)
                        if obj is None:
                            continue
                        desc = getattr(obj, "DESCRIPTOR", None)
                        if desc is None:
                            continue
                        if "envelope" in getattr(desc, "fields_by_name", {}):
                            field = desc.fields_by_name["envelope"]
                            if (
                                field.message_type is not None
                                and field.message_type.name == "OetsEventEnvelope"
                            ):
                                suspicious.append(
                                    f"{module_name}.{attr_name} has an envelope field "
                                    f"but its EventType stem ({stem!r}) is in "
                                    "_UNMAPPED_EVENT_TYPES"
                                )

        assert not suspicious, (
            "Found envelope-bearing message(s) for supposedly unmapped EventType(s).\n"
            "Move them from _UNMAPPED_EVENT_TYPES into _EVENT_TYPE_TO_MESSAGE:\n  "
            + "\n  ".join(suspicious)
        )
