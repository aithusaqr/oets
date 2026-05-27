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

The first proto set focuses on the execution core. Files live under `common/` rather than an `oets/v1/` prefix for now; relocating to the buf-canonical layout is a separate follow-up.

```text
common/account.proto
common/event_envelope.proto
common/execution_venue.proto
common/instrument.proto
common/relationships.proto
common/source.proto
common/timestamps.proto

common/execution/fill_event.proto
common/execution/order_event.proto

common/reconciliation/balance_event.proto
common/reconciliation/cash_flow_event.proto
common/reconciliation/fee_event.proto
common/reconciliation/position_event.proto
common/reconciliation/settlement_event.proto
```

---

## Getting Started

```bash
# Install runtime + dev deps (use a venv)
pip install -r requirements.txt -r requirements-test.txt

# Run tests
pytest tests/

# Regenerate Python bindings if you touched a .proto
make generate_python_protos

# buf (if installed)
buf generate
buf lint
```

---

## Project Layout

```
common/                     # .proto source files
  ├─ account.proto
  ├─ event_envelope.proto
  ├─ execution_venue.proto
  ├─ instrument.proto
  ├─ relationships.proto
  ├─ source.proto
  ├─ timestamps.proto
  ├─ execution/
  │   ├─ fill_event.proto
  │   └─ order_event.proto
  └─ reconciliation/
      ├─ balance_event.proto
      ├─ cash_flow_event.proto
      ├─ fee_event.proto
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

- [CONTRIBUTING.md](CONTRIBUTING.md) — how to file issues and propose changes
- [CHANGELOG.md](CHANGELOG.md) — version history and breaking changes
- [docs/SCALING.md](docs/SCALING.md) — int64 monetary scaling convention
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — envelope-bearing vs snapshot/delta message-type design
- [validation/oets_version.py](validation/oets_version.py) — SemVer 2.0.0 validator for `OetsEventEnvelope.oets_version`
- [buf.yaml](buf.yaml) — lint config with documented `except` rules
- [Makefile](Makefile) — proto regeneration targets
