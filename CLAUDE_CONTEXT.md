# OptionsIQ — Claude Context
> **Last Updated:** Day 5 (March 10, 2026)
> **Current Version:** v0.5 (all concurrency problems resolved, STA mapping fixed, off-hours bug diagnosed)
> **Project Phase:** Phase 3 complete → Phase 4 (market hours detection + analyze_service.py)

---

## What This System Does

OptionsIQ is a personal options analysis tool. It takes a stock ticker, pulls the live options chain from IBKR, runs gate checks, and recommends the top 3 strike/expiry combinations for the chosen direction. It records paper trades with live mark-to-market.

It is NOT a broker. It sends zero orders to IBKR. Analysis only.

---

## Relationship to STA

- **STA** (Swing Trade Analyzer) runs at `localhost:5001` — separate repo, feature-frozen
- **OptionsIQ** calls STA API endpoints to import swing fields (stop, target, ADX, pattern, etc.)
- If STA is offline, OptionsIQ falls back to Manual mode — user enters fields directly
- Zero code shared between the two projects — integration is HTTP only

---

## Current State

| Area | Status | Notes |
|------|--------|-------|
| Backend | Phase 3 complete | All 5 concurrency problems resolved |
| Frontend | Done + Day 4+5 fixes | Direction locking fixed (SELL), ticker override, STA offline |
| IBKR connection | WORKING | Live confirmed: AMD/AAPL/MEOH/CTRA/NVDA, account U11574928 |
| Gate logic | Correct (frozen) | gate_engine.py verified correct |
| P&L math | Correct (frozen) | pnl_calculator.py verified correct |
| Strategy ranking | Correct (frozen) | right=None fixed (KI-020) |
| IV store | Correct (frozen) | iv_store.py verified correct |
| constants.py | DONE | All thresholds + direction-aware DTE/strike windows |
| bs_calculator.py | DONE | Black-Scholes greeks fallback |
| ib_worker.py | DONE (Day 5) | Queue poisoning + heartbeat + RequestTimeout |
| yfinance_provider.py | DONE | Middle tier, BS greeks fill |
| data_service.py | DONE | Provider cascade + SQLite cache + single circuit breaker |
| ibkr_provider.py | DONE (Day 5) | Direction-aware, struct cache (drift-aware), broad retry |
| analyze_service.py | NOT CREATED | Day 6 P1 — extract from app.py |
| app.py | Partial refactor | 558 lines. Still needs analyze_service.py split. |

### Backend Files (current state)
```
backend/
  app.py              558 lines — routes + helpers. Needs analyze_service.py split (Day 6 P1).
  constants.py        DONE — all thresholds, direction-aware DTE/strike windows
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single thread, submit() queue, expires_at, heartbeat (30s idle)
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE — provider cascade + SQLite cache + AUTHORITATIVE circuit breaker
  ibkr_provider.py    DONE — direction-aware fetch, struct cache (drift-aware), broad retry
  mock_provider.py    PARTIAL — still partially hardcoded (low priority)
  gate_engine.py      FROZEN — math correct
  strategy_ranker.py  FROZEN — math correct, right field fixed
  pnl_calculator.py   FROZEN — math correct
  iv_store.py         FROZEN — math correct

  # TO CREATE:
  analyze_service.py  Day 6 P1 — extract _merge_swing, _extract_iv_data, _behavioral_checks
```

---

## Architecture

**Backend:** Flask on port 5051
**Frontend:** React on port 3050
**IB Gateway:** 127.0.0.1:4001 (live account U11574928)
**Database:** SQLite at `backend/data/` (chain_cache.db + iv_store.db)

### Data Provider Hierarchy (live-first)
```
[1] IBKR Live (reqMarketDataType=1)  ← DEFAULT FOR ALL OPERATIONS
[2] IBKR Cache (SQLite, TTL 2 min)  ← shows "Using cached chain" banner
[3] yfinance (emergency fallback)    ← shows "Live data unavailable" banner
[4] Mock (dev/CI testing ONLY)       ← NEVER used for paper trades
```

### IBWorker Thread Model
```
Flask thread → IBWorker.submit(fn, timeout=24s) → queue.Queue → "ib-worker" thread
                ↓ (if timeout expires on Flask side)         ↓
          TimeoutError raised                          _Request.expires_at checked
          (request already in queue)                   → expired = discard, log warning
                                                       → fresh = execute normally

Idle > 30s: worker sends reqCurrentTime() → _last_heartbeat updated
is_connected(): checks ib.isConnected() flag AND _last_heartbeat < 75s ago
```
**Critical:** All IBKRProvider calls MUST go through IBWorker.submit(). Never call
ibkr_provider methods directly from Flask routes or helpers.

### Direction-Aware Chain Fetch
```
buy_call  → DTE 45-90 (buyer sweet spot) + strikes 8-20% ITM below underlying
buy_put   → DTE 45-90 (buyer sweet spot) + strikes 8-20% ITM above underlying
sell_call → DTE 21-45 (seller sweet spot) + strikes ATM ±6%
sell_put  → DTE 21-45 (seller sweet spot) + strikes ATM ±6%
```
Structure cache (4h in-memory, invalidates if underlying drifts >15%) avoids repeated reqSecDefOptParams.
When <3 contracts qualify, automatic retry with ±15% broad window across 3 expiries.

### Market Hours Behavior
```
MARKET OPEN (9:30am–4:00pm ET, Mon–Fri):
  reqTickers returns live bid/ask/greeks → all gates work correctly
  data_source = "ibkr_live", greeks_pct ~80-100%

MARKET CLOSED (evenings, weekends, pre-market):
  reqTickers returns zero quotes → greeks_pct = 0%
  liquidity gate FAILS (OI=0), theta_burn may show 999%
  data_source falls to "ibkr_stale" (cache hit) or live with empty contracts
  FIX PLANNED (KI-024): detect market hours → use BS greeks when closed
```

### STA Field Mapping (verified Day 5)
```
STA /api/sr/{ticker}: suggestedEntry → entry_pullback, suggestedStop → stop_loss,
                      suggestedTarget → target1, riskReward → risk_reward,
                      meta.adx.adx → adx, support[-1] → s1_support
STA /api/stock/{ticker}: currentPrice → last_close + entry_momentum
STA /api/patterns/{ticker}: patterns.vcp.confidence → vcp_confidence,
                             patterns.vcp.pivot_price → vcp_pivot
STA /api/earnings/{ticker}: days_until → earnings_days_away (NOT days_away)
STA /api/context/SPY: cycles.cards[FOMC].raw_value → fomc_days_away
yfinance SPY: computed in backend → spy_above_200sma, spy_5day_return
```

---

## Four Directions

| Direction | Market View | Gate Track | Strike Preference |
|-----------|------------|------------|-------------------|
| buy_call | Extremely Bullish | Track A | ITM delta ~0.68 |
| sell_call | Neutral to Bearish | Track A | Far OTM / ATM |
| buy_put | Extremely Bearish | Track B | ITM delta ~-0.68 |
| sell_put | Neutral to Bullish | Track B | Far OTM below support |

**DTE window:** 14 to 120 days (all directions)
**Sweet spot buyers:** 45-90 DTE
**Sweet spot sellers:** 21-45 DTE (enforced by gate logic)

**Direction locking:** BUY signal → locks sell_call + buy_put. SELL signal → locks buy_call + sell_put.

---

## Known Issues

Full list: `docs/versioned/KNOWN_ISSUES_DAY5.md`

Open (Phase 6 — HIGH):
1. **Market hours detection missing** — off-hours reqTickers returns zero data; theta_burn=999%, liquidity FAIL (KI-024)
2. **Sparse strike qualification for large caps** — NVDA ITM window only gets 2 contracts on weekends; verify weekday behavior (KI-025)

Open (Phase 6 — MEDIUM):
3. **analyze_service.py missing** — app.py still 558 lines, target ≤150 (KI-001/KI-023)
4. **Synthetic swing defaults silent** — no banner when stop/target are fabricated (KI-022/KI-005)

Open (Low priority):
5. fomc_days_away manual mode defaults to 30 (KI-008)
6. mock_provider partially hardcoded AME structure (KI-003)
7. API URL hardcoded in useOptionsData.js (KI-013)

---

## Session Log

| Day | Date | What Happened |
|-----|------|--------------|
| Day 1 | Mar 5, 2026 | Project scaffolded. Phase 0 docs created. Codex files ported. |
| Day 2 | Mar 5, 2026 | GOLDEN_RULES enhanced. Full frontend UI redesign (8 files). |
| Day 3 | Mar 6, 2026 | Phase 1+2 complete. IBWorker, DataService, direction-aware fetch. Live IBKR confirmed. |
| Day 4 | Mar 7, 2026 | KI-016 queue poisoning (expires_at). KI-017 RequestTimeout=15. KI-018 legacy CB removed (821→527). KI-020 strategy_ranker right=None. Ticker override + STA offline fixed. MEOH confirmed live. |
| Day 5 | Mar 10, 2026 | KI-019 heartbeat done. STA field mapping fixed (suggestedEntry/Stop/Target). spy_above_200sma from yfinance. Direction lock SELL. Struct cache drift invalidation (15%). SMART_MAX_EXPIRIES 1→2, SMART_MAX_STRIKES 4→6, broad retry <3 contracts. start.sh .env fix. CTRA+NVDA tested. Market-closed behavior diagnosed (KI-024 new). |

---

## Next Session Priorities (Day 6)

### P1 — Market Hours Detection (highest impact)
1. Add `_market_is_open()` to `ibkr_provider.py` — check ET timezone, Mon-Fri 9:30-16:00
2. When closed: skip `reqTickers`, compute greeks from `bs_calculator.py`
3. data_source shows "ibkr_closed" (new tier) — banner: "Market closed — using estimated greeks"
4. Off-hours analysis becomes useful instead of showing 999% theta / 0 OI

### P2 — Create analyze_service.py (must do)
5. Extract `_merge_swing()` → add synthetic-default detection + warning flag
6. Extract `_extract_iv_data()` → keep IBWorker routing
7. Extract `_behavioral_checks()`
8. Extract gate assembly logic
9. app.py becomes routes-only ≤150 lines

### P3 — Paper trading verification (weekday required)
10. Record a paper trade end-to-end (AMD or CTRA when all gates pass)
11. Verify mark-to-market P&L in `GET /api/options/paper-trades`
12. Test sell_put direction (different gate track)
13. Verify NVDA broad retry works with real greeks (market open)

### Reference
- `docs/stable/CONCURRENCY_ARCHITECTURE.md` — all 5 problems resolved, market hours next
- `docs/versioned/KNOWN_ISSUES_DAY5.md` — current issue list
