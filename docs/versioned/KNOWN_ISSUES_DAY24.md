# OptionsIQ — Known Issues Day 24
> **Last Updated:** Day 24 (April 15, 2026)
> **Previous:** KNOWN_ISSUES_DAY23.md

---

## Resolved This Session (Day 24)

### KI-071: ExecutionCard not wired into App.jsx (HIGH → RESOLVED)
Redesigned ExecutionCard as pure frontend visual guide (IBKR Client Portal steps).
Wired into App.jsx AnalysisPanel after TopThreeCards. CSS added to index.css.
Day 23 TWS staging code reverted (stage_spread_order, POST /api/orders/stage, readonly=False).

### KI-070: stage_spread_order not yet live tested (MEDIUM → RESOLVED — code removed)
Staging approach reverted. User wants visual guide, not TWS API staging.
ibkr_provider.py reverted to readonly=True.

### KI-001/KI-023: app.py still ~750+ lines (MEDIUM → RESOLVED)
Extracted analyze_service.py (604 lines). app.py now 320 lines.
All helpers, data fetchers, payload builders, ETF gate post-processing, and
main orchestrator moved to analyze_service.py.

---

## Still Open

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Lower priority — ETF-only mode means stocks return 400. Deferred.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put direction for QQQ returns ITM put strikes (~$637 vs $624 underlying).
Chain struct_cache issue. Lower priority.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
~5pp gap between L2 percentile and L3 average. Data-specific, low impact.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
ETF-only enforcement, Signal Board, `_etf_payload` fields not documented.
POST /api/orders/stage removed (no longer exists). Needs cleanup.

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 999 (LOW)

### KI-013/KI-050: API URL hardcoded in JS files (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

### KI-072: deepcopy() on every cache hit in data_service.py (LOW)
Originally found Day 11 (E1). `deepcopy()` called on full chain profile on every cache hit.
10-50ms overhead per request. Consider shallow copy or immutability contract.
File: `backend/data_service.py` (lines ~264, 300 at time of finding — verify current line numbers).

### KI-073: _struct_cache grows unbounded in ibkr_provider.py (LOW)
Originally found Day 11 (E2). Dict grows with every new ticker, never trimmed.
File: `backend/ibkr_provider.py`. Fix: LRU eviction (max 50 tickers) or periodic cleanup.

### KI-074: No IBWorker health check at startup (LOW)
Originally found Day 11 (E3). App starts without checking IB Gateway — first request discovers failure.
Fix: Add `_ib_worker.is_connected()` check at startup, log warning if IB Gateway is down.

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059 deferred) |
| Medium | 3 (KI-067, KI-064, KI-044) |
| Low | 8 |
| **Total** | **12** |
| **Resolved Day 24** | **3** (KI-071, KI-070, KI-001/KI-023) |
| **Added Day 25** | **3** (KI-072, KI-073, KI-074 — recovered from Day 11 Phase E deferred) |
