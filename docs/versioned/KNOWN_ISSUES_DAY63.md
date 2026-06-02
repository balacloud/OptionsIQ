# Known Issues — Day 63 (Jun 2, 2026)

## Open — HIGH

None.

## Open — MEDIUM

None.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (not in ETF universe). Deferred — ETF-only going forward.

### KI-099: buy_call direction for Leading/Improving ETFs
bull_call_spread direction not implemented. Low priority — system now single-leg only.

### KI-110: buy_call/_rank_buy_call returns stale strategy_type names
`strategy_ranker._rank_buy_call` returns `"itm_call"`, `"atm_call"`, `"otm_call"` as strategy_type
instead of `"buy_call"`. Similarly `_rank_buy_put` returns stale names.
pnl_calculator, TradeExplainer, TopThreeCards handle old names (defensive). Functional not broken.
**Fix:** Change `stype` configs in `_rank_buy_call` to `"buy_call"`, update pnl_calculator. ~8 lines.

## New This Session (Day 63)

None.

## Resolved This Session (Day 63)

None — Day 63 was a tooling/workflow session (no backend/frontend code changes).

## Carried Forward

### Day 62 Resolved
- Dead ETF Signal Scanner ✅ (removed from App.jsx)
- Over-blocking gates ✅ (5 gates → non-blocking warn, Rule 23 added)

### Day 60 Resolved
- scan_context_parser.py shipped ✅
- _trend_ema_gate() wired ✅
- App.jsx scan context textarea ✅
