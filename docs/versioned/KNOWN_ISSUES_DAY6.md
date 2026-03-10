# OptionsIQ — Known Issues Day 6
> **Last Updated:** Day 6 (March 10, 2026)
> **Previous:** KNOWN_ISSUES_DAY5.md

---

## Resolved This Session (Day 6)

### KI-024: No market hours detection → RESOLVED
**Files:** `backend/ibkr_provider.py`, `backend/data_service.py`, `backend/app.py`, frontend
**Problem:** Outside 9:30am–4:00pm ET Mon-Fri, `reqTickers` returns zero quotes.
theta_burn=999%, liquidity FAIL, position sizing=0. Analysis looked broken.
**Fix:**
- `IBKRProvider._market_is_open()` — ET timezone check, Mon-Fri 9:30-16:00
- `IBKRProvider._get_hv_estimate(ticker)` — 20-day HV from yfinance as IV proxy
- When closed: skip `reqTickers`, compute BS greeks for all qualified contracts
  Returns `market_closed=True` flag on chain dict
- `DataService`: detects `market_closed=True` → returns `"ibkr_closed"` source, skips SQLite cache
- Frontend: amber banner "Market closed — using estimated greeks (Black-Scholes + 20-day HV)"
- Header shows "IB Closed" instead of stale/live
**Also fixed (same commit):**
- `ibkr_provider.py` was missing `import logging` / `logger` — `_struct_cached` was calling undefined `logger.info()`
- Broad retry in `get_options_chain` referenced `all_expiries`, `all_strikes`, `hard_min` from
  `_fetch_structure` scope (undefined in caller). Fixed by returning all 4 values from `_fetch_structure`.

**Behavior after fix:**
- Off-hours: delta/theta/vega are real BS-computed values (not None/999%)
- Liquidity gate still FAILs (OI=0 — expected, no market data when closed)
- Banner clearly informs user this is estimated data for setup review only
- Paper trading disabled path unchanged (gates will block before paper trade possible)

---

## Still Open

### KI-025: Sparse strike qualification for large-cap stocks (NVDA $180+)
**File:** `backend/ibkr_provider.py`
**Problem:** `reqSecDefOptParams` returns theoretical union of strikes. Specific expiries have fewer.
NVDA ITM buy_call window: only 2 contracts qualify on weekends.
**Mitigation:** SMART_MAX_EXPIRIES=2, SMART_MAX_STRIKES=6, broad retry when <3 qualify.
**Status:** Needs weekday market-hours verification. May be sufficient with live data.

### KI-001/KI-023: app.py still 558 lines
**File:** `backend/app.py`
`analyze_service.py` not yet created. Business logic still in app.py.
Target: routes-only ≤150 lines.

### KI-022/KI-005: Synthetic swing defaults silent
No banner when stop/target are fabricated from defaults (not from STA or manual entry).

### KI-008: fomc_days_away manual mode defaults to 30
When STA offline and user doesn't enter FOMC days, hardcoded 30 used silently.

### KI-013: API URL hardcoded in useOptionsData.js
`http://localhost:5051` hardcoded. Low priority for single-user tool.

---

## Summary

| Severity | Count | Resolved (Day 6) | Remaining |
|----------|-------|-----------------|-----------|
| High | 2 | 1 (KI-024) | 1 (KI-025 — verify weekday) |
| Medium | 2 | 0 | 2 (KI-001/023, KI-022/005) |
| Low | 2 | 0 | 2 (KI-008, KI-013) |
| **Total** | **6** | **1** | **5** |
