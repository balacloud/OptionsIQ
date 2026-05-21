# OptionsIQ — Known Issues Day 52
> **Last Updated:** Day 52 (May 21, 2026)
> **Previous:** KNOWN_ISSUES_DAY51.md

---

## Resolved This Session (Day 52)

### KI-106 (implicit): IBKR `get_iv_hv_batch` streaming approach returns all nan ✅ RESOLVED Day 52
**Root cause:** `reqMktData` with `snapshot=False` (streaming) requires a persistent asyncio event loop to deliver tick callbacks. The IBWorker only processes events during explicit `ib.sleep()` calls — too narrow a window for IBKR to establish the stream. All ticks (bid/ask/last/impliedVol/histVol) returned `nan` even with the correct subscription and tick list. Even `reqMarketDataType(3)` (delayed data) returned `nan`.
**Fix:** Replaced `reqMktData` approach with `reqHistoricalData` using `whatToShow="OPTION_IMPLIED_VOLATILITY"` and `whatToShow="HISTORICAL_VOLATILITY"`. Historical Data Farm (ON: ushmds) is a request-response API that works correctly in the IBWorker threading model. Returns last daily bar — today's intraday reading during market hours.
**Verification:** 7/7 ETFs returned data in live test: XLK iv=26.7%/hv=23.7%, XLE iv=27.8%/hv=28.6%, XLF iv=16.5%/hv=14.3%, XLI iv=21.0%/hv=16.9%, XLB iv=20.8%/hv=15.9%, XLV iv=15.8%/hv=14.5%, MDY iv=17.7%/hv=14.5%. UI watchlist confirmed populated (Image 3).
**File:** `backend/ibkr_provider.py`, `backend/scanner_service.py`

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 53+.

---

## Architecture Note (Day 52)

### IBKR `reqScannerSubscription` — better next approach (not a bug)
The IBKR Market Screener (user's "Options-iq-gemini" scanner) returns via `reqScannerSubscription` API:
- IV/HV ratio (scan metric)
- 52-week IVR
- Put/call volume ratio
- Average option volume
All in one API call vs current 14 sequential `reqHistoricalData` calls.

Design constraint: scanner returns top N from universe (not specific tickers). Need cross-reference with our 15 ETF list + fallback (reqHistoricalData) for ETFs not ranked in top N on quiet days.

Planned for Day 53 as P2.

---

## Resolved History (recent)
- KI-106: IBKR batch streaming all nan → reqHistoricalData ✅ Day 52
- KI-105: Tick 104 invalid for STK → 106+411+100+105 ✅ Day 51
- KI-104: snapshot=True invalid with genericTickList ✅ Day 51
- KI-103: is_connected() false-negative in scanner ✅ Day 51
- KI-102: XLI/XLB OHLCV corruption (Apr 25-26) ✅ Day 51
- KI-101: IV/HV null in watchlist ✅ Day 50
- KI-098: Absolute trend gate (weekChange) ✅ Day 49
- KI-096: IVR null → unknown confidence ✅ Day 49
- KI-097: Event density gate ✅ Day 49
- KI-100: Tier 1 GO rate reporting ✅ Day 49
