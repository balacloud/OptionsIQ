# OptionsIQ — Project Status Day 55
> **Date:** May 25, 2026 | **Version:** v0.34.0 | **Tests:** 44

## What Happened (Architectural Research Session — No Code Changes)

### reqScannerSubscription P2 — Final Architecture Confirmed
Live test results from Day 54 reviewed:
- All 3 scanner codes returned 0/15 ETFs: `HIGH_OPT_IMP_VOLAT_OVER_HIST`, `HIGH_OPT_VOLUME_PUT_CALL_RATIO`, `SCAN_ivRank52w_DESC`
- Root cause confirmed: IBKR scanner hard-limited to ~50 server-side results. Sector ETFs (moderate IV) never rank in top-50 of market-wide screens.
- `fetch_scanner_subscription_batch()` correctly simplified to delegate directly to `get_iv_hv_batch()` (reqHistoricalData).

### Data Gap Inventory (complete)

| Gap | Source | Effort | Priority |
|-----|--------|--------|----------|
| SMA20/50/200 + RSI(14) + momentum | STA priceHistory (260 bars, already fetched) | ~50 lines sta_service.py | P2 next session |
| Put/call volume ratio | Tradier options chain (per-contract volume, sum) | ~30 lines tradier_provider.py | P3 |
| Skew gate wiring | compute_skew() already exists in tradier_provider.py | ~10 lines gate_engine.py | P4 |
| Paper trade win rate | Manual user action | 0 code — user logs trades | P0 (structural) |
| OI accurate data | Platform limitation | Cannot fix | Permanent WARN |

### STA priceHistory Confirmed Available
- STA `/api/stock/{ticker}` returns `priceHistory` (260 daily OHLCV bars)
- Pattern already exists in `sector_scan_service._spy_regime()` — computes 200 SMA from SPY priceHistory
- Zero new HTTP calls needed: same call already made for spot price returns all chart data
- Live computation confirmed: XLF 2/3 SMAs (below 200 SMA), XLK/QQQ/IWM/XLE/XLY all 3/3

### Gate Calibration Assessment
- 7 blocking gates for sell_put — cannot determine if over-gated without empirical data
- All planned additions (SMA trend, put/call, skew) are advisory WARN only — not blocking
- Need 30-trade paper trade sample before tuning any blocking gate
- System may be conservative but this is intentional without calibration data

---

## Test Count
44 (unchanged — no code changes Day 55)

## Open Issues
| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH | Single-stock bear untested — deferred by design (ETF-only mode) |
| KI-099 | LOW | bull_call_spread direction for Leading/Improving + IVR 30–50% |
| GAP-001 | MEDIUM | STA priceHistory unused for chart trend gate (planned P2 Day 56) |
| GAP-002 | LOW | compute_skew() computed but gate_engine ignores it entirely |
| GAP-003 | LOW | put/call sentiment gate exists but no data source |

## Next Session Priorities
1. **P0 — Paper trade logging** — still 0/30. Log next XLF or QQQ CAUTION setup. Cannot calibrate gates without 30-trade sample. ~5 min user action.
2. **P1 — MASTER_AUDIT_FRAMEWORK sweep** — overdue since Day 42 (13 sessions). All 10 categories.
3. **P2 — STA SMA batch** — `fetch_etf_sma_batch(tickers)` in sta_service.py. STA priceHistory → SMA20/50/200 + RSI(14). Wire through analyze_service → gate_engine `_chart_trend_gate()` (non-blocking WARN). ~50 lines. Most dangerous data gap: can recommend sell_put during confirmed downtrend.
4. **P3 — Tradier put/call ratio** — `compute_put_call_ratio()` in tradier_provider.py (~30 lines). Fills Gate 7b/11b.
5. **P4 — Wire skew** — compute_skew() exists in tradier_provider.py, gate_engine has 0 references. ~10 lines to add advisory WARN.
