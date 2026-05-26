"""R3-4 (#46): EVENT_TYPE_FUNDING split into EVENT_TYPE_FUNDING_RATE and EVENT_TYPE_FUNDING_PAYMENT.

funding_event.proto has two envelope-bearing messages — FundingRate (the venue quote)
and FundingPayment (the account-level payment). The single EVENT_TYPE_FUNDING = 7 was
ambiguous. R3-4 renames 7 to EVENT_TYPE_FUNDING_RATE (wire-compat) and adds
EVENT_TYPE_FUNDING_PAYMENT = 8, preserving M1's contiguous 0-8 invariant.

Tests:
1. EVENT_TYPE_FUNDING_RATE = 7 in proto (wire-compat rename).
2. EVENT_TYPE_FUNDING_PAYMENT = 8 in proto (new value).
3. Old EVENT_TYPE_FUNDING (bare, no suffix) does NOT appear in the proto file.
4. pb2 exposes both new values as attributes on EventType.
5. All values 0-8 present with no gaps.
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_ENVELOPE_PROTO = _REPO_ROOT / "common" / "event_envelope.proto"
_GENERATED = str(_REPO_ROOT / "generated" / "python")


def _ensure_generated_on_path() -> None:
    if _GENERATED not in sys.path:
        sys.path.insert(0, _GENERATED)


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


class TestR3_4FundingSplit:

    @pytest.fixture(scope="class")
    def proto_text(self) -> str:
        return _ENVELOPE_PROTO.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def enum_values(self, proto_text: str) -> dict[str, int]:
        return _parse_enum_values(proto_text, "EventType")

    def test_funding_rate_enum_at_7(self, enum_values: dict[str, int]) -> None:
        """EVENT_TYPE_FUNDING_RATE must be declared at wire value 7 (wire-compat rename of EVENT_TYPE_FUNDING)."""
        assert "EVENT_TYPE_FUNDING_RATE" in enum_values, (
            "EVENT_TYPE_FUNDING_RATE is missing from EventType in event_envelope.proto — "
            "R3-4 (#46) requires this value so FundingRate messages have a distinct event type"
        )
        assert enum_values["EVENT_TYPE_FUNDING_RATE"] == 7, (
            "EVENT_TYPE_FUNDING_RATE must equal 7 (wire-compat with old EVENT_TYPE_FUNDING), "
            "got " + str(enum_values["EVENT_TYPE_FUNDING_RATE"])
        )

    def test_funding_payment_enum_at_8(self, enum_values: dict[str, int]) -> None:
        """EVENT_TYPE_FUNDING_PAYMENT must be declared at wire value 8 (new in R3-4)."""
        assert "EVENT_TYPE_FUNDING_PAYMENT" in enum_values, (
            "EVENT_TYPE_FUNDING_PAYMENT is missing from EventType in event_envelope.proto — "
            "R3-4 (#46) requires this value so FundingPayment messages have a distinct event type"
        )
        assert enum_values["EVENT_TYPE_FUNDING_PAYMENT"] == 8, (
            "EVENT_TYPE_FUNDING_PAYMENT must equal 8, "
            "got " + str(enum_values["EVENT_TYPE_FUNDING_PAYMENT"])
        )

    def test_old_funding_value_no_longer_present(self, proto_text: str) -> None:
        """EVENT_TYPE_FUNDING (bare, without _RATE or _PAYMENT suffix) must NOT appear in the proto.

        The old ambiguous value was removed in R3-4 (#46). Any remaining reference is a
        sign the rename was only partially applied.
        """
        # Match EVENT_TYPE_FUNDING not followed by _RATE or _PAYMENT
        bare_match = re.search(r"\bEVENT_TYPE_FUNDING\b(?!_RATE\b)(?!_PAYMENT\b)", proto_text)
        assert bare_match is None, (
            "Old name EVENT_TYPE_FUNDING (without _RATE or _PAYMENT suffix) still appears in "
            "event_envelope.proto — R3-4 (#46) renamed it to EVENT_TYPE_FUNDING_RATE; "
            "the rename was not fully applied"
        )

    def test_pb2_has_both_funding_values(self) -> None:
        """pb2 EventType must expose EVENT_TYPE_FUNDING_RATE=7 and EVENT_TYPE_FUNDING_PAYMENT=8."""
        _ensure_generated_on_path()

        import importlib

        mod_name = "common.event_envelope_pb2"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = importlib.import_module(mod_name)

        EventType = mod.EventType

        assert hasattr(EventType, "EVENT_TYPE_FUNDING_RATE"), (
            "EventType has no attribute EVENT_TYPE_FUNDING_RATE — "
            "regenerate event_envelope_pb2.py after the R3-4 proto change"
        )
        assert EventType.EVENT_TYPE_FUNDING_RATE == 7, (
            "EventType.EVENT_TYPE_FUNDING_RATE = "
            + str(EventType.EVENT_TYPE_FUNDING_RATE)
            + ", expected 7"
        )

        assert hasattr(EventType, "EVENT_TYPE_FUNDING_PAYMENT"), (
            "EventType has no attribute EVENT_TYPE_FUNDING_PAYMENT — "
            "regenerate event_envelope_pb2.py after the R3-4 proto change"
        )
        assert EventType.EVENT_TYPE_FUNDING_PAYMENT == 8, (
            "EventType.EVENT_TYPE_FUNDING_PAYMENT = "
            + str(EventType.EVENT_TYPE_FUNDING_PAYMENT)
            + ", expected 8"
        )

    def test_eventtype_contiguous_through_8(self, enum_values: dict[str, int]) -> None:
        """All values 0-8 must be present with no gaps (M1 invariant, extended by R3-4)."""
        assert enum_values, "EventType enum not found or empty in event_envelope.proto"
        nums = sorted(enum_values.values())
        assert nums[0] == 0, "EventType must start at 0, got " + str(nums[0])
        expected = list(range(0, 9))  # 0 through 8 inclusive
        assert nums == expected, (
            "EventType values are not contiguous 0-8 after R3-4: "
            + str(nums)
            + " (expected "
            + str(expected)
            + "). Gaps cause silent UNKNOWN_EVENT_TYPE decoding on the wire."
        )
