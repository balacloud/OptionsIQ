# OptionsIQ — Known Issues Day 46
> **Last Updated:** Day 46 (May 7, 2026)
> **Previous:** KNOWN_ISSUES_DAY45.md

---

## Resolved This Session (Day 46)

### KI-086: app.py `_run_one` still inline ✅ RESOLVED Day 46
**Root cause:** `_run_one` was already extracted to `best_setups_service.py` on Day 39 (docs were stale). Real remaining Rule 4 violation was `sta_fetch` route with 74 lines of inline STA HTTP calls + SPY computation.
**Fix:** Extracted to `backend/sta_service.py`. `sta_fetch` route reduced to 2 lines. Removed unused `import requests as _requests`. app.py: 472 → 402 lines.

### KI-NEW (unlabelled pre-existing): ETF sell_call DTE gate using stock constants ✅ RESOLVED Day 46
**Root cause:** `gate_engine.run()` was routing ETF `sell_call`/`bear_call_spread` through `_run_sell_call()` which uses stock DTE constants (`DTE_REC_HIGH_SIGNAL=21` as pass ceiling). ETF mode should use `ETF_DTE_SELLER_PASS_MIN=30`. A DTE=22 bear_call_spread was showing "Tradable, but slower decay" (stock message) instead of the ETF-specific DTE warning.
**Fix:** Created `_run_etf_sell_call()` (new function per Rule 5) with ETF DTE constants. Updated routing: ETF sell_call → `_run_etf_sell_call()`. DTE=22 now correctly shows "Below ETF entry floor (30 DTE) — gamma risk elevated".

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

---

## Resolved History (recent)
- KI-086: app.py `_run_one` extraction ✅ Day 46 (full close — sta_service.py extracted)
- KI-076: TradeExplainer isBearish() live test ✅ Day 44 (no bug — verified correct)
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
