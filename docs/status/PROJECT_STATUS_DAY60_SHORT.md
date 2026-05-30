# Project Status — Day 60 (May 30, 2026)
> Version: v0.35.3

## What Shipped

### Scan Context Parser (new — `backend/scan_context_parser.py`)
**What:** `parse_scan_context(text)` extracts KEY=VALUE tokens from the SCAN CONTEXT block emitted by `/ibkr-scan`. `apply_scan_context_to_gate_payload()` merges parsed values into gate_payload before `engine.run()`.
**Why it matters:** Closes the data gap between the `/ibkr-scan` skill (which reads live IBKR data) and the analyze backend (which used stale iv_history.db IVR + always-passing Put/Call gate). Pasting the SCAN CONTEXT block now activates 3 real signals: live IVR, live Put/Call ratio, and trend gate.
**Verified:** `test_scan_context.py` — 15 tests, all pass.

### Trend EMA Gate (new — `gate_engine._trend_ema_gate`)
**What:** New gate in all 4 ETF tracks. Reads `trend_pema200` and `trend_pema50` from gate_payload (set by scan_context_parser). When no scan data, silently passes. When data present:
- `sell_put`: P/EMA200 < 0 → HARD BLOCK; pullback (above 200, below 50) → WARN; both > 0 → PASS
- `sell_call`: P/EMA200 > 0 → WARN; < 0 → PASS
- `buy_call`: P/EMA200 < 0 → HARD BLOCK; pullback → WARN; both > 0 → PASS
- `buy_put`: P/EMA200 > 0 → HARD BLOCK; < 0 → PASS
**Position:** Gate 9 in sell_put, Gate 12 in sell_call, between holdings_earnings and position_size in buy tracks.
**Verified:** 8 trend gate tests in `test_scan_context.py`.

### analyze_service.py — Scan Context Integration
**What:** Imports `apply_scan_context_to_gate_payload` from `scan_context_parser`. After gate_payload construction, merges scan_context values: overrides `ivr_pct`/`hv_iv_ratio`, sets `ivr_confidence="known"`, sets `put_call_volume`, adds `trend_pema200`/`trend_pema50`.
**Verified:** Full test suite 52 pass.

### App.jsx — Scan Context Textarea
**What:** Added `scanContext` state. `AnalysisPanel` renders a compact monospace textarea below `PreAnalysisPrompts`. User pastes SCAN CONTEXT line from `/ibkr-scan`. `runAnalysis` includes `scan_context: scanContext` in the analyze payload if non-empty. Green confirmation message appears when scan context is active.

### /ibkr-scan.md — SCAN CONTEXT Output Block
**What:** Added `━━━ SCAN CONTEXT ━━━` block to the Output Format section and example output. Format: `TICKER=XLF  IVR=47  IV_HV=1.247  PEMA200=+3.1  PEMA50=+1.2  PC=0.85  DIRECTION=sell_put`. Notes on decimal conversions (IV/HV % → decimal, PEMA as raw %).

## Test Count
**52 tests** (37 Day 59 + 15 new Day 60)
- `test_scan_context.py`: 15 (NEW — parser + apply + trend gate + wiring)
- `test_gate_engine_etf.py`: existing
- `test_bs_calculator.py`: existing
- `test_direction_routing.py`: existing
- `test_etf_gate_postprocess.py`: existing
- `test_resolve_underlying_hint.py`: existing

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear untested — DEFERRED (ETF-only) |
| KI-099 | LOW | buy_call direction for Leading/Improving ETFs — deferred |
| KI-110 | LOW | _rank_buy_call returns "itm_call"/"atm_call"/"otm_call" instead of "buy_call" |

## Next Session Priorities

### P0 — Live integration test (30 min)
Paste a real `/ibkr-scan` SCAN CONTEXT output into the textarea and verify: IVR overrides stale DB value in gate output, P/C gate activates with real ratio, trend gate shows BLOCK/WARN/PASS based on P/EMA200.

### P1 — KI-110 (LOW): Fix stale strategy_type names (~8 lines)
`_rank_buy_call` returns `"itm_call"/"atm_call"/"otm_call"` instead of `"buy_call"`. Update stype configs + pnl_calculator handlers.

### P2 — End-to-end morning workflow test
Full visual: `/ibkr-scan` screenshot → SCAN CONTEXT paste → analyze → TopThreeCards expected_move + exit plan → paper trade log.

### P3 — Audit (Day 65 trigger)
MASTER_AUDIT_FRAMEWORK v1.5. Next trigger Day 65. Can do gate calibration + test coverage review.
