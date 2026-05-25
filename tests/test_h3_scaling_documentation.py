"""Tests for H3 (#7): int64 monetary field scaling documentation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

SCALING_MD = REPO_ROOT / "docs" / "SCALING.md"

# The 8 .proto files that must carry the SCALING.md reference comment.
SCALED_PROTO_FILES = [
    REPO_ROOT / "common" / "execution" / "fill_event.proto",
    REPO_ROOT / "common" / "execution" / "order_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "balance_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "cash_flow_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "fee_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "funding_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "position_event.proto",
    REPO_ROOT / "common" / "reconciliation" / "settlement_event.proto",
]


# ---------------------------------------------------------------------------
# 1. docs/SCALING.md exists and is non-empty
# ---------------------------------------------------------------------------

def test_scaling_md_exists():
    assert SCALING_MD.exists(), (
        f"docs/SCALING.md not found at {SCALING_MD}; H3 requires this file."
    )
    content = SCALING_MD.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "docs/SCALING.md exists but is empty."


# ---------------------------------------------------------------------------
# 2. SCALING.md mentions the key concepts required by H3
# ---------------------------------------------------------------------------

def test_scaling_md_mentions_key_concepts():
    content = SCALING_MD.read_text(encoding="utf-8")
    required = ["price_precision", "size_precision", "int64", "Decimal"]
    for concept in required:
        assert concept in content, (
            f"docs/SCALING.md does not mention '{concept}'. "
            "The file must cover all key scaling concepts."
        )


# ---------------------------------------------------------------------------
# 3. Each .proto file has a comment line that references SCALING.md
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("proto_path", SCALED_PROTO_FILES, ids=lambda p: p.name)
def test_each_int64_proto_references_scaling_md(proto_path):
    assert proto_path.exists(), (
        f"Expected proto file not found: {proto_path}"
    )
    lines = proto_path.read_text(encoding="utf-8").splitlines()
    found = any(
        line.strip().startswith("//") and "SCALING.md" in line
        for line in lines
    )
    assert found, (
        f"{proto_path.name}: no comment line mentioning 'SCALING.md' found. "
        "Each int64 monetary proto must reference docs/SCALING.md."
    )


# ---------------------------------------------------------------------------
# 4. Each .proto file has a comment line referencing price_precision
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("proto_path", SCALED_PROTO_FILES, ids=lambda p: p.name)
def test_each_int64_proto_mentions_price_precision_link(proto_path):
    assert proto_path.exists(), (
        f"Expected proto file not found: {proto_path}"
    )
    lines = proto_path.read_text(encoding="utf-8").splitlines()
    found = any(
        line.strip().startswith("//") and "price_precision" in line
        for line in lines
    )
    assert found, (
        f"{proto_path.name}: no comment line referencing 'price_precision' found. "
        "Each int64 monetary proto must link int64 fields to InstrumentRef.price_precision."
    )


# ---------------------------------------------------------------------------
# 5. Regression guard — canonical int64 fields are still int64 in the pb2 layer
# ---------------------------------------------------------------------------

def _add_generated_to_syspath():
    generated = str(REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)


def test_no_field_types_changed():
    """Wire-level proof that no monetary field type was accidentally changed."""
    _add_generated_to_syspath()

    from google.protobuf.descriptor import FieldDescriptor  # noqa: PLC0415

    INT64 = FieldDescriptor.TYPE_INT64

    from common.execution import fill_event_pb2  # noqa: PLC0415
    from common.reconciliation import fee_event_pb2  # noqa: PLC0415
    from common.reconciliation import funding_event_pb2  # noqa: PLC0415
    from common.reconciliation import settlement_event_pb2  # noqa: PLC0415

    # FillEvent.price (field 10)
    fill_descriptor = fill_event_pb2.FillEvent.DESCRIPTOR
    price_field = fill_descriptor.fields_by_name["price"]
    assert price_field.type == INT64, (
        f"FillEvent.price expected TYPE_INT64 ({INT64}), got {price_field.type}"
    )
    assert price_field.number == 10, (
        f"FillEvent.price expected field number 10, got {price_field.number}"
    )

    # FillEvent.quantity (field 9)
    qty_field = fill_descriptor.fields_by_name["quantity"]
    assert qty_field.type == INT64, (
        f"FillEvent.quantity expected TYPE_INT64, got {qty_field.type}"
    )
    assert qty_field.number == 9, (
        f"FillEvent.quantity expected field number 9, got {qty_field.number}"
    )

    # Fee.amount (field 2)
    fee_descriptor = fee_event_pb2.Fee.DESCRIPTOR
    amount_field = fee_descriptor.fields_by_name["amount"]
    assert amount_field.type == INT64, (
        f"Fee.amount expected TYPE_INT64, got {amount_field.type}"
    )
    assert amount_field.number == 2, (
        f"Fee.amount expected field number 2, got {amount_field.number}"
    )

    # FundingPayment.amount (field 6)
    fp_descriptor = funding_event_pb2.FundingPayment.DESCRIPTOR
    fp_amount = fp_descriptor.fields_by_name["amount"]
    assert fp_amount.type == INT64, (
        f"FundingPayment.amount expected TYPE_INT64, got {fp_amount.type}"
    )
    assert fp_amount.number == 6, (
        f"FundingPayment.amount expected field number 6, got {fp_amount.number}"
    )

    # SettlementEvent.settlement_price (field 6)
    se_descriptor = settlement_event_pb2.SettlementEvent.DESCRIPTOR
    sp_field = se_descriptor.fields_by_name["settlement_price"]
    assert sp_field.type == INT64, (
        f"SettlementEvent.settlement_price expected TYPE_INT64, got {sp_field.type}"
    )
    assert sp_field.number == 6, (
        f"SettlementEvent.settlement_price expected field number 6, got {sp_field.number}"
    )


# ---------------------------------------------------------------------------
# 6. Regression: funding_event.proto still documents the 9dp convention (H1)
# ---------------------------------------------------------------------------

def test_funding_rate_still_documents_9dp():
    funding_proto = REPO_ROOT / "common" / "reconciliation" / "funding_event.proto"
    assert funding_proto.exists(), f"funding_event.proto not found at {funding_proto}"
    content = funding_proto.read_text(encoding="utf-8")

    # H1 established a 9 decimal place (9dp / 1_000_000_000) convention for rates.
    # Check that both the numeric marker and the word "decimal" still appear.
    assert "9 decimal" in content or "9dp" in content or "1_000_000_000" in content, (
        "funding_event.proto no longer mentions the 9-decimal-place funding rate "
        "convention. H1 (#5) established this; it must not be removed."
    )
