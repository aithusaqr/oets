# Changelog

All notable changes to OETS protos are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and OETS adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The current version is communicated by `OetsEventEnvelope.oets_version` (see `validation/oets_version.py`). Wire-incompatible changes warrant a MAJOR bump; new optional fields warrant MINOR; editorial / non-breaking warrant PATCH.

## [Unreleased]

### Added
- Apache 2.0 `LICENSE`
- `CONTRIBUTING.md` describing the fork → PR workflow
- `CHANGELOG.md` (this file)
- `docs/SCALING.md` documenting the int64 monetary-field scaling convention
- `docs/ARCHITECTURE.md` documenting the envelope-bearing vs snapshot/delta message-type split
- `validation/oets_version.py` — SemVer 2.0.0 validator for `OetsEventEnvelope.oets_version`
- GitHub Actions workflow (`.github/workflows/ci.yml`) with Python 3.11 / 3.12 / 3.13 matrix, `buf lint`, `buf breaking`, and `pytest`
- `buf.yaml`, `buf.gen.yaml` for buf-based generation and lint
- `pyproject.toml` `[project]` table with `requires-python = ">=3.11"`
- `requirements.txt`, `requirements-test.txt` pinning the runtime + dev dependencies
- Pytest infrastructure (`tests/conftest.py`, hygiene/structure/CI test files)
- `SettlementType` enum and full `SettlementEvent` message (previously an empty stub): carries `OetsEventEnvelope`, settlement type/amount/asset, mark price, and related-ID fields
- `EventType.EVENT_TYPE_SETTLEMENT = 4` — fills the former gap in the contiguous value sequence
- `ORDER_SIDE_UNSPECIFIED = 0`, `ORDER_TIF_UNSPECIFIED = 0`, `ORDER_INTENTION_TYPE_UNSPECIFIED = 0` proto3 sentinel values
- `CashFlowEvent.fee` (`Fee fee = 9`) — structured fee sub-component replacing the former `fee_amount` scalar

### Changed
- `docs/ARCHITECTURE.md`: removed provisional callout; added concrete v0.1 event/snapshot/sub-component inventory tables with embedded-by relationships
- `Fee.amount`: `string` → `int64` (scaled integer per `docs/SCALING.md`)
- `Fee.fee_type`: `string` → `FeeType` enum (enum existed; zero-value `FEE_TYPE_UNKNOWN` renamed to `FEE_TYPE_UNSPECIFIED`)
- `EventType.EVENT_TYPE_CASH_FLOW_EVENT` renamed to `EVENT_TYPE_CASH_FLOW`
- `Makefile`: `generate_python_protos` now uses `python -m grpc_tools.protoc` (no bare `protoc` dependency)
- `requirements.txt`, `requirements-test.txt`, `pyproject.toml`: protobuf pin tightened to `>=5.29,<6`

### Fixed
- `.gitignore` now excludes `build/`, `*.egg-info/`, `dist/` so editable installs don't pollute the worktree
- Makefile: added `.PHONY` declarations, removed dead `PYTHONPATH=` inline from the `generate_python_protos` recipe

### Breaking changes (wire-incompatible)
- **Enum sentinel renames**: all `UNKNOWN_*_TYPE = 0` values renamed to `*_TYPE_UNSPECIFIED = 0` across `AccountType`, `VenueType`, `InstrumentType`, `ContractType`, `RelationshipType`, `SourceType`, `EventType`, `OrderType`, `OrderState`, `FeeType`
- **`OrderSide`**: `BUY` shifted from field value 0 to 1; `SELL` from 1 to 2
- **`OrderTimeInForce`**: all values shifted +1 (`GOOD_TIL_CANCEL` was 0, now 1)
- **`OrderIntentionType`**: all values shifted +1 (`RESTING` was 0, now 1)
- **`FillEvent`**: `int64 fee = 12` replaced by `Fee fee = 12` (different wire type); fields `fee_asset` (13), `notional_fee` (14), `source` (15), `timestamps` (19) removed and reserved
- **`OrderEvent`**: fields `source` (13) and `timestamps` (14) removed and reserved
- **`CashFlowEvent`**: `string event_id = 1` replaced by `OetsEventEnvelope envelope = 1`; `int64 fee_amount = 9` replaced by `Fee fee = 9`; `timestamp`, `source`, `related_events`, `metadata` fields reserved; `event_id` and `fee_amount` names reserved

[Unreleased]: https://github.com/aithusaqr/oets/compare/main...HEAD
