# OptionsIQ — Known Issues Day 1
> **Last Updated:** Day 1 (March 5, 2026)
> **Source:** Codex build audit (full code review of all 9 source files)

---

## Critical — Blocks All Paper Trading

### KI-001: app.py God Object (768 lines)
**File:** `backend/app.py`
**Problem:** Contains caching, circuit breaker, chain fetch, IV extraction, P&L assembly, paper trades, integration — all in one file. Impossible to test or maintain.
**Fix:** Split into `data_service.py` + `analyze_service.py`. app.py routes only, ≤150 lines.
**Phase:** 1 (constants) → 3 (analyze_service) → 4 (app.py refactor)
**Status:** OPEN

### KI-002: In-memory chain cache lost on restart
**File:** `backend/app.py` (CHAIN_CACHE dict)
**Problem:** Every restart fetches fresh chain. During dev/paper trading, this wastes the 2-min IBKR pacing window.
**Fix:** Persistent SQLite cache in `backend/data/cache.db` via `data_service.py`
**Phase:** 2
**Status:** OPEN

### KI-003: mock_provider.py ignores ticker — always returns AME data
**File:** `backend/mock_provider.py`
**Problem:** `MockProvider.get_chain(ticker)` uses hardcoded AME prices regardless of `ticker` param. Any non-AME ticker in mock mode gets nonsensical recommendations.
**Fix:** Dynamic pricing — use yfinance for underlying if available, else $100 default. Generate synthetic chain around actual underlying price.
**Phase:** 1
**Status:** OPEN

### KI-004: Partial chain returns AME greeks for any ticker
**File:** `backend/app.py` (_ibkr_partial workaround)
**Problem:** When IBKR returns partial results, the fallback uses hardcoded AME greek values for whichever fields are missing.
**Fix:** Remove the partial fill-in. Return `data_quality: "partial"` with whatever IBKR returned. Compute missing greeks via bs_calculator.py.
**Phase:** 2
**Status:** OPEN

---

## High — Causes Silent Wrong Behavior

### KI-005: _merge_swing() fabricates missing fields silently
**File:** `backend/app.py`
**Problem:** If request body is missing `stop_loss`, `target1`, etc., the function fills them with synthetic values derived from current price. No warning is shown. User thinks they analyzed real data.
**Fix:** Strict validation in `analyze_service.py`. If required swing field is missing: 400 error with clear message listing which fields are missing.
**Phase:** 3
**Status:** OPEN

### KI-006: No yfinance middle tier
**File:** `backend/` (missing `yfinance_provider.py`)
**Problem:** IBKR failure → immediate fall to AME mock. No real data fallback.
**Fix:** Add `yfinance_provider.py` as tier 3. Underlying price + chain structure from yfinance, greeks computed via bs_calculator.py.
**Phase:** 2
**Status:** OPEN

### KI-007: QUICK_ANALYZE_MODE silently uses mock HV20
**File:** `backend/app.py`
**Problem:** When `QUICK_ANALYZE_MODE=True`, HV20 is a hardcoded constant (not computed from real price history). Gate 2 (HV/IV ratio) becomes meaningless.
**Fix:** Remove QUICK_ANALYZE_MODE entirely. Always use real HV20 from iv_store.compute_hv().
**Phase:** 1
**Status:** OPEN

---

## Medium — Degrades Analysis Quality

### KI-008: fomc_days_away defaults to 30 — never computed
**File:** `backend/app.py`
**Problem:** `fomc_days_away` used in Gate 5 is hardcoded to 30 throughout the codebase. Gate 5 always passes with this value (30 days = safe). FOMC risk never triggers.
**Fix:** Copy FOMC 2026-2027 calendar to `constants.py`. Compute actual days in `analyze_service.py`. Pull from STA `/api/context/SPY` when connected.
**Phase:** 1 (constants) + 3 (analyze_service)
**Status:** OPEN

### KI-009: No constants.py — magic numbers everywhere
**File:** All backend files
**Problem:** Gate thresholds, DTE limits, strike windows, and IB timeouts are inline literals in multiple files. Changing one threshold requires finding all occurrences.
**Fix:** `constants.py` with all values. All other files import from it.
**Phase:** 1
**Status:** OPEN

### KI-010: reqTickers called in ThreadPoolExecutor per request
**File:** `backend/ibkr_provider.py`
**Problem:** Each Flask request spins a new ThreadPoolExecutor and calls reqTickers inside it. ib_insync is not thread-safe for multiple simultaneous IB() connections. Causes the 12s timeout issue.
**Fix:** Single `IBWorker` dedicated thread. All IBKR requests go through request/result queues.
**Phase:** 2
**Status:** OPEN

### KI-011: No Black-Scholes fallback for missing Greeks
**File:** `backend/ibkr_provider.py`
**Problem:** When `modelGreeks` is None (which happens even with live subscription for thin contracts), all greek-dependent gates fail or produce `None` errors.
**Fix:** `bs_calculator.py` — compute delta, gamma, theta, vega, price from S, K, T, r, sigma.
**Phase:** 1
**Status:** OPEN

---

## Low — Cosmetic / Minor

### KI-012: DTE max hardcoded at 90/120 inconsistently
**File:** `backend/app.py`, `backend/strategy_ranker.py`
**Problem:** Smart profile uses DTE max 120, full profile uses 90 — backwards from intended behavior.
**Fix:** Respect user's DTE window (14-120) consistently. smart/full only affects number of expiries and strike width, not DTE max.
**Phase:** 3
**Status:** OPEN

### KI-013: API URL hardcoded in useOptionsData.js
**File:** `frontend/src/hooks/useOptionsData.js` (line 3)
**Problem:** `const API = 'http://localhost:5051'` — not configurable.
**Fix:** Read from `process.env.REACT_APP_API_URL` with `localhost:5051` as fallback.
**Phase:** 5
**Status:** OPEN

---

## Summary

| Severity | Count | Resolved |
|----------|-------|---------|
| Critical | 4 | 0 |
| High | 3 | 0 |
| Medium | 4 | 0 |
| Low | 2 | 0 |
| **Total** | **13** | **0** |
