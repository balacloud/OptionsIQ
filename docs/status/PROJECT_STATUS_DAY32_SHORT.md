# OptionsIQ — Project Status Day 32
> **Date:** April 29, 2026
> **Version:** v0.24.0
> **Previous:** PROJECT_STATUS_DAY31_SHORT.md

---

## What Shipped Today

### Critical Bug Fix — VRP Gate Inverted Since Day 29

`_etf_hv_iv_seller_gate()` in `gate_engine.py` had inverted comparison operators. The `hv_iv_ratio` stored in `analyze_service.py` is `current_iv / hv_20` (IV/HV), but the gate used thresholds written for HV/IV. This caused it to:
- **FAIL** when IV > HV (best time to sell — sellers have premium edge)
- **PASS** when HV > IV (worst time to sell — sellers have no edge)

The gate was introduced Day 29 and has been blocking all seller setups incorrectly ever since in elevated-IV environments. Fix: flipped `<` to `>=` for pass/warn boundaries, removed `HV_IV_SELL_WARN_RATIO` (no longer needed), updated constant comment. Display label fixed from "HV/IV" to "IV/HV". 33 tests all pass.

### IV/HV Ratio Column in Best Setups Watchlist

`GET /api/best-setups` `_run_one` now returns `iv_hv_ratio`, `hv_20`, `current_iv` per ETF result. Best Setups watchlist table shows a 7th column "IV/HV" with color coding: green ≥1.05 (sellers have edge), amber 1.0–1.05 (thin), red <1.0 (HV exceeds IV). Lets user track how close each ETF is to flipping the VRP gate.

### LearnTab Zones Visualization Fixed

Two SVG label collision issues in `PanelZones`:
1. Zone band text moved from centered (collides with strike markers) to edge-anchored short labels (top corners of each band)
2. BE label gets horizontal offset when within 38px of short strike: `textAnchor="end"` if BE < short, `"start"` if BE > short
3. `TOTAL_H` increased 102→116 to give below-axis labels full room

---

## Current Test Count
33 tests (pytest, 5 files) — all passing.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-086 | MEDIUM | app.py ~470 lines — Rule 4 max 150. Move `_seed_iv_for_ticker` + `_run_one` to service modules |
| KI-067 | MEDIUM | QQQ sell_put returns ITM strikes — chain too narrow for current price |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift from LearnTab GATE_KB (two copies) |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested (sell_call + buy_put zone colors unverified) |
| KI-059 | HIGH (deferred) | Single-stock bear untested — ETF-only mode returns 400 |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |

---

## Next Session Priorities (Day 33)

1. **P1 (MEDIUM):** KI-086 — app.py size cleanup. Move `_seed_iv_for_ticker` + `_run_one` closure to service modules.
2. **P2 (LOW):** Skew computation — `put_iv_30delta - call_iv_30delta` from existing chain data.
3. **P3 (MEDIUM):** KI-067 — QQQ sell_put ITM strike fix.
4. **Live test:** Verify the VRP gate fix produces GO signals when market opens tomorrow.
