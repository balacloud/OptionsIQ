# OptionsIQ — Day 5 Status
> **Date:** March 10, 2026
> **Version:** v0.5
> **Phase:** Phase 3 complete → Phase 4 (market hours + analyze_service.py)

---

## What Was Done Today (Day 5)

### IBWorker Heartbeat (KI-019) ✅
- `_run()` uses `queue.get(timeout=30.0)` — fires `reqCurrentTime()` every 30s when idle
- `_last_heartbeat` updated on any successful IBKR call
- `is_connected()` now checks heartbeat freshness (stale > 75s = disconnected)
- Detects silent TCP drops without requiring a separate thread

### STA Field Mapping Fix ✅
- Root cause: `sta_fetch()` read `sr.get("levels", {})` — no such key in STA API
- STA uses camelCase top-level: `suggestedEntry`, `suggestedStop`, `suggestedTarget`, `riskReward`
- Fixed all 5 STA endpoints mapped to correct field paths
- Verified CTRA: Entry 29.57 / Stop 27.59 / Target 32.0 / RR 1.23 / ADX 38.0 ✓

### SPY Above 200 SMA Fix ✅
- `spy_above_200sma` now computed from yfinance SPY vs 200-day SMA
- `spy_5day_return` computed from 5-day SPY price history
- Fails safe to `True` if yfinance unavailable — no false Market Regime FAILs
- `bool(None)` payload parsing bug fixed in analyze endpoint

### Direction Locking Fixed (SELL signal) ✅
- SELL signal now correctly locks `buy_call` and `sell_put`
- BUY locks `sell_call` and `buy_put` (already existed)
- Tooltip updated to show correct lock reason per signal

### IBKR Strike Qualification Improvements ✅
- `_StructCacheEntry` now stores `underlying_at_cache` — invalidates on >15% price drift
- `SMART_MAX_EXPIRIES`: 1 → 2 (backup expiry when first has sparse strikes)
- `SMART_MAX_STRIKES`: 4 → 6 (more candidates to survive qualification filter)
- `SMART_MAX_CONTRACTS`: 8 → 12
- Broad-window retry (<3 qualified → retry with ±15% ATM window across 3 expiries)

### start.sh Fixes ✅
- `.env` check corrected to `backend/.env` (was checking `$ROOT/.env`)
- `venv` creation logic fixed (was broken `set -e` operator precedence)

---

## Live Testing Results (Day 5)

| Ticker | Result | Notes |
|--------|--------|-------|
| CTRA | STA Live badge now shows full data | Entry/Stop/Target populated correctly |
| NVDA | market_regime PASS, theta_burn PASS | Off-hours: 2 contracts, no greeks (expected) |
| AMD | Working from previous session | — |

---

## Current State After Day 5

| Area | Status |
|------|--------|
| app.py | 558 lines — still needs analyze_service.py extraction (Day 6 P1) |
| ib_worker.py | COMPLETE — queue poisoning + heartbeat + RequestTimeout |
| ibkr_provider.py | COMPLETE — direction-aware, struct cache (drift-aware), broad retry |
| data_service.py | COMPLETE — single CB, SQLite cache, background refresh dedup |
| sta_fetch | FIXED — correct STA API field mapping, SPY from yfinance |
| Frontend | COMPLETE — ticker override, STA offline, direction locking |
| Concurrency arch | ALL 5 PROBLEMS RESOLVED (P1-P4 from CONCURRENCY_ARCHITECTURE.md) |

---

## Day 6 Priorities

1. **KI-024: Market hours detection** — skip reqTickers when market closed, use BS greeks
   → off-hours analysis becomes useful, not broken
2. **P1: Create `analyze_service.py`** — extract business logic from app.py (558 → ≤150 lines)
3. **Paper trade end-to-end test** — record trade when all gates pass, verify mark-to-market P&L
4. **Weekday NVDA verification** — confirm broad retry works with real greeks during market hours
5. **Synthetic swing defaults warning** (KI-005/KI-022) — amber banner when stop/target are fabricated
