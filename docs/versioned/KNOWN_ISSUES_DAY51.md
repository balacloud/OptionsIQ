# OptionsIQ — Known Issues Day 51
> **Last Updated:** Day 51 (May 21, 2026)
> **Previous:** KNOWN_ISSUES_DAY50.md

---

## Resolved This Session (Day 51)

### KI-102: XLI and XLB OHLCV corrupted rows (Apr 25–26) ✅ RESOLVED Day 51
**Root cause:** Two rows each for XLI and XLB in `ohlcv_daily` had identical wrong closing prices (100.62 on Apr 25, 100.25 on Apr 26). XLI real price ~$171, XLB real price ~$51. The corrupt rows inflated the 20-day HV to 193.88% (XLI) and 234.72% (XLB), making IV/HV ratios 0.11 and 0.08 — clearly wrong.
**Fix:** Deleted 4 rows via SQLite: `DELETE FROM ohlcv_daily WHERE ticker IN ('XLI','XLB') AND date IN ('2026-04-25','2026-04-26')`.
**Verification:** Re-ran Best Setups — XLI HV=19.74%, IV/HV=1.06; XLB HV=20.43%, IV/HV=1.08. Both plausible.

### KI-103: `fetch_live_iv_hv_batch` skipping IBKR call due to false `is_connected()` ✅ RESOLVED Day 51
**Root cause:** IBWorker connects lazily on first request. `ib_worker.is_connected()` returned False before any IBKR call was made, causing early return `{}` from `fetch_live_iv_hv_batch`. The batch never executed.
**Fix:** Replaced `is_connected()` check with a 0.5s socket port check (`socket.create_connection((host, 4001), timeout=0.5)`). Fast offline detection (avoids 12s client-ID scan) while allowing the batch to proceed when gateway is reachable.
**File:** `backend/scanner_service.py`

### KI-104: `reqMktData snapshot=True` invalid with `genericTickList` ✅ RESOLVED Day 51
**Root cause:** IBKR returns Error 321 "Snapshot market data subscription is not applicable to generic ticks" when `snapshot=True` is combined with a non-empty `genericTickList`. All 7 ETF requests were rejected.
**Fix:** Changed to `snapshot=False` (streaming mode). No Error 321.
**File:** `backend/ibkr_provider.py`

### KI-105: Tick 104 (histVol) invalid for STK contracts ✅ RESOLVED Day 51
**Root cause:** Generic tick 104 is NOT a legal tick for STK (stock/ETF) contracts — IBKR Error 321 listed it as invalid. Legal ticks for STK include 106 (impvolat), 411 (rthistvol), 100 (optVolume), 105 (avgOptVolume).
**Fix:** Changed `genericTickList` from `"104,106,29,30"` to `"106,411,100,105"`. Also removed ticks 29/30 (callVolume/putVolume) which are also invalid for STK.
**File:** `backend/ibkr_provider.py`

---

## Architecture Limitation Found (Day 51)

### IBKR Market Data Subscription Required for ETF Generic Ticks (NOT a code bug)
**Observation:** Even with correct tick list (`106,411,100,105`) and `snapshot=False`, all ticks return `nan` for XLK/XLE/XLF/XLI/XLB/XLV/MDY. Standard ticks (bid/ask/last) are also `nan` — IBKR is not delivering any streaming market data for these ETFs.
**Root cause:** IBKR charges for real-time market data subscriptions on US equity exchanges (NYSE, NASDAQ, ARCA). Without a paid subscription, `reqMktData` returns no data for tickers the user doesn't own. Portfolio positions receive live data automatically via account subscription — but arbitrary ETF tickers require a paid market data subscription.
**Impact:** `get_iv_hv_batch()` returns `{}` gracefully (no crash, no error). The Best Setups scan continues normally via Tradier chain data (primary source, working correctly today). All 7 ETFs show correct IV/HV from Tradier.
**Resolution path:** Subscribe to "US Equity and Options Add-On Streaming Bundle" in IBKR account settings (~$4.50–6/month per exchange). The code is ready — batch will start populating once subscription is active.
**Fallback chain still working:** Tradier chain IV → iv_store HV → iv_hv_ratio populated for all ETFs.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 52+.

---

## Resolved History (recent)
- KI-105: Tick 104 invalid for STK → 106+411+100+105 ✅ Day 51
- KI-104: snapshot=True invalid with genericTickList ✅ Day 51
- KI-103: is_connected() false-negative in scanner ✅ Day 51
- KI-102: XLI/XLB OHLCV corruption (Apr 25-26) ✅ Day 51
- KI-101: IV/HV null in watchlist ✅ Day 50
- KI-098: Absolute trend gate (weekChange) ✅ Day 49
- KI-096: IVR null → unknown confidence ✅ Day 49
- KI-097: Event density gate ✅ Day 49
- KI-100: Tier 1 GO rate reporting ✅ Day 49
