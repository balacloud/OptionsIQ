# Project Status — Day 61 (May 31, 2026)
> Version: v0.35.3 (no change — analysis-only session)

## What Happened

### Day 61 — Analysis-Only Session (Sunday, market closed)

No code changes this session. Live ibkr-scan skill was run against the IBKR
`Options_IQ_Claude` watchlist (screenshot from May 28). Market was closed (Sunday),
so P/EMA(200) and P/EMA(50) columns all showed "—" — expected IBKR behavior
when watchlist is stale. Trend gate correctly passes silently when EMA data absent.

### IBKR Watchlist Scan Results (May 28 data, context only)

| ETF | IVR | Pctl | IV/HV | IV Chg | P/C | Score | Verdict |
|-----|-----|------|-------|--------|-----|-------|---------|
| QQQ | 36% | 65% | 1.214 | -0.370 | 0.94 | 4/7 | TOP PICK — sell_put (IF regime confirmed) |
| IWM | 28% | 53% | 1.117 | -0.106 | 1.04 | 3/7 | IVR marginal — skip or watch |
| XLF | 39% | 66% | 1.174 | -0.288 | 2.64 | 3/7 | ⚠️ P/C=2.64 extreme put buying — WARN |
| GLD | 17% | 31% | 0.927 | +0.087 | 0.93 | 0/7 | HARD BLOCK — IV/HV 0.927 < 1.00 (requires ≥1.10) |
| TQQQ | — | — | — | — | — | N/A | Cannot score without EMA data |

**Key insight confirmed:** GLD IV/HV gate_engine hard block (`_gld_iv_hv_gate` requiring ≥1.10)
is validated — GLD at IV/HV=0.927 would be correctly blocked by gate_engine even without
scan context override.

**XLF anomaly:** P/C Volume=2.64 is an extreme institutional put-buying signal (typical range:
0.8–1.3). This is a financial sector stress indicator. Not a threshold gate block but a
meaningful sentiment warning that would propagate via SCAN CONTEXT to the put_call_volume
field and activate the put/call sentiment gate.

### SCAN CONTEXT Generated (partial — EMA omitted due to Sunday/closed market)
```
TICKER=QQQ  IVR=36  IV_HV=1.214  PC=0.94  DIRECTION=sell_put
```
PEMA200/PEMA50 fields omitted — unavailable when market is closed. To be included in
Monday live test.

### Trend Gate — Confirmed Correct Behavior
When PEMA200/PEMA50 absent from SCAN CONTEXT, `_trend_ema_gate()` returns "pass" with
reason "no scan data" and does NOT block. This is the correct design — the gate only
fires when live IBKR EMA data is provided. Validated conceptually; to be confirmed in
Monday live integration test.

## Test Count
**52 tests** — no change from Day 60.

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear untested — DEFERRED (ETF-only) |
| KI-099 | LOW | buy_call direction for Leading/Improving ETFs — deferred |
| KI-110 | LOW | _rank_buy_call returns "itm_call"/"atm_call"/"otm_call" instead of "buy_call" |

## Next Session Priorities (Day 62 — Monday, market open)

### P0 — Live integration test (30 min) — MUST DO FIRST
Refresh IBKR watchlist during market hours → get live P/EMA200 and P/EMA50 values →
build full SCAN CONTEXT line including PEMA200/PEMA50 → paste into App.jsx textarea →
verify in gate output:
  (a) IVR overrides stale DB value (check ivr_confidence="known")
  (b) P/C gate activates with real ratio (check put_call_volume field)
  (c) _trend_ema_gate fires with BLOCK/WARN/PASS based on P/EMA200

### P1 — KI-110 (LOW): Fix buy_call/_rank_buy_put stale type names (~8 lines)
`_rank_buy_call` returns `"itm_call"/"atm_call"/"otm_call"` instead of `"buy_call"`.
`_rank_buy_put` returns `"itm_put"/"atm_put"/"otm_put"` instead of `"buy_put"`.
Fix stype configs + pnl_calculator handlers.

### P2 — End-to-end morning workflow test
Full visual: /ibkr-scan screenshot → SCAN CONTEXT paste → analyze → TopThreeCards
expected_move + exit_plan display → paper trade log.

### P3 — Audit (Day 65 trigger)
MASTER_AUDIT_FRAMEWORK v1.5. Last run Day 58. Next trigger Day 65.
