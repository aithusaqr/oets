# OETS int64 Scaling Convention

OETS uses `int64` for monetary, price, quantity, fee, and notional fields rather than `string`, `double`, or `decimal`. This document defines how those integers map back to real numeric values.

## Why int64 instead of string or double

- **Wire compactness:** integers serialize to fewer bytes than decimal strings.
- **Deterministic arithmetic:** integer sums never lose precision; decimal-as-string requires every consumer to parse and re-serialize through a high-precision type.
- **No floating-point error:** `double` cannot exactly represent values like `0.1`. For settlement, P&L, and fee aggregation, that error compounds.

The trade-off: every consumer must know the scale exponent before interpreting the integer.

## The convention

| Field family | Scale exponent | Where the exponent comes from |
|---|---|---|
| Price fields | `10^price_precision` | `InstrumentRef.price_precision` |
| Quantity / size fields | `10^size_precision` | `InstrumentRef.size_precision` |
| Notional, amount, fee, PnL | `10^price_precision` (default) | `InstrumentRef.price_precision`, or per-asset convention |

For amounts NOT tied to a specific instrument (e.g. a generic USDC deposit), use a fixed 8-decimal convention: `int64 = decimal × 10^8`.

For funding rates: a separate 9-decimal-place convention applies (`1_000_000_000 = 1.0`, giving sub-basis-point precision while keeping arithmetic in integer land).

## Worked example

A FillEvent for BTCUSDT-PERP at price 67_823.45, quantity 0.001, instrument has `price_precision = 2` and `size_precision = 3`:

| Field | Decimal value | int64 wire value |
|---|---|---|
| `price` | 67823.45 | `6782345` (decimal × 10^2) |
| `quantity` | 0.001 | `1` (decimal × 10^3) |
| `notional_value` | 67.82345 | `6782` (price × quantity ÷ 10^size_precision, rounded; or `67823 × 1 ÷ 10^3` using price-precision base) |
| `fee` | 0.0136 USDT | `1360000` (8-decimal asset convention) |

The exact rounding rule for derived fields like `notional_value` is the publisher's choice; consumers should not assume any specific rule beyond "the integer is scaled by the documented exponent."

## Consumer responsibility

Consumers reading OETS events MUST:
1. Resolve the `InstrumentRef` to obtain `price_precision` and `size_precision`.
2. Decode `int64` fields by dividing by `10^precision`.
3. Use a decimal type (Python `Decimal`, Java `BigDecimal`, etc.) — not `float` — for any downstream arithmetic.

## See also

- `common/instrument.proto` — `InstrumentRef.price_precision`, `InstrumentRef.size_precision`
- `common/reconciliation/fee_event.proto` — `Fee.amount` (int64, see this doc)
