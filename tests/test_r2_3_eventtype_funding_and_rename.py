"""R2-3 (#22): EVENT_TYPE_FUNDING added + EVENT_TYPE_CASH_FLOW_EVENT renamed.

Tests:
1. EVENT_TYPE_FUNDING = 7 is declared in the proto.
2. EVENT_TYPE_CASH_FLOW = 6 is declared; old name EVENT_TYPE_CASH_FLOW_EVENT is gone.
3. Values 0-7 are all present with no gaps (regression on M1 invariant).
4. Regenerated pb2 descriptor reflects both changes; old name absent as attribute.
5. Every v0.1.1 deliverable event proto has a matching EVENT_TYPE_* value.
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_ENVELOPE_PROTO = _REPO_ROOT / "common" / "event_envelope.proto"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_enum_values(proto_text: str, enum_name: str) -> dict[str, int]:
    """Return {entry_name: number} for all entries in a named enum block."""
    pattern = rf"enum\s+{re.escape(enum_name)}\s*\{{([^}}]*)\}}"
    match = re.search(pattern, proto_text, re.DOTALL)
    if not match:
        return {}
    body = match.group(1)
    return {
        name: int(number)
        for name, number in re.findall(r"(\w+)\s*=\s*(\d+)\s*;", body)
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestR2_3EventTypeFundingAndRename:

    @pytest.fixture(scope="class")
    def envelope_text(self) -> str:
        return _ENVELOPE_PROTO.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def event_type_values(self, envelope_text: str) -> dict[str, int]:
        return _parse_enum_values(envelope_text, "EventType")

    def test_event_type_funding_at_7(self, event_type_values: dict[str, int]):
        """EVENT_TYPE_FUNDING must be declared with wire value 7."""
        assert "EVENT_TYPE_FUNDING" in event_type_values, (
            "EVENT_TYPE_FUNDING is missing from EventType in event_envelope.proto — "
            "funding_event.proto (H1) cannot be addressed as a typed event"
        )
        assert event_type_values["EVENT_TYPE_FUNDING"] == 7, (
            f"EVENT_TYPE_FUNDING must equal 7, got {event_type_values['EVENT_TYPE_FUNDING']}"
        )

    def test_event_type_cash_flow_renamed(self, event_type_values: dict[str, int], envelope_text: str):
        """EVENT_TYPE_CASH_FLOW must be present at value 6; old name must not appear anywhere."""
        assert "EVENT_TYPE_CASH_FLOW" in event_type_values, (
            "EVENT_TYPE_CASH_FLOW is missing from EventType — "
            "rename from EVENT_TYPE_CASH_FLOW_EVENT was not applied"
        )
        assert event_type_values["EVENT_TYPE_CASH_FLOW"] == 6, (
            f"EVENT_TYPE_CASH_FLOW must equal 6 (wire-compat), "
            f"got {event_type_values['EVENT_TYPE_CASH_FLOW']}"
        )
        assert "EVENT_TYPE_CASH_FLOW_EVENT" not in envelope_text, (
            "Old name EVENT_TYPE_CASH_FLOW_EVENT still appears in event_envelope.proto — "
            "rename was not fully applied"
        )

    def test_eventtype_still_contiguous(self, event_type_values: dict[str, int]):
        """Values 0-7 must all be present with no gaps (regression on M1 invariant)."""
        assert event_type_values, "EventType enum not found or has no entries"
        nums = sorted(event_type_values.values())
        assert nums[0] == 0, f"EventType must start at 0, got {nums[0]}"
        expected = list(range(0, nums[-1] + 1))
        assert nums == expected, (
            f"EventType values are not contiguous after R2-3: {nums} (expected {expected}). "
            "Gaps cause silent UNKNOWN_EVENT_TYPE decoding on the wire."
        )
        assert nums[-1] == 7, (
            f"EventType should have values 0-7 after R2-3, max found: {nums[-1]}"
        )

    def test_pb2_descriptor_has_funding_and_renamed_cash_flow(self):
        """pb2 descriptor must reflect EVENT_TYPE_CASH_FLOW=6, EVENT_TYPE_FUNDING=7; old name absent."""
        generated = str(_REPO_ROOT / "generated" / "python")
        if generated not in sys.path:
            sys.path.insert(0, generated)

        import importlib
        import importlib.util

        # Force fresh import in case module was already loaded with old content
        mod_name = "common.event_envelope_pb2"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = importlib.import_module(mod_name)

        descriptor = mod.DESCRIPTOR.enum_types_by_name["EventType"]
        values_by_name = {v.name: v.number for v in descriptor.values}

        assert "EVENT_TYPE_CASH_FLOW" in values_by_name, (
            "EVENT_TYPE_CASH_FLOW missing from pb2 descriptor — regenerate event_envelope_pb2.py"
        )
        assert values_by_name["EVENT_TYPE_CASH_FLOW"] == 6, (
            f"pb2 descriptor: EVENT_TYPE_CASH_FLOW = {values_by_name['EVENT_TYPE_CASH_FLOW']}, expected 6"
        )

        assert "EVENT_TYPE_FUNDING" in values_by_name, (
            "EVENT_TYPE_FUNDING missing from pb2 descriptor — regenerate event_envelope_pb2.py"
        )
        assert values_by_name["EVENT_TYPE_FUNDING"] == 7, (
            f"pb2 descriptor: EVENT_TYPE_FUNDING = {values_by_name['EVENT_TYPE_FUNDING']}, expected 7"
        )

        assert "EVENT_TYPE_CASH_FLOW_EVENT" not in values_by_name, (
            "Old name EVENT_TYPE_CASH_FLOW_EVENT still present in pb2 descriptor — "
            "pb2 was not regenerated after the rename"
        )

    def test_all_v0_1_1_event_protos_have_eventtype_coverage(self, event_type_values: dict[str, int]):
        """Each v0.1.1 deliverable event proto must have a matching EVENT_TYPE_* value.

        fee_event is exempt: fees are a sub-component of other events (e.g. fills),
        not a standalone top-level event type in the OetsEventEnvelope routing table.
        """
        # Map proto stem → expected EventType entry name
        proto_to_event_type = {
            "fill_event": "EVENT_TYPE_FILL",
            "order_event": "EVENT_TYPE_ORDER",
            "balance_event": "EVENT_TYPE_BALANCE",
            "cash_flow_event": "EVENT_TYPE_CASH_FLOW",
            "funding_event": "EVENT_TYPE_FUNDING",
            "position_event": "EVENT_TYPE_POSITION",
            "settlement_event": "EVENT_TYPE_SETTLEMENT",
            # fee_event is exempt — sub-component, not a top-level routable event
        }

        # Verify all expected proto files actually exist on disk
        missing_protos = []
        for proto_stem in proto_to_event_type:
            matches = list(_REPO_ROOT.rglob(f"{proto_stem}.proto"))
            if not matches:
                missing_protos.append(proto_stem)
        assert not missing_protos, (
            f"v0.1.1 event proto files not found on disk: {missing_protos}"
        )

        # Verify each has a corresponding EventType entry
        missing_coverage = []
        for proto_stem, event_type_name in proto_to_event_type.items():
            if event_type_name not in event_type_values:
                missing_coverage.append(
                    f"{proto_stem}.proto → {event_type_name} (missing from EventType)"
                )
        assert not missing_coverage, (
            "Some v0.1.1 event protos lack EventType coverage:\n  "
            + "\n  ".join(missing_coverage)
        )
