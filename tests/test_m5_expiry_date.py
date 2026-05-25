"""
M5 regression tests: InstrumentRef.expiry_date format documentation.

Covers:
  - expiry_date field declaration unchanged (int32, field number 15)
  - Comment block documents YYYYMMDD encoding
  - Comment block documents zero-value semantics (no expiry)
  - days_to_expiry removed (L5's work intact, field 16 still reserved)
  - pb2 descriptor still reflects expiry_date as TYPE_INT32 at number 15
"""

import re
import pathlib
import sys
import os

PROTO_PATH = pathlib.Path(__file__).parent.parent / "common" / "instrument.proto"


def _proto_lines():
    return PROTO_PATH.read_text().splitlines()


def _comment_block_before_expiry_date():
    """Return the comment lines immediately preceding 'int32 expiry_date = 15;'."""
    lines = _proto_lines()
    expiry_idx = None
    for i, line in enumerate(lines):
        if re.search(r"\bint32\s+expiry_date\s*=\s*15\s*;", line):
            expiry_idx = i
            break
    assert expiry_idx is not None, (
        "Could not locate 'int32 expiry_date = 15;' in instrument.proto — "
        "was the field removed or its number changed?"
    )
    # Walk backwards, collecting contiguous comment lines.
    comment_lines = []
    i = expiry_idx - 1
    while i >= 0 and lines[i].strip().startswith("//"):
        comment_lines.insert(0, lines[i])
        i -= 1
    return comment_lines


# ---------------------------------------------------------------------------
# 1. Field declaration unchanged: int32, field number 15
# ---------------------------------------------------------------------------

def test_expiry_date_still_int32_at_15():
    """expiry_date must remain typed int32 at field number 15 (regression guard)."""
    found = any(
        re.search(r"\bint32\s+expiry_date\s*=\s*15\s*;", line)
        for line in _proto_lines()
    )
    assert found, (
        "Expected 'int32 expiry_date = 15;' in common/instrument.proto but it was "
        "not found — the type or field number may have been changed unexpectedly."
    )


# ---------------------------------------------------------------------------
# 2. Comment block documents YYYYMMDD
# ---------------------------------------------------------------------------

def test_expiry_date_documented_as_yyyymmdd():
    """The comment block above expiry_date must contain the literal 'YYYYMMDD'."""
    block = _comment_block_before_expiry_date()
    assert block, (
        "No comment lines found immediately above 'int32 expiry_date = 15;'. "
        "A documentation block is required per M5."
    )
    combined = "\n".join(block)
    assert "YYYYMMDD" in combined, (
        f"Comment block above expiry_date does not contain 'YYYYMMDD'.\n"
        f"Current comment block:\n{combined}"
    )


# ---------------------------------------------------------------------------
# 3. Comment block documents zero-value semantics
# ---------------------------------------------------------------------------

def test_expiry_date_documents_zero_means_no_expiry():
    """The comment block must mention '0' AND at least one of: no/perpetual/spot/FX."""
    block = _comment_block_before_expiry_date()
    assert block, (
        "No comment lines found immediately above 'int32 expiry_date = 15;'. "
        "A documentation block is required per M5."
    )
    combined = "\n".join(block)

    assert "0" in combined, (
        f"Comment block above expiry_date does not mention '0' (the sentinel for "
        f"'no expiry').\nCurrent comment block:\n{combined}"
    )

    zero_semantic_tokens = {"no", "perpetual", "spot", "FX"}
    lower_combined = combined.lower()
    found_token = any(tok.lower() in lower_combined for tok in zero_semantic_tokens)
    assert found_token, (
        f"Comment block mentions '0' but does not explain its meaning. Expected at "
        f"least one of {zero_semantic_tokens!r} to appear (case-insensitive).\n"
        f"Current comment block:\n{combined}"
    )


# ---------------------------------------------------------------------------
# 4. days_to_expiry still removed (L5 regression guard)
# ---------------------------------------------------------------------------

def test_days_to_expiry_still_removed():
    """days_to_expiry must NOT be a live field; field 16 must still be reserved."""
    lines = _proto_lines()
    full_text = "\n".join(lines)

    # Must not exist as a live field declaration anywhere in InstrumentRef.
    live_field_pattern = re.compile(
        r"^\s*\w+\s+days_to_expiry\s*=\s*\d+\s*;", re.MULTILINE
    )
    assert not live_field_pattern.search(full_text), (
        "Found a live field declaration for 'days_to_expiry' in instrument.proto — "
        "this field was removed by L5 (#18) and must not be re-added."
    )

    # Field number 16 must appear in a reserved declaration.
    reserved_16_pattern = re.compile(r"\breserved\b[^;]*\b16\b[^;]*;")
    assert reserved_16_pattern.search(full_text), (
        "Field number 16 is no longer present in a 'reserved' declaration. "
        "L5 (#18) reserved it to prevent reuse; it must remain reserved."
    )


# ---------------------------------------------------------------------------
# 5. pb2 descriptor: expiry_date present, TYPE_INT32, field number 15
# ---------------------------------------------------------------------------

def test_pb2_descriptor_still_has_expiry_date_int32():
    """pb2 descriptor must reflect expiry_date as TYPE_INT32 at field number 15."""
    # Ensure the generated package is importable.
    generated_root = str(pathlib.Path(__file__).parent.parent / "generated" / "python")
    if generated_root not in sys.path:
        sys.path.insert(0, generated_root)

    try:
        from common import instrument_pb2  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            f"Could not import common.instrument_pb2 from {generated_root}: {exc}"
        ) from exc

    descriptor = instrument_pb2.InstrumentRef.DESCRIPTOR
    field_names = [f.name for f in descriptor.fields]
    assert "expiry_date" in field_names, (
        f"'expiry_date' not found in InstrumentRef descriptor. "
        f"Present fields: {field_names}"
    )

    field = descriptor.fields_by_name["expiry_date"]

    # FieldDescriptorProto.TYPE_INT32 == 5
    TYPE_INT32 = 5
    assert field.type == TYPE_INT32, (
        f"expiry_date has type {field.type!r} in the pb2 descriptor; "
        f"expected TYPE_INT32 ({TYPE_INT32}). The int32 type must not be changed."
    )

    assert field.number == 15, (
        f"expiry_date has field number {field.number!r} in the pb2 descriptor; "
        f"expected 15. The field number must not be changed."
    )
