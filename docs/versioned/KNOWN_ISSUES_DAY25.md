# OptionsIQ — Known Issues Day 25
> **Last Updated:** Day 25 (April 17, 2026)
> **Previous:** KNOWN_ISSUES_DAY24.md

---

## Resolved This Session (Day 25)

No backend bugs fixed this session. Day 25 was a pure frontend UX overhaul (Phase 8 — Options Explainer / Learn tab). All backend issues carry forward unchanged.

---

## New Issues This Session (Day 25)

### KI-075: GateExplainer GATE_KB may drift from gate_engine.py logic (MEDIUM)
**Component:** `frontend/src/components/GateExplainer.jsx`
**Description:** GATE_KB has hardcoded plain English pass/fail answers for 12 gate IDs. If backend gate thresholds or logic changes (e.g., IVR threshold moves from 50% to 60%), the frontend answers go stale without any compile-time warning. A beginner reading a stale "Yes, IV is expensive enough" answer for a trade they shouldn't take is misleading.
**Fix path:** Run Category 9 audit after any gate_engine.py change. Consider adding a GATE_KB_VERSION constant to force manual sync review.
**Audit trigger:** Category 9 — Frontend UX Accuracy

### KI-076: TradeExplainer isBearish() not live-tested against all 4 directions (MEDIUM)
**Component:** `frontend/src/components/TradeExplainer.jsx`
**Description:** `isBearish()` determines which side of the number line is green (profit) vs red (loss). Current classification: `['bear_call_spread', 'sell_call', 'buy_put', 'itm_put', 'atm_put']`. If any strategy_type is misclassified, profit and loss zones are shown with inverted colors — critical mislead for a beginner.
Not yet live-tested with real analysis results across all 4 directions. Needs market-open smoke test.
**Fix path:** Test all 4 directions with live XLF analysis. Verify green zone is always the correct side.
**Audit trigger:** Category 9 — Frontend UX Accuracy

### KI-077: DirectionGuide "Risk: Spread width (capped)" for sell_put may be misleading (LOW)
**Component:** `frontend/src/components/DirectionGuide.jsx`
**Description:** DirectionGuide shows "Risk: Spread width (capped)" for sell_put, but strategy_ranker can return a naked sell_put (rank 1 = naked, ranks 2/3 = spread variations). A beginner reading the DirectionGuide card before analysis may assume their sell_put will always be a spread with capped risk, then be surprised to see a naked warning on the result.
**Fix path:** Change sell_put risk label to "Risk: May be naked (see recommendation for details)" or similar. Or ensure strategy_ranker always returns a spread for sell_put.
**Audit trigger:** Category 9 — Frontend UX Accuracy

---

## Still Open (Carried Forward)

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Lower priority — ETF-only mode means stocks return 400. Deferred indefinitely.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put direction for QQQ returns ITM put strikes (~$637 vs $624 underlying).
Chain struct_cache issue. Day 25: still open.

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
10-50ms overhead per request. File: `backend/data_service.py`.

### KI-073: _struct_cache grows unbounded in ibkr_provider.py (LOW)
Dict grows with every new ticker, never trimmed.

### KI-074: No IBWorker health check at startup (LOW)
App starts without checking IB Gateway — first request discovers failure.

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059 deferred) |
| Medium | 5 (KI-067, KI-064, KI-044, KI-075, KI-076) |
| Low | 9 (KI-038, KI-034, KI-008, KI-013/050, KI-049, KI-072, KI-073, KI-074, KI-077) |
| **Total** | **15** |
| **Resolved Day 25** | **0** (pure frontend UX session) |
| **Added Day 25** | **3** (KI-075, KI-076, KI-077) |
