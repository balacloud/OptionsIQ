# OptionsIQ — Known Issues Day 38
> **Last Updated:** Day 38 (May 5, 2026)
> **Previous:** KNOWN_ISSUES_DAY37.md

---

## Resolved This Session (Day 38)

None — Day 38 was a UI feature + doc correction session (no bug fixes).

---

## New Issues This Session (Day 38)

None found.

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — 497 lines (Rule 4 max = 150) (MEDIUM)
`_run_one()` closure in `best_setups()` route still inline — move to best_setups_service.py.
app.py slightly grew (492→497) from startup catch-up wiring. Target: ~420 lines after extraction.

### KI-067: QQQ sell_put returns ITM strikes (MEDIUM)
Chain too narrow for current QQQ price — sell_put picks up ITM puts.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)

### KI-076: TradeExplainer isBearish() not live-tested (LOW)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

---

## Resolved History (recent)
- APScheduler missed jobs (startup gap) ✅ Day 37 — run_startup_catchup() daemon thread
- yfinance HV in iv_history contamination ✅ Day 37 — removed from IV seeding pipeline
- KI-088: L3 stale banner ✅ Day 34
- KI-CB-FRAGILE, KI-STALE-HARDBLOCK, KI-VERDICT-NULL, KI-AMBER-YELLOW, KI-VIX-RATELIMIT, KI-OHLCV-EVERY-CALL, KI-UNDERLYING-IBKR, KI-PARALLEL-EXPIRY ✅ Day 33
- KI-VRP-INVERT ✅ Day 32
- KI-084/087: XLRE OHLCV seeded ✅ Day 31
- KI-085: VIX badge in RegimeBar ✅ Day 31
