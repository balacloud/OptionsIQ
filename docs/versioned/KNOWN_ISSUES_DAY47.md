# OptionsIQ — Known Issues Day 47
> **Last Updated:** Day 47 (May 7, 2026)
> **Previous:** KNOWN_ISSUES_DAY46.md

---

## Resolved This Session (Day 47)

No new KI resolutions — all known code issues were already closed.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design — ETF-only is the current product scope.

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
