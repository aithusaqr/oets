"""
M4 tests: verify EventTimestamp fields use google.protobuf.Timestamp (#11).
"""

import re
import sys
from pathlib import Path

import pytest

# Ensure generated/python is on the path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "generated" / "python"))

TIMESTAMPS_PROTO = REPO_ROOT / "common" / "timestamps.proto"

_PROTO_TEXT = TIMESTAMPS_PROTO.read_text()

# Extract the body of the EventTimestamp message block
_MSG_MATCH = re.search(r"message\s+EventTimestamp\s*\{([^}]+)\}", _PROTO_TEXT, re.DOTALL)
_MSG_BODY = _MSG_MATCH.group(1) if _MSG_MATCH else ""

_FIELDS = [
    ("decision_timestamp", 1),
    ("submitted_timestamp", 2),
    ("event_timestamp", 3),
    ("ledger_timestamp", 4),
    ("observed_timestamp", 5),
    ("valuation_timestamp", 6),
]


def test_timestamps_proto_imports_google_timestamp():
    """timestamps.proto must import the well-known Timestamp type."""
    assert 'import "google/protobuf/timestamp.proto";' in _PROTO_TEXT, (
        "common/timestamps.proto is missing "
        'import "google/protobuf/timestamp.proto";'
    )


def test_all_six_fields_use_google_timestamp_type():
    """Every field in EventTimestamp must be declared as google.protobuf.Timestamp."""
    for name, num in _FIELDS:
        pattern = rf"\bgoogle\.protobuf\.Timestamp\s+{name}\s*=\s*{num}\s*;"
        assert re.search(pattern, _MSG_BODY), (
            f"Field '{name} = {num}' is not declared as "
            f"google.protobuf.Timestamp in EventTimestamp. "
            f"Body:\n{_MSG_BODY}"
        )


def test_no_field_uses_string_type():
    """No field in EventTimestamp should have type 'string' after M4."""
    string_field = re.search(r"\bstring\s+\w+\s*=\s*\d+\s*;", _MSG_BODY)
    assert string_field is None, (
        f"Found a 'string' typed field in EventTimestamp — "
        f"all fields must be google.protobuf.Timestamp. "
        f"Offending declaration: '{string_field.group(0).strip()}'"
    )


def test_pb2_descriptor_uses_message_type():
    """The generated pb2 descriptor must reflect MESSAGE type pointing to google.protobuf.Timestamp."""
    from google.protobuf.descriptor import FieldDescriptor
    from common import timestamps_pb2  # noqa: PLC0415

    descriptor = timestamps_pb2.EventTimestamp.DESCRIPTOR
    for name, _ in _FIELDS:
        field = descriptor.fields_by_name.get(name)
        assert field is not None, (
            f"Field '{name}' not found in EventTimestamp descriptor"
        )
        assert field.type == FieldDescriptor.TYPE_MESSAGE, (
            f"Field '{name}' has type {field.type!r}, "
            f"expected TYPE_MESSAGE ({FieldDescriptor.TYPE_MESSAGE})"
        )
        assert field.message_type.full_name == "google.protobuf.Timestamp", (
            f"Field '{name}' message_type.full_name is "
            f"'{field.message_type.full_name}', "
            f"expected 'google.protobuf.Timestamp'"
        )


def test_roundtrip_with_real_timestamp():
    """Serialize and deserialize EventTimestamp with a real Timestamp value."""
    from google.protobuf.timestamp_pb2 import Timestamp
    from common.timestamps_pb2 import EventTimestamp

    original_ts = Timestamp(seconds=1234567890, nanos=123456789)

    original = EventTimestamp(decision_timestamp=original_ts)
    serialized = original.SerializeToString()

    recovered = EventTimestamp()
    recovered.ParseFromString(serialized)

    assert recovered.decision_timestamp.seconds == 1234567890, (
        f"Roundtrip seconds mismatch: "
        f"expected 1234567890, got {recovered.decision_timestamp.seconds}"
    )
    assert recovered.decision_timestamp.nanos == 123456789, (
        f"Roundtrip nanos mismatch: "
        f"expected 123456789, got {recovered.decision_timestamp.nanos}"
    )
    assert recovered.decision_timestamp == original_ts, (
        f"Roundtrip Timestamp mismatch: "
        f"expected {original_ts!r}, got {recovered.decision_timestamp!r}"
    )


def test_dependent_pb2_modules_still_import():
    """All pb2 modules that depend on timestamps must still import cleanly."""
    import importlib

    dependent_modules = [
        "common.event_envelope_pb2",
        "common.execution.order_event_pb2",
        "common.reconciliation.balance_event_pb2",
        "common.reconciliation.cash_flow_event_pb2",
        "common.reconciliation.position_event_pb2",
    ]
    for mod_name in dependent_modules:
        try:
            mod = importlib.import_module(mod_name)
        except ImportError as exc:
            pytest.fail(
                f"Failed to import {mod_name} after timestamps M4 regeneration: {exc}"
            )
        assert mod is not None, f"Import of {mod_name} returned None unexpectedly"
