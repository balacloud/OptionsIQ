# OptionsIQ — Project Status Day 33
> **Date:** April 30, 2026
> **Version:** v0.25.0
> **Previous:** PROJECT_STATUS_DAY32_SHORT.md

---

## What Shipped Today

### Infrastructure Overhaul — Best Setups Scan Reliability

8 root-cause fixes for the cascade of IBKR failures during Best Setups scan. The scan now returns 5-6 live CAUTION setups consistently.

**Fix 1 — CB threshold 2→5** (`constants.py`)
`IB_CB_FAILURE_THRESHOLD` was 2 — two timeouts opened the circuit for 45s. Raised to 5.

**Fix 2 — Stale spread WARN not BLOCK** (`analyze_service.py`)
`apply_etf_gate_adjustments()` now accepts `data_source` parameter. When `ibkr_stale`, spread hard-block becomes WARN with "refresh chain before trading" message instead of blocking the setup.

**Fix 3 — verdict_label null fix** (`app.py`)
`_run_one` was calling `verdict.get("label")` but `build_verdict()` returns `"headline"`. Fixed: derive label from normalized color map.

**Fix 4 — amber→yellow normalization** (`app.py`)
`build_verdict()` returns `"amber"` for CAUTION but frontend expected `"yellow"`. Normalized in `_run_one`. Also added `data_source` to `_run_one` return dict.

**Fix 5 — VIX from STA, not yfinance** (`analyze_service.py`)
yfinance `^VIX` rate-limited when 8 parallel scans hit it simultaneously (`YFRateLimitError` silently swallowed). Fix: STA `/api/stock/%5EVIX` as primary (no rate limits) + `threading.Lock()` preventing stampede. VIX now shows `source: sta, value: 17.59`.

**Fix 6 — OHLCV skip when SQLite fresh** (`analyze_service.py`)
`_extract_iv_data()` was calling `provider.get_ohlcv_daily()` via IBWorker on every call regardless of SQLite freshness. 8 ETFs × 1 `reqHistoricalData` = 8 historical data calls → all timeout (historical farm inactive) → CB trips. Fix: skip if `iv_store.get_ohlcv_stats(ticker).last_date` is ≤2 days old.

**Fix 7 — STA underlying price pre-fetch in _run_one** (`app.py`)
`_run_one` didn't pass `last_close` → every ETF called `get_underlying_price()` via IBKR simultaneously → bid/ask/last all None → `IBKRNotAvailableError` → CB trips. Fix: pre-fetch `currentPrice` from STA before `analyze_etf()`.

**Fix 8 — max_workers=1 (sequential scan)** (`app.py`)
IBWorker is single-threaded. 3 parallel workers created a queue where Worker 3 expired before being served. Sequential scan (max_workers=1) gives every ETF the full IBWorker. Scan takes ~3-4 min but all 7 ETFs return `ibkr_live` or `ibkr_cache`.

### Confirmed Working
- 6 CAUTION setups showing: XLF (9/11), XLK (9/11), XLC (8/11), XLY, XLV, XLP
- XLE correctly BLOCKED by VRP (IV/HV=0.62 — HV > IV post-tariff shock, genuine signal)
- QQQ BLOCKED by Strike OTM Check (KI-067, known separate issue)
- VIX: 17.59 from STA, no more "unavailable"
- Circuit breaker: 0 trips during sequential scan

---

## Remaining Issue (Day 34 P0)

### KI-088: L3 "Run Analysis" still shows stale banner
When user clicks "Run Analysis" from analysis panel, `analyze_etf()` gets `underlying_hint=None` (frontend doesn't send `last_close`) → calls `get_underlying_price()` via IBKR → fails → stale chain → banner. Fix is one block in `analyze_etf()`: STA fallback for `underlying_hint` when None (same pattern as `_run_one` fix). See KI-088 in KNOWN_ISSUES_DAY33.md for exact code.

---

## Current Test Count
33 tests (pytest, 5 files) — all passing.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-088 | HIGH | L3 Run Analysis stale banner — STA underlying price fallback needed in analyze_etf() |
| KI-086 | MEDIUM | app.py ~500 lines — Rule 4 max 150 |
| KI-067 | MEDIUM | QQQ sell_put ITM strikes + ibkr_stale chain |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 |
| KI-075 | MEDIUM | GateExplainer GATE_KB drift |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested |
| KI-059 | HIGH (deferred) | Single-stock bear untested |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | DirectionGuide sell_put "capped" label |

---

## Next Session Priorities (Day 34)

1. **P0 (HIGH):** KI-088 — Add STA fallback for `underlying_hint` in `analyze_etf()`. One-liner fix. Eliminates stale banner on L3.
2. **P1 (MEDIUM):** KI-086 — app.py size cleanup.
3. **P2 (MEDIUM):** KI-067 — QQQ sell_put ITM strike fix.
4. **P3 (LOW):** Skew computation.
