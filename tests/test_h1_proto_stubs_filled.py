"""Tests for H1 (#5): funding_event.proto and settlement_event.proto filled in.

Covers:
  - File existence and content for both new/updated protos.
  - buf.yaml no longer ignores settlement_event.proto.
  - pb2 imports work and key classes are accessible.
  - Wire-level roundtrip for FundingPayment and SettlementEvent.
"""

import re
import sys
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers (mirrors test_proto_structure.py helpers)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent


def _proto_text(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text(encoding="utf-8")


def _imports_from_text(text: str) -> list:
    return re.findall(r'^import\s+"([^"]+)"', text, re.MULTILINE)


def _enum_blocks(text: str) -> list:
    pattern = re.compile(r'\benum\s+(\w+)\s*\{([^}]*)\}', re.DOTALL)
    return [(m.group(1), m.group(2)) for m in pattern.finditer(text)]


def _enum_values(enum_body: str) -> list:
    """Return list of value names from an enum body."""
    return re.findall(r'(\w+)\s*=\s*\d+\s*;', enum_body)


# ---------------------------------------------------------------------------
# 1. funding_event.proto — file exists
# ---------------------------------------------------------------------------

def test_funding_event_proto_exists():
    path = _REPO_ROOT / "common" / "reconciliation" / "funding_event.proto"
    assert path.is_file(), "common/reconciliation/funding_event.proto must exist"


# ---------------------------------------------------------------------------
# 2. funding_event.proto — required messages present
# ---------------------------------------------------------------------------

def test_funding_event_has_required_messages():
    text = _proto_text("common/reconciliation/funding_event.proto")
    assert re.search(r'\bmessage\s+FundingRate\b', text), "FundingRate message missing"
    assert re.search(r'\bmessage\s+FundingPayment\b', text), "FundingPayment message missing"


# ---------------------------------------------------------------------------
# 3. funding_event.proto — FundingPaymentDirection enum with 3 entries
# ---------------------------------------------------------------------------

def test_funding_event_has_funding_payment_direction_enum():
    text = _proto_text("common/reconciliation/funding_event.proto")
    enums = dict(_enum_blocks(text))
    assert "FundingPaymentDirection" in enums, "FundingPaymentDirection enum missing"
    values = _enum_values(enums["FundingPaymentDirection"])
    assert len(values) >= 3, (
        "FundingPaymentDirection must have at least 3 entries "
        "(UNSPECIFIED, LONG_PAYS_SHORT, SHORT_PAYS_LONG)"
    )
    assert any("UNSPECIFIED" in v for v in values), "UNSPECIFIED entry missing"
    assert any("LONG_PAYS_SHORT" in v for v in values), "LONG_PAYS_SHORT entry missing"
    assert any("SHORT_PAYS_LONG" in v for v in values), "SHORT_PAYS_LONG entry missing"


# ---------------------------------------------------------------------------
# 4. funding_event.proto — imports resolve
# ---------------------------------------------------------------------------

def test_funding_event_imports_resolve():
    path = _REPO_ROOT / "common" / "reconciliation" / "funding_event.proto"
    text = path.read_text(encoding="utf-8")
    imports = _imports_from_text(text)
    project_imports = [i for i in imports if not i.startswith("google/protobuf/")]
    missing = [i for i in project_imports if not (_REPO_ROOT / i).is_file()]
    assert not missing, "funding_event.proto has unresolvable imports: " + str(missing)


# ---------------------------------------------------------------------------
# 5. settlement_event.proto — no longer a placeholder
# ---------------------------------------------------------------------------

def test_settlement_event_no_longer_placeholder():
    text = _proto_text("common/reconciliation/settlement_event.proto")
    assert re.search(r'\bmessage\s+SettlementEvent\b', text), (
        "SettlementEvent message missing — placeholder was not replaced"
    )


# ---------------------------------------------------------------------------
# 6. settlement_event.proto — SettlementType enum with 5+ entries incl UNSPECIFIED
# ---------------------------------------------------------------------------

def test_settlement_event_has_settlement_type_enum():
    text = _proto_text("common/reconciliation/settlement_event.proto")
    enums = dict(_enum_blocks(text))
    assert "SettlementType" in enums, "SettlementType enum missing"
    values = _enum_values(enums["SettlementType"])
    assert len(values) >= 5, "SettlementType must have at least 5 entries"
    assert any("UNSPECIFIED" in v for v in values), "SETTLEMENT_TYPE_UNSPECIFIED entry missing"


# ---------------------------------------------------------------------------
# 7. settlement_event.proto — imports resolve
# ---------------------------------------------------------------------------

def test_settlement_event_imports_resolve():
    path = _REPO_ROOT / "common" / "reconciliation" / "settlement_event.proto"
    text = path.read_text(encoding="utf-8")
    imports = _imports_from_text(text)
    project_imports = [i for i in imports if not i.startswith("google/protobuf/")]
    missing = [i for i in project_imports if not (_REPO_ROOT / i).is_file()]
    assert not missing, "settlement_event.proto has unresolvable imports: " + str(missing)


# ---------------------------------------------------------------------------
# 8. buf.yaml — no longer ignores settlement_event.proto
# ---------------------------------------------------------------------------

def test_buf_yaml_no_longer_ignores_settlement():
    buf_yaml = _REPO_ROOT / "buf.yaml"
    config = yaml.safe_load(buf_yaml.read_text(encoding="utf-8"))
    lint = config.get("lint", {})
    ignore_list = lint.get("ignore", [])
    settlement_path = "common/reconciliation/settlement_event.proto"
    assert settlement_path not in ignore_list, (
        "buf.yaml still ignores settlement_event.proto — "
        "the ignore entry should have been removed by H1"
    )


# ---------------------------------------------------------------------------
# 9. funding_event_pb2 — classes importable
# ---------------------------------------------------------------------------

def test_funding_event_pb2_imports():
    generated = str(_REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)

    mod = __import__("common.reconciliation.funding_event_pb2",
                     fromlist=["FundingRate", "FundingPayment"])
    assert hasattr(mod, "FundingRate"), "FundingRate class not found in funding_event_pb2"
    assert hasattr(mod, "FundingPayment"), "FundingPayment class not found in funding_event_pb2"


# ---------------------------------------------------------------------------
# 10. settlement_event_pb2 — classes importable
# ---------------------------------------------------------------------------

def test_settlement_event_pb2_imports():
    generated = str(_REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)

    mod = __import__("common.reconciliation.settlement_event_pb2",
                     fromlist=["SettlementEvent"])
    assert hasattr(mod, "SettlementEvent"), (
        "SettlementEvent class not found in settlement_event_pb2"
    )


# ---------------------------------------------------------------------------
# 11. FundingPayment — wire-level roundtrip
# ---------------------------------------------------------------------------

def test_funding_payment_roundtrip():
    generated = str(_REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)

    from common.reconciliation.funding_event_pb2 import FundingPayment
    from common.event_envelope_pb2 import OetsEventEnvelope, EventType

    original = FundingPayment(
        envelope=OetsEventEnvelope(
            event_id="fp-001",
            event_type=EventType.EVENT_TYPE_FUNDING,
        ),
        venue_id="drift",
        account_id="acct-abc",
        instrument_id="SOL-PERP",
        asset_id="USDC",
        amount=-500,          # negative = account paid out
        position_size=10_000_000_000,  # 10.0 in 9-dp fixed-point
        rate_applied=100_000,          # 0.0001 (0.01 %) in 9-dp
        related_funding_rate_event_id="fr-999",
    )
    original.metadata["source_tag"] = "test"

    serialized = original.SerializeToString()
    recovered = FundingPayment()
    recovered.ParseFromString(serialized)

    assert recovered.envelope.event_id == "fp-001"
    assert recovered.envelope.event_type == EventType.EVENT_TYPE_FUNDING
    assert recovered.venue_id == "drift"
    assert recovered.account_id == "acct-abc"
    assert recovered.instrument_id == "SOL-PERP"
    assert recovered.asset_id == "USDC"
    assert recovered.amount == -500
    assert recovered.position_size == 10_000_000_000
    assert recovered.rate_applied == 100_000
    assert recovered.related_funding_rate_event_id == "fr-999"
    assert recovered.metadata["source_tag"] == "test"


# ---------------------------------------------------------------------------
# 12. SettlementEvent — wire-level roundtrip
# ---------------------------------------------------------------------------

def test_settlement_event_roundtrip():
    generated = str(_REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)

    from common.reconciliation.settlement_event_pb2 import SettlementEvent, SettlementType
    from common.event_envelope_pb2 import OetsEventEnvelope, EventType

    original = SettlementEvent(
        envelope=OetsEventEnvelope(
            event_id="se-001",
            event_type=EventType.EVENT_TYPE_SETTLEMENT,
        ),
        venue_id="drift",
        account_id="acct-abc",
        instrument_id="SOL-PERP",
        settlement_type=SettlementType.SETTLEMENT_TYPE_PERP_MARK_SETTLEMENT,
        settlement_price=24_500_000_000,   # $24.50 in 9-dp
        quantity_settled=10_000_000_000,   # 10.0 in 9-dp
        settlement_amount=250_000_000,     # positive = inflow
        settlement_asset_id="USDC",
        realized_pnl=125_000_000,
        realized_pnl_asset_id="USDC",
    )
    original.metadata["tag"] = "h1-test"

    serialized = original.SerializeToString()
    recovered = SettlementEvent()
    recovered.ParseFromString(serialized)

    assert recovered.envelope.event_id == "se-001"
    assert recovered.envelope.event_type == EventType.EVENT_TYPE_SETTLEMENT
    assert recovered.settlement_type == SettlementType.SETTLEMENT_TYPE_PERP_MARK_SETTLEMENT
    assert recovered.settlement_price == 24_500_000_000
    assert recovered.quantity_settled == 10_000_000_000
    assert recovered.settlement_amount == 250_000_000
    assert recovered.settlement_asset_id == "USDC"
    assert recovered.realized_pnl == 125_000_000
    assert recovered.realized_pnl_asset_id == "USDC"
    assert recovered.metadata["tag"] == "h1-test"
