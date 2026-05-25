# OptionsIQ — Known Issues Day 55
> **Last Updated:** Day 55 (May 25, 2026)
> **Previous:** KNOWN_ISSUES_DAY54.md

---

## Resolved This Session (Day 55)

None — architectural research session only. No code changes.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 56+.

---

## New Findings (Day 55 — no bugs, architectural gaps identified)

### GAP-001: STA priceHistory unused for ETF chart trend (MEDIUM — P2 next session)
STA `/api/stock/{ticker}` returns `priceHistory` (260 daily bars). Already used for SPY 200 SMA in `sector_scan_service.py`. All SMA (20/50/200), RSI(14), momentum, and volume ratio are computable from the same call at zero extra HTTP cost. `gate_engine` has no chart-trend gate — a sell_put on XLK could be recommended while it's in a confirmed downtrend. This is the most dangerous data gap identified this session.

**Status:** Planned for Day 56. Implementation in `sta_service.py` → `fetch_etf_sma_batch(tickers)` → non-blocking WARN gate.

### GAP-002: compute_skew() exists but gate_engine has 0 references (LOW — P4)
`tradier_provider.compute_skew()` returns put/call IV spread (30-delta put − 30-delta call IV). This is exposed in the analyze API response but `gate_engine` has zero references to it. Elevated skew = market paying for downside protection = meaningful signal for sell_put risk.

**Status:** Deferred. Wire into gate_engine as advisory WARN when skew > threshold (e.g., >5%).

### GAP-003: put/call volume gate exists but no data source (LOW — P3)
`gate_engine._put_call_sentiment_gate()` (Gates 7b/11b) checks `put_call_volume` but it is always `None` because `fetch_scanner_subscription_batch()` no longer uses IBKR scanner. `tradier_provider.get_options_chain()` already returns per-contract volume — summing put volume / call volume for near-term expiry is ~30 lines.

**Status:** Deferred to Day 56 P3 (after chart trend gate).

---

## Architecture Finding (Day 55) — Gate Calibration Requires Paper Trade Data

Cannot determine if system is over-gated without empirical data. Key facts:
- 7 blocking gates fire on sell_put (liquidity, IVR, HV/IV, VIX regime, event density, credit-to-width, holdings earnings)
- All planned additions (SMA trend, put/call sentiment, skew) are advisory WARN only
- Need 5+ live scans across different VIX/SPY regimes to assess gate pass rate
- Paper trade logging (0/30) remains the structural blocker for calibration

**Decision:** Do not tune any blocking gate until 30-trade sample exists. Only add advisory WARNs.

---

## Resolved History (recent)
- KI-106: IBKR batch all-nan → reqHistoricalData ✅ Day 52
- KI-105: Tick 104 invalid for STK → 106+411+100+105 ✅ Day 51
- KI-104: snapshot=True invalid with genericTickList ✅ Day 51
- KI-103: is_connected() false-negative in scanner ✅ Day 51
- KI-102: XLI/XLB OHLCV corruption (Apr 25-26) ✅ Day 51
- KI-101: IV/HV null in watchlist ✅ Day 50
