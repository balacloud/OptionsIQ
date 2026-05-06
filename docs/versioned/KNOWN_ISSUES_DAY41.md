# OptionsIQ — Known Issues Day 41
> **Last Updated:** Day 41 (May 6, 2026)
> **Previous:** KNOWN_ISSUES_DAY40.md

---

## Resolved This Session (Day 41)

None — Day 41 was UI accuracy + health observability, no bug fixes.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)

### KI-076: TradeExplainer isBearish() not live-tested (LOW)

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)

---

## Resolved History (recent)
- KI-093: analyze_service iv_provider tradier mapping ✅ Day 40
- KI-092: "ibkr_cache" → "bod_cache" rename ✅ Day 40
- KI-091: Tradier direction-aware strike window ✅ Day 40
- KI-090: Tradier delta=0.0 coercion fix ✅ Day 40
- KI-086: app.py `_run_one` extraction ✅ Day 39
- KI-067: QQQ sell_put ITM strike fix ✅ Day 39
- APScheduler missed jobs (startup gap) ✅ Day 37
- yfinance HV in iv_history contamination ✅ Day 37
- KI-088: L3 stale banner ✅ Day 34
