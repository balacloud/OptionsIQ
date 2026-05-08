# OptionsIQ — Known Issues Day 49
> **Last Updated:** Day 49 (May 8, 2026)
> **Previous:** KNOWN_ISSUES_DAY48.md

---

## Resolved This Session (Day 49)

### KI-098: Absolute trend gate missing ✅ RESOLVED Day 49
**Root cause:** `quadrant_to_direction()` returned `bear_call_spread` for any Lagging ETF based purely on RS ratio/momentum. If the sector was actually rising on the week (`weekChange > 0`), suggesting a spread trade was tape-fighting.
**Fix:** Added `week_change` parameter to `quadrant_to_direction()`. When `week_change > 0` in the Lagging branch, returns `None` (skip). Size-rotation ETFs (QQQ/MDY/IWM) bypass gate because STA doesn't return `weekChange` for them.
**Tests:** 4 new tests in `test_direction_routing.py`.

### KI-096: IVR null coerced to 0.0 ✅ RESOLVED Day 49
**Root cause:** `ivr_for_gates = {k: (0.0 if v is None else v) ...}` in `analyze_service.py` — missing IVR history treated identically to "very cheap vol," causing seller gates to FAIL on new ETFs with no IV history.
**Fix:** Added `ivr_confidence = "known"/"unknown"` derived from `ivr_data.get("ivr_pct")`. Seller IVR gates in `gate_engine.py` (all 4 sell tracks) check `ivr_confidence` first — unknown → `warn` (non-blocking) with message "No IV history — cannot confirm premium is elevated."
**Tests:** 2 new tests: `test_seller_unknown_ivr_warns_not_fails`, `test_seller_known_low_ivr_still_fails`.

### KI-097: Event density gate missing ✅ RESOLVED Day 49
**Root cause:** `_etf_fomc_gate()` only checked the single nearest event. 4 macro events (FOMC+CPI+NFP+PCE) in a 22-day DTE window were treated identically to 1 event.
**Fix:** New method `_etf_event_density_gate(p, dte)` in `gate_engine.py` (Rule 5 — new function, existing not modified). Counts ALL events in the DTE window using weighted scores (FOMC=3, CPI=3, NFP=2, PCE=2). Rate-sensitive ETFs (XLF/XLRE/XLU/XLE/IWM/QQQ) block at lower thresholds. New constants block in `constants.py`. Wired into `_run_etf_sell_put` and `_run_etf_sell_call`.
**Tests:** 2 new tests: `test_event_density_high_count_blocks_rate_sensitive_etf`, `test_event_density_low_count_passes`.

### KI-100: Tier 1 GO rate not reported separately ✅ RESOLVED Day 49
**Root cause:** Best Setups aggregate includes all 15 ETFs, but Tier 2 ETFs (XLB, XLRE, XLU, XLE, XLC, XLP, XLI, MDY, TQQQ) are structurally blocked by liquidity gate regardless of vol conditions. Seeing "0 GO across 15 ETFs" looks like miscalibration, not a Tier 2 structural issue.
**Fix:** `app.py` `/api/best-setups` now computes `tier1_summary` (5 Tier 1 ETFs: IWM, QQQ, XLF, XLK, XLY) with separate GO/CAUTION/BLOCKED counts. `BestSetups.jsx` displays color-coded pills bar after the scan header with explanatory note.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 50+.

---

## Resolved History (recent)
- KI-098: Absolute trend gate (weekChange) ✅ Day 49
- KI-096: IVR null → unknown confidence ✅ Day 49
- KI-097: Event density gate ✅ Day 49
- KI-100: Tier 1 GO rate reporting ✅ Day 49
- KI-086: app.py sta_fetch extraction ✅ Day 46
- KI-076: TradeExplainer isBearish() ✅ Day 44
- KI-081: CPI/NFP/PCE macro calendar ✅ Day 43
- KI-077: DirectionGuide sell_put label ✅ Day 43
- KI-075: GateExplainer GATE_KB drift ✅ Day 43
- KI-064: IVR mismatch L2 vs L3 ✅ Day 43
- KI-094: QualityBanner dead ibkr_cache key ✅ Day 42
- KI-095: BatchStatusPanel timestamp UTC offset ✅ Day 42
