# Project Status — Day 57 (May 29, 2026)
> Version: v0.35.0 | Tests: 37 | Backend: Flask :5051 | Frontend: React :3050

## What Shipped Today

### Phase 1 — `/ibkr-scan` skill (DONE Day 57)
`.claude/commands/ibkr-scan.md` built. 4-layer scoring: Regime (SPY EMA200) → IV Gate (Pctl+IV/HV) → Trend Gate (EMA200/50) → Activity+Sentiment (skip pre-market). TQQQ satellite rules (delta 0.10 max). GLD rules (IV/HV ≥ 1.10 required). System-level warnings (macro fear, broad IV expansion). Full example output with table + TOP PICK + NEXT STEP.

### Phase 1b — FOMC 3-tier gate (DONE Day 57)
`gate_engine.py` + `constants.py` updated. 3 tiers:
- BLOCK: XLF, XLRE, TQQQ within 14 days → hard fail
- WARN: QQQ, IWM, GLD within 7 days → delta cap advisory, never blocks
- Others: FOMC inside window → warn (old behavior)
Event density block threshold raised 7→12 (1 FOMC + full macro = WARN not BLOCK).

### Phase 2 — expected_move + exit_plan in analyze response (DONE Day 57)
`analyze_service.py`: `_enrich_strategies()` + `_exit_plan()` helpers.
- `expected_move_1sd`: top-level ±1σ move (IV% × √DTE/365 × underlying)
- Per strategy: `expected_move`, `strike_vs_expected_move` (σ OTM), `strike_vs_em_label` (✅/⚠️/❌)
- Per strategy: `exit_plan` dict (rule, profit_target_pct, profit_target_credit, dte_exit, exit_date)
- TQQQ satellite: 25%/14 DTE. Standard ETF: 50%/21 DTE. Buys: 100%/50% stop.

### Phase 3 — Single-leg simplification (DONE Day 57)
`strategy_ranker.py` fully rewritten (700→280 lines):
- sell_put ETF: delta 0.20/0.15/0.28 single naked puts (was bull_put_spread)
- sell_call: delta 0.20/0.15/0.25 single naked calls (was bear_call_spread)
- buy_call: delta 0.68 ITM / 0.50 ATM / 0.30 OTM single calls (was spread rank 2)
- buy_put: delta 0.68 ITM / 0.50 ATM / 0.30 OTM single puts (was spread rank 2)
- Removed: `_credit_width`, `_build_spread`, `_build_bear_put_spread`

### Phase 3b — Tradier delta-centered chain sort for sell directions (DONE Day 57)
`tradier_provider.py`: for sell_put and sell_call, sort contracts by `|abs(delta) - 0.22|` instead of proximity to underlying. Previously returned 12 ATM-centered contracts (delta 0.38-0.53 for sells); now returns 12 contracts centered on the 0.15-0.28 target range. Confirmed: 3 distinct sell_put strikes at delta -0.20, -0.18, -0.25 for QQQ.

### Phase 4 — ETF universe 15→6 + deprecate scan services (DONE Day 57)
`constants.py`: ETF_TICKERS = {QQQ, IWM, XLF, GLD, TQQQ, SPY}. ETF_OPTIONS_LIQUID_TIER1 updated (GLD/TQQQ in, XLK/XLY out). TQQQ_MAX_DELTA=0.10, TQQQ_MAX_DTE=35, TQQQ_MIN_DTE=21, exit rules in constants.
`app.py`: /api/best-setups → 410 deprecated. /api/sectors/scan → 410. /api/sectors/analyze → 410. Removed `concurrent.futures`, `best_setups_service`, `scanner_service` imports.
`test_spread_math.py` deleted. `test_direction_routing.py` updated to single-leg assertions.

## Current Blockers
None. All 37 tests pass.

## Next Priority (Day 58)
1. Frontend: display expected_move + exit_plan in TopThreeCards.jsx
2. TQQQ gate: enforce TQQQ_MAX_DELTA=0.10 in gate_engine
3. GLD gate: IV/HV < 1.0 → hard block in gate_engine
4. End-to-end test: ibkr-scan → analyze → paper trade log
