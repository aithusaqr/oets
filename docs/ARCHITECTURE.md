# OETS Proto Architecture

## Envelope-bearing vs envelope-less messages

R2-2 ([#21](https://github.com/zachisit/oets/issues/21)) established a deliberate split between messages that carry `OetsEventEnvelope` and those that do not.

| Message | Carries OetsEventEnvelope? | Kind |
|---|---|---|
| FillEvent | yes | event |
| OrderEvent | yes | event |
| CashFlowEvent | yes | event |
| SettlementEvent | yes | event |
| FundingRate | yes | event |
| FundingPayment | yes | event |
| PositionSnapshot | no | snapshot |
| PositionDelta | no | delta |
| BalanceSnapshot | no | snapshot |
| BalanceDelta | no | delta |
| Fee | no | sub-component (embedded in FillEvent.fees and CashFlowEvent.fee) |

## Why the split

Event messages represent discrete occurrences — a fill was executed, a cash flow happened, funding was paid. Each such occurrence maps to a value in the `EventType` enum and is uniquely identified by `envelope.event_id`. The envelope is the canonical identity and routing surface for these messages.

Snapshot and delta messages represent *state*, not occurrences. A `PositionSnapshot` is the position at a point in time; a `PositionDelta` is the arithmetic change between two snapshots. Neither is an "event" in the `EventType` sense — `EVENT_TYPE_POSITION` would be semantically ambiguous between the two. These messages carry their own observation-time metadata (`event_id`, `timestamps`, `source`, `related_events`) which represent *when the state was observed*, not *when an event occurred*.

Sub-components like `Fee` exist only as embedded fields within other messages. They have no independent lifecycle and therefore carry no envelope. `Fee` is embedded at `FillEvent.fees` (repeated, field 12) to capture all fees applied to a fill, and at `CashFlowEvent.fee` (singular, field 9) to capture the fee component of a cash flow. See R3-1 ([zachisit/oets#43](https://github.com/zachisit/oets/issues/43)).

## If you're adding a new message type

1. **Is it an event?** If the message represents a discrete occurrence that belongs to an `EventType` value (see `common/event_envelope.proto`), it MUST carry `OetsEventEnvelope envelope = 1` at field 1. Add an `EventType` value for it if none exists.

2. **Is it a state snapshot or delta?** If the message represents state at a point in time or a change between two snapshots, do NOT add an envelope. Carry your own `event_id`, `timestamps`, `source`, and `related_events` fields using the same types as existing snapshot/delta messages.

3. **Is it a sub-component?** If the message is only ever embedded inside another message (like `Fee` inside `FillEvent.fees` and `CashFlowEvent.fee`), do NOT add an envelope. Sub-components inherit routing context from their parent.

## References

- `EventType` enum: `common/event_envelope.proto`
- `OetsEventEnvelope` definition: `common/event_envelope.proto`
- R2-2 ticket: https://github.com/zachisit/oets/issues/21
- Scaling conventions: `docs/SCALING.md`
