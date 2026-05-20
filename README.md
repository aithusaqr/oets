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
oets/common/event_envelope.proto
oets/common/execution_venue.proto
oets/common/instrument.proto
oets/common/relationships.proto
oets/common/source.proto
oets/common/timestamps.proto

oets/execution/order_event.proto
oets/execution/fill_event.proto

v0.1.1
oets/reconciliation/balance_event.proto
oets/reconciliation/position_event.proto
oets/reconciliation/cash_flow_event.proto
oets/reconciliation/settlement_event.proto
