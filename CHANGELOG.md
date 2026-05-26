# Changelog

All notable changes to OETS protos are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and OETS adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The current version is communicated by `OetsEventEnvelope.oets_version` (see `validation/oets_version.py`). Wire-incompatible changes warrant a MAJOR bump; new optional fields warrant MINOR; editorial / non-breaking warrant PATCH.

## [Unreleased]

The v0.1 code-review epic (aithusaqr/oets#25) collapses three review rounds (R1, R2, R3) into a single release record. Until upstream tags `v0.1.0`, every entry below lives in `[Unreleased]`; once tagged, this section will be renamed to `## [0.1.0] — <release date>` and a fresh `[Unreleased]` heading will be added.

### Added
- `docs/SCALING.md` — canonical int64 monetary scaling convention (H3, aithusaqr/oets#7)
- `docs/ARCHITECTURE.md` — envelope-bearing vs snapshot/delta classification, sub-component inventory (R2-2 / R3-7, zachisit/oets#21, #49)
- `validation/oets_version.py` — SemVer 2.0.0 validator for `oets_version` (L7, aithusaqr/oets#20)
- `common/reconciliation/funding_event.proto` — `FundingRate`, `FundingPayment` (H1, aithusaqr/oets#5)
- `common/reconciliation/settlement_event.proto` filled — `SettlementEvent`, `SettlementType` (H1, aithusaqr/oets#5)
- `EVENT_TYPE_SETTLEMENT = 4` (M1, aithusaqr/oets#8) and `EVENT_TYPE_FUNDING_RATE = 7` + `EVENT_TYPE_FUNDING_PAYMENT = 8` (R2-3 / R3-4, zachisit/oets#22, #46)
- `OetsEventEnvelope envelope = 1` carried by `CashFlowEvent`, `SettlementEvent`, `FundingRate`, `FundingPayment` (R2-2, zachisit/oets#21)
- Python test infrastructure: pytest + buf config + GitHub Actions CI workflow with Python 3.11/3.12/3.13 matrix (R1 + R3-6, aithusaqr/oets#17, zachisit/oets#48)
- `buf.yaml` + `buf.gen.yaml`, `requirements.txt`, `pyproject.toml` `[project]` table (L3, aithusaqr/oets#16)
- `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, README License section (R3-8 / R3-9 / R3-10, zachisit/oets#50, #51, #52)

### Changed (wire-breaking)
- `EventTimestamp` fields: `string` → `google.protobuf.Timestamp` (M4, aithusaqr/oets#11)
- `Fee.amount`: `string` → `int64` (M6, aithusaqr/oets#13)
- `Fee.fee_type`: `string` → `FeeType` enum (H2, aithusaqr/oets#6)
- `Fee` wired into `FillEvent` as `repeated Fee fees = 12` and into `CashFlowEvent` as `Fee fee = 9`; replaces old `FillEvent.fee`/`fee_asset`/`notional_fee` and `CashFlowEvent.fee_amount`/`fee_asset_id`; `FillEvent.notional_fee` renamed to `total_notional_fee` (R3-1, zachisit/oets#43). Reserved: `FillEvent` field 13 + names `fee`/`fee_asset`/`notional_fee`; `CashFlowEvent` field 10 + names `fee_amount`/`fee_asset_id`.
- `OrderSide`, `OrderTimeInForce`, `OrderIntentionType`: zero-value sentinel `UNKNOWN_*=0` inserted, existing values shifted +1 (M3, aithusaqr/oets#10)
- `FillEvent` fields 15 (`source`) and 19 (`timestamps`) removed + reserved (L6/M2, aithusaqr/oets#19, #9)
- `OrderEvent` fields 13 (`source`) and 14 (`timestamps`) removed + reserved (R2-1, zachisit/oets#20)
- `InstrumentRef` fields 6, 8, 11, 12, 16 removed + reserved (L5, aithusaqr/oets#18)
- `CashFlowEvent` / `SettlementEvent` / `FundingRate` / `FundingPayment`: `OetsEventEnvelope envelope = 1` replaces top-level `event_id`; top-level `source`/`timestamps`/`related_events` removed (R2-2, zachisit/oets#21)
- `CashFlowEvent.timestamp` → `timestamps` plural (R2-4, zachisit/oets#23)

### Changed (source-breaking, wire-compat)
- `EVENT_TYPE_CASH_FLOW_EVENT` renamed to `EVENT_TYPE_CASH_FLOW` (R2-3, zachisit/oets#22) — wire number 6 unchanged
- `EVENT_TYPE_FUNDING` renamed to `EVENT_TYPE_FUNDING_RATE` (R3-4, zachisit/oets#46) — wire number 7 unchanged; the second envelope-bearing message in `funding_event.proto` needed its own EventType (added as `EVENT_TYPE_FUNDING_PAYMENT = 8`)
- `Makefile generate_python_protos` now invokes `python -m grpc_tools.protoc` to match the gencode 5.x runtime (R2-5, zachisit/oets#24)
- `protobuf>=5.29,<6` pinned (R3-2, zachisit/oets#44) — matches the gencode 5.29.0 in committed `_pb2.py` files
- `requires-python = ">=3.11"` (R3-5, zachisit/oets#47) — matches the `tomllib` usage in tests

### Removed
- `InstrumentRef.days_to_expiry`, `price_precision_rounding`, `size_precision_rounding`, `lot_size`, `notional_lot_size` (L5)

### Fixed
- `EventType` gap at value 4 closed (M1, aithusaqr/oets#8)
- Makefile `.PHONY` declaration added (L1, aithusaqr/oets#14)
- `validation/` exposed in `pyproject.toml` setuptools config (R2-6, zachisit/oets#26)
- `.gitignore` excludes `build/`, `*.egg-info/`, `dist/` (R3-3, zachisit/oets#45)
- Test infrastructure scaffolded (zachisit/oets#4)

[Unreleased]: https://github.com/aithusaqr/oets/pull/25
