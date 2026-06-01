# Known Issues — Day 62 (Jun 1, 2026)

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
`strategy_ranker._rank_buy_call` returns `"itm_call"`, `"atm_call"`, `"otm_call"` as strategy_type instead of `"buy_call"`. Similarly `_rank_buy_put` returns `"itm_put"`, `"atm_put"`, `"otm_put"`. pnl_calculator, TradeExplainer, and TopThreeCards all handle these old names correctly (defensive).
**Fix:** Change `stype` configs in `_rank_buy_call` to use `"buy_call"`, update `_rank_buy_put` to `"buy_put"`. Then update pnl_calculator to match. ~8 lines.

## New This Session (Day 62)

None logged.

## Resolved This Session (Day 62)

### Dead ETF Signal Scanner ✅
`ETF Signal Scanner` UI panel was calling `/api/sectors/scan` → 410 on every click.
Removed from App.jsx entirely. `useSectorData` hook + `ScannerRow` + `L2InlineDetail` deleted.

### Over-blocking gates ✅
5 gates were hard-blocking on conditions that `/ibkr-scan` already validates upstream.
Changed to non-blocking warn per Rule 23. GLD IV/HV < 1.10 hard block preserved.
See `docs/stable/GOLDEN_RULES.md` Rule 23 for the full ownership table.

## Carried Forward (resolved in earlier sessions)

### Day 61 (no resolutions — analysis-only session)
- ibkr-scan live test: QQQ 4/7, GLD hard block, XLF P/C=2.64

### Day 60 Resolved
- scan_context_parser.py shipped
- _trend_ema_gate() added to all 4 ETF tracks
- App.jsx scan context textarea added

### Day 59 Resolved
- KI-107 ✅: TQQQ delta guard
- KI-108 ✅: GLD IV/HV < 1.10 hard block
- KI-109 ✅: sell_call FOMC gate consistency
