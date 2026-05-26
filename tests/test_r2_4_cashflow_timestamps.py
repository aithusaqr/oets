"""R2-4 (#23): CashFlowEvent.timestamp → timestamps (plural) for schema consistency.

CashFlowEvent was the only message using the singular `timestamp`; every
other event/snapshot/delta uses plural `timestamps`. Field number 17 is
unchanged (rename is wire-compatible in proto3).

R2-2 (#21) update: CashFlowEvent.timestamps (field 17) was subsequently
removed in R2-2 and replaced by OetsEventEnvelope (field 1). Field 17 is
now reserved. Tests below have been updated to reflect the R2-2 state.

See: https://github.com/zachisit/oets/issues/23
See: https://github.com/zachisit/oets/issues/21
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

def test_cashflow_has_envelope_at_field_1():
    """R2-2 (#21): CashFlowEvent field 1 must be OetsEventEnvelope envelope (not event_id string).

    R2-4 established that timestamps must be plural. R2-2 subsequently moved
    timestamps into the envelope, reserving field 17. This test verifies the
    R2-2 state: envelope is at field 1.
    """
    text = _CASH_FLOW_PROTO.read_text(encoding="utf-8")
    body = _proto_message_body(text, "CashFlowEvent")

    envelope_pattern = r"OetsEventEnvelope\s+envelope\s*=\s*1\s*;"
    assert re.search(envelope_pattern, body), (
        "CashFlowEvent must contain 'OetsEventEnvelope envelope = 1;' "
        "(R2-2 architectural fix) but the pattern was not found in:\n" + body
    )

    # Old string event_id must be gone (reserved, not a live field).
    event_id_field_pattern = r"string\s+event_id\s*=\s*1\s*;"
    assert not re.search(event_id_field_pattern, body), (
        "CashFlowEvent still contains the old 'string event_id = 1;' field — "
        "R2-2 was not applied"
    )


def test_cashflow_field_17_is_reserved():
    """R2-2 (#21): CashFlowEvent field 17 (formerly EventTimestamp timestamps) must be reserved."""
    text = _CASH_FLOW_PROTO.read_text(encoding="utf-8")
    body = _proto_message_body(text, "CashFlowEvent")

    # reserved 17 should be present (may also include 18, 19 in same statement).
    reserved_pattern = r"reserved\s+[0-9, ]*\b17\b"
    assert re.search(reserved_pattern, body), (
        "CashFlowEvent field 17 must be listed in a 'reserved' declaration "
        "(R2-2 removed EventTimestamp timestamps from the top-level message). "
        "Body:\n" + body
    )

    # The old live timestamps declaration must not appear.
    timestamps_field_pattern = r"EventTimestamp\s+timestamps\s*=\s*17\s*;"
    assert not re.search(timestamps_field_pattern, body), (
        "CashFlowEvent still contains the live 'EventTimestamp timestamps = 17;' field — "
        "R2-2 was not fully applied"
    )


def test_pb2_descriptor_has_envelope_at_field_1():
    """The generated pb2 descriptor must expose 'envelope' at field 1, not 'timestamps'."""
    mod = _import_cash_flow_pb2()
    descriptor = mod.CashFlowEvent.DESCRIPTOR

    assert 1 in descriptor.fields_by_number, (
        "CashFlowEvent pb2 descriptor has no field at number 1 — "
        "regenerate cash_flow_event_pb2.py from the updated proto"
    )
    field_1 = descriptor.fields_by_number[1]
    assert field_1.name == "envelope", (
        "CashFlowEvent pb2 descriptor field 1 should be 'envelope', "
        "got '" + field_1.name + "' — pb2 may not have been regenerated"
    )

    assert "timestamps" not in descriptor.fields_by_name, (
        "CashFlowEvent pb2 descriptor still exposes top-level 'timestamps' field — "
        "R2-2 was not applied or pb2 was not regenerated"
    )
    assert "event_id" not in descriptor.fields_by_name, (
        "CashFlowEvent pb2 descriptor still exposes top-level 'event_id' field — "
        "R2-2 was not applied or pb2 was not regenerated"
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
