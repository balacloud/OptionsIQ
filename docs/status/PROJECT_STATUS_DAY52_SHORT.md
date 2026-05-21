# OptionsIQ — Project Status Day 52
> **Date:** May 21, 2026 | **Version:** v0.33.2 | **Tests:** 44

## What Shipped

### Fix: IBKR `get_iv_hv_batch` — reqMktData → reqHistoricalData

**Problem:** Streaming `reqMktData` with `snapshot=False` returned all `nan` for every ETF (bid/ask/last/impliedVol/histVol). Even with correct tick list (106,411,100,105), correct subscription ("US Equity and Options Add-On Streaming Bundle" active), and market hours.

**Root cause:** The IBWorker threading model processes asyncio events only during explicit `ib.sleep()` calls. Streaming market data (`snapshot=False`) requires a persistent event loop to receive tick callbacks. The 6-second sleep window is insufficient for IBKR to establish and deliver the stream. Even `reqMarketDataType(3)` (delayed mode) failed — confirming the issue is threading-level, not subscription-level.

**Fix:** Replaced with `reqHistoricalData` per ticker:
- `whatToShow="OPTION_IMPLIED_VOLATILITY"` → IV from options market (last daily bar)
- `whatToShow="HISTORICAL_VOLATILITY"` → HV computed by IBKR (last daily bar)
- Historical Data Farm (ushmds confirmed ON) uses request-response pattern — works correctly in IBWorker.

**Result:**
- 7/7 ETFs returning real data during market hours
- XLK iv=26.7%/hv=23.7% (ratio 1.13), XLE iv=27.8%/hv=28.6% (ratio 0.97), XLF iv=16.5%/hv=14.3% (ratio 1.16), XLI iv=21.0%/hv=16.9% (ratio 1.25), XLB iv=20.8%/hv=15.9% (ratio 1.31), XLV iv=15.8%/hv=14.5% (ratio 1.09), MDY iv=17.7%/hv=14.5% (ratio 1.22)
- UI watchlist IV/HV column confirmed populated (Image 3 verified)

**File:** `backend/ibkr_provider.py` — `get_iv_hv_batch()` fully rewritten (~55 lines)
**File:** `backend/scanner_service.py` — timeout 35s→90s, docstring updated

---

### Architecture Discussion: IBKR `reqScannerSubscription`

Identified `reqScannerSubscription` as a better long-term approach for the batch:
- One API call returns IV/HV ratio, 52-week IVR, put/call volume for all ETFs in universe
- User's "Options-iq-gemini" scanner shows exactly what's available
- Would replace 14 sequential reqHistoricalData calls with 1-2 scanner calls
- Put/call ratio included for free (current P2 priority)
- Design challenge: scanner returns top N ranked results, not specific tickers — need cross-reference + fallback

Planned as Day 53 P2.

---

## Test Count
44 (unchanged — IBKR batch is data plumbing, not gate logic)

## Open Issues
| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH | Single-stock bear untested — deferred by design (ETF-only mode) |
| KI-099 | LOW | bull_call_spread direction for Leading/Improving + IVR 30–50% |

## Next Session Priorities
1. **P0 — Paper trade logging** — still 0/30. Log next XLF or QQQ CAUTION setup. Cannot calibrate gates without 30-trade sample. ~5 min user action.
2. **P1 — MASTER_AUDIT_FRAMEWORK sweep** — overdue since Day 42 (10 sessions). All 10 categories. Category 10 (Trading Effectiveness) + gate calibration.
3. **P2 — IBKR `reqScannerSubscription`** — replace reqHistoricalData batch with scanner approach. Gets IV/HV + IVR + put/call ratio in 1-2 calls. Plan before implementing.
4. **P3 — KI-099** — bull_call_spread for Leading/Improving ETFs. Plan before touching.
5. **P4 — deferred** — (IBKR subscription no longer needed — reqHistoricalData works on Historical Data Farm)
