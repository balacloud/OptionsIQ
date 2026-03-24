# OptionsIQ — Known Issues Day 19
> **Last Updated:** Day 19 (March 24, 2026)
> **Previous:** KNOWN_ISSUES_DAY18.md

---

## Resolved This Session (Day 19)

### KI-062: ETF earnings_days_away defaulted to 45 (HIGH → RESOLVED)
`_merge_swing` in app.py defaulted `earnings_days_away` to 45 when None. ETFs don't have earnings.
Fix: default changed to None. Gate's `int(p.get("earnings_days_away", 999) or 999)` handles None→999→PASS correctly.

### KI-063: SPY regime fabricated defaults (HIGH → RESOLVED)
`spy_above_200sma` defaulted to True, `spy_5day_return` to 0.0 in `_merge_swing` when not in payload.
Fix: created `_fetch_spy_regime()` helper that calls STA's `_spy_regime()` with 2-min TTL cache.
SPY 5d return unit mismatch also fixed: STA returns percentage (-1.23), gates expect decimal (-0.0123).

### KI-065: Deep Dive bear_call_spread → buy_call mismatch (HIGH → RESOLVED)
Frontend `SECTOR_DIR_TO_CORE` in App.jsx was missing `bear_call_spread` mapping → defaulted to `buy_call`.
User clicking Deep Dive on a bearish ETF got bullish gate analysis. Fix: added `bear_call_spread: 'sell_call'`.

### KI-066: DTE Selection gate false FAIL for ETFs (MEDIUM → RESOLVED)
Buy_call track DTE gate depends on VCP/ADX which ETFs don't have → always `rec None` → FAIL.
Fix: ETF post-processing in app.py auto-passes DTE gate when failure is due to missing VCP (same pattern as pivot_confirm).

### L2 None→buy_call bug (MEDIUM → RESOLVED)
Pre-existing bug in `analyze_sector_etf()` where `raw_dir or "buy_call"` caused SKIP ETFs to silently fetch buy_call chain.
Fix: DIRECTION_TO_CHAIN_DIR mapping; None direction → skip chain fetch entirely.

---

## Still Open

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Sector ETF bear directions (bear_call_spread/sell_call) now tested ✅.
Single-stock buy_put and sell_call still need market-hours live test with a bearish stock.
Partially addressed: sell_call track gates verified working on XLV (ibkr_stale data).

### KI-064: IVR mismatch between L2 and L3 (MEDIUM — NEW)
L2 sector analyze shows IVR 97.22% (ATM contract IV → iv_store percentile).
L3 gate analysis shows IVR 21.43 (average of all contracts' impliedVol).
Different aggregation methods produce different values. Needs investigation to align.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
Sector scan `market_regime` field, `bear_call_spread` direction, `ivr_bear_warning` not documented.
Partially updated this session (market_regime added).

### KI-001/KI-023: app.py still ~650 lines (MEDIUM)
analyze_service.py not yet created. Added more code this session (SPY regime helpers, ETF post-processing).

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
| High | 1 (KI-059 single-stock bear) |
| Medium | 5 (KI-064, KI-044, KI-001, KI-022, KI-025) |
| Low | 5 |
| **Total** | **11** |
| **Resolved Day 19** | **5** (KI-062, KI-063, KI-065, KI-066, L2 None→buy_call) |
