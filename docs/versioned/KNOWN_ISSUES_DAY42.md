# OptionsIQ — Known Issues Day 42
> **Last Updated:** Day 42 (May 6, 2026)
> **Previous:** KNOWN_ISSUES_DAY41.md

---

## Resolved This Session (Day 42)

### KI-094: QualityBanner dead `ibkr_cache` key — App.jsx (HIGH) ✅ RESOLVED Day 42
**Root cause:** Day 40 renamed `ibkr_cache` → `bod_cache` in backend but App.jsx's QualityBanner BANNERS dict still used `ibkr_cache`. When `data_source="bod_cache"` (normal BOD cache path), `BANNERS["bod_cache"]` was undefined → no banner rendered. Silent R8 Golden Rule violation.
**Fix:** Renamed key to `bod_cache`, added `tradier` to early-return no-banner list (live-equivalent source).

### KI-095: BatchStatusPanel timestamp UTC offset bug — DataProvenance.jsx (MEDIUM) ✅ RESOLVED Day 42
**Root cause:** SQLite `CURRENT_TIMESTAMP` stores UTC. `new Date("YYYY-MM-DD HH:MM:SS")` without 'Z' is treated as local time by Chrome. In EDT (UTC-4), table showed times 4 hours ahead of button (which already had the `+'Z'` fix).
**Fix:** Normalized SQLite timestamps before `new Date()` in `fmtTime()` — replace space with 'T', append 'Z'.

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
- KI-094: QualityBanner dead ibkr_cache key ✅ Day 42
- KI-095: BatchStatusPanel timestamp UTC offset ✅ Day 42
- KI-093: analyze_service iv_provider tradier mapping ✅ Day 40
- KI-092: "ibkr_cache" → "bod_cache" rename ✅ Day 40
- KI-091: Tradier direction-aware strike window ✅ Day 40
- KI-090: Tradier delta=0.0 coercion fix ✅ Day 40
- KI-086: app.py `_run_one` extraction ✅ Day 39
- KI-067: QQQ sell_put ITM strike fix ✅ Day 39
- APScheduler missed jobs (startup gap) ✅ Day 37
- yfinance HV in iv_history contamination ✅ Day 37
- KI-088: L3 stale banner ✅ Day 34
