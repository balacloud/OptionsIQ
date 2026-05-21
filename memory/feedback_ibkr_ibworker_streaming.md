---
name: feedback-ibkr-ibworker-streaming
description: IBKR reqMktData streaming returns all-nan in IBWorker threading model — use reqHistoricalData instead
metadata:
  type: feedback
---

`reqMktData` with `snapshot=False` (streaming) returns all-nan in the IBWorker threading model, even with:
- Correct tick list (106,411,100,105)
- Active market data subscription
- Market hours confirmed open
- IB Gateway connected (Market Data Farm ON: usfarm)

**Why:** The IBWorker's `_run` loop processes asyncio events only during explicit `ib.sleep()` calls via `loop.run_until_complete()`. Streaming market data (`snapshot=False`) requires a persistent running event loop to receive tick callbacks from IBKR. The 4-6 second `ib.sleep()` window is insufficient — IBKR needs a continuously running event loop to establish and deliver the stream. Even `reqMarketDataType(3)` (delayed, no subscription needed) failed the same way, confirming it's a threading issue not a subscription issue.

**Fix:** Use `reqHistoricalData` instead:
- `whatToShow="OPTION_IMPLIED_VOLATILITY"` → IV (last daily bar)
- `whatToShow="HISTORICAL_VOLATILITY"` → HV (last daily bar)
- Uses Historical Data Farm (ushmds) — confirmed active separately from Market Data Farm
- Request-response pattern works correctly in IBWorker (no persistent event loop needed)
- 7/7 ETFs returned real data in live test (Day 52)

**How to apply:** For any use case needing per-ticker IV/HV from IBKR via IBWorker, prefer `reqHistoricalData` over `reqMktData` streaming. For a better future approach, use `reqScannerSubscription` — one call returns IV/HV + IVR + put/call ratio for entire ETF universe. See [[feedback-ibkr-reqmktdata]] for reqMktData streaming constraints.

**Why:** Discovered Day 52 during live test after confirming subscription exists and market hours confirmed. Even delayed mode (type 3) returned nan. Root cause is IBWorker threading, not IBKR entitlement.
