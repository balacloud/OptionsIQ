# OptionsIQ — Known Issues Day 50
> **Last Updated:** Day 50 (May 21, 2026)
> **Previous:** KNOWN_ISSUES_DAY49.md

---

## Resolved This Session (Day 50)

### KI-101: Best Setups watchlist IV/HV ratio shows — when chain IV is missing ✅ RESOLVED Day 50
**Root cause:** `hv_iv_ratio` in `best_setups_service` came solely from `ivr_data.hv_iv_ratio`, which was null whenever Tradier chain returned no IV for the ATM contract.
**Fix (two-layer):**
1. **Live IBKR batch** — `ibkr_provider.get_iv_hv_batch()` calls `reqMktData` ticks 104 (histVol) + 106 (impliedVol) for all 15 ETFs in one round-trip (single `ib.sleep(4.0)`). Fetched once before the Best Setups scan loop in `app.py`. Passed as `live_scanner` dict to `run_one_setup()`.
2. **File cache fallback** — `/etf-scan` Claude command writes `backend/data/scanner_cache.json` (4h TTL) parsed from IBKR Market Screener screenshot. `scanner_service.get_scanner_data(ticker)` reads it when live data unavailable.
**Priority chain:** live IBKR → scanner_cache.json → null (never fabricated).

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 51+.

---

## Resolved History (recent)
- KI-101: IV/HV null in watchlist ✅ Day 50
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
