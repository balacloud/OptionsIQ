# Project Status — Day 21 (April 9, 2026)
> **Version:** v0.15.0
> **Session Type:** Major refactor + full ETF pivot

## What Happened

### ETF-Only Pivot (v0.15.0)
Pivoted OptionsIQ from arbitrary single-stock + ETF support to **ETF-only** analysis covering
16 ETFs: 11 SPDR sectors (XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC),
3 cap-size (MDY, IWM, SCHB), QQQ, TQQQ.
- Non-ETF tickers return HTTP 400 with `etf_universe` list
- Signal Board UI replaces tab-based layout: RegimeBar (top) + Scanner (left) + Analysis Panel (right)
- Direction auto-derived from sector regime (SECTOR_DIR_TO_CORE mapping)

### ETF Gate Tracks Added (gate_engine.py)
New `etf_mode: bool` parameter on `gate_engine.run()`. When True, routes to ETF-specific tracks:
- `_run_etf_buy_call()` — 8 gates: IVR buyer, HV/IV, theta burn, DTE (IVR-based), FOMC, liquidity, SPY regime bull, position sizing
- `_run_etf_buy_put()` — 8 gates: same with SPY regime bear
- `_run_etf_sell_put()` — 7 gates: IVR seller, strike OTM, DTE seller, FOMC, liquidity, SPY regime seller, max loss
- sell_call reuses `_run_sell_call()` unchanged (already ETF-clean)

### ETF Payload (app.py)
`_etf_payload()` provides real SPY regime data + all swing fields as None + `swing_data_quality: "etf"`.
No swing fabrication for ETFs. `direction_locked: []` for all ETFs (regime, not signal, drives direction).

### Delta-Based Spread Legs (strategy_ranker.py)
ETF mode uses delta-based spread targeting (short leg delta 0.30, protection delta 0.15) instead of
fabricated swing targets. Detected via `swing_data_quality == "etf"`.

### P&L Scenarios (pnl_calculator.py)
ETF: price-relative scenarios (-10%, -5%, Current, +5%, +10%, +15%). Stock: explicit None guards.

### Signal Board Frontend
- `RegimeBar.jsx` (new) — SPY regime, 5d return, market state, cap-size signal. Red bg on BROAD_SELLOFF.
- `App.jsx` (full rewrite) — Signal Board layout, ScannerRow, L2InlineDetail, AnalysisPanel
- `index.css` (~250 lines added) — .regime-bar, .signal-board, .scanner-panel, .scanner-row,
  .l2-inline-panel, .analysis-panel, .ivr-badge, quadrant color classes

## Pipeline Test Results (all 4 directions on XLU)
| Direction | is_etf | gates | strategies | P&L |
|-----------|--------|-------|-----------|-----|
| buy_call | ✅ True | 8 gates | 3 strats | -10% to +15% scenarios |
| sell_call | ✅ True | 7 gates | 3 strats | ✅ |
| buy_put | ✅ True | 8 gates | 3 strats | ✅ |
| sell_put | ✅ True | 7 gates | 3 strats | ✅ |

Sector scan: ✅ 15 ETFs, spy_regime correct, market_regime=NORMAL, sta_status=ok

## Bugs Fixed
- pnl_calculator TypeError: float() on None (ETF swing fields) — price-relative scenarios fix
- IBKR clientId conflict — old process blocking new connection after restart
- React crash on STA offline — missing `.catch(() => {})` on useEffect

## Open Issues
- KI-067: QQQ chain too narrow (price dropped ~15% from Day 20, may self-resolve)
- KI-064: IVR mismatch L2 vs L3
- KI-044: API_CONTRACTS.md stale (ETF-only fields not documented)

## Next Session Priorities
1. **P0:** Market-open frontend smoke test — RegimeBar + scanner + click ANALYZE → L3 panel
2. **P1:** QQQ chain test post-price-drop (KI-067)
3. **P1:** IVR mismatch (KI-064)
4. **P2:** API_CONTRACTS.md ETF fields sync (KI-044)
5. **P3:** analyze_service.py extraction (KI-001/023)
