# OptionsIQ — Known Issues Day 31
> **Last Updated:** Day 31 (April 29, 2026)
> **Previous:** KNOWN_ISSUES_DAY30.md

---

## Resolved This Session (Day 31)

### KI-084/087: XLRE, SCHB (and XLC) OHLCV gap — HV-20 null ✅ RESOLVED Day 31
`_seed_iv_for_ticker()` in `app.py` enhanced to also seed OHLCV via `get_ohlcv_daily()` (IBKR primary, yfinance fallback, 90 days). XLRE and SCHB seeded. HV-20 and stress check now have valid data.

### KI-085: VIX not shown in any UI component ✅ RESOLVED Day 31
`_fetch_vix()` now called in the `/api/sectors/scan` route so VIX cache is always warm. `get_vix_status()` result wired into `sectorData.vix`. `RegimeBar.jsx` shows color-coded badge: green (15-30), orange (>30), red (>40), grey (<15 or unavailable).

---

## New Issues This Session (Day 31)

None identified.

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — ~470 lines (Rule 4 max = 150) (MEDIUM)
`_seed_iv_for_ticker()` and `_run_one()` (best-setups closure) belong in service modules. Route handlers should be ≤10 lines.

### KI-067: QQQ sell_put returns ITM strikes (MEDIUM)
Chain too narrow for current QQQ price — sell_put picks up ITM puts. Struct cache issue.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)
L2 and L3 use slightly different IVR computation paths.

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)
GateExplainer.jsx and LearnTab.jsx each have their own GATE_KB copy. Audit scheduled (Category 9).

### KI-076: TradeExplainer isBearish() not live-tested (LOW)
All 4 directions not verified live post-Day 21. sell_call and buy_put zone colors unverified.

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
ETF-only mode: stocks return 400. Deferred indefinitely.

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)
Only FOMC is tracked in the events gate.

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

---

## Resolved History (recent)
- KI-083: XLE OHLCV corruption ✅ Day 30
- KI-IWM-OHLCV: IWM OHLCV corruption ✅ Day 30
- KI-082: Credit-to-width ratio gate ✅ Day 29
- KI-IVR-NULL: IVR showing "—" in Best Setups ✅ Day 29
- KI-SIGNAL-BOARD-SCROLL: Signal board scroll ✅ Day 29
- KI-079: ETF holdings earnings gate ✅ Day 28
- KI-080: Spread hard-block >20% ✅ Day 28
- KI-FOMC-WINDOW: FOMC gate warns inside DTE window ✅ Day 28
- KI-008: FOMC gate fallback ✅ Day 26
- KI-076 (strike zone overlap in TradeExplainer) ✅ Day 26
