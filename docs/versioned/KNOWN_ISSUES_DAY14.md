# OptionsIQ — Known Issues Day 14
> **Last Updated:** Day 14 (March 19, 2026)
> **Previous:** KNOWN_ISSUES_DAY13.md

---

## New This Session (Day 14)

### KI-050: API URL hardcoded in useSectorData.js (LOW)
Same pattern as KI-013 — `http://localhost:5051` hardcoded in new hook.

---

## Still Open

### KI-044: API_CONTRACTS.md stale — 5+ mismatches vs code (HIGH)
Now includes 2 new sector endpoints not yet in spec.

### KI-001/KI-023: app.py still ~620 lines (MEDIUM)
`analyze_service.py` not yet created. Added ~20 lines for sector routes.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 30 (LOW)

### KI-013: API URL hardcoded in useOptionsData.js (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

### KI-050: API URL hardcoded in useSectorData.js (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-044) |
| Medium | 3 |
| Low | 5 |
| **Total** | **9** |
