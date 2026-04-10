# OptionsIQ — Known Issues Day 21
> **Last Updated:** Day 21 (April 9, 2026)
> **Previous:** KNOWN_ISSUES_DAY20.md

---

## Resolved This Session (Day 21)

### pnl_calculator TypeError on ETF analyze (HIGH → RESOLVED)
`_etf_payload()` sets `stop_loss=None`. `swing_data.get("stop_loss", default)` returns `None`
(key exists with None value — Python's dict.get default doesn't replace existing None).
Fix: `pnl_calculator.py` detects `swing_data_quality == "etf"` → uses price-relative scenarios
(`-10%` to `+15%` of current price) instead of swing-based targets. Stock mode uses
`float(x) if x is not None else fallback` pattern to guard all 4 swing fields.

### IBKR clientId conflict on backend restart (MEDIUM → RESOLVED)
Old backend process (PID 74987/75819) continued listening on port 5051 after code edits.
IBWorker was silently blocked from connecting (clientId=101 already in use).
Fix: `kill <old_pid>` before restart. IBWorker lazy-connects on first chain request;
health endpoint shows `ibkr_connected: false` until first analyze call triggers connection.

### React crash when STA offline on startup (MEDIUM → RESOLVED)
`useEffect` in `App.jsx` called `sectorHook.scanSectors()` without `.catch(() => {})`.
When STA is offline, the unhandled promise rejection crashed the React app.
Fix: `.catch(() => {})` added to `useEffect` call. `scanner-sta-offline` panel shows
"Retry" button for graceful offline state.

---

## Still Open

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Sector ETF all 4 directions now tested ✅ (buy_call, sell_call, buy_put, sell_put on XLU).
Single-stock buy_put and sell_call still need market-hours live test with a bearish stock.
ETF-only pivot (Day 21) makes this lower priority — stocks are no longer accepted by the API.
**Status:** Lower priority — ETF-only mode means stocks return 400.

### KI-067: QQQ chain too narrow for current price (MEDIUM)
QQQ underlying at ~$480 (Day 21, market down ~15% from Day 20's $563.79).
Chain width issue may be self-resolving as price dropped. Needs re-test at next market open.
Root cause: direction-aware fetch window for sell_call (-2% to +8%) may not reach OTM strikes.
**Fix needed:** Test QQQ sell_call with live backend at market open.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
L2 sector analyze shows IVR 97% (ATM contract IV → iv_store percentile).
L3 gate analysis shows IVR 21% (average of all contracts' impliedVol).
Different aggregation methods produce different values.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
ETF-only enforcement (`is_etf`, `direction_locked: []`, `etf_universe` 400 response),
Signal Board changes, `_etf_payload` fields not documented.

### KI-001/KI-023: app.py still ~660+ lines (MEDIUM)
analyze_service.py not yet created. ETF pivot added more code this session.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM — lower priority post ETF pivot)
ETF mode uses `_etf_payload()` with explicit None fields + `swing_data_quality: "etf"`.
Still an issue for any remaining stock-related code paths.

### KI-025: QQQ sparse strikes (MEDIUM — related to KI-067)

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 999 (LOW — changed from 30 in ETF pivot)

### KI-013/KI-050: API URL hardcoded in JS files (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059, lower priority post-ETF pivot) |
| Medium | 5 (KI-067, KI-064, KI-044, KI-001, KI-022) |
| Low | 5 |
| **Total** | **11** |
| **Resolved Day 21** | **3** (pnl TypeError, IBKR clientId conflict, React crash on STA offline) |
