# OptionsIQ — Known Issues Day 32
> **Last Updated:** Day 32 (April 29, 2026)
> **Previous:** KNOWN_ISSUES_DAY31.md

---

## Resolved This Session (Day 32)

### KI-VRP-INVERT: VRP gate logic inverted since Day 29 ✅ RESOLVED Day 32
`_etf_hv_iv_seller_gate()` compared `hv_iv_ratio` (which is `current_iv / hv_20` = IV/HV) against thresholds originally written for HV/IV. This caused the gate to **fail when IV > HV** (best time to sell) and **pass when HV > IV** (worst time to sell). Fix: flipped comparison operators to `>= HV_IV_SELL_PASS_RATIO` for pass, `>= 1.0` for warn, `< 1.0` for fail. Removed `HV_IV_SELL_WARN_RATIO` constant (no longer needed). Updated constant comment to reflect IV/HV interpretation. All 33 tests pass.

### LearnTab zones visual overlap ✅ RESOLVED Day 32
Two issues in PanelZones SVG:
1. Zone band text ("OTM puts here") was centered in the band, landing on top of strike marker labels. Fixed: moved to edge-anchored short labels (top-left / top-right corners of each band).
2. BE label and short strike label colliding horizontally when spread is narrow (e.g., $0.53 credit on $1.50 wide spread). Fixed: collision detection — when `|bx - sx| < 38px`, BE label offsets horizontally with `textAnchor="end"` or `"start"`. Same for long strike vs current price.
3. TOTAL_H increased to 116 to prevent below-axis labels from being clipped.

---

## New Issues This Session (Day 32)

None identified.

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — ~470 lines (Rule 4 max = 150) (MEDIUM)
`_seed_iv_for_ticker()` and `_run_one()` (best-setups closure) belong in service modules. Route handlers should be ≤10 lines.

### KI-067: QQQ sell_put returns ITM strikes (MEDIUM)
Chain too narrow for current QQQ price — sell_put picks up ITM puts. Struct cache issue.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)
L2 and L3 use slightly different IVR computation paths.

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)
GateExplainer.jsx and LearnTab.jsx each have their own GATE_KB copy. Audit scheduled (Category 9).

### KI-076: TradeExplainer isBearish() not live-tested (LOW)
All 4 directions not verified live post-Day 21. sell_call and buy_put zone colors unverified.

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
ETF-only mode: stocks return 400. Deferred indefinitely.

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)
Only FOMC is tracked in the events gate.

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

---

## Resolved History (recent)
- KI-084/087: XLRE, SCHB OHLCV seeded ✅ Day 31
- KI-085: VIX badge in RegimeBar ✅ Day 31
- KI-083: XLE OHLCV corruption ✅ Day 30
- KI-IWM-OHLCV: IWM OHLCV corruption ✅ Day 30
- KI-082: Credit-to-width ratio gate ✅ Day 29
- KI-IVR-NULL: IVR showing "—" in Best Setups ✅ Day 29
