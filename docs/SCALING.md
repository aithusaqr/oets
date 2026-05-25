# OETS int64 Scaling Convention

## Why int64

All monetary and rate fields in OETS are stored as `int64` integers rather than
`float` or `double`. Floating-point representations accumulate rounding errors that
make exact comparison and reconciliation unreliable. Integers are wire-compact,
trivially serialisable, and allow exact arithmetic in any language. The scale factor
is declared separately on the related `InstrumentRef` (or is a fixed constant) so
the full precision is always recoverable.

## Per-field categories

| Field category | Scaling source | Notes |
|---|---|---|
| `price` fields | `10^price_precision` from `InstrumentRef` | e.g. `price_precision=8` → divide int64 by `10^8` |
| `quantity` / `size` fields | `10^size_precision` from `InstrumentRef` | also called `quantity_precision` on some instruments |
| `notional_value` / `notional_delta` | `10^price_precision` from `InstrumentRef` | denominated in quote asset |
| `fee` / `fee_amount` fields | `10^price_precision` of related instrument | or 8 decimals for non-instrument fees |
| `amount` in `FundingPayment` | `10^price_precision` of related instrument / asset | asset-native scale |
| `realized_pnl` / `open_pnl` / `closed_pnl` / `total_pnl` | `10^price_precision` from `InstrumentRef` | signed; positive = gain |
| `funding_rate` / `rate_applied` in `FundingRate` | fixed-point 9 decimal places | `1_000_000_000` = 1.0 (per H1 / #5) |
| balance / cash-flow amounts (no instrument) | 8 decimals by default | see `BalanceSnapshot`, `CashFlowEvent` |

## Worked examples

**Example 1 — BTC-PERP fill price**

`InstrumentRef.price_precision = 2` (USDC-quoted perp, tick = $0.01)
`FillEvent.price = 6_750_000`
Real price = `6_750_000 / 10^2` = **$67,500.00**

**Example 2 — SOL quantity**

`InstrumentRef.size_precision = 4` (SOL lot size = 0.0001)
`FillEvent.quantity = 12_500`
Real quantity = `12_500 / 10^4` = **1.2500 SOL**

**Example 3 — USDC funding payment**

`InstrumentRef.price_precision = 6` (USDC asset, 6 dp)
`FundingPayment.amount = -150_000`
Real amount = `-150_000 / 10^6` = **-0.150000 USDC** (account paid $0.15)

## Computing the real value in Python

```python
from decimal import Decimal

def real_price(int64_value: int, instrument_ref) -> Decimal:
    return Decimal(int64_value) / Decimal(10 ** instrument_ref.price_precision)

def real_quantity(int64_value: int, instrument_ref) -> Decimal:
    return Decimal(int64_value) / Decimal(10 ** instrument_ref.size_precision)

def real_amount(int64_value: int, precision: int) -> Decimal:
    """For notional, fee, pnl, or balance amounts."""
    return Decimal(int64_value) / Decimal(10 ** precision)
```

## Special cases

**Funding rate fields** (`FundingRate.rate`, `FundingPayment.rate_applied`): these
use a fixed 9-decimal-place convention set by H1 (#5). `1_000_000_000` represents
`1.0` (100%). A typical 8-hour perpetual rate of ~0.01% is stored as `100_000`.
This is more specific than the general per-`price_precision` rule and takes
precedence for rate fields only.

**Non-instrument fees and balance/cash-flow amounts** (e.g. `FeeType.FEE_TYPE_NETWORK`,
`CashFlowEvent.amount`, `BalanceSnapshot` balance fields): when there is no related
`InstrumentRef` to provide a `price_precision`, the default scale is **8 decimal
places** (`10^8`). Individual message comments note any deviation from this default.
