"""
Tests for L6 (#19): FillEvent.source (field 15) deduplication.

Asserts that:
- The top-level `source` field is removed from FillEvent.
- Field number 15 and the name "source" are both reserved.
- The `envelope` field is untouched (regression guard).
- The `timestamps` field (19) is untouched (M2 / #9's territory).
- The now-unused `import "common/source.proto"` is absent.
- The regenerated pb2 descriptor matches the proto changes.
"""

import re
import sys
import pathlib

import pytest

PROTO_PATH = pathlib.Path(__file__).parent.parent / "common" / "execution" / "fill_event.proto"
GENERATED_ROOT = pathlib.Path(__file__).parent.parent / "generated" / "python"


def _proto_text() -> str:
    return PROTO_PATH.read_text()


def _fillevent_body(text: str) -> str:
    """Extract the body of the FillEvent message (between the outermost braces)."""
    match = re.search(r"message\s+FillEvent\s*\{(.+?)\n\}", text, re.DOTALL)
    assert match, "Could not locate FillEvent message body in proto file"
    return match.group(1)


# ---------------------------------------------------------------------------
# Proto-level assertions
# ---------------------------------------------------------------------------

def test_source_field_removed():
    """No top-level field declaration for `source` inside FillEvent."""
    body = _fillevent_body(_proto_text())
    # A field declaration looks like:  <type> source = <number>;
    # We must NOT match the reserved "source"; line or comments.
    # Pattern: word characters, whitespace, then the name 'source', then '=', then digits.
    field_decl = re.compile(r"^\s*\w[\w.]*\s+source\s*=\s*\d+", re.MULTILINE)
    matches = field_decl.findall(body)
    assert not matches, (
        f"Found unexpected top-level 'source' field declaration(s) in FillEvent: {matches}"
    )


def test_field_15_reserved():
    """Field number 15 must be reserved in FillEvent."""
    body = _fillevent_body(_proto_text())
    # Accept:  reserved 15;  or  reserved 14, 15, 16;  etc.
    assert re.search(r"\breserved\b[^;]*\b15\b", body), (
        "Expected 'reserved 15;' (or equivalent) in FillEvent body but did not find it.\n"
        f"FillEvent body:\n{body}"
    )


def test_field_name_source_reserved():
    """The name "source" must be reserved in FillEvent."""
    body = _fillevent_body(_proto_text())
    assert re.search(r'reserved\s+"source"', body), (
        'Expected reserved "source"; in FillEvent body but did not find it.\n'
        f"FillEvent body:\n{body}"
    )


def test_envelope_field_still_present():
    """OetsEventEnvelope envelope = 1 must remain (regression guard)."""
    body = _fillevent_body(_proto_text())
    assert re.search(r"\benvelope\s*=\s*1\b", body), (
        "envelope field (number 1) appears to have been removed from FillEvent — "
        "this should NOT have been touched.\n"
        f"FillEvent body:\n{body}"
    )


def test_timestamps_field_still_present():
    """EventTimestamp timestamps = 19 must remain (M2 / #9 handles its removal)."""
    body = _fillevent_body(_proto_text())
    assert re.search(r"\btimestamps\s*=\s*19\b", body), (
        "timestamps field (number 19) appears to have been removed from FillEvent — "
        "that is M2 (#9)'s territory and must NOT be touched in this PR.\n"
        f"FillEvent body:\n{body}"
    )


def test_unused_source_import_removed():
    """import \"common/source.proto\" must NOT appear now that the field is gone."""
    text = _proto_text()
    assert 'import "common/source.proto"' not in text, (
        "Found 'import \"common/source.proto\"' still present in fill_event.proto. "
        "It is unused after field 15 was removed and should be deleted."
    )


# ---------------------------------------------------------------------------
# Generated pb2 descriptor assertions
# ---------------------------------------------------------------------------

def test_generated_pb2_in_sync():
    """The regenerated fill_event_pb2 descriptor must reflect all proto changes."""
    # Ensure generated/python is importable
    gen_root = str(GENERATED_ROOT)
    if gen_root not in sys.path:
        sys.path.insert(0, gen_root)

    try:
        from common.execution import fill_event_pb2  # noqa: PLC0415
    except ImportError as exc:
        pytest.fail(f"Could not import fill_event_pb2: {exc}")

    descriptor = fill_event_pb2.FillEvent.DESCRIPTOR

    field_names = {f.name for f in descriptor.fields}
    field_numbers = {f.number for f in descriptor.fields}

    # `source` must be absent
    assert "source" not in field_names, (
        f"'source' is still present in FillEvent descriptor fields: {field_names}"
    )

    # Field number 15 must not be assigned to any field
    assert 15 not in field_numbers, (
        f"Field number 15 is still in use in FillEvent descriptor: "
        f"{descriptor.fields_by_number.get(15)}"
    )

    # `envelope` must be at number 1
    assert "envelope" in field_names, (
        f"'envelope' field is missing from FillEvent descriptor: {field_names}"
    )
    assert descriptor.fields_by_name["envelope"].number == 1, (
        f"'envelope' field number changed: {descriptor.fields_by_name['envelope'].number}"
    )

    # `timestamps` must be at number 19 (M2 must not have been touched)
    assert "timestamps" in field_names, (
        f"'timestamps' field is missing from FillEvent descriptor: {field_names}"
    )
    assert descriptor.fields_by_name["timestamps"].number == 19, (
        f"'timestamps' field number changed: {descriptor.fields_by_name['timestamps'].number}"
    )
