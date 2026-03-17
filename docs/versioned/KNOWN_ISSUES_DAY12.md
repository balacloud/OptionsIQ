# OptionsIQ — Known Issues Day 12
> **Last Updated:** Day 12 (March 17, 2026)
> **Previous:** KNOWN_ISSUES_DAY11.md

---

## Resolved This Session (Day 12)

### KI-040: logger undefined in app.py → RESOLVED ✅
Added `logger = logging.getLogger(__name__)` after `logging.basicConfig()`. Startup no longer crashes.

### KI-041: QualityBanner checks wrong data_source → RESOLVED ✅
Fixed `source === "ibkr"` → `source === "ibkr_live"` in App.jsx. Live banner now fires correctly.

### KI-042: SQLite without WAL mode → RESOLVED ✅
Added `timeout=5.0` and `conn.execute("PRAGMA journal_mode=WAL")` to `data_service.py _conn()`.

### KI-043: reqMktData subscriptions leak on exception → RESOLVED ✅
Wrapped reqMktData subscription block in try-finally in `ibkr_provider.py`. All subs guaranteed to cancel.

### KI-045: No outer try-except on /api/options/analyze → RESOLVED ✅
Refactored into thin validator + `_analyze_options_inner()`. All unhandled exceptions return structured JSON.

### KI-046: Bare except blocks with no logging → RESOLVED ✅
Added `as exc` + `logger.warning(...)` to all silent except blocks in `_get_live_price`, `seed_iv`, `sta_fetch`, SPY regime fetch.

### KI-047: gate_engine.py hardcodes constants → RESOLVED ✅
Added 40-line import block from constants.py. Replaced 60+ hardcoded thresholds.
19 new constants added to constants.py (IV abs fallback, DTE signal quality, SPY regime per direction).

### KI-048: Missing quality banners for alpaca/ibkr_stale → RESOLVED ✅
Added `ibkr_stale` and `alpaca` banner cases to App.jsx. Added `alpaca` label to Header.jsx sourceLabel map.

### KI-035: OI = 0 — CONFIRMED PLATFORM LIMITATION ✅
**Finding:** `genericTickList="101"` does NOT deliver per-contract OI via reqMktData.
Volume IS available (live test: Vol > 0). OI is simply not available from IBKR via this method.
**Resolution:** Graceful degradation in `_liquidity_gate()`:
- OI=0 with Vol>0 → WARN only (not block)
- `spread_fail_block` (spread > 15%) is the only hard liquidity block
- Gate shows `OI 0 [OI unavailable], Vol/OI N/A` in result

### sell_put naked warning missing → RESOLVED ✅
All 3 sell_put strategy cards now show `warning: "NAKED PUT — max loss = strike × 100. Cash-secured margin required."`

### ACCOUNT_SIZE silent default → RESOLVED ✅
Added startup guard: `if not os.getenv("ACCOUNT_SIZE"): raise RuntimeError("ACCOUNT_SIZE not set in .env")`

---

## Still Open

### KI-044: API_CONTRACTS.md stale — 5 major mismatches (HIGH)
**File:** `docs/stable/API_CONTRACTS.md`
**Problem:** Verdict structure, gate field names, strategy fields, behavioral_checks, direction_locked
all differ between spec and actual code. Frontend matches code, not spec.
**Fix:** Update API_CONTRACTS.md to match actual implementation. (Phase B deferred)

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)
NVDA buy_put: only 3 contracts qualify.

### KI-001/KI-023: app.py still ~600 lines (MEDIUM)
`analyze_service.py` not yet created.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)
No banner when swing fields are null and defaults are synthesized.

### KI-038: Alpaca OI/volume fields missing (LOW)
Alpaca model does not expose OI or volume. Permanent platform limitation.

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 30 (LOW)

### KI-013: API URL hardcoded in useOptionsData.js (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

---

## Open Investigation

### OI via IBKR alternative methods
`reqMktData` tick type 101 does not deliver per-contract OI. Potential alternatives:
- `reqContractDetails` — no OI
- `reqFundamentalData` — no OI
- `reqHistoricalData` whatToShow=OPTION_VOLUME — daily volume only
**Status:** Graceful degradation is permanent solution. OI verify manually before trading.

---

## Summary

| Severity | Count | Resolved (Day 12) | Remaining |
|----------|-------|-------------------|-----------|
| Critical | 3 | 3 (KI-040, KI-041, KI-042) | 0 |
| High | 2 | 1 (KI-043) | 1 (KI-044) |
| Medium | 7 | 4 (KI-045, KI-046, KI-047, KI-048) + KI-035 graceful | 3 |
| Low | 4 | 0 | 4 |
| Additional | 2 | 2 (sell_put warning, ACCOUNT_SIZE guard) | 0 |
| **Total** | **18** | **10** | **8** |
