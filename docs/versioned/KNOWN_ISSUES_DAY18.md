# OptionsIQ — Known Issues Day 18
> **Last Updated:** Day 18 (March 23, 2026)
> **Previous:** KNOWN_ISSUES_DAY17.md

---

## Resolved This Session (Day 18)

None — review/planning session, no code changes.

---

## Still Open

### KI-059: buy_put + sell_call directions not live tested end-to-end (HIGH)
Code implemented (Day 7/12). Gate tracks exist (_run_buy_put, _run_sell_call). Strategy builders
exist. Never exercised against real IBKR chain with a live bearish setup. Per Rule 13, no module
is frozen until all 4 directions tested. Requires market hours + IB Gateway.

### KI-044: API_CONTRACTS.md stale (HIGH)
Full spec sync (verdict, gates, strategies, behavioral_checks schemas) still not done.

### KI-001/KI-023: app.py still ~631 lines (MEDIUM)
analyze_service.py not yet created. sta_fetch route alone = 155 lines of embedded business logic.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)
QQQ returns 0 contracts.

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 30 (LOW)

### KI-013/KI-050: API URL hardcoded in JS files (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 2 (KI-059 bear untested, KI-044 API docs) |
| Medium | 3 (KI-001, KI-022, KI-025) |
| Low | 5 |
| **Total** | **10** |
| **Resolved Day 18** | **0** (review/planning session) |
