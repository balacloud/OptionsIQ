# Known Issues — Day 65 (Jun 4, 2026)

## Open — HIGH
None.

## Open — MEDIUM
None.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (not in ETF universe). Deferred — ETF-only going forward.

### KI-099: buy_call direction for Leading/Improving ETFs
bull_call_spread direction not implemented. Low priority — system now single-leg only.

## Resolved This Session (Day 65)

### RESOLVED: KI-110 — buy_call/_rank_buy_put stale strategy_type names
`strategy_ranker._rank_buy_call` was returning `"itm_call"`, `"atm_call"`, `"otm_call"`.
`strategy_ranker._rank_buy_put` was returning `"itm_put"`, `"atm_put"`, `"otm_put"`.
Fixed: all configs now return unified `"buy_call"` / `"buy_put"`.
`pnl_calculator.py` updated to handle new names; old names kept for backward compat with existing paper trade records.

## Carried Forward from Day 64
- KI-059: single-stock bear (ETF-only, permanent deferral)
- KI-099: buy_call Leading/Improving ETFs (single-leg only, deferred)
