# Known Issues — Day 59 (May 29, 2026)

## Open — HIGH

None currently.

## Open — MEDIUM

None currently. KI-107/108/109 all resolved Day 59.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (not in ETF universe). Deferred — ETF-only going forward.

### KI-099: buy_call direction for Leading/Improving ETFs
bull_call_spread direction not implemented. Low priority — system now single-leg only.

### KI-110: buy_call/_rank_buy_call returns stale strategy_type names
`strategy_ranker._rank_buy_call` returns `"itm_call"`, `"atm_call"`, `"otm_call"` as strategy_type instead of `"buy_call"`. Similarly `_rank_buy_put` returns `"itm_put"`, `"atm_put"`, `"otm_put"`. pnl_calculator, TradeExplainer, and TopThreeCards all handle these old names correctly (defensive). The canonical name in the design is `"buy_call"` / `"buy_put"`. This is LOW because the system works correctly with the old names but the naming is inconsistent with Day 57 design intent.
**Fix:** Change `stype` configs in `_rank_buy_call` to use `"buy_call"`, update `_rank_buy_put` to `"buy_put"`. Then update pnl_calculator to match. ~8 lines.

## Resolved This Session (Day 59)

### KI-107: TQQQ delta guard not enforced (resolved Day 59)
`strategy_ranker._rank_sell_put_etf` now branches on `is_tqqq` — TQQQ uses delta targets 0.10/0.08/0.06 (was 0.20/0.15/0.28 like other ETFs). `gate_engine._tqqq_satellite_gate()` added: informational gate wired into both `_run_etf_sell_put` (Gate 9) and `_run_etf_sell_call` (Gate 12). Gate checks VIX and reminds user of TQQQ constraints (delta cap, VIX < 18, QQQ EMA alignment). All 37 tests pass.

### KI-108: GLD IV/HV gate not enforced in gate_engine (resolved Day 59)
`gate_engine._etf_hv_iv_seller_gate` now branches on `is_gld`. When `ticker == "GLD"` and `ratio < 1.10`, gate returns hard block ("fail", blocking=True). Threshold string distinguishes GLD (≥1.10 required) from other ETFs (≥1.05 pass, 1.0–1.05 warn, <1.0 fail). Replaces ibkr-scan-only enforcement with backend gate enforcement.

### KI-109: sell_call FOMC gate uses legacy events check (resolved Day 59)
Replaced 22-line manual events/FOMC check in `_run_etf_sell_call` Gate 6 with single call:
`out.append(self._etf_fomc_gate(p, dte, "sell_call"))`. XLF/XLRE/TQQQ sell_call within 14 days of FOMC now hard-blocks (same as sell_put). QQQ/IWM/GLD sell_call gets warn-only within 7 days. Eliminates inconsistency where sell_call was under-blocked vs sell_put for rate-sensitive ETFs.

## Carried Forward (resolved in earlier sessions)

### Day 58 Resolved
- AUDIT-001 ✅: otm_call/otm_put P&L always zero in pnl_calculator — fixed Day 58
- AUDIT-002 ✅: TradeExplainer isBearish/getMoneyness/headline missing otm_put — fixed Day 58
- AUDIT-003 ✅: DirectionGuide sell_call "Spread width" → "Uncapped naked call" — fixed Day 58
- AUDIT-004 ✅: FOMC gate hard-blocked buy directions for XLF/TQQQ — direction-aware fix Day 58

### Day 57 Resolved
- FOMC over-blocking ✅ (3-tier tiered gate)
- Spread strategies returning for ETFs ✅ (strategy_ranker single-leg rewrite)
- Tradier ATM-centered sort ✅ (delta-centered for sell directions)
