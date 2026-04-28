# OptionsIQ — Known Issues Day 30
> **Last Updated:** Day 30 (April 28, 2026)
> **Previous:** KNOWN_ISSUES_DAY29.md

---

## Resolved This Session (Day 30)

### KI-083: XLE OHLCV data corruption ✅ RESOLVED Day 30
Deleted 18 rows where `close > 80.0` from `ohlcv_daily` for XLE. Root cause: IBKR historical data contained doubled/adjusted prices from a prior seeding pass. After deletion, `compute_hv(XLE, 20) = 16.96%` (was 413%).

### KI-IWM-OHLCV: IWM OHLCV corruption ✅ RESOLVED Day 30
Discovered during McMillan stress check development. IWM had 17 rows at ~$93-101 interspersed with real data at $240-277, causing worst_21d_drawdown=65% and rally=184%. Deleted rows with `close < 150`. After fix: 70 rows, range $239-$277.

---

## New Issues This Session (Day 30)

### KI-087: XLRE and SCHB have 0 OHLCV rows — stress check warns "insufficient data" (MEDIUM)
**Component:** `backend/data/iv_history.db` — `ohlcv_daily` for XLRE and SCHB
**Description:** `compute_max_21d_move()` returns `bars_available=0` for XLRE and SCHB. The `_historical_stress_gate()` returns WARN with "Not enough OHLCV history" for both. Same root issue as KI-084 (no OHLCV at all).
**Fix:** Seed OHLCV for XLRE and SCHB with IBKR connected. Same as KI-084 fix path.
**Severity:** MEDIUM — stress gate silently degrades for XLRE/SCHB sellers

---

## Still Open (Carried Forward)

### KI-084: XLC and XLRE have no OHLCV data — HV-20 null (MEDIUM)
HV-20 null + VRP gate skips for XLC/XLRE. Need OHLCV seeding from IBKR.

### KI-085: VIX value not displayed in any UI component (LOW)
VIX gate runs correctly, VIX value not shown in RegimeBar.

### KI-086: app.py is 470 lines — Rule 4 violation (MEDIUM)
Move `_seed_iv_for_ticker()` → analyze_service. Move `_run_one()` → best_setups_service.py.

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)
### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH — deferred indefinitely)
### KI-067: QQQ chain fractional strikes (MEDIUM)
### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
### KI-044: API_CONTRACTS.md partially stale (MEDIUM)
### KI-075: GateExplainer GATE_KB may drift (MEDIUM)
### KI-076: TradeExplainer isBearish() not live-tested (MEDIUM)
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
| High | 1 (KI-059 deferred) |
| Medium | 8 (KI-067, KI-064, KI-044, KI-075, KI-076, KI-084, KI-086, KI-087) |
| Low | 10 (KI-038, KI-034, KI-013/050, KI-049, KI-072, KI-073, KI-074, KI-077, KI-081, KI-085) |
| **Total** | **19** |
| **Resolved Day 30** | **2** (KI-083, KI-IWM-OHLCV) |
| **Added Day 30** | **1** (KI-087) |
