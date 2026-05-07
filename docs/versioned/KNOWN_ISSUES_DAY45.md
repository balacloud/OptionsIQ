# OptionsIQ — Known Issues Day 45
> **Last Updated:** Day 45 (May 6, 2026)
> **Previous:** KNOWN_ISSUES_DAY44.md

---

## Resolved This Session (Day 45)

None — framework/docs session only. No code changes.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21.

### KI-086 partial: app.py `_run_one` still inline (LOW)
`_run_one` closure still inline in app.py. app.py ~449 lines — Rule 4 (max 150) still violated.
Partial fix already done (Day 39): best_setups_service.py extracted. Remaining: move `_run_one` to best_setups_service.py or a new module.
**P0 for Day 46.**

---

## Resolved History (recent)
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
- KI-086: app.py `_run_one` extraction ✅ Day 39 (partial — _run_one still inline)
- KI-067: QQQ sell_put ITM strike fix ✅ Day 39
- KI-088: L3 stale banner ✅ Day 34
