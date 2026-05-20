# Open Execution Telemetry Standard

## An Open Standard for Observable Execution Records Across Fragmented Markets

### Reproducible, explainable, auditable execution telemetry for decentralized and multi-venue trading systems

> “Our meal will be accompanied by wine. Now, wine is many things. It has a bouquet, colour and richness of taste that all complement the food. It has alcohol that can enliven the mind. Wine enriches all our senses. At the end of our feast, we will have grappa. Grappa is one thing: alcohol. Grappa is wine distilled.
>
> Humanity is many things: passionate, curious, rational, altruistic, creative, self-interested. But the market is one thing: self-interested. The market is humanity distilled. And then he challenged us: Your job is to turn the grappa back into wine, to turn the market back into humanity. This isn’t theology. This is reality. This is the truth.”
>
> — Mark Carney, *Values*, recounting a speech by Pope Francis

---

## 1. Project Summary

Open Execution Telemetry Standard, or **OETS**, is a free and open-source standard for observable execution records across decentralized and multi-venue trading systems.

It defines shared event models, timestamp semantics, source observation metadata, relationship fields, synthetic datasets, validation examples, and documentation for execution-related events such as orders, fills, balance changes, fees, funding, settlement events, and reported state differences.

OETS does not assume one perfect source of truth. Instead, it makes execution records easier to inspect, compare, explain, and audit across systems that may observe different facts at different times.

The goal is not to build another trading venue, analytics platform, or reconciliation product. The goal is to define a public language for describing execution completeness.

**OETS-Solana** will serve as the first ecosystem-specific reference profile.

Markets have always depended on more than price and quantity. Exchange also depends on context, provenance, trust, timing, accountability, and shared interpretation. OETS brings that missing context into machine-readable execution records.

---

## 2. Why This Matters Now

Modern markets are increasingly electronic, fragmented, and difficult to reconstruct.

Execution can pass through wallets, routers, protocols, market makers, OTC desks, RFQ systems, indexers, RPC providers, risk engines, and downstream reporting systems. Each layer may use different identifiers, timestamps, event names, and assumptions about state.

The shift from human-intermediated markets to electronic markets increased speed and access, but it also compressed transaction context. The faster and more fragmented markets become, the more important it becomes to preserve structured evidence of what happened.

In many systems, the problem is not a lack of data. The problem is too many partial records, each with hidden assumptions.

OETS treats this as a public infrastructure problem.

The public-good layer is not another trading venue. It is a shared language for explaining execution.

---

## 3. Markets Are Not Only Price Engines

Markets have never been only about price discovery.

Across many Indigenous, community-based, and pre-modern exchange systems, exchange was not only a price-and-quantity event. The relationship between parties, provenance of goods, reciprocal obligations, community norms, and accountability all shaped the meaning of a transaction.

OETS does not try to recreate those systems. It draws a narrower lesson: transaction records are more useful when they preserve context.

Modern electronic markets often reduce execution to price, quantity, venue, and timestamp. That compression is useful, but it can hide the information required for auditability, accountability, and reconstruction.

Execution telemetry should preserve enough context to explain:

- what happened
- who or what observed it
- when it was observed
- how it relates to other events
- what assumptions were used to interpret it
- where reported state differs from reconstructed state

This is the difference between a raw trade log and an execution record.

---

## 4. Fragmentation in Modern Electronic Markets

Traditional financial markets already show the consequences of fragmented execution infrastructure.

Examples include:

- venue fragmentation
- dark pools and internalization
- OTC and RFQ workflows
- broker, router, and intermediary chains
- clearing and settlement layers
- market data latency
- inconsistent views across systems

Reg NMS helped reshape U.S. equity market routing and venue competition, but it also contributed to fragmented liquidity and complex execution paths. Dark pools and OTC/RFQ markets show that trades often happen in environments where execution context is not fully visible to all downstream observers.

Crypto inherits these problems and adds new ones.

Execution can now span on-chain settlement, off-chain routing, wallet state, indexers, RPC providers, protocol-specific semantics, MEV-aware ordering, cross-venue hedging, oracle dependencies, and centralized exchange interactions.

If execution spans many systems, those systems need a shared event language.

OETS addresses execution fragmentation as an interoperability problem.

---

## 5. Fragility, Hidden Assumptions, and Model Risk

Complex markets often fail in ways that are difficult to reconstruct.

The problem is not always missing data. More often, it is partial data treated as complete. One system records the order state. Another records the fill. Another records the balance update. Another records the valuation. Another records the risk calculation. Each record may be locally correct, but incomplete.

Under normal conditions, these systems may appear consistent. Under stress, latency, volatility, partial fills, delayed settlement, stale prices, indexer lag, or missing state transitions can expose assumptions that were never made explicit.

This is where execution fragility hides: not only in what happened, but in how each system interpreted what happened.

OETS does not try to remove uncertainty from markets.

It gives uncertainty structure.

OETS standardizes observable execution facts so disagreement between systems can be inspected rather than buried. It records who observed an event, when they observed it, how the event relates to other execution records, and where reported state diverges from reconstructed state.

In complex markets, the failure mode is often not silence.

It is a room full of systems all telling slightly different truths.

OETS gives those truths a common format.

---

## 6. Crypto Inherits the Old Problems and Adds New Ones

Crypto and DeFi inherit fragmentation from traditional markets, then add:

- on-chain settlement
- off-chain routing
- RPC and indexer delays
- wallet-level state
- protocol-specific semantics
- MEV-aware ordering
- cross-venue hedging
- oracle and mark-price dependencies
- CEX/DEX interaction
- fragmented data providers
- inconsistent finality assumptions
- multiple observers with different views of the same event

Just as electronic equities created routing and venue complexity, decentralized markets create protocol and observation complexity.

The difference is that crypto still has a chance to build open standards earlier in the market structure lifecycle.

OETS is an attempt to make execution transparency part of the public infrastructure layer, not an afterthought.

---

## 7. Proposed Solution

OETS defines a shared telemetry model for observable execution facts.

Initial event categories include:

- order events
- fill events
- balance events
- fee events
- funding events
- settlement events
- source observation events
- reported state difference events
- optional risk and exposure observation events

The standard includes:

- common event envelope
- event type vocabulary
- timestamp semantics
- source observation model
- relationship model
- extension model
- synthetic example records
- validation examples
- documentation

Earlier markets relied on social and institutional context to make exchange meaningful. Modern digital markets need machine-readable context to make execution explainable.

OETS is not a trading system. It is a public language for execution records.

---

## 8. Design Principles

### 8.1 Reproducible Interpretation, Not Perfect Determinism

OETS does not assume all systems will derive the same state.

Instead, given the same event record, systems should be able to derive comparable interpretations or explain why they differ.

This responds to the model-risk problem: do not hide uncertainty. Represent assumptions clearly.

### 8.2 Regularity Without Uniformity

Protocols and venues should not have to flatten their behavior into one generic model.

OETS standardizes the observable record while allowing protocol-specific extensions.

Interoperability should not require every venue, protocol, wallet, or indexer to become identical.

### 8.3 Context Is Part of the Record

Source, timestamp, relationship, and assumption metadata are not optional decoration.

They are part of the execution record.

Without them, downstream systems may know that something happened, but not enough to explain how, when, why, or according to whom.

### 8.4 Public Standards Over Proprietary Silos

Execution transparency should not depend on a single commercial platform.

Fragmented markets become harder to audit when each participant uses private schemas, private logs, and private interpretation logic.

OETS provides a public, reusable base layer that others can implement, extend, inspect, and challenge.

---

## 9. Technical Scope

### 9.1 Event Envelope

The common event envelope will define shared fields such as:

```text
event_id
event_type
oets_version
source
timestamps
relationships
extensions