# OETS Protos

## Open Execution Telemetry Standard

Machine-readable execution records for fragmented markets.

OETS protos define the core event structures for describing what happened during execution: orders, fills, balances, fees, funding, settlement, source observations, timestamps, and reported state differences.

The goal is not to create another trading system.

The goal is to make execution explainable.

---

## Why These Protos Exist

Modern execution does not happen in one clean place.

An order may start in a wallet, bot, OMS, router, or frontend. It may pass through a protocol, venue, bridge, market maker, indexer, RPC provider, broker, or reporting layer. Each system may record the same event differently.

That is where the rot begins.

One system says the order was filled.

Another system says the balance never changed.

A dashboard says the position is flat.

The ledger says otherwise.

The risk engine is quietly sweating in the corner.

OETS exists so these records can be described using a shared event language.

Not a single source of truth.

A shared structure for comparing partial truths.

---

## What OETS Captures

OETS protos are designed to preserve execution context, not just execution outputs.

They describe:

- what happened
- when it happened
- when it was observed
- who or what observed it
- what other events it relates to
- what assumptions were used to interpret it
- where reported state diverges from reconstructed state

A fill is not just price and quantity.

A fill may imply:

- an order state transition
- a fee
- a balance change
- a position update
- realized PnL
- settlement
- downstream reconciliation
- a future argument with your own logs

OETS keeps the chain visible.

---

## Initial Proto Scope

The first proto set focuses on the execution core:

```text
v0.1.0
common/event_envelope.proto
common/execution_venue.proto
common/instrument.proto
common/relationships.proto
common/source.proto
common/timestamps.proto

common/execution/order_event.proto
common/execution/fill_event.proto

v0.1.1
common/reconciliation/balance_event.proto
common/reconciliation/position_event.proto
common/reconciliation/cash_flow_event.proto
common/reconciliation/fee_event.proto
common/reconciliation/funding_event.proto
common/reconciliation/settlement_event.proto
```

> **Note:** The top-level layout (no `oets/` prefix; `execution` and `reconciliation` as subfolders of `common`) reflects the current structure. The originally proposed path prefix scheme is tracked in open issue [zachisit/oets#7](https://github.com/zachisit/oets/issues/7).

---

## v0.1 Code Review Breaking Changes

The following wire-incompatible changes were introduced during the v0.1 code-review epic ([aithusaqr/oets#25](https://github.com/aithusaqr/oets/pull/25)). Consumers pinned to pre-review proto definitions must update their generated code and any serialized data.

| Change | Details | Issue |
|--------|---------|-------|
| `EventTimestamp` fields: `string` → `google.protobuf.Timestamp` | All timestamp fields migrated from ISO-8601 strings to well-known Timestamp type. Wire-incompatible. | M4 / [aithusaqr/oets#11](https://github.com/aithusaqr/oets/issues/11) |
| `Fee.amount`: `string` → `int64` | Monetary amount uses int64 scaled integer (see `docs/SCALING.md`). Wire-incompatible. | M6 / [aithusaqr/oets#13](https://github.com/aithusaqr/oets/issues/13) |
| `Fee.fee_type`: `string` → `FeeType` enum | Fee classification moved to a typed enum. Wire-incompatible. | H2 / [aithusaqr/oets#6](https://github.com/aithusaqr/oets/issues/6) |
| `OrderSide` enum values shifted | `BUY` 0→1, `SELL` 1→2; `UNKNOWN_ORDER_SIDE=0` added as sentinel. Same sentinel pattern applied to `OrderTimeInForce` and `OrderIntentionType`. Wire-incompatible. | M3 / [aithusaqr/oets#10](https://github.com/aithusaqr/oets/issues/10) |
| `FillEvent` fields 15 (`source`) and 19 (`timestamps`) removed + reserved | Source and timestamps deduplication; now carried by envelope. Wire-incompatible. | L6 / [aithusaqr/oets#19](https://github.com/aithusaqr/oets/issues/19), M2 / [aithusaqr/oets#9](https://github.com/aithusaqr/oets/issues/9) |
| `OrderEvent` fields 13 (`source`) and 14 (`timestamps`) removed + reserved | Same deduplication as FillEvent. Wire-incompatible. | R2-1 / [zachisit/oets#20](https://github.com/zachisit/oets/issues/20) |
| `InstrumentRef` fields 6, 8, 11, 12, 16 removed + reserved | Removed `days_to_expiry`, `lot_size`, and related fields. Wire-incompatible. | L5 / [aithusaqr/oets#18](https://github.com/aithusaqr/oets/issues/18) |
| `OetsEventEnvelope envelope = 1` replaces top-level `event_id` | `CashFlowEvent`, `SettlementEvent`, `FundingRate`, `FundingPayment` now carry an `OetsEventEnvelope` at field 1. Top-level `source` and `timestamps` removed; carried by envelope. Wire-incompatible. | R2-2 / [zachisit/oets#21](https://github.com/zachisit/oets/issues/21) |
| `EVENT_TYPE_CASH_FLOW_EVENT` renamed to `EVENT_TYPE_CASH_FLOW` | Wire-number unchanged (source-breaking rename). | R2-3 / [zachisit/oets#22](https://github.com/zachisit/oets/issues/22) |
| `EventType` added `EVENT_TYPE_SETTLEMENT = 4` and `EVENT_TYPE_FUNDING = 7` | New enum values for settlement and funding event routing. | M1, R2-3 / [zachisit/oets#22](https://github.com/zachisit/oets/issues/22) |
| `CashFlowEvent.timestamp` → `timestamps` plural | Field renamed for consistency (wire-number unchanged; source-breaking by name). | R2-4 / [zachisit/oets#23](https://github.com/zachisit/oets/issues/23) |

---

## Getting Started

```bash
# Install runtime + dev deps
pip install -r requirements.txt -r requirements-test.txt

# Run tests
pytest tests/

# Regenerate Python bindings (uses grpc_tools.protoc for gencode 5.x compat)
make generate_python_protos

# Or via buf (if installed)
buf generate
buf lint
```

> **Note:** Bare `protoc` 35+ produces gencode 7.x, which is incompatible with the pinned runtime. Use the Makefile target (`make generate_python_protos`) or `python -m grpc_tools.protoc` directly.

---

## Project Layout

```
common/                     # .proto source files
  ├─ event_envelope.proto
  ├─ instrument.proto
  ├─ ...
  ├─ execution/
  │   ├─ fill_event.proto
  │   └─ order_event.proto
  └─ reconciliation/
      ├─ balance_event.proto
      ├─ cash_flow_event.proto
      ├─ fee_event.proto
      ├─ funding_event.proto
      ├─ position_event.proto
      └─ settlement_event.proto
generated/python/           # compiled _pb2.py bindings
validation/                 # Python validators (oets_version.py)
tests/                      # pytest suite
docs/                       # SCALING.md, ARCHITECTURE.md
```

---

## License

OETS protos are released under the Apache License 2.0 — see [LICENSE](LICENSE).

The Apache 2.0 license permits use, modification, and distribution with attribution. Patent grants are included, and changes must be marked. Full terms in the LICENSE file.

---

## See Also

- [CHANGELOG.md](CHANGELOG.md) — version history and breaking changes
- `docs/SCALING.md` — int64 monetary scaling convention
- `docs/ARCHITECTURE.md` — envelope-bearing vs snapshot/delta messages
- `validation/oets_version.py` — SemVer 2.0.0 validator for `OetsEventEnvelope.oets_version`
- `buf.yaml` — lint config with documented `except` rules
- `Makefile` — proto regeneration targets
- [Epic PR aithusaqr/oets#25](https://github.com/aithusaqr/oets/pull/25) — the full v0.1 review
- Open follow-ups:
  - [zachisit/oets#7](https://github.com/zachisit/oets/issues/7) — layout restructure (path prefix)
  - [zachisit/oets#38](https://github.com/zachisit/oets/issues/38) — POSITION/BALANCE event coverage
  - [zachisit/oets#40](https://github.com/zachisit/oets/issues/40) — Phase 2 STANDARD compliance
