# Known Issues — Day 58 (May 29, 2026)

## Open — HIGH

None currently.

## Open — MEDIUM

### KI-107: TQQQ delta guard not enforced in gate_engine
The ibkr-scan skill enforces delta 0.10 max for TQQQ at the read/decision layer, but `gate_engine.py` has no gate that blocks TQQQ strategies with delta > 0.10. `TQQQ_MAX_DELTA=0.10` constant exists in constants.py but is not read by gate_engine. A user who bypasses /ibkr-scan and calls /api/options/analyze directly for TQQQ could receive a delta 0.25 strategy without a hard block.
**Fix:** Add TQQQ delta check in `_run_etf_sell_put` or a new `_tqqq_special_gate`. ~10 lines.

### KI-108: GLD IV-cheap gate not enforced in gate_engine
GLD has a rule: if IV/HV < 1.10, "IV CHEAP — do not sell". The ibkr-scan skill enforces this at the read layer, but gate_engine has no GLD-specific IV/HV gate. A GLD sell_put analysis with IV/HV < 1.10 would pass the IV gate with a WARN rather than a hard block.
**Fix:** Check ticker == "GLD" AND hv_iv_ratio < 1.10 in `_etf_hv_iv_seller_gate`. 3 lines.

### KI-109: sell_call FOMC gate uses legacy events check (not _etf_fomc_gate)
`_run_etf_sell_call` has its own manual events/FOMC check that does not tier-block by ticker type. XLF and TQQQ sell_call within 14 days of FOMC only get a WARN (not a hard block), unlike sell_put which uses `_etf_fomc_gate` with tier-1 hard block. Design inconsistency: same seller logic should apply to both sell_put and sell_call.
**Fix:** Replace the manual events block in `_run_etf_sell_call` with `self._etf_fomc_gate(p, dte, "sell_call")`. ~10 lines removed, 1 line added.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (not in ETF universe). Deferred — ETF-only going forward.

### KI-099: buy_call direction for Leading/Improving ETFs
bull_call_spread direction not implemented. Low priority — system now single-leg only.

### KI-110: buy_call/_rank_buy_call returns stale strategy_type names
`strategy_ranker._rank_buy_call` returns `"itm_call"`, `"atm_call"`, `"otm_call"` as strategy_type instead of `"buy_call"`. Similarly `_rank_buy_put` returns `"itm_put"`, `"atm_put"`, `"otm_put"`. pnl_calculator, TradeExplainer, and TopThreeCards all handle these old names correctly (defensive). The canonical name in the design is `"buy_call"` / `"buy_put"`. This is LOW because the system works correctly with the old names but the naming is inconsistent with Day 57 design intent.
**Fix:** Change `stype` configs in `_rank_buy_call` to use `"buy_call"`, update `_rank_buy_put` to `"buy_put"`. Then update pnl_calculator to match. ~8 lines.

## Resolved This Session (Day 58)

### AUDIT-001: otm_call/otm_put P&L always zero (resolved Day 58)
`pnl_calculator._scenario_pnl()` handled `itm_call` and `atm_call` but not `otm_call` → P&L table for R3 of buy_call showed $0 in all scenarios. Same for `otm_put`. Fixed: added `otm_call` to the `itm_call/atm_call` set, and `otm_put` to the `itm_put/atm_put` set.

### AUDIT-002: TradeExplainer profit zone wrong for buy_put R3 (resolved Day 58)
`isBearish()` did not include `otm_put`, so buy_put R3 rendered a bullish profit zone (green right of breakeven) when it should be bearish (green left). `getMoneyness()` also missing `otm_put` → would not treat the position as a put. `getTradeHeadline()` switch missing `otm_call`/`otm_put` → null headline for R3 of buy directions. All three fixed in TradeExplainer.jsx.

### AUDIT-003: DirectionGuide sell_call risk label stale (resolved Day 58)
DirectionGuide showed "Risk: Spread width (capped with spread)" for sell_call. Since Day 57, sell_call is single-leg naked — capped risk text is actively misleading. Fixed: "Risk: Uncapped (naked call — unlimited upside exposure)".

### AUDIT-004: FOMC gate hard-blocked buy directions for XLF/TQQQ (resolved Day 58)
`_etf_fomc_gate` had no direction-awareness. `_run_etf_buy_call` and `_run_etf_buy_put` both called it, causing XLF/TQQQ buy_call/buy_put to be hard-blocked within 14 days of FOMC. Design intent: buyers have defined risk — FOMC is a WARN, not a block. Fixed: added `direction` param to `_etf_fomc_gate` (default "sell_put"); Tier 1 block only when `direction in ("sell_put", "sell_call")`; buyers get "warn" instead of "fail".

### FOMC over-blocking (resolved Day 57)
FOMC gate was blocking QQQ 70-95% of the time. Fixed: 3-tier sensitivity. XLF/XLRE/TQQQ hard block within 14 days (sellers only); QQQ/IWM/GLD warn-only within 7 days.

### Spread strategies returning for ETFs (resolved Day 57)
strategy_ranker was returning bull_put_spread/bear_call_spread for ETF sell directions. Fixed: complete rewrite to single-leg only.

### Tradier chain ATM-centered for sell directions (resolved Day 57)
Tradier was fetching puts sorted by proximity to underlying (ATM-centered), giving delta 0.38-0.53 range. Fixed: sort by |abs(delta) - 0.22| for sell directions.
