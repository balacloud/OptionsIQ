# OptionsIQ — Project Status Day 34
> **Date:** April 30, 2026
> **Version:** v0.25.1
> **Previous:** PROJECT_STATUS_DAY33_SHORT.md

---

## What Shipped Today

### KI-088: L3 "Run Analysis" Stale Banner — FIXED

**Root cause (traced by Opus):** `analyze_etf()` read `underlying_hint` from `payload.get("last_close")` — always None from the frontend. With no hint, `ibkr_provider.get_options_chain()` internally called `reqMktData(snapshot=True)` + sleep 1.2s → bid/ask/last all None → `IBKRNotAvailableError` → chain fetch fell through to stale SQLite cache → `data_source: ibkr_stale` → banner.

**Fix:** Added `_resolve_underlying_hint(ticker, payload)` helper to `analyze_service.py`.
Precedence: payload `last_close` → STA `/api/stock/{ticker}` currentPrice → None.
Called at the start of `analyze_etf()` before `get_chain()`. The hint bypasses the internal `reqMktData` snapshot call entirely.

**Verified:**
- XLF: `data_source: ibkr_live`, `underlying: 52.02` ✅
- XLK: `data_source: ibkr_live` ✅
- STA-down: falls back gracefully to `ibkr_cache`, no error ✅
- 36 tests pass (was 33) ✅

### `_run_one` in app.py simplified
Inline STA fetch removed — same logic now lives in `_resolve_underlying_hint`. Best Setups scan behavior unchanged.

### Data Provenance updated
`underlying_price` field added to `field_resolution` in `data_health_service.py`.
`DataProvenance.jsx` FIELDS array updated to show it. Source: "sta".

### MarketData.app diagnostic
Live chain test confirmed: IV, delta, theta, gamma, vega, bid/ask, OI, volume all present per contract.
Historical IV: not available (0 contracts for past dates). IVR endpoint: no_data.
**Recommendation:** Viable as primary chain provider for daily analysis (replaces IBKR chain fetch).
Keep IBKR for nightly IV seeding only. $12/mo. Plan for Day 35.

---

## Architectural Decision (permanent)

**STA is the canonical source for ETF underlying spot price** in all analysis paths.
- Faster than IBKR snapshot (<100ms vs 1.2s unreliable window)
- No rate limits, no connection-state dependencies
- Documented in Data Provenance tab under "Underlying Price"
- Graceful fallback: if STA unreachable, `underlying_hint=None` → IBKR path runs

This is an explicit user choice, not a workaround. STA is the user's own system.

---

## Current Test Count
36 tests (pytest, 6 files) — all passing.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-089 | MEDIUM | MarketData.app as primary chain provider — Day 35 plan |
| KI-086 | MEDIUM | app.py 536 lines — Rule 4 max 150 |
| KI-067 | MEDIUM | QQQ sell_put ITM strikes + ibkr_stale chain |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 |
| KI-075 | MEDIUM | GateExplainer GATE_KB drift |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested |
| KI-059 | HIGH (deferred) | Single-stock bear untested |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | DirectionGuide sell_put "capped" label |

---

## Next Session Priorities (Day 35)

1. **P0 (MEDIUM):** KI-089 — Evaluate MarketData.app as primary chain provider. Subscribe ($12/mo), wire as chain source in `data_service.py` provider cascade (above Alpaca, below IBKR live). Eliminates IBKR chain dependency during trading hours.
2. **P1 (MEDIUM):** KI-086 — app.py size cleanup. Move `_seed_iv_for_ticker` + `seed_iv_all` + `_run_one` to service modules.
3. **P2 (MEDIUM):** KI-067 — QQQ sell_put ITM strike fix.
4. **P3 (LOW):** Skew computation.
5. **Live testing** — market opens tomorrow. Run Best Setups scan, click through to L3, verify no stale banner, paper trade if a GO appears.
