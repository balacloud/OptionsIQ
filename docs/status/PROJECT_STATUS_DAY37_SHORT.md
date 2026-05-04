# OptionsIQ — Project Status Day 37
> **Version:** v0.27.0
> **Date:** May 4, 2026
> **Tests:** 36 (unchanged)

---

## What Shipped

### 1. Startup catch-up for missed BOD/EOD jobs (`batch_service.py`)
**Problem:** APScheduler only fires when Flask is running. If backend was down at 9:31 AM or 4:05 PM
ET, those jobs are silently skipped — no chain pre-warm, no IV seeding.
**Fix:** `run_startup_catchup()` daemon thread (starts 10s after app boot, waits for IBWorker to
connect). Checks `batch_run_log` for:
1. Previous trading day EOD missing → fire `run_eod_batch()` (fills IV history gap)
2. Today's BOD missing + current time past 9:31 AM ET → fire `run_bod_batch()`
3. Today's EOD missing + current time past 4:05 PM ET → fire `run_eod_batch()`
Weekend check: skips entirely on Sat/Sun.
**Helpers added:** `_prev_trading_date(ref)` (Mon→Fri), `_ran_on(runs, type, date_str)`
**Wired:** `app.py` imports `run_startup_catchup`, calls it after `_scheduler.start()`
**Verification:** Confirmed May 2 (Friday EOD missed) + May 4 (Monday BOD missed) scenario
that triggered this work.

### 2. yfinance IV fallback removed from IV seeding pipeline (`batch_service.py`)
**Problem:** When IBKR offline, `seed_iv_for_ticker()` fell back to yfinance for IV. yfinance
computes 20-day rolling realized HV from price returns — **not implied volatility**. Storing HV
rows in `iv_history.db` contaminates IVR percentile (compares current IV against HV values).
**Fix:** yfinance IV fallback removed entirely. If IBKR offline → IV seeding skipped, logged as
"IBKR offline — IV seeding skipped (no HV proxy)". yfinance OHLCV fallback kept (price data
is correct from both sources).

### 3. docs/Research/ reorganization
18 files with inconsistent names → 6 topic subdirectories:
- `data-providers/` — provider research (Day 10, 26, 34) + new synthesis
- `system-audits/` — behavioral + coherence + sector audits
- `sector-rotation/` — all sector ETF research
- `ux-design/` — UX synthesis + multi-LLM design
- `multi-llm-synthesis/` — improvement research + book reviews
- `ki-plans/` — KI-088 implementation plan
- `archive/` — drafts, HTML, zip, Perplexity export

**New:** `data-providers/DATA_PROVIDERS_SYNTHESIS.md` — canonical provider decisions doc.
Captures full stack decision (IBKR + MD.app $12/mo), all provider verdicts (Tradier free,
Massive.com don't buy, EODHD blocked on free), and why yfinance was removed from IV pipeline.

### 4. Provider research completed (Day 37)
- **Tradier:** Confirmed by support — free with brokerage account (no separate dev plan). API:
  `/v1/markets/options/chains?greeks=true` returns full chain + OI/volume + ORATS greeks (hourly
  updated). `smv_vol` = ORATS smoothed ATM IV. Hourly delay acceptable for multi-week analysis.
  Pending: open account, test live call, implement `tradier_provider.py`.
- **Massive.com:** Final verdict — don't buy. No historical IV at any tier. Free tier has zero
  options entitlement. Paid tiers (~$29/mo) duplicate MD.app capability at 2.4× the cost.
  Auth confirmed: `Authorization: Bearer` on `api.massive.com`.
- **EODHD:** Free key tested live — options blocked at free tier. Not worth paid plan.

---

## File Changes

| File | Change | Lines |
|------|--------|-------|
| `backend/batch_service.py` | startup catch-up + yfinance IV fix | 148 → 231 |
| `backend/app.py` | wired run_startup_catchup | 492 → 497 |
| `backend/analyze_service.py` | MD.app IV accumulation (Day 36, confirmed) | 835 → 841 |
| `docs/Research/` | reorganized 18 files + new synthesis | — |
| `memory/MEMORY.md` | updated Research paths | — |

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-086 | MEDIUM | app.py 497 lines — `_run_one` still inline |
| KI-067 | MEDIUM | QQQ sell_put returns ITM strikes |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift |
| KI-059 | HIGH (deferred) | Single-stock bear untested |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | sell_put "capped" label may mislead |

---

## Next Session Priorities (Day 38)

| Priority | Task | Effort |
|----------|------|--------|
| P0 | Tradier: open account, test live chain call, implement `tradier_provider.py` | 2 hrs |
| P1 | KI-086: move `_run_one` to `best_setups_service.py` | 45 min |
| P2 | KI-067: QQQ sell_put ITM strike fix | 30 min |
| P3 | Live test: verify startup catch-up fires on next restart, check backend.log | 15 min |
| P4 | FOMC dates audit: verify 2026 dates in constants.py are complete | 15 min |
