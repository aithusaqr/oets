"""R2-3 (#22): EVENT_TYPE_FUNDING added + EVENT_TYPE_CASH_FLOW_EVENT renamed.
R3-4 (#46): EVENT_TYPE_FUNDING split into EVENT_TYPE_FUNDING_RATE = 7 (wire-compat
rename) and EVENT_TYPE_FUNDING_PAYMENT = 8 (new).

Tests:
1. EVENT_TYPE_FUNDING_RATE = 7 is declared in the proto (was EVENT_TYPE_FUNDING).
2. EVENT_TYPE_FUNDING_PAYMENT = 8 is declared in the proto (new, R3-4).
3. EVENT_TYPE_CASH_FLOW = 6 is declared; old name EVENT_TYPE_CASH_FLOW_EVENT is gone.
4. Values 0-8 are all present with no gaps (regression on M1 invariant).
5. Regenerated pb2 descriptor reflects all changes; old names absent as attributes.
6. Every v0.1.1 deliverable event proto has a matching EVENT_TYPE_* value.
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
        """EVENT_TYPE_FUNDING_RATE must be declared with wire value 7 (R3-4 rename of EVENT_TYPE_FUNDING)."""
        assert "EVENT_TYPE_FUNDING_RATE" in event_type_values, (
            "EVENT_TYPE_FUNDING_RATE is missing from EventType in event_envelope.proto — "
            "R3-4 (#46) renamed EVENT_TYPE_FUNDING to EVENT_TYPE_FUNDING_RATE; "
            "FundingRate messages in funding_event.proto cannot be addressed as a typed event"
        )
        assert event_type_values["EVENT_TYPE_FUNDING_RATE"] == 7, (
            "EVENT_TYPE_FUNDING_RATE must equal 7 (wire-compat with old EVENT_TYPE_FUNDING), "
            "got " + str(event_type_values["EVENT_TYPE_FUNDING_RATE"])
        )

    def test_event_type_funding_payment_at_8(self, event_type_values: dict[str, int]):
        """EVENT_TYPE_FUNDING_PAYMENT must be declared with wire value 8 (new in R3-4)."""
        assert "EVENT_TYPE_FUNDING_PAYMENT" in event_type_values, (
            "EVENT_TYPE_FUNDING_PAYMENT is missing from EventType in event_envelope.proto — "
            "R3-4 (#46) added this value so FundingPayment messages have a distinct event type"
        )
        assert event_type_values["EVENT_TYPE_FUNDING_PAYMENT"] == 8, (
            "EVENT_TYPE_FUNDING_PAYMENT must equal 8, "
            "got " + str(event_type_values["EVENT_TYPE_FUNDING_PAYMENT"])
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
        """Values 0-8 must all be present with no gaps (regression on M1 invariant; R3-4 adds 8)."""
        assert event_type_values, "EventType enum not found or has no entries"
        nums = sorted(event_type_values.values())
        assert nums[0] == 0, f"EventType must start at 0, got {nums[0]}"
        expected = list(range(0, nums[-1] + 1))
        assert nums == expected, (
            "EventType values are not contiguous after R3-4: "
            + str(nums)
            + " (expected "
            + str(expected)
            + "). Gaps cause silent UNKNOWN_EVENT_TYPE decoding on the wire."
        )
        assert nums[-1] == 8, (
            "EventType should have values 0-8 after R3-4, max found: " + str(nums[-1])
        )

    def test_pb2_descriptor_has_funding_and_renamed_cash_flow(self):
        """pb2 descriptor must reflect EVENT_TYPE_CASH_FLOW=6, EVENT_TYPE_FUNDING_RATE=7,
        EVENT_TYPE_FUNDING_PAYMENT=8; old names absent (R3-4 split).
        """
        generated = str(_REPO_ROOT / "generated" / "python")
        if generated not in sys.path:
            sys.path.insert(0, generated)

        import importlib

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
            "pb2 descriptor: EVENT_TYPE_CASH_FLOW = "
            + str(values_by_name["EVENT_TYPE_CASH_FLOW"])
            + ", expected 6"
        )

        assert "EVENT_TYPE_FUNDING_RATE" in values_by_name, (
            "EVENT_TYPE_FUNDING_RATE missing from pb2 descriptor — "
            "regenerate event_envelope_pb2.py (R3-4 rename of EVENT_TYPE_FUNDING)"
        )
        assert values_by_name["EVENT_TYPE_FUNDING_RATE"] == 7, (
            "pb2 descriptor: EVENT_TYPE_FUNDING_RATE = "
            + str(values_by_name["EVENT_TYPE_FUNDING_RATE"])
            + ", expected 7"
        )

        assert "EVENT_TYPE_FUNDING_PAYMENT" in values_by_name, (
            "EVENT_TYPE_FUNDING_PAYMENT missing from pb2 descriptor — "
            "regenerate event_envelope_pb2.py (new in R3-4)"
        )
        assert values_by_name["EVENT_TYPE_FUNDING_PAYMENT"] == 8, (
            "pb2 descriptor: EVENT_TYPE_FUNDING_PAYMENT = "
            + str(values_by_name["EVENT_TYPE_FUNDING_PAYMENT"])
            + ", expected 8"
        )

        assert "EVENT_TYPE_CASH_FLOW_EVENT" not in values_by_name, (
            "Old name EVENT_TYPE_CASH_FLOW_EVENT still present in pb2 descriptor — "
            "pb2 was not regenerated after the rename"
        )

        assert "EVENT_TYPE_FUNDING" not in values_by_name, (
            "Old name EVENT_TYPE_FUNDING still present in pb2 descriptor — "
            "R3-4 (#46) renamed it to EVENT_TYPE_FUNDING_RATE; regenerate event_envelope_pb2.py"
        )

    def test_all_v0_1_1_event_protos_have_eventtype_coverage(self, event_type_values: dict[str, int]):
        """Each v0.1.1 deliverable event proto must have a matching EVENT_TYPE_* value.

        fee_event is exempt: fees are a sub-component of other events (e.g. fills),
        not a standalone top-level event type in the OetsEventEnvelope routing table.

        funding_event.proto has TWO envelope-bearing messages (FundingRate, FundingPayment)
        so it maps to two EventType entries after R3-4 (#46).
        """
        # Map proto stem → expected EventType entry name(s).
        # funding_event maps to two entries after R3-4 split.
        proto_to_event_types: dict[str, list[str]] = {
            "fill_event": ["EVENT_TYPE_FILL"],
            "order_event": ["EVENT_TYPE_ORDER"],
            "balance_event": ["EVENT_TYPE_BALANCE"],
            "cash_flow_event": ["EVENT_TYPE_CASH_FLOW"],
            "funding_event": ["EVENT_TYPE_FUNDING_RATE", "EVENT_TYPE_FUNDING_PAYMENT"],
            "position_event": ["EVENT_TYPE_POSITION"],
            "settlement_event": ["EVENT_TYPE_SETTLEMENT"],
            # fee_event is exempt — sub-component, not a top-level routable event
        }

        # Verify all expected proto files actually exist on disk
        missing_protos = []
        for proto_stem in proto_to_event_types:
            matches = list(_REPO_ROOT.rglob(proto_stem + ".proto"))
            if not matches:
                missing_protos.append(proto_stem)
        assert not missing_protos, (
            "v0.1.1 event proto files not found on disk: " + str(missing_protos)
        )

        # Verify each has a corresponding EventType entry (or entries)
        missing_coverage = []
        for proto_stem, event_type_names in proto_to_event_types.items():
            for event_type_name in event_type_names:
                if event_type_name not in event_type_values:
                    missing_coverage.append(
                        proto_stem + ".proto → " + event_type_name + " (missing from EventType)"
                    )
        assert not missing_coverage, (
            "Some v0.1.1 event protos lack EventType coverage:\n  "
            + "\n  ".join(missing_coverage)
        )
