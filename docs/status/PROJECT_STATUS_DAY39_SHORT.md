# OptionsIQ — Project Status Day 39 (Short)
> **v0.28.0** — May 5, 2026 | Tests: 36 | Next: Day 40

---

## What Shipped

### 1. Tradier as primary live chain source (ARCH CHANGE)
- `backend/tradier_provider.py` — new provider: real-time REST option chains with greeks, OI, bid/ask, OHLCV. Uses `smv_vol` as primary IV (smoothed surface vol). 165 lines.
- `backend/data_service.py` — IBKR live removed from `get_chain()` cascade. New order: BOD cache → Tradier → stale cache → Alpaca → yfinance → Mock
- `backend/app.py` — `TradierProvider` initialized from `TRADIER_KEY` env var, passed to DataService
- **Backup:** `backend/data_service.py.pre_tradier_primary` — full restore with one `cp` command
- **Arch doc:** `docs/stable/ARCH_DECISION_TRADIER_PRIMARY.md` — rationale, old cascade, revert instructions
- **Result:** IB Gateway now only needed for EOD batch (4:05 PM ET IV seeding). Live analysis runs without IBKR.

### 2. KI-086 resolved — best_setups_service.py extracted
- `backend/best_setups_service.py` — new file (80 lines) containing `run_one_setup()`, extracted from inline `_run_one` closure in app.py
- app.py: 497 → 449 lines (still above Rule 4 limit of 150, but meaningful progress)
- Root cause: `_run_one` captured 10 module-level globals; refactored to explicit dependency injection

### 3. KI-067 resolved — QQQ sell_put ITM strike fix
- `backend/ibkr_provider.py` `_fetch_structure()`: added OTM-only filter (`strike <= underlying`) before descending sort for sell_put direction. Prevents ITM strikes filling the 12-strike cap.
- `backend/strategy_ranker.py` `_rank_sell_put_spread()`: changed fallback from "use all puts" to `return []`. Prevents ITM spreads from slip through even if chain has no OTM puts.

### 4. Manual BOD/EOD triggers with idempotency (from Day 38/39)
- DataProvenance.jsx: `ManualBatchTriggers` component — mounts, checks today's runs from `/api/admin/batch-status`, shows "already ran" status. Two-click confirm pattern if re-running same day.
- `backend/batch_service.py`: `_ran_on()` now requires `duration_sec >= 1.0` (sub-1s = cache-hit no-op, doesn't count). Startup catchup delay: 10s → 30s.

### 5. Startup catchup + time display fixes (from Day 38/39)
- `batch_service.py`: `_ran_on(min_duration=1.0)` — ignores sub-1s BOD runs (IBKR not connected, cache hit)
- `DataProvenance.jsx` `fmtTime()`: fixed EDT/EST confusion — now always shows "ET" (timeZone: 'America/New_York' + ' ET' suffix)

---

## Tests
36 passing. No new tests added this session (Tradier provider not unit-tested — live-tested manually).

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-090 | HIGH | Tradier `delta=0.0` coerced to None — deep OTM contracts get wrong delta score |
| KI-091 | HIGH | Tradier strike window not direction-aware — will reproduce KI-067 for Tradier-sourced chains |
| KI-092 | MEDIUM | `"ibkr_cache"` label misleading when BOD cache is Tradier-sourced |
| KI-093 | MEDIUM | `analyze_service.py:680` iv_provider breaks for `data_source="tradier"` |
| KI-059 | HIGH (deferred) | Single-stock bear untested |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB drift risk |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |

---

## Day 40 Priorities (Opus-ordered)

| # | Priority | Task | Effort |
|---|----------|------|--------|
| P0 | BLOCKING | Fix KI-090 + KI-091 — Tradier delta coercion + direction-aware strike window | 30 min |
| P1 | BLOCKING | End-to-end smoke test — IB Gateway OFF, Best Setups scan, confirm data_source=tradier, real deltas, strikes ≤ underlying | 30 min |
| P2 | BLOCKING | Fix KI-092 + KI-093 — data_source label drift (`ibkr_cache` → `bod_cache`), iv_provider tradier mapping | 45 min |
| P3 | NICE | Update DataFlowDiagram SVG in DataProvenance.jsx — IBKR demoted to EOD only | 20 min |
| P4 | NICE | FOMC 2026 dates audit in constants.py + Tradier startup health ping | 15 min |
