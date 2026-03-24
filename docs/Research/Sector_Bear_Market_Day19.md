# Sector Bear Market Strategies — Phase 7b Research
> **Date:** March 23, 2026 (Day 19)
> **Author:** Claude + User
> **Status:** Implemented and live-tested

---

## Question

When should OptionsIQ suggest bearish options plays on sector ETFs, and what conditions must be met?

## Background

Prior to Day 19, the sector scan module only recommended bullish plays:
- Leading → buy_call (or bull_call_spread if IVR > 50)
- Improving → bull_call_spread
- Weakening → None (WAIT)
- Lagging → None (SKIP)

In a bear market (SPY below 200 SMA, March 2026), this leaves money on the table. 9/15 sectors were Weakening or Lagging, yet the system had zero actionable bearish recommendations.

## Research Decision: bear_call_spread (Not buy_put)

The original Day 13 research (3-model consensus) concluded: "Lagging ETFs mean-revert too fast for puts." This remains true for **directional puts** (buy_put), but does NOT apply to **bear call spreads** because:

1. **Bear call spreads are theta-positive** — time works for you, unlike buy_put
2. **Defined risk** — max loss = width of spread minus credit received
3. **You don't need the ETF to fall** — just need it to NOT rally through your short strike in 21-45 DTE
4. **Mean-reversion is priced in** — the spread's short strike is typically 5-8% above current price, giving room for a bounce

## Threshold Design

### Lagging → bear_call_spread

Two conditions (AND logic):
- **RS < 98.0** — underperforming SPY by 2+ points on RS scale (not borderline)
- **Momentum < -0.5** — still declining, not bottoming (positive momentum means improving)

Live validation (March 23, 2026):
| ETF | RS Ratio | Momentum | Qualifies? | Reason |
|-----|----------|----------|------------|--------|
| XLY | 93.77 | -0.81 | YES | Deep underperformance + declining |
| XLV | 97.07 | -2.69 | YES | Below 98 + steep decline |
| QQQ | 98.83 | -0.29 | NO | RS > 98 (borderline, not actionable) |
| TQQQ | 98.83 | -0.29 | NO | Inherits QQQ, RS > 98 |

### Why not RS < 95 (from original roadmap)?

RS < 95 would miss XLV (97.07), which has the steepest negative momentum (-2.69) — a stronger bear signal than XLY despite higher RS. The 98 threshold captures both meaningful cases while excluding borderline QQQ.

### Why not RS < 99?

RS 98-100 includes ETFs that just crossed below SPY performance. These are too close to mean-reverting back. 98 gives a 2-point buffer.

## What Was NOT Implemented (and Why)

### Weakening → sell_call (DROPPED)

Original plan included: Weakening ETFs with strong negative momentum in bearish macro → sell_call.

**Dropped because:**
1. Weakening ETFs have RS > 100 — still outperforming SPY
2. In a selloff, utilities (XLU) and staples (XLP) are *safe haven* sectors actively being bought
3. Selling calls on a sector getting defensive rotation inflows is walking into a short squeeze
4. Would need CYCLICAL_SECTORS vs DEFENSIVE_SECTORS distinction to be safe — adds complexity without research backing

Deferred to Phase 7c after backtesting research.

### IVR as L1 gate (CHANGED to L2 soft warning)

L1 scan never has IVR (no chain fetch). Making IVR a hard gate would mean bear_call_spread never appears in L1.

**Decision:** IVR is a soft warning in L2 only. If IVR available and < 40%, show: "Premium may be thin for bear call spread. Wait for volatility to expand." Not a gate — many ETFs lack IV history.

## Broad Selloff Detection

**Condition:** >50% of sectors Weakening+Lagging AND SPY below 200 SMA.

**March 23 live data:** 9/15 = 60% Weakening/Lagging + SPY below 200 → BROAD_SELLOFF fires.

**User action:** Consider defined-risk bear spreads over directional calls. Reduce bullish exposure.

## Bug Fix: L2 None → buy_call Fallback

Pre-existing bug in `analyze_sector_etf()`:
```python
raw_dir = etf_data.get("suggested_direction") or "buy_call"  # None → buy_call!
```

For SKIP ETFs (Lagging/Weakening with no direction), this silently fetched a buy_call chain. Trader sees IV data based on wrong DTE/strike window. Fixed to skip chain fetch entirely when direction is None.

## Files Changed

| File | Change |
|------|--------|
| `backend/constants.py` | +RS_LAGGING_BEAR_RS, RS_LAGGING_BEAR_MOM, BROAD_SELLOFF_SECTOR_PCT, IVR_BEAR_SPREAD_WARN, DIRECTION_TO_CHAIN_DIR |
| `backend/sector_scan_service.py` | quadrant_to_direction() bear logic, _detect_regime(), L2 chain fix, IVR soft warning |
| `frontend/src/components/ETFCard.jsx` | bear_call_spread in DIR_LABELS, BEAR_DIRECTIONS set, badge-bear styling |
| `frontend/src/components/SectorRotation.jsx` | Broad selloff banner, IVR bear warning display |
| `frontend/src/index.css` | .badge-bear, .sector-selloff-banner, .etf-warning-bear styles |

## Live Test Results (March 23, 2026)

### L1 Scan
- XLY: bear_call_spread, ANALYZE ✅
- XLV: bear_call_spread, ANALYZE ✅
- QQQ: SKIP ✅ (RS > 98)
- market_regime: BROAD_SELLOFF ✅
- All bullish paths unchanged (no regression)

### L2 Analysis (XLY)
- direction: bear_call_spread ✅
- data_source: ibkr_live ✅ (sell_call chain fetched, not buy_call)
- iv_current: 26.0% ✅
- L3 note: direction=sell_call ✅

### L2 Bug Fix Verification (QQQ)
- data_source: None ✅ (no chain fetch for SKIP — was previously buy_call!)
- note: "not applicable" ✅
