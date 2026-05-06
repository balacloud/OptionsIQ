# OptionsIQ — Known Issues Day 43
> **Last Updated:** Day 43 (May 6, 2026)
> **Previous:** KNOWN_ISSUES_DAY42.md

---

## Resolved This Session (Day 43)

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) — analyze_service.py (MEDIUM) ✅ RESOLVED Day 43
**Root cause:** L2 scan used the single ATM contract IV; L3 `_extract_iv_data()` averaged all direction-filtered contracts. For sell_put, fetching only puts and averaging them introduced OTM put skew (typically 5-8pp higher than ATM IV). IBKR's historical IV baseline (`reqHistoricalData OPTION_IMPLIED_VOLATILITY`) is ATM-weighted — so the average approach broke IVR percentile consistency.
**Fix:** Changed `_extract_iv_data()` to select the ATM contract (`min(..., key=lambda c: abs(c.strike - underlying_price))`) and use its `impliedVol` as `current_iv`. Fallback to average if ATM IV is null/missing.
**Verification:** XLF sell_put vs sell_call test — same-direction gap reduced from ~5pp to ~2pp (pure timing/microstructure noise). ✅

### KI-075: GateExplainer GATE_KB drift (MEDIUM) ✅ RESOLVED Day 43
Three sub-issues:
1. **Missing `hv_iv_vrp` GATE_KB entry** — seller tracks emit `"hv_iv_vrp"` gate ID (from `_etf_hv_iv_seller_gate()`), but GATE_KB only had `"hv_iv"`. Users saw raw gate ID text. Fixed: added `hv_iv_vrp` entry.
2. **Missing `vix_regime` GATE_KB entry** — `_vix_regime_gate()` emits `"vix_regime"`, was absent from GATE_KB. Fixed: added `vix_regime` entry.
3. **Wrong DTE constants in `_run_etf_sell_put`** — gate was using single-stock VCP constants (`DEFAULT_MIN_DTE=14` to `DTE_REC_HIGH_SIGNAL=21`) instead of `ETF_DTE_SELLER_PASS_MIN/MAX` (21–45 DTE per tastylive). `ETF_DTE_SELLER_PASS_MIN/MAX` existed in constants.py but were never imported into gate_engine.py. Fixed: added import + updated gate logic.

### KI-077: DirectionGuide sell_put "capped" label — DirectionGuide.jsx (LOW) ✅ RESOLVED Day 43
**Root cause:** sell_put risk text said "Risk: Spread width (capped with spread)" — misleading since system can return naked puts.
**Fix:** Updated to "Risk: Large (up to full strike value if naked). Bull put spread caps this — check strategy type."

### KI-081: No CPI/NFP/PCE macro events calendar (LOW) ✅ RESOLVED Day 43
**Root cause:** Events gate only checked FOMC; CPI/NFP/PCE dates had no coverage.
**Fix:** 
- `constants.py`: Added `MACRO_DATES` dict (CPI, NFP, PCE dates for 2026-2027)
- `analyze_service.py`: Added `_days_until_next_macro()` → `(days, event_name)`. Computed `_fomc_days` and `_macro_days` once before gate_payload construction (also fixed pre-existing bug: `fomc_days_away` was always 999 in gate_payload because explicit line overrode swing_data value when frontend didn't send it)
- `gate_engine.py`: Extended `_etf_fomc_gate()` → picks nearest event (FOMC vs macro), emits combined computed_value (`"FOMC 43d · CPI 7d · DTE 23"`). Updated `_run_sell_call` gate 4 inline similarly.
- `GateExplainer.jsx`: Updated `events` GATE_KB entry to mention CPI/NFP/PCE/FOMC.
**Verification:** Live test XLF sell_put → `events: warn, "CPI in 7d falls inside holding window (23 DTE)"` ✅

---

## Pre-existing Bug Fixed (Bonus)

### fomc_days_away always 999 in gate_payload for ETFs (silent)
`gate_payload` was spreading `**swing_data` (which had the computed fomc days) then overriding with `_i(payload.get("fomc_days_away"), 999)`. Since the frontend never sends `fomc_days_away`, the gate always got 999 → always passed. Fixed by computing `_fomc_days` once before gate_payload and using it consistently.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21.

### KI-076: TradeExplainer isBearish() not live-tested (LOW)
All 4 directions not verified live for TradeExplainer zone colors.

---

## Resolved History (recent)
- KI-081: CPI/NFP/PCE macro events calendar ✅ Day 43
- KI-077: DirectionGuide sell_put label ✅ Day 43
- KI-075: GateExplainer GATE_KB drift ✅ Day 43
- KI-064: IVR mismatch L2 vs L3 ✅ Day 43
- KI-094: QualityBanner dead ibkr_cache key ✅ Day 42
- KI-095: BatchStatusPanel timestamp UTC offset ✅ Day 42
- KI-093: analyze_service iv_provider tradier mapping ✅ Day 40
- KI-092: "ibkr_cache" → "bod_cache" rename ✅ Day 40
- KI-091: Tradier direction-aware strike window ✅ Day 40
- KI-090: Tradier delta=0.0 coercion fix ✅ Day 40
- KI-086: app.py `_run_one` extraction ✅ Day 39
- KI-067: QQQ sell_put ITM strike fix ✅ Day 39
- KI-088: L3 stale banner ✅ Day 34
