# OptionsIQ — Known Issues Day 17
> **Last Updated:** Day 17 (March 22, 2026)
> **Previous:** KNOWN_ISSUES_DAY16.md

---

## Resolved This Session (Day 17)

### KI-060: spy_5day_return None → 0.0 silent coercion in all 4 gate tracks (HIGH — FIXED)
All 4 SPY regime gate blocks in gate_engine.py read `float(p.get("spy_5day_return", 0.0) or 0.0)`.
When STA is offline, spy_5day_return is None — coerced to 0.0, gate treated it as "SPY flat this week"
and potentially passed when it should have flagged data as unavailable.
Fix: all 4 blocks now check `spy_5d_raw = p.get("spy_5day_return")` for None first.
If None → non-blocking "warn" gate: "SPY regime unavailable — verify STA connection".

### KI-061: iv_store.py IVR formula unverified (HIGH — CLOSED, VERIFIED CORRECT)
Formula confirmed: `count(hist_iv ≤ current_iv) / total × 100` (percentile, not range-based).
IVR 100% = current IV exceeds all 252 days of history. IVR 0% = cheapest IV in a year.
Correct thresholds in constants.py: IVR_BUYER_PASS=30%, IVR_SELLER_PASS=50%.

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
| **Resolved Day 17** | **2** (KI-060 SPY None masking, KI-061 IVR formula verified) |
