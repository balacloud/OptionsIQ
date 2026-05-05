# OptionsIQ — Known Issues Day 39
> **Last Updated:** Day 39 (May 5, 2026)
> **Previous:** KNOWN_ISSUES_DAY38.md

---

## Resolved This Session (Day 39)

### ✅ KI-086: app.py size violation (497 lines, Rule 4 max = 150) — RESOLVED Day 39
Root cause: `_run_one` closure (57 lines) was inline in `best_setups()` route, capturing 10 globals.
Fix: Extracted to `best_setups_service.py` as `run_one_setup()` with explicit dependency injection.
app.py: 497 → 449 lines. Verified: 36 tests pass.

### ✅ KI-067: QQQ sell_put returns ITM strikes — RESOLVED Day 39
Root cause (dual):
1. `ibkr_provider._fetch_structure()`: SELL_PUT_STRIKE_HIGH_PCT=0.02 buffer allowed ITM strikes into window; descending sort + SMART_MAX_STRIKES=12 cap filled all 12 slots with $481-$489 ITM puts for QQQ at $480.
2. `strategy_ranker._rank_sell_put_spread()` line 285: fallback `otm_puts = sorted(puts, ...)` used ALL puts including ITM when `otm_puts` was empty.
Fix: (1) Added `window_strikes = [s for s in window_strikes if s <= underlying]` in ibkr_provider before sell_put descending sort. (2) Changed fallback to `return []`.
Verified: 36 tests pass. Tradier path has same vulnerability — tracked as KI-091 for Day 40 fix.

---

## New Issues This Session (Day 39) — from Opus review

### KI-090: Tradier delta=0.0 coerced to None (HIGH)
`tradier_provider.py` lines 189-192: `_f(g.get("delta")) or None` converts `0.0` (legitimate deep-OTM delta) to `None`. strategy_ranker `_closest_delta()` treats None as `abs(0.0)=0`, making deep-OTM contracts appear to perfectly match delta=0.30 target.
Same problem for gamma, theta, vega, impliedVol.
Fix: Use `float(g["delta"]) if g.get("delta") is not None else None` — keep None only when key is truly absent.

### KI-091: Tradier strike window not direction-aware — will re-trigger KI-067 (HIGH)
`tradier_provider.get_options_chain()` uses symmetric ±10% window regardless of direction. The KI-067 fix in `ibkr_provider` (OTM filter for sell_put) does not apply to Tradier-sourced chains. First Tradier-sourced QQQ sell_put will likely return ITM strikes.
Fix: Apply direction-aware filtering in `tradier_provider` — at minimum, filter `strike <= underlying` for sell_put before the proximity sort, and `strike >= underlying` for sell_call.

### KI-092: `data_source="ibkr_cache"` label misleading for Tradier-sourced BOD cache (MEDIUM)
`run_bod_batch()` calls `data_svc.get_chain()`, which now goes to Tradier first. The result is stored in SQLite. On next analysis call, cache hit returns `("ibkr_cache", chain)` even though data came from Tradier. Affects DataProvenance UI (shows IBKR when it's Tradier), `data_health_service.py:124-139`, and `analyze_service.py:680`.
Fix: Rename `"ibkr_cache"` → `"bod_cache"` in `_cache_get` return paths, or stamp chain dict with `provenance.original_source` at write time.

### KI-093: `analyze_service.py:680` iv_provider breaks for `data_source="tradier"` (MEDIUM)
`iv_provider` selection falls through to `mock_provider` when `data_source == "tradier"`. This is mostly harmless (current_iv is read from `chain.contracts[].impliedVol`), but the logic is wrong and could cause subtle bugs if `_extract_iv_data` path changes.
Fix: Add explicit `"tradier"` branch mapping to the same live-provider logic used for ibkr_cache, or make iv_provider selection data-source-agnostic.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)

### KI-076: TradeExplainer isBearish() not live-tested (LOW)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

---

## Resolved History (recent)
- KI-086: app.py `_run_one` extraction ✅ Day 39
- KI-067: QQQ sell_put ITM strike fix ✅ Day 39
- APScheduler missed jobs (startup gap) ✅ Day 37 — run_startup_catchup() daemon thread
- yfinance HV in iv_history contamination ✅ Day 37 — removed from IV seeding pipeline
- KI-088: L3 stale banner ✅ Day 34
