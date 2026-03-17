# OptionsIQ — Known Issues Day 7
> **Last Updated:** Day 7 (March 10, 2026)
> **Previous:** KNOWN_ISSUES_DAY6.md

---

## Resolved This Session (Day 7)

### KI-021: sell_call and buy_put strategy builders missing → RESOLVED
**File:** `backend/strategy_ranker.py`
**Problem:** `sell_call` routed to `_rank_track_a` (long call / bull call spread — wrong direction).
`buy_put` routed to `_rank_track_b` (sell put — wrong direction entirely).
**Fix:**
- `rank()` now has explicit `if` branch per direction (all 4)
- `_rank_sell_call()`: bear call spread (delta 0.30 short / 0.15 long) + higher PoP variant + far OTM option
- `_rank_buy_put()`: ITM put (delta ~0.68) + bear put spread (short leg at target1) + ATM put
- `_build_long_put()`, `_build_bear_put_spread()` added
- `_rank_track_b` (sell_put) unchanged — still correct

### KI-027: reqTickers() never fires tickOptionComputation → RESOLVED
**File:** `backend/ibkr_provider.py`
**Problem:** `reqTickers()` is a snapshot wrapper that does NOT reliably trigger
`tickOptionComputation` (IBKR tick type 13 = modelGreeks). Result: `delta=None`, `gamma=None`
for all contracts during market hours despite valid OPRA subscription.
**Root cause confirmed via:** IBKR TWS API docs + ib_insync community — tick type 13 only fires
via `reqMktData()` with `snapshot=False`.
**Fix:**
- Phase 4c: replaced `reqTickers(*chunk)` batch loop with `reqMktData(snapshot=False)` per contract
- Subscribe all contracts, `ib.sleep(3)`, extract from live Ticker objects, cancel all subscriptions
- Phase 4d: if 0 greeks after 3s, `ib.sleep(5)` more and re-read (subscriptions still active)
- Phase 4e: if still 0 greeks after extended wait, fall back to BS greeks with 20-day HV
- `IBKR_BATCH_SIZE` import and `batch_size` variable removed (batch loop eliminated)
**Status:** Code change done. Live market-hours verification required (Day 8 P0).

---

## Still Open

### KI-026: reqMktData live greeks unverified (HIGH — Day 8 P0)
**File:** `backend/ibkr_provider.py`
reqTickers→reqMktData change was made but not yet tested during market hours with IB Gateway live.
Must confirm `greeks_pct > 0` and `delta != 0.0` from IBKR (not Phase 4e BS fallback).
**Test:** Run AMD analyze 9:30am–4:00pm ET. Check log for "Phase 4e" message — if it appears,
reqMktData still not getting greeks and needs further investigation.

### KI-025: Sparse strike qualification for large-cap stocks (NVDA $180+)
**File:** `backend/ibkr_provider.py`
NVDA ITM buy_call window: only 2 contracts qualify on weekends.
Broad retry mitigates but weekday live verification still needed.

### KI-001/KI-023: app.py still 558 lines
`analyze_service.py` not yet created. Business logic still in app.py.
Target: routes-only ≤150 lines.

### KI-022/KI-005: Synthetic swing defaults silent
No banner when stop/target are fabricated from defaults (not from STA or manual entry).

### KI-008: fomc_days_away manual mode defaults to 30
When STA offline and user doesn't enter FOMC days, hardcoded 30 used silently.

### KI-013: API URL hardcoded in useOptionsData.js
`http://localhost:5051` hardcoded. Low priority for single-user tool.

---

## Summary

| Severity | Count | Resolved (Day 7) | Remaining |
|----------|-------|-----------------|-----------|
| High | 4 | 2 (KI-021, KI-027) | 2 (KI-026 verify, KI-025 verify) |
| Medium | 2 | 0 | 2 (KI-001/023, KI-022/005) |
| Low | 2 | 0 | 2 (KI-008, KI-013) |
| **Total** | **8** | **2** | **6** |
