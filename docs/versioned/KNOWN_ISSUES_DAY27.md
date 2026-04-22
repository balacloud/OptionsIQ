# OptionsIQ — Known Issues Day 27
> **Last Updated:** Day 27 (April 21, 2026)
> **Previous:** KNOWN_ISSUES_DAY25.md (Day 26 did not create a new file)

---

## Resolved This Session (Day 27)

### KI-008: fomc_days_away defaults to 999 when STA offline ✅ RESOLVED Day 26
`_days_until_next_fomc()` in analyze_service.py now used as fallback. Resolved Day 26 — carried forward incorrectly in KNOWN_ISSUES_DAY25.md.

### KI-078: FOMC calendar had wrong dates (P0) ✅ RESOLVED Day 27
**Root cause:** `constants.py` had `2026-05-06` as next FOMC date — not a real FOMC date. The actual meeting is April 28–29 (announcement April 29). Gate calculated ~15 days → passed. Correct answer: 8 days → WARN.
Also fixed: June 17 → June 18, November 4 → November 5.
Caught by ChatGPT stress test on a live XLY sell_put trade — real-world validation of the pre-trade research workflow.

---

## New Issues This Session (Day 27)

### KI-079: No ETF holdings earnings gate (HIGH)
**Component:** `backend/gate_engine.py` — events gate, ETF mode
**Description:** For ETF sell_put trades, the events gate checks `earnings_days_away` which is always 999 for ETFs (they have no earnings). It never checks if major holdings are reporting inside the DTE window. For XLY: TSLA (18.22%) reports April 22, AMZN (25.52%) reports April 29 — together 44% concentration. Both inside a 31-DTE window. Gate passed. ChatGPT caught this as the most dangerous risk in the XLY trade.
**Impact:** Events gate gives a false pass on ETFs with concentrated earnings risk. Any ETF with a top-3 holding reporting inside DTE is silently approved.
**Fix path:** Add a hardcoded `ETF_KEY_EARNINGS` lookup dict in constants.py with top 3 holdings + earnings dates per ETF (quarterly update). Gate checks if any key holding reports before expiry date. FMP REST API could automate this in Phase 10.
**Audit trigger:** Category 1 (Gate Logic), Category 5 (Behavioral Claims)

### KI-080: Liquidity gate does not hard-fail on extreme bid-ask spread (MEDIUM)
**Component:** `backend/gate_engine.py` — liquidity gate
**Description:** For the XLY trade, the top strategy had a 27.52% bid-ask spread. This indicates severely illiquid or bad data — delta was -0.045 for an essentially ATM put (should be ~-0.45). The liquidity gate may warn on wide spreads but does not hard-fail. A strategy built on a 27% spread is not actionable — the fill would be at best 13% away from mid.
**Fix path:** Add a hard-fail threshold in constants.py: if `atm_spread_pct > 20%`, liquidity gate FAILs (not just warns). Current threshold review needed.
**Audit trigger:** Category 1 (Gate Logic)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)
**Component:** `backend/gate_engine.py` — events gate
**Description:** Only FOMC is tracked. CPI (May 12 in the XLY trade), NFP, PCE, and other major macro releases are not in the events gate. These can spike sector ETF IV significantly around release dates.
**Fix path:** Add a macro events calendar to constants.py (similar to FOMC_DATES). Low urgency — FOMC is the most market-moving event for ETFs.

---

## Still Open (Carried Forward)

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
ETF-only mode means stocks return 400. Deferred indefinitely.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put direction for QQQ returns ITM put strikes (~$637 vs $624 underlying).
Chain struct_cache issue. Still open.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
~5pp gap between L2 percentile and L3 average. Data-specific, low impact.

### KI-044: API_CONTRACTS.md partially stale (MEDIUM)
ETF-only enforcement documented Day 27. OI supplement documented. Some ETF fields still not documented. Lower priority after Day 27 updates.

### KI-075: GateExplainer GATE_KB may drift from gate_engine.py logic (MEDIUM)
GATE_KB has hardcoded plain English pass/fail answers. If gate thresholds change, frontend answers go stale silently.

### KI-076: TradeExplainer isBearish() not live-tested against all 4 directions (MEDIUM)
`isBearish()` determines profit/loss zone colors. Not yet verified live for all 4 directions.

### KI-038: Alpaca OI/volume fields missing (LOW)
### KI-034: OHLCV temporal gap not validated (LOW)
### KI-013/KI-050: API URL hardcoded in JS files (LOW)
### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)
### KI-072: deepcopy() on every cache hit in data_service.py (LOW)
### KI-073: _struct_cache grows unbounded in ibkr_provider.py (LOW)
### KI-074: No IBWorker health check at startup (LOW)
### KI-077: DirectionGuide "Risk: Spread width (capped)" for sell_put may mislead (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 2 (KI-059 deferred, KI-079 new) |
| Medium | 6 (KI-067, KI-064, KI-044, KI-075, KI-076, KI-080) |
| Low | 9 (KI-038, KI-034, KI-013/050, KI-049, KI-072, KI-073, KI-074, KI-077, KI-081) |
| **Total** | **17** |
| **Resolved Day 27** | **2** (KI-008 backfilled, KI-078 FOMC dates fixed) |
| **Added Day 27** | **3** (KI-079, KI-080, KI-081) |
