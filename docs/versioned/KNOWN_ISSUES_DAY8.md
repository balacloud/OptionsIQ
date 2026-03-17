# OptionsIQ — Known Issues Day 8
> **Last Updated:** Day 8 (March 11, 2026)
> **Previous:** KNOWN_ISSUES_DAY7.md

---

## Resolved This Session (Day 8)

None — process-only session. No code changes.

---

## Still Open

### KI-026: reqMktData live greeks unverified (HIGH — Day 9 P0)
**File:** `backend/ibkr_provider.py`
reqTickers→reqMktData change was made (Day 7) but not yet tested during market hours with IB Gateway live.
Must confirm `greeks_pct > 0` and `delta != 0.0` from IBKR (not Phase 4e BS fallback).
**Test:** Run AMD analyze 9:30am–4:00pm ET. Check log for "Phase 4e" message — if it appears,
reqMktData still not getting greeks and needs further investigation.

### KI-025: Sparse strike qualification for large-cap stocks (NVDA $180+)
**File:** `backend/ibkr_provider.py`
NVDA ITM buy_call window: only 2 contracts qualify on weekends.
Broad retry mitigates but weekday live verification still needed.

### KI-001/KI-023: app.py still 558 lines
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

| Severity | Count | Resolved (Day 8) | Remaining |
|----------|-------|-----------------|-----------|
| High | 2 | 0 | 2 (KI-026 verify, KI-025 verify) |
| Medium | 2 | 0 | 2 (KI-001/023, KI-022/005) |
| Low | 2 | 0 | 2 (KI-008, KI-013) |
| **Total** | **6** | **0** | **6** |
