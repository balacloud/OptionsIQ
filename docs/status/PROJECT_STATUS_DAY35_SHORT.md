# OptionsIQ — Project Status Day 35
> **Date:** May 1, 2026
> **Version:** v0.26.0
> **Tests:** 36 (unchanged)

---

## What Shipped Day 35

### 1. Batch Infrastructure — APScheduler + batch_service.py
**Root cause addressed:** Batch jobs (IV seeding, chain cache warm-up) were manual — forgetting them degrades IVR accuracy over time.
**Fix:** APScheduler wired into Flask backend. BOD fires 9:31 AM ET, EOD fires 4:05 PM ET, Mon-Fri, automatically.
**New module:** `batch_service.py` (148 lines) — `seed_iv_for_ticker()`, `run_bod_batch()`, `run_eod_batch()`. Extracted from app.py (536 → 492 lines, partial KI-086 progress).
**Verification:** Scheduler started confirmed in logs. Manual EOD trigger ran successfully (15 tickers, 59.6s, status: ok). batch_run_log SQLite table populated.

### 2. Batch Status Dashboard in Data Provenance
**What:** Two new panels in DataProvenance.jsx — `BatchStatusPanel` (last 10 runs, next BOD/EOD time) + `IVCoverageGrid` (per-ETF: days of history, % of 252, IVR valid, OHLCV rows, chain cache age).
**New endpoint:** `GET /api/admin/batch-status` — recent runs + next scheduled times.
**New endpoint:** `POST /api/admin/warm-cache` — manual BOD trigger.

### 3. MarketData.app Credit Tracking
**What:** `get_oi_volume()` now reads `X-Api-Ratelimit-Remaining` + `X-Api-Ratelimit-Consumed` from response headers and logs them.
**Why:** Enables monitoring actual credit usage before deciding to upgrade from Free to Starter ($12/mo).

### 4. Architecture Decisions Locked
- **Two-arch model confirmed:** Live hours = Alpaca Free + MarketData.app Free + STA. Off-hours = IBKR batch only.
- **MarketData.app Free sufficient:** ~33 credits/day actual usage vs 100 limit. Stay on Free, monitor.
- **Full Greeks at all MD tiers confirmed** via docs scrape — no need for Starter just for field coverage.
- **SCHB not in app** — confirmed 15 ETFs, not 16. Memory corrected.
- **Session skills created:** `/session-start` and `/session-close` as Claude Code project skills.

---

## Open Issues Table

| ID | Severity | Description |
|----|----------|-------------|
| KI-086 | MEDIUM | app.py 492 lines (Rule 4 max 150) — _run_one still inline |
| KI-067 | MEDIUM | QQQ sell_put picks ITM strikes (chain too narrow for ~$658) |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift from gate_engine |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested all 4 directions |
| KI-059 | HIGH-DEFERRED | Single-stock bear untested (ETF-only pivot makes this low priority) |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |

---

## Next Session Priorities

| Priority | Item | Effort |
|----------|------|--------|
| P0 | Verify EOD auto-batch fired at 4:05 PM — check Data Provenance batch log | 5 min |
| P1 | Live market test — run Best Setups, verify batch-warmed chain cache hits | 20 min |
| P2 | MarketData.app support reply — confirm Greeks on Starter (likely already answered by docs) | 5 min |
| P3 | KI-086 — move _run_one to best_setups_service.py (app.py 492→~420) | 45 min |
| P4 | KI-067 — QQQ sell_put ITM strike fix | 30 min |
