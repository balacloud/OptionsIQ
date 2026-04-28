# OptionsIQ — Day 30 Session Status
> **Date:** April 28, 2026 | **Version:** v0.22.0 | **Session:** Day 30

## What Was Done

### McMillan Rolling Stress Check (Gemini book-audit → P1)
- `compute_max_21d_move(ticker)` in `iv_store.py` — computes worst 21-day drawdown AND best 21-day rally from all available OHLCV bars
- `_historical_stress_gate(p, direction)` in `gate_engine.py` — WARN (non-blocking) if:
  - `sell_put`: strike ≥ `current_price × (1 - max_drawdown_pct)` (inside danger floor)
  - `sell_call`: strike ≤ `current_price × (1 + max_rally_pct)` (inside danger ceiling)
- Wired into both sell tracks: `_run_etf_sell_put` and `_run_sell_call`
- `gate_payload` in `analyze_service.py` gets 3 new fields: `max_21d_drawdown_pct`, `max_21d_rally_pct`, `stress_bars_available`
- Live test: XLK sell_put → stress gate WARN "Short strike inside historical worst drawdown zone (9.2% drop → $144.98)"

### OHLCV Data Cleanup
- **XLE**: deleted 18 corrupted rows (close > 80.0, ~2x real price from split artifact). HV-20: 413% → 16.96%
- **IWM**: deleted 17 corrupted rows (close < 150, ~$94-101 mixed with real $240-277 data). worst_dd: 65% → 9.2%
- Discovered by: stress check returning impossibly high drawdowns during development

## Tests
- 29 → 33 passing (all green)

## Current State
- IBKR connected, backend running on :5051
- All 14 ETFs with OHLCV data have valid stress numbers (XLRE, SCHB still 0 rows — KI-084/087)

## Next Priorities (Day 31)
1. **P1:** Seed OHLCV for XLC, XLRE, SCHB (KI-084/087) — analyze triggers seeding but these may not have been analyzed recently
2. **P2:** VIX display in RegimeBar (KI-085) — small badge, 1-hour task
3. **P3:** Skew gate — put_iv_30delta - call_iv_30delta from chain contracts
4. **P4:** app.py cleanup (KI-086) — move _seed_iv_for_ticker + _run_one to service modules
