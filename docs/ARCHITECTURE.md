# OETS Proto Architecture

This document captures the design principles behind the OETS message-type taxonomy. As schema work lands, this file will be filled in with concrete embedded-by inventories; for now it describes the principles those inventories must obey.

## Three kinds of messages

OETS splits its `.proto` definitions into three categories:

1. **Event messages.** Discrete occurrences in the execution lifecycle — an order placed, a fill executed, a cash flow recorded. Each event has a stable identity, a routing surface (which observer recorded it, when, related to which other events), and maps to a value in the `EventType` enum. Examples in scope for v0.1: `FillEvent`, `OrderEvent`, `CashFlowEvent`, `SettlementEvent`.

2. **Snapshot / delta messages.** State representations — "what is the position right now" or "what changed between two timestamps." These are *not* occurrences; they don't map to an `EventType` value because the same state can be re-observed any number of times. Examples: `PositionSnapshot`, `PositionDelta`, `BalanceSnapshot`, `BalanceDelta`.

3. **Sub-components.** Message types that exist only as embedded fields within other messages. They have no independent lifecycle and inherit routing context from their parent. Examples: `AccountRef`, `InstrumentRef`, `ExecutionVenue`, `EventTimestamp`, `SourceReference`, `EventRelationship`, `Fee`.

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

## Why this split exists

Events and snapshots both end up in the same stream from a consumer's vantage point, but they answer different questions:

- An event answers: *what happened?* It has a timestamp of occurrence and a chain of related events.
- A snapshot/delta answers: *what is the state right now?* It has a timestamp of observation and may be re-issued without anything "happening."

Forcing snapshots to wear an envelope would conflate observation-time with occurrence-time and would require an `EventType` value for every state-shape — which doesn't generalize (the same position state can be observed from many sources, none of which is "the position event").

## See also

- `common/event_envelope.proto` — `OetsEventEnvelope`, `EventType` enum
- `docs/SCALING.md` — int64 scaling convention used by event/snapshot/delta payloads
