# OptionsIQ — System Coherence Audit (Day 11)

> **Date:** March 13, 2026
> **Scope:** End-to-end coherence: frontend↔backend fields, provider consistency, error handling, performance, documentation accuracy
> **Method:** 4 parallel audit streams — backend API, frontend mapping, provider data, error/perf
> **Status:** Findings documented. Execution deferred to next session.

---

## Audit Summary

| Severity | Count | Category |
|----------|-------|----------|
| **CRITICAL** | 6 | Blocks startup, breaks UI, or causes silent data corruption |
| **HIGH** | 8 | API contract mismatches, field inconsistencies between modules |
| **MEDIUM** | 14 | Error handling gaps, performance, concurrency risks |
| **LOW** | 19 | Documentation drift, cosmetic, minor redundancy |

---

## Phase A — CRITICAL FIXES (do first, ~30 min)

### A1: `logger` undefined at module level
- **File:** `backend/app.py` line 42
- **Bug:** `logger.info(...)` called before `logger = logging.getLogger(__name__)` is defined
- **Impact:** App crashes on startup when AlpacaProvider init runs
- **Fix:** Add `logger = logging.getLogger(__name__)` after line 29

### A2: No outer try-except on `/api/options/analyze`
- **File:** `backend/app.py` line 274
- **Bug:** Any unhandled exception returns HTML 500 instead of JSON
- **Impact:** Frontend sees blank page instead of structured error
- **Fix:** Wrap route body in try-except, return `jsonify({"error": str(e)}), 500`

### A3: QualityBanner checks wrong data_source value
- **File:** `frontend/src/App.jsx` line 39
- **Bug:** Frontend checks `source === "ibkr"` but backend sends `"ibkr_live"`
- **Impact:** Quality banner logic is broken — banners may not display correctly
- **Fix:** Change to `source === "ibkr_live"`

### A4: SQLite without WAL mode
- **Files:** `backend/data_service.py` line 75, `backend/iv_store.py`
- **Bug:** No WAL + no timeout = Flask threads hang on concurrent writes from background refresh
- **Impact:** Flask threads can block indefinitely during cache writes
- **Fix:** Add `conn.execute("PRAGMA journal_mode=WAL")` + `timeout=5.0` in `_conn()`

### A5: Bare except blocks with no logging
- **File:** `backend/app.py` lines 61, 65, 468, 491
- **Bug:** Silent failures mask IBKR disconnects, yfinance errors, IV seed failures
- **Impact:** Impossible to debug production issues — no log trail
- **Fix:** Add `logger.warning(...)` to every bare except

### A6: Missing `"delayed"` quality label in frontend
- **File:** `frontend/src/App.jsx`
- **Bug:** Alpaca returns `data_source="alpaca"` → quality_label `"delayed"` — frontend has no banner for this
- **Impact:** No banner shown when using Alpaca fallback data
- **Fix:** Add `"delayed"` case to QualityBanner and Header sourceLabel map

---

## Phase B — API CONTRACT ALIGNMENT (~1 hr)

### B1: Verdict structure mismatch
- **Spec (API_CONTRACTS.md):** `pass/warn/fail/total`
- **Code (gate_engine.py):** `gates_passed/gates_total/status`
- **Frontend:** Uses `color/score_label/headline` (matches code, not spec)
- **Action:** Update API_CONTRACTS.md to match reality — spec is stale

### B2: Gate field names differ from spec
- **Spec:** `value/detail`
- **Code:** `computed_value/reason`
- **Frontend:** Uses `computed_value/reason` (matches code)
- **Action:** Update API_CONTRACTS.md

### B3: Strategy response has 25+ undocumented fields
- **Spec:** Shows 11 fields
- **Code returns:** `premium_per_lot`, `breakeven`, `max_gain_per_lot`, `why`, `warning`, etc.
- **Action:** Update API_CONTRACTS.md to document all fields

### B4: `behavioral_checks` not in API spec
- **Backend returns it, frontend renders it, spec doesn't mention it**
- **Action:** Add to API_CONTRACTS.md

### B5: `direction_locked` undocumented and incomplete
- **Backend:** Only locks on BUY signal, not SELL
- **Frontend:** Does its own locking locally (works independently)
- **Action:** Document in spec. Add SELL signal logic to backend.

---

## Phase C — PROVIDER DATA CONSISTENCY (~45 min)

### C1: Alpaca volume always 0
- **Impact:** vol/OI ratio gate always fails. Strategy cards show volume=0.
- **Action:** Consider: if data_source="alpaca", mark vol/OI gate as "unavailable" instead of failing with 0.

### C2: `bs_greeks` flag only from IBKR
- **Impact:** Frontend can't show "estimated greeks" banner for yfinance/Alpaca BS-computed greeks
- **Action:** Either all providers set flag, or remove it entirely

### C3: None vs 0 inconsistency across providers
- **IBKR/Alpaca:** Return `None` for missing greeks
- **yfinance:** Fills via BS (never None)
- **Mock:** Never None
- **Action:** Define contract: "None = truly unavailable, 0.0 = measured as zero"

### C4: `market_closed` flag only from IBKR
- **Impact:** Other providers can't signal off-hours data
- **Action:** Low priority — other providers are inherently delayed

### C5: gate_engine.py hardcodes constants
- **Issue:** `MIN_OPEN_INTEREST=1000`, `MIN_VOLUME_OI_RATIO=0.10`, etc. hardcoded instead of importing from constants.py where they already exist
- **Action:** Import from constants.py (violates Golden Rule 3)

---

## Phase D — ERROR HANDLING & ROBUSTNESS (~45 min)

### D1: reqMktData subscriptions leak on exception
- **File:** `backend/ibkr_provider.py` lines 590-623
- **Bug:** If exception between reqMktData and cancelMktData, subscriptions never canceled
- **Impact:** IB Gateway accumulates zombie subscriptions, depleting slots
- **Fix:** Wrap in try-finally to guarantee cancelMktData cleanup

### D2: No ticker validation
- **File:** `backend/app.py` line 277
- **Bug:** Empty ticker silently defaults to "AME" — frontend never gets an error
- **Fix:** Validate: non-empty, alphanumeric, 1-5 chars. Return 400 if invalid.

### D3: PnL calculator crashes on missing keys
- **File:** `backend/pnl_calculator.py` lines 71-99
- **Bug:** `strategy["strike"]` with no `.get()` — KeyError if strategy malformed
- **Fix:** Change to `strategy.get("strike", 0.0)` with guard

### D4: IVR data coercion too aggressive
- **File:** `backend/app.py` line 328
- **Bug:** `{k: (0.0 if v is None else v)}` coerces boolean `fallback_used` to 0.0
- **Fix:** Use explicit field extraction with proper types

### D5: STA fetch swallows all exceptions
- **File:** `backend/app.py` line 491
- **Bug:** Network errors, JSON parse, timeouts all become "offline" with no logging
- **Fix:** Log the actual exception before returning offline status

### D6: Cache JSON decode failure silent
- **File:** `backend/data_service.py` line 175
- **Bug:** Malformed cache JSON silently returns None — no log
- **Fix:** Add `logger.warning("Cache decode error for %s", key)`

---

## Phase E — PERFORMANCE & OPERATIONAL (~30 min)

### E1: `deepcopy()` on every cache hit
- **File:** `backend/data_service.py` lines 264, 300
- **Issue:** 10-50ms overhead per request for full profile chains
- **Fix:** Consider shallow copy or document immutability contract

### E2: `_struct_cache` grows unbounded
- **File:** `backend/ibkr_provider.py` line 78
- **Issue:** Dict grows with every new ticker, never trimmed
- **Fix:** Add LRU eviction (max 50 tickers) or periodic cleanup

### E3: No IBWorker health check at startup
- **File:** `backend/app.py` lines 38-51
- **Issue:** App starts without checking IB Gateway — first request discovers failure
- **Fix:** Add `_ib_worker.is_connected()` check at startup, log warning if down

### E4: Circuit breaker race condition
- **File:** `backend/data_service.py` lines 267-281
- **Issue:** Two threads can pass `_cb_allowed()` simultaneously — counter increments twice
- **Impact:** Low — CB opens slightly too aggressively but self-corrects after cooldown

### E5: `account_size` hardcoded in frontend
- **File:** `frontend/src/components/PaperTradeBanner.jsx`
- **Issue:** Uses hardcoded `50000` instead of reading from backend `.env` ACCOUNT_SIZE=24813
- **Fix:** Read from backend response or add to /api/health response

---

## Phase F — DOCUMENTATION SYNC (~20 min)

### F1: API_CONTRACTS.md stale
- Verdict, gates, strategies, behavioral_checks all differ from actual code
- Frontend matches code, not spec — spec needs update

### F2: Alpaca limitations undocumented in cascade
- No OI, no volume — should be noted in provider hierarchy docs

### F3: Swing field synthesis defaults undocumented
- 3% pullback, 8% stop — not in any doc or constants.py

### F4: `"delayed"` missing from documented quality labels

### F5: Paper trade response schema undocumented

---

## Recommended Execution Order

```
Next Session — Phase A first:
  A1-A6: Critical fixes (~30 min)
  D1-D6: Error handling (~45 min)

Following Session:
  B1-B5: API contract sync (~1 hr, mostly doc updates)
  C1-C5: Provider consistency (~45 min)

Then:
  E1-E5: Performance (~30 min)
  F1-F5: Documentation (~20 min)
```

**Phase A is non-negotiable** — A1 (logger crash) and A3 (QualityBanner mismatch) are bugs in the current codebase.

---

## Behavioral Audit (Deferred — Next Session After Phase A)

After fixing the critical issues above, run a behavioral audit using the structured
audit prompt to verify that what the system actually accomplishes matches what we intend
to build. This covers:
- Does each gate actually enforce what it claims to enforce?
- Do strategies match the documented direction behavior?
- Does the frontend accurately represent the backend's analysis?
- Are the Golden Rules actually enforced in code, or only in documentation?

The behavioral audit prompt is saved in CLAUDE_CONTEXT.md under Next Session Priorities.
