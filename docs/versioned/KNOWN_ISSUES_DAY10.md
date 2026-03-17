# OptionsIQ — Known Issues Day 10
> **Last Updated:** Day 10 (March 12, 2026)
> **Previous:** KNOWN_ISSUES_DAY9.md

---

## Resolved This Session (Day 10)

### KI-035: OI = 0 for all individual option contracts via reqMktData → RESOLVED ✅
**File:** `backend/ibkr_provider.py` line 593
**Problem:** `genericTickList=""` didn't request tick type 22 (optOpenInterest) for individual
option contracts. OI was always 0 → liquidity gate always failed.
**Fix:** Changed `genericTickList=""` → `genericTickList="101"` in reqMktData call.
**Status:** Code fix applied. Needs market-hours verification Day 11.

### KI-036: Alpaca data provider missing → RESOLVED ✅
**File:** `backend/alpaca_provider.py` (NEW — ~296 lines)
**Problem:** No REST fallback provider between IBKR cache and yfinance.
**Fix:** Created `AlpacaProvider` class with:
- `OptionHistoricalDataClient` via alpaca-py SDK
- OCC symbol parsing, direction-aware DTE/strike windows
- Output format matches ibkr_provider exactly
- Wired into DataService cascade as tier 4 (between stale cache and yfinance)
- Wired into app.py with graceful degradation
**Live test findings:**
- Greeks: ✅ 100% within ATM ±15% zone
- IV: ✅ 61% overall (100% ATM zone)
- OI: ❌ field does NOT exist in OptionsSnapshot model (always 0)
- Volume: ❌ field does NOT exist in OptionsSnapshot model (always 0)
- Bid/ask: ✅ 87-100%

---

## Still Open

### KI-037: MarketData.app historical IV/greeks = null → CONFIRMED PLATFORM LIMITATION ✅
**Context:** MarketData.app Starter Trial tested live. Current chain returns full greeks+IV.
Historical chain (using `?date=` parameter) returns `iv=null, delta=null` for all contracts.
**Confirmed:** Support replied March 13, 2026: *"Our historical data does not include IV/greeks
at this time. This is something we hope to add soon."*
**Conclusion:** IBKR is the only source for historical IV under $30/mo. MarketData.app is still
useful as a current-chain provider (greeks+IV+OI+volume) but cannot help with IVR calculation.

### KI-038: Alpaca OI/volume fields missing from OptionsSnapshot model (LOW)
**File:** `backend/alpaca_provider.py`
**Problem:** `open_interest` and `volume` fields do not exist in Alpaca's `OptionsSnapshot` model.
`hasattr(snapshot, 'open_interest')` → False. Liquidity gate always fails on Alpaca data.
**Workaround:** OI hardcoded to 0 in provider output. Documented in research doc.
**Impact:** Alpaca cannot support liquidity gate (OI ≥ 1000). Still better than yfinance (has greeks).

### KI-034: OHLCV temporal gap not validated at write time (LOW)
**File:** `backend/iv_store.py` (compute_hv or data write path)
**Problem:** `compute_hv` does `ORDER BY date DESC LIMIT 21` assuming contiguous daily data.

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM — verify Day 11)
**File:** `backend/ibkr_provider.py`
NVDA buy_put: only 3 contracts qualify during market hours. May be resolved by
SMART_MAX_STRIKES increase (6→12). Needs verification.

### KI-001/KI-023: app.py still 558 lines (MEDIUM)
`analyze_service.py` not yet created. Business logic still in app.py.
Target: routes-only ≤150 lines.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)
No banner when stop/target are fabricated from defaults.

### KI-008: fomc_days_away manual mode defaults to 30 (LOW)
When STA offline and user doesn't enter FOMC days, hardcoded 30 used silently.

### KI-013: API URL hardcoded in useOptionsData.js (LOW)
`http://localhost:5051` hardcoded. Low priority for single-user tool.

---

## Planned (Day 11)

### KI-039: marketdata_provider.py — MarketData.app integration
**Files:** New file needed: `backend/marketdata_provider.py`
**Context:** MarketData.app Starter ($12/mo) provides current chain with full greeks+IV+OI+volume.
15-min delay on paid plan. Better than Alpaca (has OI/volume). Pending support ticket response
on historical IV availability.
**Integration plan:** Wire as tier 2.5 (between IBKR stale cache and Alpaca) in DataService cascade.
**Priority:** After support ticket response received.

---

## Summary

| Severity | Count | Resolved (Day 10) | Remaining |
|----------|-------|-------------------|-----------|
| High | 1 | 1 (KI-035 ✅) | 0 |
| Medium | 4 | 0 | 4 (KI-037, KI-025, KI-001/023, KI-022) |
| Low | 4 | 1 (KI-036 ✅) | 3 (KI-038, KI-034, KI-008, KI-013) |
| Planned | 1 | — | 1 (KI-039 MarketData.app) |
| **Total** | **10** | **2** | **8** |
