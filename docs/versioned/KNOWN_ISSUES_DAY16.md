# OptionsIQ — Known Issues Day 16
> **Last Updated:** Day 16 (March 20, 2026)
> **Previous:** KNOWN_ISSUES_DAY15.md

---

## Resolved This Session (Day 16)

### KI-SPY-REGIME: SPY regime returning all null from yfinance rate limit (HIGH — FIXED)
`_spy_regime()` in `sector_scan_service.py` called `yfinance.Ticker("SPY").history(period="1y")` repeatedly during testing → `Too Many Requests` error → all three fields returned `None` → SPY regime gate always missing. Fix: replaced yfinance with `requests.get(STA_BASE_URL/api/stock/SPY)` → reads `priceHistory` list (260 daily bars), computes `closes[-1]`, `mean(closes[-200:])`, `closes[-6]` for 5-day return. No rate limit (local HTTP). API_CONTRACTS.md updated.

---

## Still Open

### KI-044: API_CONTRACTS.md stale — 5+ mismatches vs code (HIGH)
Sector endpoints added Day 15, SPY regime rows updated Day 16, but duplicate old yfinance rows still on lines 366-367. Full sync (verdict, gates, strategies, behavioral_checks schema) still not done.

### KI-058: Duplicate yfinance rows in API_CONTRACTS.md (LOW)
Lines 366-367 still have old yfinance entries for `spy_above_200sma` and `spy_5day_return`. These are now superseded by STA rows added Day 16 but the old rows were not cleaned up.

### KI-059: buy_put + sell_call directions not live tested end-to-end (MEDIUM)
`buy_call` and `sell_put` are verified live. `sell_call` (bear_call_spread strategy) and `buy_put` (ITM put + bear put spread) have been code-implemented (Day 7/12) but never exercised against a real bearish setup with live IBKR chain. Per Rule 13, no module is frozen until all 4 directions are tested.

### KI-001/KI-023: app.py still ~600 lines (MEDIUM)
`analyze_service.py` not yet created. Added ~20 lines for sector routes.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)
QQQ returns 0 contracts on buy_call (8-20% ITM window too narrow for $587 stock). sell_call ATM ±6% also returns 0.

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
| Medium | 4 (KI-059 new, KI-001, KI-022, KI-025) |
| Low | 6 |
| **Total** | **11** |
| **Resolved Day 16** | **1** (SPY regime yfinance → STA) |
