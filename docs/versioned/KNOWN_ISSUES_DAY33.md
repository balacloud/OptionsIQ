# OptionsIQ — Known Issues Day 33
> **Last Updated:** Day 33 (April 30, 2026)
> **Previous:** KNOWN_ISSUES_DAY32.md

---

## Resolved This Session (Day 33)

### KI-CB-FRAGILE: Circuit breaker opening during Best Setups scan ✅ RESOLVED Day 33
`IB_CB_FAILURE_THRESHOLD = 2` was too low. Parallel Best Setups scan (6 workers) triggered cascade timeouts → CB opened → all subsequent IBKR calls failed immediately. Fix: raised threshold to 5.

### KI-STALE-HARDBLOCK: Stale chain spread hard-blocking morning scan ✅ RESOLVED Day 33
`apply_etf_gate_adjustments()` applied `spread_pct > 20%` hard-block regardless of whether chain was from yesterday's close (meaningless) or live market. Fix: `data_source == "ibkr_stale"` → downgrade spread fail to WARN with "refresh chain before trading" message.

### KI-VERDICT-NULL: verdict_label always None in Best Setups ✅ RESOLVED Day 33
`_run_one` called `verdict.get("label")` but `build_verdict()` returns `"headline"` not `"label"`. All ETFs showed `verdict_label: None` → `setups` array always empty → "No GO or CAUTION" despite ETFs passing gates. Fix: derive label from normalized color.

### KI-AMBER-YELLOW: CAUTION ETFs never appeared in setups section ✅ RESOLVED Day 33
`build_verdict()` returns `color="amber"` for CAUTION but `app.py` and `BestSetups.jsx` both filter for `"yellow"`. Fix: normalize `"amber"→"yellow"` in `_run_one` result dict.

### KI-VIX-RATELIMIT: VIX always null (yfinance rate-limited) ✅ RESOLVED Day 33
Best Setups scan fires 8 `analyze_etf()` calls simultaneously, all hitting `yfinance ^VIX` before the 5-min cache is populated. Yahoo rate-limits → `YFRateLimitError` swallowed by `except Exception: pass` → VIX null. Fix: STA `/api/stock/%5EVIX` as primary (no rate limits, already connected) + `threading.Lock()` to prevent stampede.

### KI-OHLCV-EVERY-CALL: reqHistoricalData called on every analysis ✅ RESOLVED Day 33
`_extract_iv_data()` called `provider.get_ohlcv_daily()` via IBWorker on every `analyze_etf()` call regardless of SQLite freshness. During Best Setups scan: 8 ETFs × 1 `reqHistoricalData` each = 8 IBWorker historical data calls → all timeout (historical farm inactive) → CB trips → chain fetches fail. Fix: skip IBWorker call if SQLite OHLCV `last_date` is ≤2 days old.

### KI-UNDERLYING-IBKR: get_underlying_price() failing for all parallel ETFs ✅ RESOLVED Day 33 (Best Setups only)
`_run_one` didn't set `last_close` in payload → every scan ETF called `get_underlying_price()` via IBWorker simultaneously → all failed (bid/ask/last None within 1.2s window) → CB trips. Fix: pre-fetch `currentPrice` from STA `/api/stock/{ticker}` in `_run_one` and pass as `last_close`, bypassing the IBKR call entirely.

### KI-PARALLEL-EXPIRY: max_workers=3/6 caused queue expiry for later ETFs ✅ RESOLVED Day 33
IBWorker is single-threaded — "parallel" workers just created a queue. Worker 3 submitted at t=0 with 40s expires_at. Workers 1+2 each taking 15-20s meant Worker 3's request was already expired when IBWorker got to it. Fix: max_workers=1 (fully sequential). Chain fetches take ~3-4 min total but every ETF gets fresh data.

---

## New Issues This Session (Day 33)

### KI-088: L3 analysis "Run Analysis" still shows stale banner (HIGH)
**Root cause (fully traced):** When user clicks "Run Analysis" from the analysis panel (L3), `app.py` builds the payload from frontend POST body. `underlying_hint = payload.get("last_close")` is None because the frontend doesn't send `last_close`. `analyze_etf()` calls `data_svc.get_chain()` → `ibkr_provider.get_options_chain()` → `get_underlying_price()` → `reqMktData(snapshot=True, sleep=1.2s)` → bid/ask/last all None (IBKR snapshot unreliable with current connection state) → `IBKRNotAvailableError` → falls back to SQLite stale chain → `data_source = "ibkr_stale"` → frontend banner.

**Exact fix for Opus (Day 34 P0):**
In `analyze_service.analyze_etf()`, before calling `data_svc.get_chain()`, if `underlying_hint` is None, try STA:
```python
if underlying_hint is None:
    try:
        import requests as _req
        r = _req.get(f"{STA_BASE_URL}/api/stock/{ticker}", timeout=3)
        underlying_hint = r.json().get("currentPrice")
        if underlying_hint:
            underlying_hint = float(underlying_hint)
    except Exception:
        pass
```
This is the same pattern used in `_run_one` (Best Setups scan), just needs to be applied to the main `analyze_etf()` path too. STA is always connected and returns currentPrice for all 16 ETFs.

**Note:** The gate analysis IS correct despite the stale chain. The banner is the only issue — it's not causing wrong verdicts, just user confusion.

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — ~500 lines (Rule 4 max = 150) (MEDIUM)
`_seed_iv_for_ticker()` and `_run_one()` (best-setups closure) belong in service modules. Route handlers should be ≤10 lines.

### KI-067: QQQ sell_put returns ITM strikes (MEDIUM)
Chain too narrow for current QQQ price (~$658) — sell_put picks up ITM puts. Struct cache issue. QQQ also shows `ibkr_stale` because chain fetch fails — related.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)

### KI-076: TradeExplainer isBearish() not live-tested (LOW)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

---

## Resolved History (recent)
- KI-VRP-INVERT: VRP gate inverted since Day 29 ✅ Day 32
- LearnTab zones SVG overlap ✅ Day 32
- KI-084/087: XLRE, SCHB OHLCV seeded ✅ Day 31
- KI-085: VIX badge in RegimeBar ✅ Day 31
