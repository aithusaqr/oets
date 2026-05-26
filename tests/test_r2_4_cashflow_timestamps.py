"""R2-4 (#23): CashFlowEvent.timestamp → timestamps (plural) for schema consistency.

CashFlowEvent was the only message using the singular `timestamp`; every
other event/snapshot/delta uses plural `timestamps`. Field number 17 is
unchanged (rename is wire-compatible in proto3).

See: https://github.com/zachisit/oets/issues/23
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_CASH_FLOW_PROTO = _REPO_ROOT / "common" / "reconciliation" / "cash_flow_event.proto"
_COMMON_DIR = _REPO_ROOT / "common"
_GENERATED = str(_REPO_ROOT / "generated" / "python")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _proto_message_body(proto_text: str, message_name: str) -> str:
    """Return the body text of a top-level message block (without braces)."""
    pattern = r"message\s+" + re.escape(message_name) + r"\s*\{([^}]*)\}"
    match = re.search(pattern, proto_text, re.DOTALL)
    if not match:
        raise ValueError("Message " + message_name + " not found in proto text")
    return match.group(1)


def _import_cash_flow_pb2():
    if _GENERATED not in sys.path:
        sys.path.insert(0, _GENERATED)
    import importlib
    return importlib.import_module("common.reconciliation.cash_flow_event_pb2")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cashflow_field_is_timestamps_plural():
    """cash_flow_event.proto must declare EventTimestamp timestamps = 17 (plural)."""
    text = _CASH_FLOW_PROTO.read_text(encoding="utf-8")
    body = _proto_message_body(text, "CashFlowEvent")

    plural_pattern = r"EventTimestamp\s+timestamps\s*=\s*17\s*;"
    assert re.search(plural_pattern, body), (
        "CashFlowEvent must contain 'EventTimestamp timestamps = 17;' "
        "(plural) but the pattern was not found in:\n" + body
    )

    singular_pattern = r"EventTimestamp\s+timestamp\s*=\s*17\s*;"
    assert not re.search(singular_pattern, body), (
        "CashFlowEvent still contains the old singular 'EventTimestamp timestamp = 17;' "
        "— the rename was not applied"
    )


def test_cashflow_field_number_unchanged():
    """The renamed timestamps field must still carry field number 17."""
    text = _CASH_FLOW_PROTO.read_text(encoding="utf-8")
    body = _proto_message_body(text, "CashFlowEvent")

    match = re.search(r"EventTimestamp\s+timestamps\s*=\s*(\d+)\s*;", body)
    assert match is not None, (
        "EventTimestamp timestamps field not found in CashFlowEvent body"
    )
    field_number = int(match.group(1))
    assert field_number == 17, (
        "CashFlowEvent.timestamps must be field number 17 (wire-compatible); "
        "got " + str(field_number)
    )


def test_pb2_descriptor_has_timestamps_plural():
    """The generated pb2 descriptor must expose 'timestamps', not 'timestamp'."""
    mod = _import_cash_flow_pb2()
    descriptor = mod.CashFlowEvent.DESCRIPTOR
    fields_by_name = descriptor.fields_by_name

    assert "timestamps" in fields_by_name, (
        "CashFlowEvent pb2 descriptor is missing 'timestamps' field — "
        "regenerate cash_flow_event_pb2.py from the updated proto"
    )
    assert "timestamp" not in fields_by_name, (
        "CashFlowEvent pb2 descriptor still contains old singular 'timestamp' field — "
        "pb2 was not regenerated from the updated proto"
    )


def test_all_event_messages_use_plural_timestamps():
    """Every top-level message with an EventTimestamp field must name it 'timestamps' (plural).

    Iterates all .proto files under common/. For each top-level message body that
    contains an EventTimestamp field, asserts the field name is exactly 'timestamps'.
    Fails with file + message name if any use the singular form, generalising the
    lesson from R2-4.
    """
    violations = []

    for proto_path in sorted(_COMMON_DIR.rglob("*.proto")):
        text = proto_path.read_text(encoding="utf-8")
        relative = proto_path.relative_to(_REPO_ROOT)

        # Find all top-level message blocks (single level of braces only).
        for msg_match in re.finditer(r"message\s+(\w+)\s*\{([^}]*)\}", text, re.DOTALL):
            msg_name = msg_match.group(1)
            body = msg_match.group(2)

            # Check every EventTimestamp field declaration in this message body.
            for field_match in re.finditer(
                r"EventTimestamp\s+(\w+)\s*=\s*\d+\s*;", body
            ):
                field_name = field_match.group(1)
                if field_name != "timestamps":
                    violations.append(
                        str(relative) + " :: " + msg_name
                        + " — field name is '" + field_name
                        + "', expected 'timestamps'"
                    )

    assert not violations, (
        "Found EventTimestamp fields not named 'timestamps' (plural):\n  "
        + "\n  ".join(violations)
    )
