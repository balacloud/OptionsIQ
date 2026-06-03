# Known Issues — Day 64 (Jun 3, 2026)

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
**Fix:** Change `stype` configs in `_rank_buy_call` + `_rank_buy_put` to unified names, update pnl_calculator. ~8 lines.
P4 priority for next session.

## Resolved This Session (Day 64)

### RESOLVED: R3 magic number in gate_engine.py sell_put OTM check
`gate_engine.py:1263` had raw `3.0` (OTM% threshold). Added `SELL_PUT_OTM_PASS_PCT = 3.0` to
`constants.py` (parallel to existing `SELL_CALL_OTM_PASS_PCT = 2.0`), imported and used in gate_engine.

### RESOLVED: fomc_gate missing from GateExplainer GATE_KB
When FOMC gate fired, UI showed raw gate ID "fomc_gate" with no explanation. Added complete `fomc_gate`
entry to GATE_KB explaining 3-tier logic (XLF/TQQQ block 14d, QQQ/IWM/GLD warn 7d, buyers warn-only).

### RESOLVED: ivr_seller GATE_KB missing 35% threshold
`ivr_seller` pass answer said "IV is elevated" with no specific number. Updated to explicitly state
"IVR ≥ 35%" and cite tastylive empirical basis.

### RESOLVED: MASTER_AUDIT_FRAMEWORK trend_ema description too narrow
Framework described trend_ema as "blocks sellers when below 200EMA" but code is fully direction-aware:
blocks sell_put+buy_call when pema200 < 0; blocks buy_put when pema200 > 0; warns sell_call when pema200 > 0.
Framework updated to reflect all 4 direction branches.

## Carried Forward

### Day 63 Resolved
None — Day 63 was a tooling/workflow session (no backend/frontend code changes).

### Day 62 Resolved
- Dead ETF Signal Scanner ✅ (removed from App.jsx)
- Over-blocking gates ✅ (5 gates → non-blocking warn, Rule 23 added)

### Day 60 Resolved
- scan_context_parser.py shipped ✅
- _trend_ema_gate() wired ✅
- App.jsx scan context textarea ✅
