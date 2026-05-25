# About

## Markets Are Still Poorly Understood Systems

Markets are ancient, but the formal academic study of modern financial markets is still relatively young. Many core ideas in finance, market microstructure, portfolio theory, derivatives pricing, and behavioral finance were developed only in the last century, and many of them continue to evolve as markets change.

This matters because markets are not static systems. They are adaptive, reflexive, technological, and increasingly automated. The structure of markets changes as participants, venues, protocols, regulations, instruments, and execution systems change. A model that explains one market structure may fail when the underlying plumbing changes.

This is especially visible in modern execution environments. Trading no longer happens in a single place with a single record of truth. It happens across exchanges, brokers, liquidity providers, internal books, bridges, custodians, smart contracts, oracles, indexers, and risk systems. Each system may observe only part of the event sequence.

As a result, the problem is not only prediction. It is observation.

Before a system can explain a market event, it must be able to reconstruct what happened. Which order was sent? Which fill occurred? Which balance changed? Which position moved? Which price was used? Which fee or funding event was applied? Which timestamp should be trusted?

OETS starts from a modest premise: if markets are still not fully understood, then execution facts should be represented in a way that makes disagreement visible rather than hidden. The goal is not to claim certainty over complex markets. The goal is to make uncertainty inspectable.

History has shown that failures in markets are often hard to understand after the fact. Knight Capital’s 2012 trading incident showed how quickly software and execution-system failures can become financially material. The 2010 Flash Crash showed how difficult it can be to reconstruct market behavior across fragmented venues, participants, and time horizons.

OETS is not a claim that markets can be made perfectly predictable or even that execution can be assumed to be deterministic. It is a narrower claim: execution facts should be represented in a way that makes disagreement inspectable. Orders, fills, balances, positions, fees, funding, and timestamps should be structured enough that systems can replay what happened instead of relying on partial narratives after the fact.

## Core Motivation

Past market failures point to a simple lesson: when systems break, the problem is rarely “no data.” It is usually partial data, inconsistent data, delayed data, or data interpreted through hidden assumptions.

This is true in traditional trading infrastructure and in DeFi. In DeFi, the data may be public on-chain, but public does not automatically mean understandable. Liquidations, oracle updates, collateral movements, debt changes, fees, MEV, and protocol-specific accounting rules still need to be reconstructed into a coherent sequence.

OETS exists to make execution facts replayable before they become forensic archaeology.


## Historical Context

### Knight Capital, 2012

Knight Capital is a useful reminder that execution failures are not abstract. When trading systems behave unexpectedly, teams need to reconstruct what happened quickly, across code paths, orders, fills, positions, and risk state.

### The Flash Crash, 2010

The 2010 Flash Crash showed how difficult it can be to interpret market events after the fact when activity is fragmented across venues, participants, order types, and time horizons.

### DeFi Liquidations and Liquidation Cascades

DeFi lending protocols make execution-state reconstruction especially important because liquidations are automated, composable, and time-sensitive. A liquidation is not just a single event. It can involve collateral valuation, oracle updates, health-factor calculations, debt repayment, collateral seizure, liquidation bonuses, gas dynamics, MEV competition, and downstream effects on liquidity.

This makes DeFi a natural use case for OETS. When a liquidation occurs, the important question is not only “was the position liquidated?” but:

- What collateral and debt state existed before liquidation?
- Which price or oracle update made the position liquidatable?
- Which transaction executed the liquidation?
- What collateral was seized?
- What debt was repaid?
- What bonus or penalty was applied?
- Did the liquidation create bad debt, price impact, or follow-on liquidations?
- Which timestamp should be used for replay: block time, observed time, oracle update time, or canonical replay time?

Historical DeFi stress events show that liquidations are often difficult to interpret after the fact. During market stress, falling collateral prices can trigger liquidations, liquidations can create further sell pressure, and that sell pressure can make more positions liquidatable. This feedback loop is commonly described as a liquidation cascade.

MakerDAO’s March 2020 “Black Thursday” is a useful example. The event exposed how fast market moves, network congestion, auction mechanics, and liquidator behavior can interact in ways that leave protocols and users with outcomes that are difficult to reconstruct cleanly from a single system’s view.

Aave-style lending liquidations are another useful example. A liquidation may be fully visible on-chain, but visibility is not the same as interpretation. The raw transaction can show that collateral was seized and debt was repaid, but a useful reconstruction needs the surrounding state: collateral prices, oracle timing, health factor before and after liquidation, liquidation threshold, close factor, bonus, gas conditions, and any related market moves.

For OETS, DeFi liquidations strengthen the core argument: even when execution data is public, it still needs structure. The goal is not merely to record that an event happened. The goal is to make the event replayable, attributable, and comparable across systems.

On-chain transparency does not remove the need for execution telemetry. It raises the standard for it.
