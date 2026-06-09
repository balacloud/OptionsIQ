# Canadian TSX Options Expansion — Research Note
> **Day 67 (Jun 6, 2026)**
> **Status:** Non-urgent backlog idea — filed for future consideration
> **Source:** One-off discussion, external analysis

---

## The Idea

Expand OptionsIQ to support options analysis on highly liquid Canadian mega-caps (TSX-listed), using spread strategies suited to a neutral-to-bullish outlook.

---

## Strategies Identified

### Bull Call Spread (Neutral to Moderately Bullish)
- Buy ITM call + sell OTM call, same expiry
- Caps upside but significantly reduces theta decay vs naked long call
- Max risk: net premium paid. Max profit: strike spread minus premium
- Works sideways or slightly up — avoids theta bleed on pure long call
- Recommended DTE: 45 days

### Long Calendar Spread (Heavily Neutral / Range-Bound)
- Sell near-term call (~30d) + buy longer-term call (~90d) at same strike
- Profits from near-term theta decay; long leg gives future directional exposure
- Works when stock stays flat short-term but expected to move later

---

## Target Tickers (TSX — Highest Options Liquidity)

| Ticker | Name | Liquidity | Best Strategy |
|--------|------|-----------|--------------|
| RY | Royal Bank of Canada | High | 45-day Bull Call Spread |
| TD | Toronto-Dominion Bank | High | 45-day Bull Call Spread |
| MFC | Manulife Financial | Medium-High | 30-day Calendar Spread |
| ENB | Enbridge Inc. | High | 60-day Bull Call Spread |

---

## Constraints vs Current OptionsIQ Architecture

| Constraint | Detail |
|-----------|--------|
| Data provider | Tradier does NOT cover TSX. Would need IBKR (already integrated for EOD batch) or Questrade API |
| Currency | CAD vs USD — need separate account size + P&L tracking in CAD |
| Options chain | TSX monthlies only (no weeklies on most names) — DTE windows are different |
| Spread support | OptionsIQ removed spread builders Day 57 (single-leg only). Bull Call Spread + Calendar would need spread builder reinstated or a Canadian-specific mode |
| Gate logic | ETF holdings earnings gate doesn't apply — single-stock gates needed (direct earnings gate) |
| Liquidity | TSX options have wider bid-ask spreads than equivalent US ETFs — 20% block threshold may need loosening for Canadian names |

---

## If This Gets Built

Minimum viable path:
1. Add IBKR as live chain source for TSX symbols (already have IBWorker, just need TSX symbol format)
2. Reinstate spread builder for bull_call_spread direction (was removed Day 57)
3. Add CAD account size config
4. Gate logic: use direct earnings gate (not ETF holdings), skip FOMC (Canadian rate decisions are different calendar)
5. New constants: TSX_TICKERS, TSX_LIQUID_TIER1, CA_EARNINGS dates

---

## Decision Deferred
- Current focus: US ETF short-premium workflow
- Revisit when: 30+ paper trades logged on US ETFs and gate calibration confirmed
