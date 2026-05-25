"""M1 (#8): EventType enum must have no gaps.

Verifies that wire value 4 (EVENT_TYPE_SETTLEMENT) is declared so that
protobuf cannot silently decode it as UNKNOWN_EVENT_TYPE = 0.

See: https://github.com/aithusaqr/oets/issues/8
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


def _parse_all_enums(proto_text: str) -> dict[str, dict[str, int]]:
    """Return {enum_name: {entry_name: number}} for all enums in a proto file."""
    result = {}
    for m in re.finditer(r"enum\s+(\w+)\s*\{([^}]*)\}", proto_text, re.DOTALL):
        ename = m.group(1)
        entries = {
            name: int(number)
            for name, number in re.findall(r"(\w+)\s*=\s*(\d+)\s*;", m.group(2))
        }
        if entries:
            result[ename] = entries
    return result


def _values_are_contiguous(values: dict[str, int]) -> bool:
    nums = sorted(values.values())
    return nums == list(range(nums[0], nums[-1] + 1))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEventTypeNoGap:
    """All tests target common/event_envelope.proto EventType."""

    @pytest.fixture(scope="class")
    def envelope_text(self) -> str:
        return _ENVELOPE_PROTO.read_text(encoding="utf-8")

    @pytest.fixture(scope="class")
    def event_type_values(self, envelope_text: str) -> dict[str, int]:
        return _parse_enum_values(envelope_text, "EventType")

    def test_eventtype_values_contiguous(self, event_type_values: dict[str, int]):
        """All EventType entries must form a contiguous sequence from 0 with no gaps."""
        assert event_type_values, "EventType enum not found or has no entries"
        nums = sorted(event_type_values.values())
        assert nums[0] == 0, f"EventType must start at 0, got {nums[0]}"
        expected = list(range(0, nums[-1] + 1))
        assert nums == expected, (
            f"EventType values are not contiguous: {nums} (expected {expected}). "
            "Gaps cause silent UNKNOWN_EVENT_TYPE decoding on the wire."
        )

    def test_event_type_settlement_at_4(self, event_type_values: dict[str, int]):
        """EVENT_TYPE_SETTLEMENT must be declared with wire value 4."""
        assert "EVENT_TYPE_SETTLEMENT" in event_type_values, (
            "EVENT_TYPE_SETTLEMENT is missing from EventType — wire value 4 is a gap"
        )
        assert event_type_values["EVENT_TYPE_SETTLEMENT"] == 4, (
            f"EVENT_TYPE_SETTLEMENT must equal 4, got {event_type_values['EVENT_TYPE_SETTLEMENT']}"
        )

    def test_known_entries_preserved(self, event_type_values: dict[str, int]):
        """Original 6 entries must still exist with their original wire values (regression guard)."""
        expected_originals = {
            "UNKNOWN_EVENT_TYPE": 0,
            "EVENT_TYPE_FILL": 1,
            "EVENT_TYPE_ORDER": 2,
            "EVENT_TYPE_POSITION": 3,
            "EVENT_TYPE_BALANCE": 5,
            "EVENT_TYPE_CASH_FLOW_EVENT": 6,
        }
        for entry, wire_value in expected_originals.items():
            assert entry in event_type_values, f"{entry} is missing from EventType"
            assert event_type_values[entry] == wire_value, (
                f"{entry} has wrong wire value: "
                f"expected {wire_value}, got {event_type_values[entry]}"
            )

    def test_pb2_descriptor_in_sync(self):
        """The regenerated _pb2.py must reflect all 7 EventType values including SETTLEMENT=4."""
        generated = str(_REPO_ROOT / "generated" / "python")
        if generated not in sys.path:
            sys.path.insert(0, generated)

        import importlib
        mod = importlib.import_module("common.event_envelope_pb2")

        descriptor = mod.DESCRIPTOR.enum_types_by_name["EventType"]
        values_by_name = {v.name: v.number for v in descriptor.values}

        assert "EVENT_TYPE_SETTLEMENT" in values_by_name, (
            "EVENT_TYPE_SETTLEMENT missing from pb2 descriptor — regenerate the file"
        )
        assert values_by_name["EVENT_TYPE_SETTLEMENT"] == 4, (
            f"pb2 descriptor: EVENT_TYPE_SETTLEMENT = {values_by_name['EVENT_TYPE_SETTLEMENT']}, expected 4"
        )

        nums = sorted(values_by_name.values())
        assert nums == list(range(0, nums[-1] + 1)), (
            f"pb2 EventType values are not contiguous: {nums}"
        )
        assert len(values_by_name) == 7, (
            f"Expected 7 EventType entries in pb2 descriptor, got {len(values_by_name)}: {list(values_by_name)}"
        )


class TestNoOtherEnumHasSkippedValue:
    """Generalisation of M1 — every enum in every common/ proto must be gap-free."""

    def test_no_other_enum_has_skipped_value(self):
        """All enums under common/ must have contiguous value sequences (no wire gaps)."""
        proto_files = sorted(_REPO_ROOT.joinpath("common").rglob("*.proto"))
        gaps_found: list[str] = []

        for fpath in proto_files:
            text = fpath.read_text(encoding="utf-8")
            enums = _parse_all_enums(text)
            for ename, entries in enums.items():
                if not _values_are_contiguous(entries):
                    nums = sorted(entries.values())
                    expected = list(range(nums[0], nums[-1] + 1))
                    missing = sorted(set(expected) - set(nums))
                    rel = fpath.relative_to(_REPO_ROOT)
                    gaps_found.append(
                        f"{rel}: {ename}: missing values {missing} (have {nums})"
                    )

        assert not gaps_found, (
            "Found enums with gap(s) in common/ — each missing value is a silent "
            "UNKNOWN decode hazard on the wire:\n  " + "\n  ".join(gaps_found)
        )
