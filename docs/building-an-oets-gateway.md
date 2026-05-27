# Building an OETS Gateway Adapter

> Status: provisional v0.1 guide. This document describes how a trading gateway, broker adapter, protocol indexer, or internal system can emit OETS messages. It is instructional, not a mandatory implementation framework.

An OETS gateway adapter is the translation layer between a venue, broker, protocol, or internal trading system and a structured execution event stream.

It is not required to be a trading engine.

Its job is to:

- observe execution activity
- normalize venue or broker payloads
- preserve source context
- preserve timestamp semantics
- emit typed OETS messages
- expose enough state for replay, reconciliation, debugging, and audit workflows

## Adapter Responsibility

A gateway adapter SHOULD preserve the distinction between:

1. **Execution events**: discrete things that happened, such as an order submission, fill, cancel, fee, funding payment, or cash flow.
2. **State observations**: reported state observed from a source, such as open orders, balances, positions, or margin state.
3. **Operational telemetry**: gateway/process state, such as REST availability, WebSocket connectivity, readiness to send orders, and async task failures.

This distinction mirrors the OETS message taxonomy:

| OETS category | Question answered | Examples |
|---|---|---|
| Event messages | What happened? | `OrderEvent`, `FillEvent`, `CashFlowEvent` |
| Snapshot / delta messages | What state was observed? | `PositionSnapshot`, `BalanceSnapshot`, `PositionDelta`, `BalanceDelta` |
| Operational telemetry | What did the adapter observe about itself? | `GatewayEvent`, `TaskEvent`, `TelemetryEvent` |
| Sub-components | What shared context is embedded? | `AccountRef`, `InstrumentRef`, `ExecutionVenue`, `EventTimestamp`, `SourceReference`, `EventRelationship`, `Fee` |

## Event vs Snapshot

A fill is an event.

A reported position is usually a state observation.

For example:

- `FillEvent` means an execution occurred.
- `PositionSnapshot` means a source reported position state at a point in time.
- A gateway may emit a position observation after a REST poll or WebSocket update, but the underlying position state is not itself the same kind of occurrence as a fill.

If a snapshot is emitted independently into an event stream, the surrounding event or observation wrapper should describe the observation of state, not imply that the market itself produced a new execution event.

## Typical Gateway Operations

A gateway adapter MAY support some or all of the following operations:

| Gateway operation | Typical source interaction | Typical OETS output |
|---|---|---|
| `create_order` | REST order submission | `OrderEvent` |
| `cancel_order` | REST cancel request | `OrderEvent` |
| `cancel_orders` | REST batch cancel | repeated `OrderEvent` |
| `cancel_all` | REST cancel-all request | repeated `OrderEvent` or `GatewayEvent` |
| `get_open_orders` | REST open-order snapshot | repeated `OrderEvent` or `OrderSnapshot` |
| `get_order_history` | REST order history | repeated `OrderEvent` |
| `get_fills` | REST trade/fill history | repeated `FillEvent` |
| `get_balances` | REST balance snapshot | repeated `BalanceSnapshot` or `BalanceEvent` |
| `get_positions` | REST position snapshot | repeated `PositionSnapshot` or `PositionEvent` |
| `stream_orders` | WebSocket order updates | stream of `OrderEvent` |
| `stream_fills` | WebSocket execution updates | stream of `FillEvent` |
| `stream_balances` | WebSocket balance updates | stream of `BalanceSnapshot` / `BalanceDelta` |
| `stream_positions` | WebSocket position updates | stream of `PositionSnapshot` / `PositionDelta` |
| `stream_gateway_status` | local gateway state | stream of `GatewayEvent` |
| async task tracking | local runtime observation | `TaskEvent` |

## Minimum Adapter Contract

A minimal OETS gateway SHOULD preserve:

- `gateway_id`
- account identifier
- venue / exchange / protocol
- instrument identifier, when applicable
- source system
- source payload identifier, when available
- event timestamp, when provided by the source
- observed timestamp, when the adapter saw the event
- ingestion timestamp, when the event entered the local pipeline
- normalized OETS message
- relationship to upstream or downstream events, when known

## Example: create_order

A `create_order` implementation usually has two observable moments:

1. the local system sends an order intention
2. the venue/broker/protocol acknowledges, rejects, or returns an order state

A gateway may emit:

- an `OrderEvent` when the order intention is sent
- another `OrderEvent` when the venue response is observed
- a `GatewayEvent` if the gateway is not ready to send orders
- a `TaskEvent` if the async operation fails unexpectedly

The important point is not that every adapter uses the same internal implementation. The important point is that the resulting OETS messages preserve enough context to reconstruct the order lifecycle.

## Example: get_positions

A `get_positions` call usually observes reported state.

It SHOULD NOT be treated as proof that a new execution occurred.

A gateway may emit:

- `PositionSnapshot` for each reported position
- `PositionDelta` if the adapter computes a change from a previous observation
- relationships to recent `FillEvent`, `CashFlowEvent`, `FundingPaymentEvent`, or `BalanceSnapshot` messages when known

This allows downstream systems to compare reported state against reconstructed state without conflating state observation with execution.

## Example: stream_fills

A fill stream emits execution facts.

A gateway SHOULD map each source execution update into a `FillEvent` and preserve:

- source trade ID / execution ID
- order ID / client order ID
- account
- instrument
- side
- price
- quantity
- fee, when present
- source timestamp
- observed timestamp
- relationship to the parent order, when known

## Operational Telemetry

Gateway health matters because missing, delayed, duplicated, or reordered events often come from infrastructure behavior.

Adapters SHOULD emit operational telemetry for:

- REST process up/down
- WebSocket connected/disconnected/reconnected

This telemetry helps downstream systems understand whether a reconciliation gap came from market activity, source behavior, or adapter/runtime behavior.

## Adapter Design Principle

An OETS gateway adapter should make integration boring:

1. observe the source
2. preserve the timestamps
3. preserve the source context
4. normalize into OETS messages
5. emit the messages
6. let downstream systems validate, replay, reconcile, and explain the chain