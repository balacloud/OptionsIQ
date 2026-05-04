# OptionsIQ — Known Issues Day 37
> **Last Updated:** Day 37 (May 4, 2026)
> **Previous:** KNOWN_ISSUES_DAY36.md

---

## Resolved This Session (Day 37)

### ✅ APScheduler missed jobs (startup gap) — RESOLVED
**Root cause:** Flask process not running at scheduled BOD/EOD times → APScheduler never fires.
**Fix:** `run_startup_catchup()` daemon thread in `batch_service.py` — detects missed BOD/EOD jobs
on startup by checking `batch_run_log` for prev-day EOD, today's BOD, and today's EOD, then fires
any that are missing. Called once from `app.py` after `_scheduler.start()`.

### ✅ yfinance HV contaminating iv_history.db — RESOLVED
**Root cause:** `seed_iv_for_ticker()` fell back to yfinance when IBKR offline. yfinance computes
20-day rolling realized HV from price returns (`np.std(returns) * sqrt(252) * 100`) — this is
**historical volatility, not implied volatility**. Storing HV in iv_history.db corrupts the
IVR percentile calculation (compares current IV against historical HV = apples vs oranges).
**Fix:** yfinance IV fallback removed entirely from `seed_iv_for_ticker()`. If IBKR offline,
IV seeding is skipped for that run (logs: "IBKR offline — IV seeding skipped (no HV proxy)").
yfinance OHLCV fallback kept (price data is correct from both sources).

---

## New Issues This Session (Day 37)

None found.

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — 497 lines (Rule 4 max = 150) (MEDIUM)
`_run_one()` closure in `best_setups()` route still inline — move to best_setups_service.py.
app.py slightly grew (492→497) from startup catch-up wiring. Target: ~420 lines after extraction.

### KI-067: QQQ sell_put returns ITM strikes (MEDIUM)
Chain too narrow for current QQQ price (~$658) — sell_put picks up ITM puts.

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
