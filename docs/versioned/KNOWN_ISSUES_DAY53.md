# OptionsIQ — Known Issues Day 53
> **Last Updated:** Day 53 (May 23, 2026)
> **Previous:** KNOWN_ISSUES_DAY52.md

---

## Resolved This Session (Day 53)
None — research/planning session only.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 54+.

---

## Architecture Finding (Day 53) — IBKR Screener Data Scales

IBKR Market Screener 2.0 ETF universe (143 ETFs at Avg Option Volume > 487) uses these actual data scales:

| Factor | Scale | Notes |
|--------|-------|-------|
| Opt. Implied Volatility % | DECIMAL (0.01 = 1%, 0.20 = 20%) | NOT percentage — critical for filter values |
| Implied Vol./Hist. Vol % | Percentage (100 = IV/HV ratio of 1.0) | Range 0–237% in current universe |
| 52 Week IV Rank | Percentage (0–100) | Current universe max 45.6% — high-IVR ETFs may be filtered |
| Put/Call Volume | Ratio (0–1.84) | Direct ratio, not percentage |
| Last | USD price | Default cap $100 excludes XLK (~$220), QQQ (~$500), IWM (~$195), MDY (~$580) |
| Opt. Volume | Contracts (1.78K = 1,780) | K suffix = thousands |
| Average Option Volume | Contracts (raw number) | > 487 gives 143 ETF universe |

**Critical for P2 implementation (reqScannerSubscription):**
- When reading Opt. Implied Volatility % from scanner results, multiply by 100 to get percentage
- Remove Last price filter (or set > $1) to include all 15 ETFs
- Set IVR range to 0–99.99 to capture XLI (88%), XLE (94%), XLK (77%)

---

## Resolved History (recent)
- KI-106: IBKR batch all-nan → reqHistoricalData ✅ Day 52
- KI-105: Tick 104 invalid for STK → 106+411+100+105 ✅ Day 51
- KI-104: snapshot=True invalid with genericTickList ✅ Day 51
- KI-103: is_connected() false-negative in scanner ✅ Day 51
- KI-102: XLI/XLB OHLCV corruption (Apr 25-26) ✅ Day 51
- KI-101: IV/HV null in watchlist ✅ Day 50
