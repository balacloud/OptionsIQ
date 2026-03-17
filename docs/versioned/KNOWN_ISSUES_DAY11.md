# OptionsIQ — Known Issues Day 11
> **Last Updated:** Day 11 (March 13, 2026)
> **Previous:** KNOWN_ISSUES_DAY10.md

---

## Resolved This Session (Day 11)

### KI-037: MarketData.app historical IV/greeks = null → CONFIRMED PLATFORM LIMITATION ✅
**Confirmed:** Support replied March 13, 2026: *"Our historical data does not include IV/greeks
at this time. This is something we hope to add soon."*
**Conclusion:** IBKR is the only source for historical IV under $30/mo. No timeline for MarketData.app to add it.

---

## New Issues Found (Day 11 — System Coherence Audit)

Full audit: `docs/Research/System_Coherence_Audit_Day11.md`

### KI-040: logger undefined in app.py (CRITICAL)
**File:** `backend/app.py` line 42
**Problem:** `logger.info(...)` called before `logger = logging.getLogger(__name__)` is defined.
App crashes on startup when AlpacaProvider init runs.
**Fix:** Add `logger = logging.getLogger(__name__)` after line 29.

### KI-041: QualityBanner checks wrong data_source (CRITICAL)
**File:** `frontend/src/App.jsx` line 39
**Problem:** Frontend checks `source === "ibkr"` but backend sends `"ibkr_live"`.
Banner logic broken — banners may not display correctly.
**Fix:** Change to `source === "ibkr_live"`.

### KI-042: SQLite without WAL mode (CRITICAL)
**Files:** `backend/data_service.py` line 75, `backend/iv_store.py`
**Problem:** No WAL + no timeout. Flask threads hang on concurrent writes from background refresh.
**Fix:** Add `conn.execute("PRAGMA journal_mode=WAL")` + `timeout=5.0`.

### KI-043: reqMktData subscriptions leak on exception (HIGH)
**File:** `backend/ibkr_provider.py` lines 590-623
**Problem:** If exception between reqMktData and cancelMktData, subscriptions never canceled.
IB Gateway accumulates zombie subscriptions over time.
**Fix:** Wrap in try-finally to guarantee cancelMktData cleanup.

### KI-044: API_CONTRACTS.md stale — 5 major mismatches (HIGH)
**File:** `docs/stable/API_CONTRACTS.md`
**Problem:** Verdict structure, gate field names, strategy fields, behavioral_checks, direction_locked
all differ between spec and actual code. Frontend matches code, not spec.
**Fix:** Update API_CONTRACTS.md to match actual implementation.

### KI-045: No outer try-except on /api/options/analyze (MEDIUM)
**File:** `backend/app.py` line 274
**Problem:** Unhandled exception returns HTML 500 instead of JSON.
**Fix:** Wrap in try-except, return structured JSON error.

### KI-046: Bare except blocks with no logging (MEDIUM)
**File:** `backend/app.py` lines 61, 65, 468, 491
**Problem:** Silent failures mask IBKR disconnects, yfinance errors, IV seed failures.

### KI-047: gate_engine.py hardcodes constants (MEDIUM)
**File:** `backend/gate_engine.py`
**Problem:** MIN_OPEN_INTEREST, MIN_VOLUME_OI_RATIO etc. hardcoded instead of importing
from constants.py where they already exist. Violates Golden Rule 3.

### KI-048: Missing "delayed" quality label in frontend (MEDIUM)
**File:** `frontend/src/App.jsx`
**Problem:** Alpaca data_source="alpaca" → quality_label "delayed" — no frontend banner/styling.

### KI-049: account_size hardcoded to 50000 in frontend (LOW)
**File:** `frontend/src/components/PaperTradeBanner.jsx`
**Problem:** Should read from .env ACCOUNT_SIZE=24813.

---

## Still Open (from previous sessions)

### KI-035: OI = 0 fix — pending market-hours verification
genericTickList="101" applied Day 10. Needs live market test.

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)
NVDA buy_put: only 3 contracts qualify.

### KI-001/KI-023: app.py still 558 lines (MEDIUM)
analyze_service.py not yet created.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 30 (LOW)

### KI-013: API URL hardcoded in useOptionsData.js (LOW)

---

## Summary

| Severity | Count | New (Day 11) | Remaining |
|----------|-------|-------------|-----------|
| Critical | 3 | 3 (KI-040, KI-041, KI-042) | 3 |
| High | 2 | 2 (KI-043, KI-044) | 2 |
| Medium | 7 | 3 (KI-045, KI-046, KI-047, KI-048) | 7 |
| Low | 4 | 1 (KI-049) | 4 |
| **Total** | **16** | **10** | **16** |
