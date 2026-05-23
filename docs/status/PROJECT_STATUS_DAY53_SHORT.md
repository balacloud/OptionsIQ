# OptionsIQ — Project Status Day 53
> **Date:** May 23, 2026 | **Version:** v0.33.2 | **Tests:** 44

## What Shipped

**Research session — no code changes.**

### IBKR Market Screener 2.0 Configuration Research

Analyzed all available Add Factors categories in IBKR Screener 2.0 and confirmed actual data scales from live screener (143 ETFs with Avg Option Volume > 487).

**Selected columns for OptionsIQ screener (8 of 10 max):**
From Options section: Average Option Volume, Implied Vol./Hist. Vol %, 52 Week IV Rank, Opt. Implied Volatility %, Opt. Volume, Put/Call Volume
From Popular section: Last, Change %

**Key scale discoveries:**
- `Opt. Implied Volatility %` is in DECIMAL format — 0.15 = 15% IV, NOT 15 units. Filter must use 0.10–0.50 for our ETFs (not 10–50).
- `Last` price default cap at $100 excludes XLK (~$220), QQQ (~$500), IWM (~$195), MDY (~$580). Must set Last to $1–$9999.
- `52 Week IV Rank` universe max showing 45.6% with current filter — excludes our high-IVR ETFs (XLI 88%, XLE 94%). Set range 0.00–99.99.
- `Implied Vol./Hist. Vol %` correct — percentage format, range 0–237% in universe.
- `Put/Call Volume` correct — ratio format, 0–1.84.

**Recommended MultiSort settings (finalized):**

| Factor | Filter | Sort |
|--------|--------|------|
| Average Option Volume | > 500 | Higher Values |
| Implied Vol./Hist. Vol % | 85 TO 237 | Higher Values |
| 52 Week IV Rank | 0 TO 99.99 | No Preference |
| Opt. Implied Volatility % | 0.05 TO 0.99 | No Preference |
| Opt. Volume | 100 TO max | No Preference |
| Put/Call Volume | 0 TO 10 | No Preference |
| Last | 1 TO 9999 | No Preference |
| Change % | -20 TO 20 | No Preference |

**Impact on P2 (reqScannerSubscription) implementation:**
The scanner returns data in these exact scales. When parsing ScanData results in code:
- Multiply `optImpliedVolatility` by 100 to get percentage
- No price filter — all 15 ETFs will be in results once Last filter is removed
- IVR values 0–100 (direct percentage) — no conversion needed

---

## Test Count
44 (unchanged)

## Open Issues
| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH | Single-stock bear untested — deferred by design (ETF-only mode) |
| KI-099 | LOW | bull_call_spread direction for Leading/Improving + IVR 30–50% |

## Next Session Priorities
1. **P0 — Paper trade logging** — still 0/30. Log next XLF or QQQ CAUTION setup. Cannot calibrate gates without 30-trade sample. ~5 min user action.
2. **P1 — MASTER_AUDIT_FRAMEWORK sweep** — overdue since Day 42 (11 sessions). All 10 categories.
3. **P2 — IBKR `reqScannerSubscription` implementation** — screener config now fully researched. One call replaces 14 reqHistoricalData calls + delivers put/call ratio. Plan: save screener as "options-iq" in ETFs tab → call via API → parse 8 columns → merge with our 15 ETF list.
4. **P3 — KI-099** — bull_call_spread for Leading/Improving ETFs. Plan before touching.
