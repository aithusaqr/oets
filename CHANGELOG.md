# Changelog

All notable changes to OETS protos are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and OETS adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The current version is communicated by `OetsEventEnvelope.oets_version` (see `validation/oets_version.py`). Wire-incompatible changes warrant a MAJOR bump; new optional fields warrant MINOR; editorial / non-breaking warrant PATCH.

## [Unreleased]

### Added
- (nothing yet — open follow-ups tracked in zachisit/oets#7, #38, #40)

## [0.1.0] — 2026-05-26

Epic v0.1 code review (epic PR aithusaqr/oets#25) — schema, build, design, test infra.

### Added
- `docs/SCALING.md` — canonical int64 monetary scaling convention (H3)
- `docs/ARCHITECTURE.md` — envelope-bearing vs snapshot/delta classification (R2-2)
- `validation/oets_version.py` — SemVer 2.0.0 validator for `oets_version` (L7)
- `common/reconciliation/funding_event.proto` — `FundingRate`, `FundingPayment` (H1)
- `common/reconciliation/settlement_event.proto` filled — `SettlementEvent`, `SettlementType` (H1)
- `EVENT_TYPE_SETTLEMENT = 4` (M1) and `EVENT_TYPE_FUNDING = 7` (R2-3)
- `OetsEventEnvelope` carried by `CashFlowEvent`, `SettlementEvent`, `FundingRate`, `FundingPayment` (R2-2)
- Python test infrastructure: pytest + buf config + GitHub Actions CI workflow
- `buf.yaml` + `buf.gen.yaml`, `requirements.txt`, `pyproject.toml` `[project]` table

### Changed (wire-breaking)
- `EventTimestamp` fields: `string` → `google.protobuf.Timestamp` (M4, aithusaqr/oets#11)
- `Fee.amount`: `string` → `int64` (M6, aithusaqr/oets#13)
- `Fee.fee_type`: `string` → `FeeType` enum (H2, aithusaqr/oets#6)
- `OrderSide`, `OrderTimeInForce`, `OrderIntentionType`: zero-value sentinel `UNKNOWN_*=0` inserted, existing values shifted +1 (M3, aithusaqr/oets#10)
- `FillEvent` fields 15 (`source`) and 19 (`timestamps`) removed + reserved (L6/M2, aithusaqr/oets#19, #9)
- `OrderEvent` fields 13 (`source`) and 14 (`timestamps`) removed + reserved (R2-1, zachisit/oets#20)
- `InstrumentRef` fields 6, 8, 11, 12, 16 removed + reserved (L5, aithusaqr/oets#18)
- `CashFlowEvent` / `SettlementEvent` / `FundingRate` / `FundingPayment`: `OetsEventEnvelope envelope = 1` replaces top-level `event_id`; top-level `source`/`timestamps`/`related_events` removed (R2-2, zachisit/oets#21)
- `CashFlowEvent.timestamp` → `timestamps` plural (R2-4, zachisit/oets#23)

### Changed (source-breaking, wire-compat)
- `EVENT_TYPE_CASH_FLOW_EVENT` renamed to `EVENT_TYPE_CASH_FLOW` (R2-3, zachisit/oets#22)
- `Makefile generate_python_protos` now invokes `python -m grpc_tools.protoc` to match runtime gencode (R2-5)
- `protobuf>=5.29,<6` pinned (R3-2)
- `requires-python = ">=3.11"` (R3-5)

### Removed
- `InstrumentRef.days_to_expiry`, `price_precision_rounding`, `size_precision_rounding`, `lot_size`, `notional_lot_size` (L5)

### Fixed
- `EventType` gap at value 4 closed (M1)
- Makefile `.PHONY` declaration added (L1)
- Test infrastructure scaffolded (zachisit/oets#4)

[Unreleased]: https://github.com/aithusaqr/oets/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/aithusaqr/oets/releases/tag/v0.1.0
