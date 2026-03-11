# OptionsIQ — Project Status Day 9
> **Date:** March 11, 2026
> **Version:** v0.8
> **Phase:** Phase 4 — Live verification + strategy routing complete

---

## Session Summary

Market was open. IB Gateway connected. First live market-hours test since reqMktData fix (Day 7).

**P0 — Live greeks: CONFIRMED ✅**
- `data_source: ibkr_live`, `greeks_complete_pct: 100%`
- Phase 4e BS fallback never triggered
- usopt reconnects lazily on first options request (not at startup)

**KI-030 — HV bug fixed ✅**
- AMD hv_20 was 613% due to corrupt ohlcv rows (mid-2025 ~$95 prices in 2026 table)
- Deleted 20 rows. hv_20 now 52.28%. Root cause (temporal gap assumption) → KI-034

**KI-031 — pnl_calculator fixed ✅**
- `_fmt(None)` TypeError crash fixed
- Added P&L formulas for: `itm_put`, `atm_put`, `bear_call_spread`, `sell_call`
- Fixed `spread` handler: now direction-aware (puts use `long_strike - price`)

**KI-033 — sell_call spread now building ✅**
- Root cause: proximity sort + SMART_MAX_STRIKES=6 squeezed out OTM protection leg strikes
- `$2.5-increment` stubs from reqSecDefOptParams filled all 6 slots; $5 OTM strikes excluded
- Fix: direction-aware sort (ascending for sell_call) + SMART_MAX_STRIKES 6→12 + MAX_CONTRACTS 12→26
- AMD sell_call now returns: rank 1 = 225/230 bear_call_spread, rank 2 = 230C sell_call

**OI fix (partial) ✅**
- Changed `callOpenInterest` → `optOpenInterest` (correct field for individual options)
- OI still 0 intraday — `genericTickList="101"` needed to request tick 22 from IBKR (KI-035)

**Alpaca research ✅**
- Free tier provides: bid/ask, delta, gamma, theta, vega, IV, OI, volume via REST
- Single GET call vs IBKR's reqMktData subscription cycle
- 15-min delayed on free tier — acceptable for swing analysis
- Needs API secret (only key added to .env)
- Plan: alpaca_provider.py as Tier 2 (between IBKR and yfinance)

---

## Test Results (Day 9)

| Ticker | Direction | Source | Greeks | Strategies | Issues |
|--------|-----------|--------|--------|------------|--------|
| AMD | buy_call | ibkr_live | 100% | 3 ✅ | OI=0 → liquidity gate fails |
| AMD | sell_call | ibkr_live | 83-100% | 2 ✅ | OI=0 → liquidity gate fails |
| AMD | sell_put | ibkr_live | 14% | 3 ✅ | OI=0, greeks sparse (2nd fetch) |
| NVDA | buy_put | ibkr_live | 33% | 3 | DTE gate fails, 3 contracts only |

---

## Still Blocked

1. **Liquidity gate always fails (OI=0)** — KI-035 — reqMktData needs genericTickList="101"
2. **NVDA buy_put sparse** — only 3 contracts, DTE gate blocks
3. **analyze_service.py not created** — app.py still 558 lines

---

## Data Provider Hierarchy (current)
```
[1] IBKR Live (reqMktData snapshot=False)  ← DEFAULT
[2] IBKR Cache (SQLite, 2-min TTL)
[3] yfinance                               ← fallback (no greeks — BS computed)
[4] Mock (dev/CI only)

PLANNED (Day 10):
[2.5] Alpaca (indicative/opra)            ← between IBKR and yfinance
       → REST, no Gateway dep, HAS greeks
       → needs alpaca_provider.py + API secret
```

---

## Next Session Priorities (Day 10)

1. **P0:** Fix KI-035 — change `genericTickList=""` → `"101"` in reqMktData for options
2. **P1:** Create `alpaca_provider.py` — REST client for Alpaca options data
   - User needs to add `APLACA_SECRET` to `.env` (get from Alpaca dashboard)
   - Test: AMD sell_call → check if OI, greeks, bid/ask match IBKR live
3. **P2:** Create `analyze_service.py` — extract from app.py, reduce to ≤150 lines
4. **P3:** bull_put_spread builder for sell_put direction (currently naked sell_put only)
5. **P4:** Paper trade E2E test (once OI gate passes)
