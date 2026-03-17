# OptionsIQ — Day 7 Status
> **Date:** March 10, 2026
> **Version:** v0.7
> **Phase:** Phase 4 in progress — reqMktData fix done, live greeks test pending

---

## What Was Done Today (Day 7)

### Strategy Ranker — All 4 Directions (KI-021) ✅
- `sell_call` was routing to `_rank_track_a` (buy_call builder) — wrong strategies shown
- `buy_put` was routing to `_rank_track_b` (sell_put builder) — wrong strategies shown
- Added `_rank_sell_call()`: bear call spread options (delta 0.30/0.15 + higher PoP variant)
- Added `_rank_buy_put()`: ITM long put + bear put spread + ATM long put
- Added `_build_long_put()` and `_build_bear_put_spread()` helper builders
- `rank()` now has explicit branch for all 4 directions

### reqMktData Fix — modelGreeks Root Cause (KI-027) ✅ (code only, live test pending)
- **Root cause diagnosed:** `reqTickers()` does NOT fire `tickOptionComputation` (tick type 13)
  reliably — it's a snapshot wrapper that misses the async greek computation callback
- **Confirmed via:** IBKR TWS API docs + ib_insync community research
- **Fix:** Replaced entire Phase 4c batch `reqTickers` loop with `reqMktData(snapshot=False)`
  per contract. Subscribe all, sleep(3), read live Ticker objects, cancel subscriptions.
- Phase 4d: extended wait (sleep 5 more if 0 greeks after initial 3s wait)
- Phase 4e: BS fallback (HV-based) if usopt still silent after extended wait
- Removed `IBKR_BATCH_SIZE` import + `batch_size` variable (batch loop gone)

### OPRA Subscription Confirmed Adequate
- Research confirmed: "US Equity and Options Add-On Streaming Bundle (NP)" includes OPRA
- No additional subscription needed
- IB Gateway not sending 2104 for usopt is a known IB Gateway behavior — data can still flow

### Stale AMD Chain Cache Cleared
- AMD chain_cache had strikes from when AMD was ~182 — IBKR rejected as "No security definition"
- Cleared manually. Fresh fetch on next analyze will use current price (~205).

---

## Live Testing Results (Day 7)

| Test | Result | Notes |
|------|--------|-------|
| AMD buy_call (market closed) | greeks_pct=100% via BS fallback | Phase 4e working correctly |
| AMD underlying price | 204.83 (live from IBKR) | usfarm OK after IB Gateway restart |
| usopt greeks during market hours | NOT TESTED | IB Gateway off — test Day 8 |

---

## Current State After Day 7

| Area | Status |
|------|--------|
| app.py | 558 lines — still needs analyze_service.py extraction (Day 8 P1) |
| ibkr_provider.py | reqMktData fix done — live verification pending |
| strategy_ranker.py | All 4 directions have explicit builders |
| gate_engine.py | FROZEN — correct for all 4 directions |
| data_service.py | COMPLETE |
| BS fallback (Phase 4e) | Working — covers usopt failures gracefully |

---

## Day 8 Priorities

1. **P0: Live greeks verification** — IB Gateway restart → AMD analyze during market hours
   → confirm `greeks_pct > 0` from IBKR live (not Phase 4e BS fallback)
2. **P1: Create `analyze_service.py`** — extract business logic from app.py (558 → ≤150 lines)
3. **P2: Paper trade end-to-end test** — record trade when gates pass, verify mark-to-market P&L
4. **P2: Test all 4 directions live** — sell_call (bear call spread), buy_put (long put), sell_put
