---
name: project-ibkr-screener-config
description: IBKR Market Screener 2.0 ETF factor data scales and correct MultiSort settings for OptionsIQ reqScannerSubscription P2
metadata:
  type: project
---

IBKR Screener 2.0 ETF universe (143 ETFs at Avg Option Volume > 487) — actual data scales confirmed Day 53:

**Why:** Researched to prepare for reqScannerSubscription P2 implementation. Wrong scale assumptions would produce incorrect filter values and garbled parsed data from the API.

**Scale facts:**
- `Opt. Implied Volatility %` → **DECIMAL** (0.15 = 15%). When parsing from API, multiply by 100.
- `Implied Vol./Hist. Vol %` → **PERCENTAGE** (100.0 = IV/HV ratio of 1.0). Direct use OK.
- `52 Week IV Rank` → **PERCENTAGE** (0–100). Direct use OK.
- `Put/Call Volume` → **RATIO** (1.50 = puts 1.5× calls). Direct use OK.
- `Opt. Volume` → **Contracts** (1.78K = 1,780). K suffix = thousands.
- `Last` → **USD price**. Default cap $100 excludes XLK (~$220), QQQ (~$500), IWM (~$195), MDY (~$580).
- `Average Option Volume` → **Contracts/day**. > 487 gives 143 ETF universe.

**Correct MultiSort settings for OptionsIQ (all 15 ETFs captured):**
| Factor | Min | Max | Sort |
|--------|-----|-----|------|
| Average Option Volume | 500 | open | Higher Values |
| Implied Vol./Hist. Vol % | 85 | 237 | Higher Values |
| 52 Week IV Rank | 0 | 99.99 | No Preference |
| Opt. Implied Volatility % | 0.05 | 0.99 | No Preference |
| Opt. Volume | 100 | open | No Preference |
| Put/Call Volume | 0 | 10 | No Preference |
| Last | 1 | 9999 | No Preference |
| Change % | -20 | 20 | No Preference |

**How to apply:** When implementing reqScannerSubscription in ibkr_provider.py:
- Parse `optImpliedVolatility` field → multiply by 100 for percentage
- Set numberOfRows ≥ 200 to ensure all 15 ETFs appear
- After getting results, filter to our ETF_UNIVERSE list; fall back to reqHistoricalData for any missing
- Put/call ratio from `putCallRatio` field → wire directly into gate_engine sentiment WARN
