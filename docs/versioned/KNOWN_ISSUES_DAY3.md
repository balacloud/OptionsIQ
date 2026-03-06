# OptionsIQ — Known Issues Day 3
> **Last Updated:** Day 3 (March 6, 2026)
> **Previous:** KNOWN_ISSUES_DAY1.md

---

## Resolved This Session (Day 3)

### KI-002: In-memory chain cache lost on restart → RESOLVED
**Fix:** `data_service.py` uses SQLite at `backend/data/chain_cache.db`. 2-min TTL, survives restarts.

### KI-006: No yfinance middle tier → RESOLVED
**Fix:** `yfinance_provider.py` created — tier 3 in provider cascade.

### KI-007: QUICK_ANALYZE_MODE silently uses mock HV20 → RESOLVED
**Fix:** QUICK_ANALYZE_MODE removed from app.py. Always uses real HV20 from iv_store.

### KI-009: No constants.py — magic numbers everywhere → RESOLVED
**Fix:** `constants.py` created with all thresholds, DTE limits, direction-aware strike windows.

### KI-010: reqTickers in ThreadPoolExecutor per request → RESOLVED
**Fix:** `ib_worker.py` — single IBWorker thread, all IBKR calls via submit().

### KI-011: No Black-Scholes fallback for missing Greeks → RESOLVED
**Fix:** `bs_calculator.py` created. `yfinance_provider.py` calls fill_missing_greeks().

### KI-014: ibkr_provider.py market_data_type defaults to 3 → RESOLVED
**Fix:** `market_data_type = 1` hardcoded in IBKRProvider.__init__().

### KI-015: /api/integrate/sta-fetch/{ticker} endpoint missing → RESOLVED
**Fix:** `GET /api/integrate/sta-fetch/<ticker>` implemented in app.py.

---

## Still Open

### KI-001: app.py God Object → PARTIALLY RESOLVED / STILL OPEN
**Status:** DataService wired in. data_svc.get_chain() used for chain fetch.
But app.py still ~820 lines — legacy circuit breaker, helpers, and analyze logic not yet extracted.
**Remaining:** Create analyze_service.py. Remove legacy CB code. Reduce to ≤150 lines.
**Phase:** 3 (Phase 4 for routes-only refactor)

### KI-003: mock_provider.py ignores ticker → PARTIALLY RESOLVED
**Status:** Dynamic pricing added (yfinance underlying if available). Structure still uses
AME contract shapes. Low impact now that yfinance is the real fallback.
**Phase:** 5 (backlog)

### KI-004: Partial chain fallback uses AME greeks → RESOLVED (removed)
**Status:** `_build_partial_chain_from_ib()` still exists but is dead code since DataService
handles fallback properly. Should be deleted in Phase 4 cleanup.

### KI-005: _merge_swing() fabricates missing fields silently → PARTIALLY RESOLVED
**Status:** Empty-string fields now handled safely by `_f()` / `_i()` helpers (no crashes).
But defaults are still synthetic (e.g., stop_loss = underlying × 0.92 with no warning).
**Remaining:** Add validation in analyze_service.py — warn when using synthetic defaults.

### KI-008: fomc_days_away never computed → PARTIALLY RESOLVED
**Status:** FOMC dates hardcoded in constants.py (2026-2027). Defaults to 30 if not provided.
STA integration computes actual days when connected.
**Remaining:** Auto-compute from constants.FOMC_DATES in analyze_service.py.

### KI-012: DTE max hardcoded inconsistently → RESOLVED
**Fix:** constants.py has SMART/FULL DTE windows. ibkr_provider._fetch_structure() respects
direction sweet spot (buyers 45-90, sellers 21-45) then falls back to global window.

### KI-013: API URL hardcoded in useOptionsData.js → OPEN
**Phase:** 5

---

## New Issues Found Day 3

### KI-016: IBWorker queue poisoning
**File:** `backend/ib_worker.py`
**Problem:** When `submit(fn, timeout=24s)` times out on Flask side, the worker continues executing `fn`.
Next requests queue behind the still-running call. Each request waits for all previous to complete.
**Example:** 3 simultaneous AMD requests = first runs 30s, second waits 30s + 30s = 60s, third waits 90s.
**Fix:** Add `expires_at` to `_Request`. Worker discards expired requests before executing.
**See:** `docs/stable/CONCURRENCY_ARCHITECTURE.md` — Problem 1
**Phase:** 4 (P1 — must fix before paper trading)
**Status:** OPEN

### KI-017: No ib_insync RequestTimeout set
**File:** `backend/ibkr_provider.py`
**Problem:** `ib.RequestTimeout = 0` (unlimited). If IBKR pacing kicks in or bad data returned,
`reqTickers` blocks indefinitely inside the worker thread.
**Fix:** Set `self.ib.RequestTimeout = timeout_sec` around reqTickers calls.
**See:** `docs/stable/CONCURRENCY_ARCHITECTURE.md` — Problem 3
**Phase:** 4 (P1 — must fix before paper trading)
**Status:** OPEN

### KI-018: Dual circuit breakers
**File:** `backend/app.py` (legacy) + `backend/data_service.py`
**Problem:** Two independent circuit breakers track IBKR failures. They can diverge —
one open, one closed — causing inconsistent behavior.
**Fix:** Remove `_ib_chain_failures`, `_ib_chain_open_until`, `_ib_chain_lock`,
`_ib_chain_allowed()`, `_ib_chain_record()` from app.py. DataService CB is authoritative.
**Phase:** 4
**Status:** OPEN

### KI-019: No IBWorker connection heartbeat
**File:** `backend/ib_worker.py`
**Problem:** `is_connected()` checks `ib.isConnected()` flag only. Silent TCP drops
(NAT timeout, network blip) don't trigger disconnect events — connection appears alive but hangs.
**Fix:** Worker sends `ib.reqCurrentTime()` every 30s when idle. `is_connected()` also checks
heartbeat timestamp freshness.
**See:** `docs/stable/CONCURRENCY_ARCHITECTURE.md` — Problem 4
**Phase:** 4
**Status:** OPEN

### KI-020: strategy_ranker returns right=None in top_strategies
**File:** `backend/strategy_ranker.py`
**Problem:** `top_strategies` from `/api/options/analyze` shows `"right": null` for strategies.
This indicates the ranker is not setting the `right` field (C/P) in its output dict.
**Impact:** Frontend cannot show "CALL" / "PUT" label correctly.
**Phase:** 4 — investigation needed
**Status:** OPEN

### KI-021: Pre-market: 0% quote completion
**File:** `backend/ibkr_provider.py`
**Problem:** During pre-market (before 9:30am ET), IBKR options quotes return bid=0/ask=0.
`get_options_chain` correctly records None for bid/ask but `quote_complete_pct = 0%`.
**Note:** This is EXPECTED behavior — options don't have live quotes before market open.
Not a bug, but the UI should show a "Market closed — greeks only" banner.
**Phase:** 5 (UX improvement)
**Status:** KNOWN / LOW PRIORITY

---

## Summary

| Severity | Count | Resolved (Day 3) | Remaining |
|----------|-------|-----------------|-----------|
| Critical | 5 | 4 (KI-002, 006, 010, 014) | 1 (KI-001 partial) |
| High | 4 | 3 (KI-007, 009, 015) | 1 (KI-005 partial) |
| Medium | 4 | 2 (KI-008 partial, KI-012) | 2 remaining |
| Low | 2 | 0 | 2 |
| New Day 3 | 6 | 0 | 6 |
| **Total** | **21** | **9** | **12** |
