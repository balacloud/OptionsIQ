# OptionsIQ — Data Gaps & STA SMA Architecture (Day 55)
> **Date:** May 25, 2026 | **Session Type:** Architectural Research (no code changes)
> **Rule 19:** Architectural findings must be documented before next session.

---

## Context

Day 55 was a planning session after P2 (reqScannerSubscription) was conclusively ruled out. The goal was to audit all data gaps and identify the highest-leverage fix with minimal new HTTP calls or external dependencies.

---

## reqScannerSubscription: Final Verdict

Live test confirmed (Day 54, IB Gateway connected):

| Scan Code | Result |
|-----------|--------|
| HIGH_OPT_IMP_VOLAT_OVER_HIST | 0/15 ETFs (CEPO, FLTR, FLRN were top results — bond ETFs) |
| HIGH_OPT_VOLUME_PUT_CALL_RATIO | 0/15 ETFs (IEFA appeared, not sector ETFs) |
| SCAN_ivRank52w_DESC | 0/15 ETFs (individual stocks only) |
| SCAN_impVolatOverHist_DESC | DISABLED by IBKR |

**Root cause**: IBKR scanner is hard-limited to ~50 results server-side regardless of `numberOfRows`. Market-wide screens rank all ~12,000 US equities; sector ETFs with moderate IV (XLK ~25%, XLF ~20%) are middle-of-the-pack and never surface.

**Architecture**: `fetch_scanner_subscription_batch()` now delegates directly to `fetch_live_iv_hv_batch()` → `get_iv_hv_batch()` (reqHistoricalData, request-response, ~2s/ticker). This path is reliable since Day 52. Scanner code is preserved as a dead-end reference with explanatory docstring.

---

## Data Gap Inventory

### Category 1: Zero-Effort Gaps (data already available, just not used)

#### STA priceHistory — SMA20/50/200 + RSI(14) + Momentum
**Discovery**: STA `/api/stock/{ticker}` returns `priceHistory` — 260 daily OHLCV bars.

**Evidence**: `sector_scan_service._spy_regime()` already uses this endpoint for SPY:
```python
resp = requests.get(f"{STA_BASE_URL}/api/stock/SPY", timeout=5)
hist = resp.json()["stock"]["priceHistory"]  # 260 bars
closes = [bar["close"] for bar in hist]
sma200 = sum(closes[-200:]) / 200
```

**Plan**: `fetch_etf_sma_batch(tickers)` in `sta_service.py`:
- One HTTP call per ETF (same call as spot price, already made in best_setups scan)
- Returns: `sma20`, `sma50`, `sma200`, `price_vs_sma200_pct`, `rsi_14`, `momentum_20d`, `vol_ratio`
- Wire into `analyze_service` → `gate_payload` → `gate_engine._chart_trend_gate()` (advisory WARN)
- Estimated ~50 lines

**Importance — HIGHEST**: This is the most dangerous data gap. A sell_put could be recommended while the ETF is in a confirmed downtrend below 200 SMA (high IV + declining price = wrong time to sell puts).

**Live confirmation (Day 55)**:
| ETF | Price vs SMA20 | Price vs SMA50 | Price vs SMA200 | Trend |
|-----|----------------|----------------|-----------------|-------|
| XLF | Below | Above | Below | Mixed (2/3) |
| XLK | Above | Above | Above | Uptrend (3/3) |
| QQQ | Above | Above | Above | Uptrend (3/3) |
| IWM | Above | Above | Above | Uptrend (3/3) |
| XLE | Above | Above | Above | Uptrend (3/3) |
| XLY | Above | Above | Above | Uptrend (3/3) |

Note: XLF is in mixed trend (below 200 SMA) — a sell_put on XLF would currently get an advisory WARN if this gate existed.

#### compute_skew() — Already Computed, Gate Ignores It
`tradier_provider.compute_skew()` returns:
```python
{
  "skew": 4.2,           # put_iv_30d - call_iv_30d in percent
  "put_iv_30d": 22.1,
  "call_iv_30d": 17.9,
  "expiry": "2026-06-20",
  "dte": 26
}
```
`gate_engine` has ZERO references to `skew`. The value is returned in the analyze API response but never gated.

**Gap**: Elevated skew (>5%) = market is paying for downside protection = risk signal for sell_put. At skew >10%, selling puts into elevated put premium is dangerous.

**Plan**: ~10 lines in gate_engine. Non-blocking WARN above threshold.

### Category 2: Small Code (new data, ~30 lines each)

#### Tradier Put/Call Volume Ratio
`tradier_provider.get_options_chain()` already returns `volume` per contract. Summing call volume / put volume across near-term expiry requires ~30 lines. 

Gate infrastructure already exists (`_put_call_sentiment_gate()`, Gates 7b/11b in sell_put + sell_call). Currently always passes because `put_call_volume` is always `None`.

**Plan**: `compute_put_call_ratio(ticker, dte_target=30)` in tradier_provider.py:
- Call `get_options_chain()` for nearest expiry to `dte_target`
- Sum `volume` for all calls → total_call_vol
- Sum `volume` for all puts → total_put_vol
- Return total_put_vol / total_call_vol
- Pass to `gate_payload` → Gates 7b/11b

### Category 3: Structural Gaps (cannot be fixed with code alone)

#### Paper Trade Win Rate (0/30)
**Gap**: Cannot calibrate blocking gates without empirical win rate data.
**Why**: The 30-trade sample determines whether the system is over-conservative or under-conservative. Without it, tuning any blocking gate is guesswork.
**Resolution**: User action only. Log next CAUTION setup (XLF or QQQ when they surface).

#### OI (Open Interest) Data
**Gap**: Platform limitation confirmed Day 12. IBKR reqMktData tick 101 returns 0 for ETFs. MarketData.app ($100/day free tier) has OI but it's used for supplementary greeks, not as a reliable OI source.
**Impact**: Liquidity gate permanently shows WARN (OI=0) for all ETFs.
**Resolution**: None planned. Gate correctly degraded to WARN.

---

## Gate Calibration Assessment

### Current Blocking Gates for sell_put (7 gates)
1. `_etf_ivr_seller_gate()` — IVR < 35% → FAIL
2. `_etf_hv_iv_seller_gate()` — IV/HV < 1.05 → FAIL
3. `_vix_regime_gate()` — VIX > 40 → FAIL
4. `_etf_event_density_gate()` — high event density → FAIL
5. `_etf_holdings_earnings_gate()` — key holding earnings imminent → FAIL
6. `_credit_width_gate()` — credit/width < 33% → FAIL (strategy_ranker)
7. `_spread_pct_gate()` — bid-ask > 20% → FAIL

### All Planned Additions Are Advisory
- `_chart_trend_gate()` (STA SMA) → WARN only
- `_put_call_sentiment_gate()` (already exists) → WARN only
- Skew gate → WARN only

### Calibration Rule
Do NOT modify any blocking gate until 30-trade paper trade sample shows win rate data. Current gates are research-backed (tastylive empirical, Sinclair VRP) but untested against live outcomes.

---

## Implementation Priority Order

1. **Paper trade logging** (P0, user action) — 0/30, blocks all calibration
2. **MASTER_AUDIT_FRAMEWORK sweep** (P1, overdue 13 sessions)  
3. **`fetch_etf_sma_batch()`** (P2, ~50 lines) — closes most dangerous gap
4. **Tradier put/call ratio** (P3, ~30 lines) — fills existing Gate 7b/11b data
5. **Wire skew** (P4, ~10 lines) — existing data, missing gate reference

---

## Why Not TradingView?

User asked about pasting TradingView screenshots with Pine Script patterns. Assessment: unnecessary.
STA already returns 260 bars of daily OHLCV. All standard indicators (SMA, RSI, momentum, volume ratio) are computable from this data. TradingView would add zero information that isn't already available from STA's own data feed.

The only value TradingView would add: chart pattern recognition (VCP, cup-and-handle, flags). These are detectable via Pine Script but not easily automatable. For now, the system uses STA's own pattern detection (`patterns.vcp.confidence` already wired into the analyze pipeline for swing fields).
