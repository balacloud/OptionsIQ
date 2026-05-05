# OptionsIQ — Known Issues Day 40
> **Last Updated:** Day 40 (May 5, 2026)
> **Previous:** KNOWN_ISSUES_DAY39.md

---

## Resolved This Session (Day 40)

### ✅ KI-090: Tradier delta=0.0 coerced to None — RESOLVED Day 40
`tradier_provider.py` lines 195-198: `_f(g.get("delta")) or None` converted `0.0` (deep-OTM delta) to `None`.
strategy_ranker `_closest_delta()` then treated None as `abs(0.0)=0`, making deep-OTM contracts appear to perfectly match delta=0.30 target.
Fix: `float(g["delta"]) if g.get("delta") is not None else None` — keeps None only when key is truly absent.
Applied to delta, gamma, theta, vega. Verified: QQQ chain shows `delta=None: 0/24`.

### ✅ KI-091: Tradier strike window not direction-aware — RESOLVED Day 40
`tradier_provider.get_options_chain()` used symmetric ±10% window, bypassing the KI-067 OTM filter.
First Tradier-sourced QQQ sell_put would have reproduced ITM strike bug.
Fix: Added direction-aware filter in the per-expiry loop: `sell_put` skips `strike > underlying`; `sell_call` skips `strike < underlying`.
Verified: QQQ sell_put smoke test — 0 ITM puts, short_strike=680.0 < underlying=683.98.

### ✅ KI-092: `data_source="ibkr_cache"` misleading for Tradier-sourced BOD cache — RESOLVED Day 40
BOD batch calls `data_svc.get_chain()` which goes to Tradier first. Stored result returned as `"ibkr_cache"` on analysis.
Fix: Renamed `"ibkr_cache"` → `"bod_cache"` in `data_service.py` (docstring, `_cache_get` return, `quality_label()`) and `data_health_service.py` chain_src label.

### ✅ KI-093: `analyze_service.py:680` iv_provider falls through to mock for data_source="tradier" — RESOLVED Day 40
iv_provider selection only handled `ibkr_*` and `yfinance` sources. `"tradier"` fell through to `mock_provider`.
Fix: Added `data_source in {"yfinance", "tradier", "alpaca"}` → `yf_provider` branch. Also updated `"ibkr_cache"` → `"bod_cache"` in the IBKR set.

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
- APScheduler missed jobs (startup gap) ✅ Day 37 — run_startup_catchup() daemon thread
- yfinance HV in iv_history contamination ✅ Day 37 — removed from IV seeding pipeline
- KI-088: L3 stale banner ✅ Day 34
