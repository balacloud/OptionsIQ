# OptionsIQ — Claude Context
> **Last Updated:** Day 4 (March 7, 2026)
> **Current Version:** v0.4 (concurrency P1 complete, legacy CB removed)
> **Project Phase:** Phase 3 P1 complete → Phase 3 P2 (analyze_service.py) next

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
| Backend | Phase 3 P1 complete | Concurrency fixes done |
| Frontend | Done + bug fixes (Day 4) | Ticker override fixed, STA offline fixed |
| IBKR connection | WORKING | Live confirmed: AMD/AAPL/MEOH, account U11574928 |
| Gate logic | Correct (frozen) | gate_engine.py verified correct |
| P&L math | Correct (frozen) | pnl_calculator.py verified correct |
| Strategy ranking | Correct (frozen) | right=None fixed (KI-020) |
| IV store | Correct (frozen) | iv_store.py verified correct |
| constants.py | DONE (Day 3) | All thresholds + direction-aware DTE/strike windows |
| bs_calculator.py | DONE (Day 3) | Black-Scholes greeks fallback |
| ib_worker.py | DONE (Day 4) | Queue poisoning fixed (expires_at) |
| yfinance_provider.py | DONE (Day 3) | Middle tier, BS greeks fill |
| data_service.py | DONE (Day 3) | Provider cascade + SQLite cache + circuit breaker |
| ibkr_provider.py | DONE (Day 4) | RequestTimeout=15 around reqTickers |
| analyze_service.py | NOT CREATED | Day 5 P1 — extract from app.py |
| app.py | Partial refactor | 527 lines (down from 821). Legacy CB removed. Still >150 target. |

### Backend Files (current state)
```
backend/
  app.py              527 lines — legacy CB gone, routes + helpers. Still needs analyze_service.py split.
  constants.py        DONE — all thresholds, direction-aware DTE/strike windows
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier
  data_service.py     DONE — provider cascade + SQLite cache + AUTHORITATIVE circuit breaker
  ibkr_provider.py    DONE — direction-aware fetch, 4h structure cache, RequestTimeout=15
  mock_provider.py    PARTIAL — still partially hardcoded (low priority)
  gate_engine.py      FROZEN — math correct
  strategy_ranker.py  FROZEN — math correct, right field fixed
  pnl_calculator.py   FROZEN — math correct
  iv_store.py         FROZEN — math correct

  # TO CREATE:
  analyze_service.py  Day 5 P1 — extract _merge_swing, _extract_iv_data, _behavioral_checks
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
Structure cache (4h in-memory) avoids repeated reqSecDefOptParams.

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

---

## Known Issues

Full list: `docs/versioned/KNOWN_ISSUES_DAY4.md`

Open (Phase 5):
1. **analyze_service.py missing** — app.py still 527 lines, target ≤150 (KI-001/KI-023)
2. **Synthetic swing defaults silent** — no banner when stop/target are fabricated (KI-022/KI-005)
3. **No IBWorker heartbeat** — silent TCP drops not detected (KI-019)
4. **fomc_days_away not auto-computed** — defaults to 30 always (KI-008)

Backlog (low priority):
5. mock_provider partially hardcoded AME structure (KI-003)
6. API URL hardcoded in useOptionsData.js (KI-013)

---

## Session Log

| Day | Date | What Happened |
|-----|------|--------------|
| Day 1 | Mar 5, 2026 | Project scaffolded. Phase 0 docs created. Codex files ported. |
| Day 2 | Mar 5, 2026 | GOLDEN_RULES enhanced. Full frontend UI redesign (8 files). |
| Day 3 | Mar 6, 2026 | Phase 1+2 complete. IBWorker, DataService, direction-aware fetch. Live IBKR confirmed. |
| Day 4 | Mar 7, 2026 | KI-016 queue poisoning fixed (expires_at). KI-017 RequestTimeout=15. KI-018 legacy CB removed from app.py (821→527 lines). KI-020 strategy_ranker right=None fixed. Ticker override bug fixed (App.jsx spread order). STA offline detection fixed (SwingImportStrip). MEOH confirmed live. |

---

## Next Session Priorities (Day 5)

### P1 — Create analyze_service.py (must do)
1. Extract `_merge_swing()` → add synthetic-default detection + warning flag
2. Extract `_extract_iv_data()` → keep IBWorker routing
3. Extract `_behavioral_checks()`
4. Extract gate assembly logic
5. app.py becomes routes-only ≤150 lines

### P2 — IBWorker heartbeat (KI-019)
6. Add `_heartbeat_loop()` in IBWorker — `reqCurrentTime()` every 30s when idle
7. `is_connected()` checks heartbeat timestamp freshness (max 60s gap)

### P3 — Paper trading verification
8. Record a paper trade end-to-end (AMD or NVDA)
9. Verify mark-to-market P&L in `GET /api/options/paper-trades`
10. Test sell_put direction (different gate track)

### Reference
- `docs/stable/CONCURRENCY_ARCHITECTURE.md` — full concurrency plan
- `docs/versioned/KNOWN_ISSUES_DAY4.md` — current issue list
