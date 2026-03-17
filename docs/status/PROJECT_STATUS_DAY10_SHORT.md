# OptionsIQ — Project Status Day 10
> **Date:** March 12, 2026
> **Version:** v0.9
> **Phase:** Phase 4 — Data provider research + Alpaca integration complete

---

## Session Summary

Research-heavy session. Market was closed (post-hours). Three data providers evaluated with live API calls.

**P0 — KI-035 OI fix applied ✅**
- `genericTickList=""` → `"101"` in ibkr_provider.py reqMktData for options
- Enables tick type 22 (optOpenInterest) for individual option contracts
- Needs market-hours verification Day 11

**P0 — .env syntax fix ✅**
- Line 38 had bare `Alpaca Key` (no `#` prefix) → dotenv parse error
- Fixed: `# Alpaca Key`

**P1 — alpaca_provider.py CREATED ✅**
- Full AlpacaProvider class (~296 lines) using alpaca-py SDK
- OCC symbol parsing, direction-aware DTE/strike windows
- Output matches ibkr_provider contract format exactly
- Wired into DataService cascade (tier 4, between stale cache and yfinance)
- Wired into app.py with graceful degradation

**Live API testing — Alpaca ✅**
- AMD tested, 572 contracts returned
- Greeks: 100% within ATM ±15% zone
- IV: 61% overall, 100% ATM zone
- **OI: field does NOT exist** in OptionsSnapshot model (always 0)
- **Volume: field does NOT exist** in OptionsSnapshot model (always 0)
- Bid/ask: 87-100% coverage

**Live API testing — MarketData.app ✅**
- Subscribed to Starter Trial (free 30 days, then $12/mo)
- Current chain: full greeks + IV + OI + volume ✅
- Historical chain: **greeks = None, IV = None** for all tickers (including AAPL premium)
- Support ticket drafted to clarify if this is trial vs platform limitation

**Research doc created ✅**
- `docs/Research/Options_Data_Provider_Research_Day10.md`
- Evidence-based comparison: IBKR vs Alpaca vs MarketData.app
- Perplexity research: 9 providers evaluated (Tradier, Polygon, UW, Cboe, etc.)
- Gate impact analysis by data source
- Golden Rule 19 added: research sessions produce a .md in docs/Research/

---

## Provider Cascade (updated)

```
Tier 1:   IBKR Live         — real-time, full data + historical IV for IVR
Tier 2:   IBKR Cache        — SQLite, 2-min TTL
Tier 2.5: MarketData.app    — PLANNED ($12/mo, 15-min delayed, greeks+IV+OI+volume)
Tier 3:   Alpaca            — free, greeks but NO OI/volume
Tier 4:   yfinance          — emergency, no greeks
Tier 5:   Mock              — dev/CI only
```

**Key finding:** No provider under $30/mo provides historical IV for IVR calculation.
IBKR remains required for `reqHistoricalData(whatToShow="OPTION_IMPLIED_VOLATILITY")`.

---

## Still Blocked

1. **KI-035 verification** — genericTickList="101" applied but untested during market hours
2. **Historical IV** — IBKR is the only source. MarketData.app support ticket pending.
3. **analyze_service.py not created** — app.py still 558 lines

---

## Next Session Priorities (Day 11)

1. **P0:** Verify KI-035 fix — test AMD during market hours, confirm OI > 0
2. **P1:** Based on MarketData.app support response → create `marketdata_provider.py` or deprioritize
3. **P2:** Create `analyze_service.py` — extract from app.py
4. **P3:** bull_put_spread builder for sell_put direction
5. **P4:** Paper trade E2E test (once OI gate passes)
