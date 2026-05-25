# OptionsIQ — Project Status Day 54
> **Date:** May 23, 2026 | **Version:** v0.34.0 | **Tests:** 44

## What Shipped

### P2: reqScannerSubscription — Implemented, Tested Live, Scanner Approach Ruled Out

**Implementation completed across 7 files:**
- `constants.py`: `PUT_CALL_RATIO_BEAR_WARN=1.3`, `PUT_CALL_RATIO_BULL_WARN=0.6`
- `ibkr_provider.py`: `get_scanner_batch()` — two scanner passes (IV/HV + put/call)
- `scanner_service.py`: `fetch_scanner_subscription_batch()` — primary entry point for Best Setups
- `app.py`: import updated, comment updated
- `gate_engine.py`: `_put_call_sentiment_gate()` — non-blocking WARN gate (Gates 7b/11b)
- `analyze_service.py`: `put_call_volume` threaded into `gate_payload`
- `best_setups_service.py`: scanner data injected into payload before `analyze_etf()`

**Live test result — scanner approach ruled out:**
- Tested `HIGH_OPT_IMP_VOLAT_OVER_HIST`, `HIGH_OPT_VOLUME_PUT_CALL_RATIO`, `SCAN_ivRank52w_DESC`
- All returned 0/15 ETFs — even with 15s wait and 5000-row limit
- Root cause: IBKR scanner streams top-50 of ~12,000 US stocks. Sector ETFs (moderate IV) never rank in top 50 of market-wide screens. IBKR hard-limits to ~50 results regardless of `numberOfRows`.
- `SCAN_impVolatOverHist_DESC` confirmed disabled by IBKR

**Final architecture — `fetch_scanner_subscription_batch()` simplified:**
- Removed scanner step (was adding 25s of wasted latency before always falling through)
- Now delegates directly to `fetch_live_iv_hv_batch()` → `get_iv_hv_batch()` (reqHistoricalData)
- IV/HV data: ✅ from reqHistoricalData (working reliably since Day 52)
- Put/call volume: always None (gate gracefully handles missing data as advisory pass)

### Put/Call Sentiment Gate (Gates 7b / 11b)
- Added as non-blocking advisory to `_run_etf_sell_put()` and `_run_etf_sell_call()`
- >1.3 = heavy put buying (bearish crowd WARN), <0.6 = aggressive calls (complacency WARN)
- When data is None: "pass / advisory only" — never blocks a trade
- Data path exists; put/call values will populate if data source added later (e.g., Tradier chain compute)

---

## Test Count
44 (unchanged — P2 implementation is data-path infrastructure, no new unit test targets)

## Open Issues
| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH | Single-stock bear untested — deferred by design (ETF-only mode) |
| KI-099 | LOW | bull_call_spread direction for Leading/Improving + IVR 30–50% |

## Next Session Priorities
1. **P0 — Paper trade logging** — still 0/30. Log next XLF or QQQ CAUTION setup. Cannot calibrate gates without 30-trade sample. ~5 min user action.
2. **P1 — MASTER_AUDIT_FRAMEWORK sweep** — overdue since Day 42 (12 sessions). All 10 categories.
3. **P2 done — put/call data future option**: Compute from Tradier options chain (sum call volume / sum put volume across near-term expiry). ~30 lines in tradier_provider.py. Lower priority than audit sweep.
4. **P3 — KI-099** — bull_call_spread for Leading/Improving ETFs. Plan before touching.
