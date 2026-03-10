# OptionsIQ — Known Issues Day 5
> **Last Updated:** Day 5 (March 10, 2026)
> **Previous:** KNOWN_ISSUES_DAY4.md

---

## Resolved This Session (Day 5)

### KI-019: No IBWorker connection heartbeat → RESOLVED
**Fix:** `IBWorker._run()` now uses `queue.get(timeout=30.0)`. On `queue.Empty`, calls
`self._provider.ib.reqCurrentTime()` and updates `_last_heartbeat`. `is_connected()` now
checks both `ib.isConnected()` flag AND heartbeat freshness (stale > 75s = disconnected).
Detects silent TCP drops within 30-90s without requiring a separate thread.

### STA field mapping mismatch → RESOLVED (Day 5, not previously in KI list)
**File:** `backend/app.py` (`sta_fetch` endpoint)
**Problem:** `sta_fetch()` read `sr.get("levels", {})` but STA's `/api/sr/<ticker>` uses
camelCase top-level fields — no `levels` nested object. All swing fields returned `None`.
**Fix:** Updated to read `sr.get("suggestedEntry")`, `sr.get("suggestedStop")`,
`sr.get("suggestedTarget")`, `sr.get("riskReward")`, `sr["meta"]["adx"]["adx"]`,
`patterns["patterns"]["vcp"]` (not `patterns["vcp"]`), earnings `days_until` (not `days_away`),
FOMC from `context.cycles.cards[name=FOMC].raw_value`.
**Verified:** CTRA now shows Entry 29.57, Stop 27.59, Target 32.0, RR 1.23, ADX 38.0.

### spy_above_200sma always None → RESOLVED (Day 5, not previously in KI list)
**File:** `backend/app.py` (`sta_fetch` + analyze payload parser)
**Problem:** STA doesn't expose `spy_above_200sma` or `spy_5day_return`. Both returned `None`.
`bool(None) = False` → market_regime gate always FAILED even when SPY is above 200 SMA.
**Fix:** `sta_fetch()` now computes `spy_above_200sma` and `spy_5day_return` from yfinance SPY
history. Fails safe to `True` if yfinance unavailable. Payload parser uses explicit None check:
`bool(payload.get("spy_above_200sma") if payload.get("spy_above_200sma") is not None else True)`.

### Direction locking SELL signal → RESOLVED (Day 5)
**File:** `frontend/src/App.jsx`, `frontend/src/components/DirectionSelector.jsx`
**Problem:** `lockedBySignal` only locked directions for BUY signal. SELL signal locked nothing,
allowing contradictory directions (buy_call/sell_put when signal=SELL).
**Fix:** SELL signal now locks `['buy_call', 'sell_put']`. BUY signal locks `['sell_call', 'buy_put']`.
Tooltip shows correct message per signal type.

### Struct cache price drift (stale $47.69 NVDA) → RESOLVED (Day 5)
**File:** `backend/ibkr_provider.py`
**Problem:** 4h in-memory structure cache stored strikes/expiries but not the underlying price.
If stock price moved >15% (e.g. gap up/down, or stale cache across restart), the direction-aware
strike window would select wrong strikes → all contracts fail qualification → empty chain.
**Fix:** `_StructCacheEntry` now stores `underlying_at_cache`. Cache invalidates if current
underlying differs >15% from cached price.

---

## Still Open

### KI-001 / KI-023: app.py God Object → PARTIALLY RESOLVED
**Status:** app.py 821 → 558 lines (KI-018 done Day 4, SPY computation added Day 5).
Still needs `analyze_service.py` extraction.
**Remaining:** Create `analyze_service.py`. Extract `_merge_swing`, `_extract_iv_data`,
`_behavioral_checks`, gate assembly. app.py → ≤150 lines routes-only.
**Phase:** 6 (Day 6 P1)

### KI-003: mock_provider.py partially hardcoded AME structure
**Status:** No change. yfinance covers fallback adequately.
**Phase:** Backlog

### KI-005 / KI-022: Synthetic swing defaults not surfaced to user
**Status:** No change. When STA doesn't have SR levels for a ticker, backend silently uses
`stop = underlying × 0.92` etc. User sees P&L table with fabricated levels — no warning.
**Fix needed:** Return `"swing_data_quality": "synthetic"` in response. Frontend shows amber banner.
**Phase:** 6

### KI-008: fomc_days_away not auto-computed in manual mode
**Status:** PARTIALLY RESOLVED. STA-connected mode now correctly reads FOMC days from
`context.cycles.cards`. Manual mode still defaults to 30. Should compute from `constants.FOMC_DATES`.
**Phase:** 6 (low priority — STA is usually connected)

### KI-013: API URL hardcoded in useOptionsData.js
**Phase:** Backlog

---

## New Issues Found Day 5

### KI-024: No market hours detection — off-hours analysis returns zero greeks
**File:** `backend/ibkr_provider.py`
**Problem:** When market is closed (outside 9:30am–4:00pm ET Mon-Fri), IBKR's `reqTickers`
returns contracts with bid=0, ask=0, greeks=None. This causes:
- theta_burn gate: 999% (division by zero premium)
- liquidity gate: FAIL (OI=0, Vol/OI=0, Prem=0)
- Position sizing: lots_allowed=0
- data_source shows `ibkr_stale` (live fetch times out, falls back to stale cache)
**Impact:** Pre-market/after-hours/weekend analysis is misleading — looks like a broken analysis.
**Fix:** Detect market hours. When closed, skip `reqTickers` and use Black-Scholes greeks
from `bs_calculator.py` instead. Analysis becomes useful off-hours with estimated greeks.
**Phase:** 6 (HIGH — impactful for any off-hours review)

### KI-025: Sparse strike qualification for large-cap stocks (NVDA at $180+)
**File:** `backend/ibkr_provider.py`
**Problem:** `reqSecDefOptParams` returns a theoretical union of strikes across ALL expiries.
For specific expiries (especially weeklies), only a subset of those strikes have actual contracts.
For NVDA ITM buy_call window (8-20% below $180 = $144-$165), only $160 and $165 qualify for
monthly expiries. Weekly expiries have even fewer. Result: 2 contracts instead of 6+ needed.
**Mitigation applied:** SMART_MAX_EXPIRIES 1→2, SMART_MAX_STRIKES 4→6, broad-window retry
when <3 contracts qualify. Still only gets 2 contracts for deep ITM NVDA on weekends.
**Full fix needed:** When market is open, the broad retry picks ATM/near-ATM strikes which DO
have contracts — need weekday verification. Consider widening ITM window to 5-15% for high-price stocks.
**Phase:** 6 (verify weekday behavior first)

---

## Summary

| Severity | Count | Resolved (Day 5) | Remaining |
|----------|-------|-----------------|-----------|
| Critical | 0 | 0 | 0 |
| High | 2 | 0 | 2 (KI-024, KI-025) |
| Medium | 3 | 3 (KI-019, STA map, spy_above) | 0 |
| Low/Frontend | 2 | 2 (direction lock, struct drift) | 0 |
| Still open from Day 4 | 4 | 0 | 4 (KI-001, KI-005, KI-008, KI-013) |
| **Total** | **11** | **5** | **6** |
