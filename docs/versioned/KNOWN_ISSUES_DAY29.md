# OptionsIQ — Known Issues Day 29
> **Last Updated:** Day 29 (April 27, 2026)
> **Previous:** KNOWN_ISSUES_DAY28.md

---

## Resolved This Session (Day 29)

### KI-082: No credit-to-width ratio gate ✅ RESOLVED Day 29
`MIN_CREDIT_WIDTH_RATIO = 0.33` in constants.py (raised from 0.20 based on multi-LLM synthesis — tastylive/Sinclair empirical data: 33% is the practical minimum, not 20%). `_credit_width()` helper in `strategy_ranker.py`. `credit_to_width_ratio` and warning wired into bear_call R1/R2 and bull_put R1/R2. Four tests added in `test_spread_math.py`.

### KI-IVR-NULL: IVR showing "—" in Best Setups watchlist ✅ RESOLVED Day 29
Root cause: `app.py` was reading `result.get("iv_data", ...)` but `analyze_etf()` returns `"ivr_data"`. One-character key mismatch — always returned empty dict → IVR always null. Fixed by correcting key to `"ivr_data"`.

### KI-SIGNAL-BOARD-SCROLL: Signal board not scrollable after tab state fix ✅ RESOLVED Day 29
Root cause: `style={{ display: 'block' }}` on signal board div overrode CSS class `display: grid`. The two-panel layout collapsed, losing scroll. Fixed with `display: undefined` (React removes the property, CSS class `display: grid` takes over).

---

## New Issues This Session (Day 29)

### KI-083: XLE OHLCV data corruption — HV-20 = 413% (HIGH)
**Component:** `backend/data/iv_history.db` — `ohlcv_daily` table, ticker = XLE
**Description:** Stray rows at ~$99-101 scattered among real XLE prices of ~$57-63 (e.g. 2026-03-01: 97.96, 2026-03-08: 101.49, 2026-03-15: 99.94). These are ~2x the actual price — likely stock split artifacts or bad IBKR data. These huge log return spikes cause `compute_hv(XLE, 20) = 413.72%`. The HV gate and HV/IV VRP gate both get fed this corrupt value. HV-20 of 413% means sell_put will always fail the VRP gate for XLE.
**Discovered by:** Data provenance tab field-level view showing HV-20 = 413% for XLE.
**Fix:** Delete corrupted ohlcv rows for XLE (rows where close > 80.0), then re-seed from IBKR/yfinance. Check other ETFs too.
**Severity:** HIGH — XLE gate decisions corrupted by phantom HV

### KI-084: XLC and XLRE have no OHLCV data — HV-20 null (MEDIUM)
**Component:** `backend/data/iv_history.db` — `ohlcv_daily` table
**Description:** `ohlcv_rows: 0` for both XLC and XLRE. `compute_hv()` returns null. The HV/IV VRP gate (`_etf_hv_iv_seller_gate`) cannot run — will skip or default pass. IVR history is present (370 rows each) but HV-20 cannot be computed without OHLCV.
**Discovered by:** Data provenance tab IV history section showing `hv_status: no_ohlcv`.
**Fix:** Run `_extract_iv_data()` for XLC and XLRE with IBKR connected — this calls `provider.get_ohlcv_daily()` and stores bars. Or add explicit OHLCV seeding endpoint.
**Severity:** MEDIUM — VRP gate silently skips for XLC/XLRE sellers

### KI-085: VIX value not displayed in any UI component (LOW)
**Component:** `frontend/src/components/RegimeBar.jsx`
**Description:** VIX is now fetched and included in the analyze result (`result.vix.value`) and in the data health endpoint. The VIX gate (`_vix_regime_gate`) runs and blocks/warns. But VIX is never shown to the user in the UI — they can't see what VIX level triggered the gate decision.
**Fix:** Add VIX to `RegimeBar.jsx` alongside SPY regime (small badge: "VIX: 19.4").
**Severity:** LOW — gate runs correctly, just not visible

### KI-086: app.py is 470 lines — Rule 4 violation (MEDIUM)
**Component:** `backend/app.py`
**Description:** Rule 4 mandates ≤150 lines. `app.py` is 470+ lines. `_run_one()` closure in `/api/best-setups` contains 30+ lines of business logic. `_seed_iv_for_ticker()` (25 lines) belongs in `analyze_service.py`. These are direct Rule 4 violations — makes the route file untestable.
**Fix:** Move `_seed_iv_for_ticker()` to `analyze_service.py`. Move `_run_one()` closure to a dedicated `best_setups_service.py`. Route handlers should be 5-10 lines each.
**Severity:** MEDIUM — testability and maintainability risk

---

## Still Open (Carried Forward)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)
Only FOMC is tracked. CPI, NFP, PCE releases not in events gate.

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
ETF-only mode means stocks return 400. Deferred indefinitely.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put for QQQ returns ITM put strikes. Chain struct_cache issue.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
~5pp gap between L2 percentile and L3 average.

### KI-044: API_CONTRACTS.md partially stale (MEDIUM)
`/api/data-health` and `/api/best-setups` not yet documented. `/api/best-setups` field_resolution section also undocumented.

### KI-075: GateExplainer GATE_KB may drift from gate_engine.py logic (MEDIUM)
Hardcoded plain English answers in GATE_KB can go stale silently when thresholds change.

### KI-076: TradeExplainer isBearish() not live-tested against all 4 directions (MEDIUM)

### KI-038: Alpaca OI/volume fields missing (LOW)
### KI-034: OHLCV temporal gap not validated (LOW)
### KI-013/KI-050: API URL hardcoded in JS files (LOW)
### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)
### KI-072: deepcopy() on every cache hit in data_service.py (LOW)
### KI-073: _struct_cache grows unbounded in ibkr_provider.py (LOW)
### KI-074: No IBWorker health check at startup (LOW)
### KI-077: DirectionGuide "Risk: Spread width (capped)" for sell_put may mislead (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 2 (KI-059 deferred, KI-083 XLE OHLCV corruption) |
| Medium | 7 (KI-067, KI-064, KI-044, KI-075, KI-076, KI-084, KI-086) |
| Low | 10 (KI-038, KI-034, KI-013/050, KI-049, KI-072, KI-073, KI-074, KI-077, KI-081, KI-085) |
| **Total** | **19** |
| **Resolved Day 29** | **3** (KI-082, KI-IVR-NULL, KI-SIGNAL-BOARD-SCROLL) |
| **Added Day 29** | **4** (KI-083, KI-084, KI-085, KI-086) |
