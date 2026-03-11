# OptionsIQ — Known Issues Day 9
> **Last Updated:** Day 9 (March 11, 2026)
> **Previous:** KNOWN_ISSUES_DAY7.md (Day 8 was process-only, no new issues)

---

## Resolved This Session (Day 9)

### KI-026: reqMktData live greeks unverified → RESOLVED ✅
**File:** `backend/ibkr_provider.py`
**Problem:** reqMktData(snapshot=False) change was done Day 7 but not tested during market hours.
**Resolution:** Confirmed live during market hours Day 9.
- `data_source: ibkr_live`, `greeks_complete_pct: 100%`
- Phase 4e BS fallback NEVER triggered — usopt reconnects lazily on first options request
- `delta`, `gamma`, `theta`, `vega` all populated from live IBKR modelGreeks

### KI-030: hv_20 = 613.17% on AMD → RESOLVED ✅ (band-aid)
**File:** `backend/data/iv_history.db` (SQL direct fix)
**Problem:** ohlcv_daily table had 20 rows with AMD `close < 150` (mid-2025 prices ~$95) mixed
with 2026 prices (~$205), creating fake 88% log returns → `compute_hv` returned 613%.
**Fix:** Deleted the 20 corrupt rows via SQL. hv_20 now correct: 52.28%.
**Root cause still present:** `compute_hv` uses `ORDER BY date DESC LIMIT 21` which assumes
contiguous daily data. A temporal gap produces bogus returns. Proper fix → KI-034.

### KI-031: pnl_calculator crash on None → RESOLVED ✅
**File:** `backend/pnl_calculator.py`
**Problem:** `_fmt(None)` crashed with TypeError when strategy fields were None.
Also: `_scenario_pnl` returned 0.0 silently for all Day 7 strategy types (bear_call_spread,
sell_call, itm_put, atm_put) — they had no formula.
**Fix:**
- Added None guard to `_fmt(v)`
- Added `_scenario_pnl` handlers for: `itm_put`, `atm_put`, `bear_call_spread`, `sell_call`
- Fixed `spread` handler: now checks `right` field — puts use `long_strike - scenario_price`,
  calls use `scenario_price - long_strike` (was always using call-side formula)

### KI-033: sell_call only produces 1 strategy (same strike for short + protection) → RESOLVED ✅
**Files:** `backend/constants.py`, `backend/ibkr_provider.py`
**Problem:** `SELL_CALL_STRIKE_HIGH_PCT` was 0.08 (only reached delta ~0.30 range).
Bear call spread needs short leg at delta ~0.30 AND protection leg at delta ~0.15,
requiring strikes ~12-15% OTM. Proximity sort + SMART_MAX_STRIKES=6 cut off OTM strikes
because $2.5-increment stubs (from reqSecDefOptParams) filled all 6 proximity slots.
**Fix:**
1. `SELL_CALL_STRIKE_HIGH_PCT`: 0.08 → 0.15 (window reaches delta ~0.15 range)
2. `SELL_PUT_STRIKE_LOW_PCT`: 0.08 → 0.15 (symmetric for sell_put)
3. `SMART_MAX_STRIKES`: 6 → 12 (buffer for $2.5 stubs that fail qualifyContracts)
4. `SMART_MAX_CONTRACTS`: 12 → 26 (12 strikes × 2 expiries + ATM anchors)
5. `_fetch_structure` direction-aware sort:
   - `sell_call` → ascending by strike (ATM edge first, OTM last)
   - `sell_put` → descending by strike (ATM edge first, OTM downward)
   - buy directions → proximity to underlying (unchanged)
**Result:** AMD sell_call now returns 2 strategies: 225/230 bear_call_spread + far-OTM sell_call

---

## Still Open

### KI-035: OI = 0 for all individual option contracts via reqMktData (MEDIUM — Day 10)
**File:** `backend/ibkr_provider.py` lines 563-567
**Problem:** `callOpenInterest` / `putOpenInterest` are aggregate fields on the underlying
stock's Ticker — NOT on individual option contract subscriptions. Individual option OI
is available via `ticker.optOpenInterest` (tick type 22), but this may require
`genericTickList="101"` to be requested. Currently using `genericTickList=""`.
**Symptom:** All option OI = 0 → liquidity gate always fails (MIN_OPEN_INTEREST=1000)
even for highly liquid contracts (AMD, NVDA, AAPL).
**Fix path:** Change `genericTickList=""` → `genericTickList="101"` in reqMktData calls
AND read `ticker.optOpenInterest` instead of `callOpenInterest`/`putOpenInterest`.
Note: `ticker.optOpenInterest` fix was already applied in Day 9 but OI field may still
be None until genericTickList is updated. Test Day 10 market open.

### KI-034: OHLCV temporal gap not validated at write time (LOW)
**File:** `backend/iv_store.py` (compute_hv or data write path)
**Problem:** `compute_hv` does `ORDER BY date DESC LIMIT 21` assuming contiguous daily data.
If there's a gap (e.g. sparse historical seeding), log returns include multi-day jumps
causing wildly inflated HV values.
**Fix:** Add write-time validation: reject `ohlcv_daily` rows where `close` deviates >50%
from the prior close. Or: compute returns only between consecutive calendar trading days.

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM — verify Day 10)
**File:** `backend/ibkr_provider.py`
NVDA buy_put: only 3 contracts qualify during market hours (need more ITM put strikes).
May be resolved by SMART_MAX_STRIKES increase (6→12). Verify Day 10.

### KI-001/KI-023: app.py still 558 lines (MEDIUM)
`analyze_service.py` not yet created. Business logic still in app.py.
Target: routes-only ≤150 lines.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)
No banner when stop/target are fabricated from defaults (not from STA or manual entry).

### KI-008: fomc_days_away manual mode defaults to 30 (LOW)
When STA offline and user doesn't enter FOMC days, hardcoded 30 used silently.

### KI-013: API URL hardcoded in useOptionsData.js (LOW)
`http://localhost:5051` hardcoded. Low priority for single-user tool.

---

## Planned (New Day 10)

### KI-036: Alpaca data provider missing — needs alpaca_provider.py
**Files:** New file needed: `backend/alpaca_provider.py`
**Context:** Alpaca Markets free tier provides options data via REST API:
- Endpoint: `https://data.alpaca.markets/v1beta1/options/snapshots/{symbol}`
- Fields: bid, ask, delta, gamma, theta, vega, IV, open_interest, volume — all in one call
- Free tier: `feed=indicative` (15-min delayed, OK for swing analysis)
- Paid tier: `feed=opra` ($99/mo, real-time)
- Pure REST — no async/threading conflicts, no Gateway dependency
- This is a significantly better fallback than yfinance (which has NO greeks)
**Needs:** API secret (user to add `APLACA_SECRET=...` to `.env`)
**Integration plan:** Replace yfinance in cascade: IBKR Live → Alpaca (indicative) → yfinance → Mock
**Priority:** Day 10 P1 (after KI-035 OI fix)

---

## Summary

| Severity | Count | Resolved (Day 9) | Remaining |
|----------|-------|-----------------|-----------|
| High | 3 | 3 (KI-026 ✅, KI-030 ✅, KI-033 ✅) | 0 |
| Medium | 5 | 1 (KI-031 ✅) | 4 (KI-035, KI-025, KI-001/023, KI-022) |
| Low | 3 | 0 | 3 (KI-034, KI-008, KI-013) |
| Planned | 1 | — | 1 (KI-036 Alpaca) |
| **Total** | **12** | **4** | **8** |
