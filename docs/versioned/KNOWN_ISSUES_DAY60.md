# Known Issues — Day 60 (May 30, 2026)

## Open — HIGH

None currently.

## Open — MEDIUM

None currently.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (not in ETF universe). Deferred — ETF-only going forward.

### KI-099: buy_call direction for Leading/Improving ETFs
bull_call_spread direction not implemented. Low priority — system now single-leg only.

### KI-110: buy_call/_rank_buy_call returns stale strategy_type names
`strategy_ranker._rank_buy_call` returns `"itm_call"`, `"atm_call"`, `"otm_call"` as strategy_type instead of `"buy_call"`. Similarly `_rank_buy_put` returns `"itm_put"`, `"atm_put"`, `"otm_put"`. pnl_calculator, TradeExplainer, and TopThreeCards all handle these old names correctly (defensive). The canonical name in the design is `"buy_call"` / `"buy_put"`. This is LOW because the system works correctly with the old names but the naming is inconsistent with Day 57 design intent.
**Fix:** Change `stype` configs in `_rank_buy_call` to use `"buy_call"`, update `_rank_buy_put` to `"buy_put"`. Then update pnl_calculator to match. ~8 lines.

## New This Session (Day 60)

None. All work this session was new features (scan_context_parser, trend_ema_gate).

## Resolved This Session (Day 60)

None. (All KI-107/108/109 resolved Day 59.)

## Carried Forward (resolved in earlier sessions)

### Day 59 Resolved
- KI-107 ✅: TQQQ delta guard — strategy_ranker + _tqqq_satellite_gate wired into sell_put + sell_call
- KI-108 ✅: GLD IV/HV < 1.10 now hard-blocks at gate_engine level
- KI-109 ✅: sell_call FOMC gate — replaced 22-line check with _etf_fomc_gate(p, dte, "sell_call")

### Day 58 Resolved
- AUDIT-001 ✅: otm_call/otm_put P&L always zero in pnl_calculator — fixed Day 58
- AUDIT-002 ✅: TradeExplainer isBearish/getMoneyness/headline missing otm_put — fixed Day 58
- AUDIT-003 ✅: DirectionGuide sell_call "Spread width" → "Uncapped naked call" — fixed Day 58
- AUDIT-004 ✅: FOMC gate hard-blocked buy directions for XLF/TQQQ — direction-aware fix Day 58

### Day 57 Resolved
- FOMC over-blocking ✅ (3-tier tiered gate)
- Spread strategies returning for ETFs ✅ (strategy_ranker single-leg rewrite)
- Tradier ATM-centered sort ✅ (delta-centered for sell directions)
