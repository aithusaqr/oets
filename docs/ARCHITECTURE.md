# OETS Proto Architecture

This document captures the design principles behind the OETS message-type taxonomy and the concrete v0.1 inventory of messages in each category.

## Three kinds of messages

OETS splits its `.proto` definitions into three categories:

1. **Event messages.** Discrete occurrences in the execution lifecycle — an order placed, a fill executed, a cash flow recorded. Each event has a stable identity, a routing surface (which observer recorded it, when, related to which other events), and maps to a value in the `EventType` enum.

2. **Snapshot / delta messages.** State representations — "what is the position right now" or "what changed between two timestamps." These are *not* occurrences; they don't map to an `EventType` value because the same state can be re-observed any number of times.

3. **Sub-components.** Message types that exist only as embedded fields within other messages. They have no independent lifecycle and inherit routing context from their parent.

### v0.1 event message inventory

| Message | File | `EventType` value |
|---|---|---|
| `FillEvent` | `common/execution/fill_event.proto` | `EVENT_TYPE_FILL` |
| `OrderEvent` | `common/execution/order_event.proto` | `EVENT_TYPE_ORDER` |
| `CashFlowEvent` | `common/reconciliation/cash_flow_event.proto` | `EVENT_TYPE_CASH_FLOW` |
| `SettlementEvent` | `common/reconciliation/settlement_event.proto` | `EVENT_TYPE_SETTLEMENT` |

### v0.1 snapshot / delta message inventory

| Message | File |
|---|---|
| `BalanceSnapshot` | `common/reconciliation/balance_event.proto` |
| `BalanceDelta` | `common/reconciliation/balance_event.proto` |
| `PositionSnapshot` | `common/reconciliation/position_event.proto` |
| `PositionDelta` | `common/reconciliation/position_event.proto` |

### v0.1 sub-component inventory

| Message | File | Embedded by |
|---|---|---|
| `OetsEventEnvelope` | `common/event_envelope.proto` | `FillEvent`, `OrderEvent`, `CashFlowEvent`, `SettlementEvent` |
| `AccountRef` | `common/account.proto` | `FillEvent`, `OrderEvent` |
| `InstrumentRef` | `common/instrument.proto` | `FillEvent`, `OrderEvent` |
| `ExecutionVenue` | `common/execution_venue.proto` | `FillEvent`, `OrderEvent` |
| `Fee` | `common/reconciliation/fee_event.proto` | `FillEvent`, `CashFlowEvent` |
| `EventTimestamp` | `common/timestamps.proto` | `OetsEventEnvelope`, `BalanceSnapshot`, `BalanceDelta`, `PositionSnapshot`, `PositionDelta` |
| `SourceReference` | `common/source.proto` | `OetsEventEnvelope`, `BalanceSnapshot`, `BalanceDelta`, `PositionSnapshot`, `PositionDelta` |
| `EventRelationship` | `common/relationships.proto` | `OetsEventEnvelope`, `BalanceSnapshot`, `BalanceDelta`, `PositionSnapshot`, `PositionDelta` |

## The envelope rule

Event messages MUST carry an `OetsEventEnvelope envelope = 1` at field 1. The envelope owns:
- `event_id` — stable unique identifier
- `oets_version` — SemVer of the OETS schema this event was emitted against
- `event_type` — `EventType` enum value
- `source` — which observer recorded it
- `timestamps` — lifecycle timestamps
- `relationships` — links to other events
- `extensions` — opaque metadata for forward/backward compatibility

Snapshot / delta messages MUST NOT carry an envelope. They carry their own observation-time metadata (`event_id`, `timestamps`, `source`, `related_events`) using the same sub-component types as the envelope (`EventTimestamp`, `SourceReference`, `EventRelationship`) — but at the message level, not nested under an `OetsEventEnvelope`.

Sub-components MUST NOT carry an envelope. They inherit routing context from their parent.

## If you're adding a new message type

1. **Is it an event?** If it represents a discrete occurrence that belongs to an `EventType` value (see `common/event_envelope.proto`), it MUST carry `OetsEventEnvelope envelope = 1` at field 1. Add an `EventType` value if none exists.

2. **Is it a state snapshot or delta?** If it represents state at a point in time or a change between two snapshots, do NOT add an envelope. Carry your own `event_id`, `timestamps`, `source`, and `related_events` fields using the existing sub-component types.

3. **Is it a sub-component?** If it's only ever embedded inside another message, do NOT add an envelope. Sub-components inherit routing context from their parent. Before introducing a new sub-component, check whether `AccountRef`, `InstrumentRef`, `ExecutionVenue`, `EventTimestamp`, `SourceReference`, `EventRelationship`, etc. already capture what you need.

## Rich sub-component refs vs bare string IDs

Execution-path events (`FillEvent`, `OrderEvent`) embed rich sub-component messages (`AccountRef`, `InstrumentRef`, `ExecutionVenue`) because the context they need — precision settings, lot sizes, venue type — is available at execution time from the system recording the event.

Reconciliation-path events (`CashFlowEvent`, `SettlementEvent`) use bare string IDs (`venue_id`, `account_id`, `instrument_id`) because they are often recorded by reconciliation systems that receive only identifiers from downstream feeds, not the full execution context. Embedding `AccountRef` or `InstrumentRef` into a reconciliation event would require the reconciliation system to look up context it may not have.

This is not an inconsistency — it is a deliberate modelling choice that reflects the information available to each event source. Consumers that need the rich context for a reconciliation event should join on the identifier against a fill or order event that shares the same `related_*` IDs.

## Why this split exists

Events and snapshots both end up in the same stream from a consumer's vantage point, but they answer different questions:

- An event answers: *what happened?* It has a timestamp of occurrence and a chain of related events.
- A snapshot/delta answers: *what is the state right now?* It has a timestamp of observation and may be re-issued without anything "happening."

Forcing snapshots to wear an envelope would conflate observation-time with occurrence-time and would require an `EventType` value for every state-shape — which doesn't generalize (the same position state can be observed from many sources, none of which is "the position event").

## See also

- `common/event_envelope.proto` — `OetsEventEnvelope`, `EventType` enum
- `docs/SCALING.md` — int64 scaling convention used by event/snapshot/delta payloads
