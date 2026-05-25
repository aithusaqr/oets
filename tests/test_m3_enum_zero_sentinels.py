"""M3 (#10): Zero-value enum entries must be UNKNOWN sentinels, not semantic values.

In proto3, the default value for any unset enum field is always 0. With
BUY=0, GOOD_TIL_CANCEL=0, RESTING=0 at the zero slot, unset fields silently
decoded as real semantic values. Fix: insert UNKNOWN_X=0 sentinels and shift
existing entries up by 1.

See: https://github.com/aithusaqr/oets/issues/10
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_ORDER_EVENT_PROTO = _REPO_ROOT / "common" / "execution" / "order_event.proto"
_GENERATED = str(_REPO_ROOT / "generated" / "python")


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


def _import_order_event_pb2():
    if _GENERATED not in sys.path:
        sys.path.insert(0, _GENERATED)
    import importlib
    return importlib.import_module("common.execution.order_event_pb2")


# ---------------------------------------------------------------------------
# Proto text fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def order_event_text() -> str:
    return _ORDER_EVENT_PROTO.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def order_side_values(order_event_text: str) -> dict[str, int]:
    return _parse_enum_values(order_event_text, "OrderSide")


@pytest.fixture(scope="module")
def order_tif_values(order_event_text: str) -> dict[str, int]:
    return _parse_enum_values(order_event_text, "OrderTimeInForce")


@pytest.fixture(scope="module")
def order_intention_values(order_event_text: str) -> dict[str, int]:
    return _parse_enum_values(order_event_text, "OrderIntentionType")


# ---------------------------------------------------------------------------
# OrderSide tests
# ---------------------------------------------------------------------------

def test_order_side_has_unknown_sentinel(order_side_values: dict[str, int]):
    """OrderSide must declare UNKNOWN_ORDER_SIDE = 0 as its zero sentinel."""
    assert "UNKNOWN_ORDER_SIDE" in order_side_values, (
        "UNKNOWN_ORDER_SIDE is missing from OrderSide; "
        "proto3 default=0 would silently decode as BUY without a sentinel"
    )
    assert order_side_values["UNKNOWN_ORDER_SIDE"] == 0, (
        "UNKNOWN_ORDER_SIDE must be 0, got "
        + str(order_side_values["UNKNOWN_ORDER_SIDE"])
    )


def test_order_side_buy_is_now_1(order_side_values: dict[str, int]):
    """After M3, BUY must have wire value 1 (shifted up from old 0)."""
    assert "BUY" in order_side_values, "BUY is missing from OrderSide"
    assert order_side_values["BUY"] == 1, (
        "BUY must equal 1 after M3 renumbering, got " + str(order_side_values["BUY"])
    )


def test_order_side_sell_is_now_2(order_side_values: dict[str, int]):
    """After M3, SELL must have wire value 2 (shifted up from old 1)."""
    assert "SELL" in order_side_values, "SELL is missing from OrderSide"
    assert order_side_values["SELL"] == 2, (
        "SELL must equal 2 after M3 renumbering, got " + str(order_side_values["SELL"])
    )


# ---------------------------------------------------------------------------
# OrderTimeInForce tests
# ---------------------------------------------------------------------------

def test_order_time_in_force_has_unknown_sentinel(order_tif_values: dict[str, int]):
    """OrderTimeInForce must declare UNKNOWN_ORDER_TIME_IN_FORCE = 0."""
    assert "UNKNOWN_ORDER_TIME_IN_FORCE" in order_tif_values, (
        "UNKNOWN_ORDER_TIME_IN_FORCE is missing from OrderTimeInForce; "
        "unset fields would silently decode as GOOD_TIL_CANCEL"
    )
    assert order_tif_values["UNKNOWN_ORDER_TIME_IN_FORCE"] == 0, (
        "UNKNOWN_ORDER_TIME_IN_FORCE must be 0, got "
        + str(order_tif_values["UNKNOWN_ORDER_TIME_IN_FORCE"])
    )


def test_order_time_in_force_old_zero_value_shifted(order_tif_values: dict[str, int]):
    """After M3, GOOD_TIL_CANCEL must have wire value 1 (shifted up from old 0)."""
    assert "GOOD_TIL_CANCEL" in order_tif_values, "GOOD_TIL_CANCEL is missing from OrderTimeInForce"
    assert order_tif_values["GOOD_TIL_CANCEL"] == 1, (
        "GOOD_TIL_CANCEL must equal 1 after M3, got " + str(order_tif_values["GOOD_TIL_CANCEL"])
    )


# ---------------------------------------------------------------------------
# OrderIntentionType tests
# ---------------------------------------------------------------------------

def test_order_intention_type_has_unknown_sentinel(order_intention_values: dict[str, int]):
    """OrderIntentionType must declare UNKNOWN_ORDER_INTENTION_TYPE = 0."""
    assert "UNKNOWN_ORDER_INTENTION_TYPE" in order_intention_values, (
        "UNKNOWN_ORDER_INTENTION_TYPE is missing from OrderIntentionType; "
        "unset fields would silently decode as RESTING"
    )
    assert order_intention_values["UNKNOWN_ORDER_INTENTION_TYPE"] == 0, (
        "UNKNOWN_ORDER_INTENTION_TYPE must be 0, got "
        + str(order_intention_values["UNKNOWN_ORDER_INTENTION_TYPE"])
    )


def test_order_intention_type_old_zero_value_shifted(order_intention_values: dict[str, int]):
    """After M3, RESTING must have wire value 1 (shifted up from old 0)."""
    assert "RESTING" in order_intention_values, "RESTING is missing from OrderIntentionType"
    assert order_intention_values["RESTING"] == 1, (
        "RESTING must equal 1 after M3, got " + str(order_intention_values["RESTING"])
    )


# ---------------------------------------------------------------------------
# pb2 descriptor tests
# ---------------------------------------------------------------------------

def test_pb2_order_side_descriptor():
    """The generated pb2 must reflect M3 OrderSide values: UNKNOWN=0, BUY=1, SELL=2."""
    mod = _import_order_event_pb2()
    desc = mod.DESCRIPTOR.enum_types_by_name["OrderSide"]
    by_name = {v.name: v.number for v in desc.values}

    assert by_name.get("UNKNOWN_ORDER_SIDE") == 0, (
        "pb2 OrderSide.UNKNOWN_ORDER_SIDE must be 0, got "
        + str(by_name.get("UNKNOWN_ORDER_SIDE"))
    )
    assert by_name.get("BUY") == 1, (
        "pb2 OrderSide.BUY must be 1, got " + str(by_name.get("BUY"))
    )
    assert by_name.get("SELL") == 2, (
        "pb2 OrderSide.SELL must be 2, got " + str(by_name.get("SELL"))
    )


def test_pb2_order_time_in_force_descriptor():
    """The generated pb2 must reflect M3 OrderTimeInForce values."""
    mod = _import_order_event_pb2()
    desc = mod.DESCRIPTOR.enum_types_by_name["OrderTimeInForce"]
    by_name = {v.name: v.number for v in desc.values}

    assert by_name.get("UNKNOWN_ORDER_TIME_IN_FORCE") == 0, (
        "pb2 OrderTimeInForce.UNKNOWN_ORDER_TIME_IN_FORCE must be 0, got "
        + str(by_name.get("UNKNOWN_ORDER_TIME_IN_FORCE"))
    )
    assert by_name.get("GOOD_TIL_CANCEL") == 1, (
        "pb2 OrderTimeInForce.GOOD_TIL_CANCEL must be 1, got "
        + str(by_name.get("GOOD_TIL_CANCEL"))
    )
    assert by_name.get("ORDER_TIF_IMMEDIATE_OR_CANCEL") == 2, (
        "pb2 OrderTimeInForce.ORDER_TIF_IMMEDIATE_OR_CANCEL must be 2, got "
        + str(by_name.get("ORDER_TIF_IMMEDIATE_OR_CANCEL"))
    )
    assert by_name.get("ORDER_TIF_FILL_OR_KILL") == 3, (
        "pb2 OrderTimeInForce.ORDER_TIF_FILL_OR_KILL must be 3, got "
        + str(by_name.get("ORDER_TIF_FILL_OR_KILL"))
    )


def test_pb2_order_intention_type_descriptor():
    """The generated pb2 must reflect M3 OrderIntentionType values."""
    mod = _import_order_event_pb2()
    desc = mod.DESCRIPTOR.enum_types_by_name["OrderIntentionType"]
    by_name = {v.name: v.number for v in desc.values}

    assert by_name.get("UNKNOWN_ORDER_INTENTION_TYPE") == 0, (
        "pb2 OrderIntentionType.UNKNOWN_ORDER_INTENTION_TYPE must be 0, got "
        + str(by_name.get("UNKNOWN_ORDER_INTENTION_TYPE"))
    )
    assert by_name.get("RESTING") == 1, (
        "pb2 OrderIntentionType.RESTING must be 1, got " + str(by_name.get("RESTING"))
    )
    assert by_name.get("CROSSING") == 2, (
        "pb2 OrderIntentionType.CROSSING must be 2, got " + str(by_name.get("CROSSING"))
    )
    assert by_name.get("CANCEL") == 3, (
        "pb2 OrderIntentionType.CANCEL must be 3, got " + str(by_name.get("CANCEL"))
    )
    assert by_name.get("ONE_CANCELS_OTHER") == 4, (
        "pb2 OrderIntentionType.ONE_CANCELS_OTHER must be 4, got "
        + str(by_name.get("ONE_CANCELS_OTHER"))
    )


# ---------------------------------------------------------------------------
# Wire-level proof: unset field decodes as UNKNOWN, not old semantic value
# ---------------------------------------------------------------------------

def test_default_value_is_unknown():
    """An OrderEvent with side unset must deserialize as UNKNOWN_ORDER_SIDE, not BUY.

    This is the wire-level proof that the fix actually works: before M3, an
    unset side field would silently read as BUY=0. After M3, it reads as
    UNKNOWN_ORDER_SIDE=0 — a distinct, distinguishable sentinel.
    """
    mod = _import_order_event_pb2()
    OrderSide = mod.OrderSide
    OrderEvent = mod.OrderEvent

    event = OrderEvent()
    serialized = event.SerializeToString()
    decoded = OrderEvent()
    decoded.ParseFromString(serialized)

    assert decoded.side == OrderSide.UNKNOWN_ORDER_SIDE, (
        "Unset OrderEvent.side must decode as UNKNOWN_ORDER_SIDE (0), "
        "got " + str(decoded.side)
    )
    assert decoded.side != OrderSide.BUY, (
        "Unset OrderEvent.side must NOT decode as BUY after M3 fix"
    )


# ---------------------------------------------------------------------------
# Regression: no enum has a gap (M1 generalisation + M3 new enums)
# ---------------------------------------------------------------------------

def test_no_enum_has_skipped_value():
    """All enums in order_event.proto must have contiguous 0..N values (no wire gaps).

    Regression guard for M1 (EventType gap), and correctness check for the
    three M3-touched enums which now start at 0 with a sentinel.
    """
    text = _ORDER_EVENT_PROTO.read_text(encoding="utf-8")
    enums = _parse_all_enums(text)

    assert enums, "No enums found in order_event.proto — file may have moved"

    gaps_found: list[str] = []
    for ename, entries in enums.items():
        if not _values_are_contiguous(entries):
            nums = sorted(entries.values())
            expected = list(range(nums[0], nums[-1] + 1))
            missing = sorted(set(expected) - set(nums))
            gaps_found.append(
                ename + ": missing values " + str(missing) + " (have " + str(nums) + ")"
            )

    assert not gaps_found, (
        "Found enums with gaps in order_event.proto — each missing value is a "
        "silent UNKNOWN decode hazard:\n  " + "\n  ".join(gaps_found)
    )
