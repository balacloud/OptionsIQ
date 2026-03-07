# OptionsIQ — Known Issues Day 4
> **Last Updated:** Day 4 (March 7, 2026)
> **Previous:** KNOWN_ISSUES_DAY3.md

---

## Resolved This Session (Day 4)

### KI-016: IBWorker queue poisoning → RESOLVED
**Fix:** `_Request` now stores `expires_at = time.monotonic() + timeout`.
Worker discards expired requests (logs warning, puts TimeoutError in result_q, continues).
Submit() timeout and worker expiry now use the same `timeout` value — synchronized.

### KI-017: No ib.RequestTimeout set → RESOLVED
**Fix:** `self.ib.RequestTimeout = 15` set before each `reqTickers` batch in `ibkr_provider.py`.
Restored to 0 in `finally` block. Prevents indefinite blocking on IBKR pacing or bad data.

### KI-018: Dual circuit breakers → RESOLVED
**Fix:** All legacy CB code removed from `app.py`:
`_ib_chain_failures`, `_ib_chain_open_until`, `_ib_chain_lock`, `_ib_chain_allowed()`,
`_ib_chain_record()`, `_get_chain_with_timeout()`, `_fetch_chain_with_retry()`,
`_provider_pair()`, `_load_ibkr_provider()`, `_chain_cache` (in-memory dict),
`_cache_chain_set()`, `_cache_chain_get()`, `_refresh_chain_async()`, `_warm_cache_startup()`,
`_build_partial_chain_from_ib()`.
DataService circuit breaker is now the single authoritative CB. app.py: 821 → 527 lines.

### KI-020: strategy_ranker returns right=None → RESOLVED (Day 3/4)
**Fix:** Added `"right": c.get("right")` to `_build_long_call` and
`"right": long_leg.get("right")` to `_build_spread` in `strategy_ranker.py`.

### Ticker override bug (not in KI list) → RESOLVED
**File:** `frontend/src/App.jsx`
**Fix:** Moved `ticker` after `...swing` spread to prevent stale STA `ticker` from
shadowing current input: `{ direction, ...swing, ticker: ticker.toUpperCase() }`.

### STA offline detection bug (not in KI list) → RESOLVED
**File:** `frontend/src/components/SwingImportStrip.jsx`
**Fix:** `if (json && !json.error)` → `if (json?.status === 'ok')`.
Offline response `{ status: "offline", message: "..." }` now correctly stays in Manual mode.

---

## Still Open

### KI-001: app.py God Object → PARTIALLY RESOLVED
**Status:** app.py 821 → 527 lines (legacy CB removed, debug endpoints cleaned up).
Still needs `analyze_service.py` extraction — business logic helpers remain in app.py.
**Remaining:** Create `analyze_service.py`. Extract `_merge_swing`, `_extract_iv_data`,
`_behavioral_checks`, gate assembly. app.py → ≤150 lines routes-only.
**Phase:** 5 (Day 5 P1)

### KI-003: mock_provider.py still partially hardcoded AME structure
**Status:** No change. yfinance covers fallback adequately.
**Phase:** Backlog

### KI-005: _merge_swing() uses synthetic defaults silently → OPEN
**Status:** Empty-string crash fixed (Day 3). But when STA doesn't have SR levels
(e.g. illiquid ticker like MEOH), backend silently uses `stop = underlying × 0.92` etc.
User sees P&L table with fabricated levels — no warning shown.
**Remaining:** Show "Using synthetic defaults" banner when swing fields were null from STA.
**Phase:** 5

### KI-008: fomc_days_away not auto-computed → PARTIALLY RESOLVED
**Status:** Constants.py has FOMC dates. Defaults to 30 if not provided. STA fetch provides
actual value when connected. Auto-compute in analyze_service.py still deferred.
**Phase:** 5

### KI-013: API URL hardcoded in useOptionsData.js → OPEN
**Phase:** Backlog

### KI-019: No IBWorker connection heartbeat → OPEN
**File:** `backend/ib_worker.py`
**Problem:** Silent TCP drops (NAT timeout, network blip) not detected.
`is_connected()` checks flag only; stale connection appears alive but hangs on next submit.
**Fix:** Worker sends `ib.reqCurrentTime()` every 30s when idle. `is_connected()` also
checks heartbeat timestamp freshness (max 60s gap = disconnected).
**Phase:** 5

---

## New Issues Found Day 4

### KI-022: Synthetic swing defaults not surfaced to user
**File:** `backend/app.py` (`_merge_swing`) + `frontend/src/App.jsx`
**Problem:** When STA doesn't have SR levels for a ticker (MEOH, illiquid stocks), the backend
silently computes synthetic stop/target/entry from underlying × constant. The user sees the P&L
table but has no indication the levels are fabricated, not real STA data.
**Impact:** User may evaluate P&L scenarios as real analysis when they are synthetic.
**Fix:** Return `"swing_data_quality": "synthetic"` in response when key fields were defaulted.
Frontend shows amber banner: "Swing levels estimated — enter actual stop/target for accurate P&L."
**Phase:** 5
**Status:** OPEN

### KI-023: app.py still exceeds 150-line target
**File:** `backend/app.py`
**Problem:** app.py is 527 lines after legacy CB removal. Target is ≤150 lines (routes only).
Business logic (`_merge_swing`, `_extract_iv_data`, `_behavioral_checks`) still in app.py.
**Fix:** Create `analyze_service.py` — extract all business logic.
**Phase:** 5 (Day 5 P1)
**Status:** OPEN

---

## Summary

| Severity | Count | Resolved (Day 4) | Remaining |
|----------|-------|-----------------|-----------|
| Critical | 1 | 1 (KI-018) | 0 |
| High | 3 | 2 (KI-016, KI-017) | 1 (KI-001 partial) |
| Medium | 4 | 1 (KI-020) | 3 |
| Low | 2 | 0 | 2 |
| Bug fixes | 2 | 2 (ticker, STA offline) | 0 |
| New Day 4 | 2 | 0 | 2 (KI-022, KI-023) |
| **Total** | **14** | **6** | **8** |
