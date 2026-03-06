# OptionsIQ — Claude Context
> **Last Updated:** Day 3 (March 6, 2026)
> **Current Version:** v0.3 (data layer complete, live IBKR confirmed working)
> **Project Phase:** Phase 2 complete → Phase 3 (analyze_service.py) next

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
| Backend | Phase 2 complete | IBWorker + DataService + yfinance working |
| Frontend | Done (Day 2) | Two-panel layout, verdict hero, collapsible sections |
| IBKR connection | WORKING | Live confirmed: AMD/AAPL chains fetched, account U11574928 |
| Gate logic | Correct (frozen) | gate_engine.py verified correct |
| P&L math | Correct (frozen) | pnl_calculator.py verified correct |
| Strategy ranking | Correct (frozen) | strategy_ranker.py verified correct |
| IV store | Correct (frozen) | iv_store.py verified correct |
| constants.py | DONE (Day 3) | All thresholds + direction-aware DTE/strike windows |
| bs_calculator.py | DONE (Day 3) | Black-Scholes greeks fallback |
| ib_worker.py | DONE (Day 3) | Single IB() thread, submit() queue |
| yfinance_provider.py | DONE (Day 3) | Middle tier, BS greeks fill |
| data_service.py | DONE (Day 3) | Provider cascade + SQLite cache + circuit breaker |
| ibkr_provider.py | DONE (Day 3) | Direction-aware fetch, structure cache, market_data_type=1 |
| analyze_service.py | NOT CREATED | Phase 3 — extract from app.py |
| app.py | Partial refactor | Still God Object (>150 lines). DataService wired in but legacy code still present. |
| /api/integrate/sta-fetch/{ticker} | DONE (Day 3) | KI-015 resolved |

### Backend Files (current state)
```
backend/
  app.py              PARTIAL — DataService wired, legacy CB + helpers still present
  constants.py        DONE — all thresholds, direction-aware DTE/strike windows
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single thread, submit() queue
  yfinance_provider.py DONE — middle tier
  data_service.py     DONE — provider cascade + SQLite cache + circuit breaker
  ibkr_provider.py    DONE — direction-aware fetch, 4h structure cache, live market data type
  mock_provider.py    PARTIAL — still partially hardcoded (low priority)
  gate_engine.py      FROZEN — math correct
  strategy_ranker.py  FROZEN — math correct
  pnl_calculator.py   FROZEN — math correct
  iv_store.py         FROZEN — math correct
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
                                                                  ↓
                                                           IBKRProvider methods
                                                           (single IB() instance)
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

Full list: `docs/versioned/KNOWN_ISSUES_DAY3.md`

Critical (blocks paper trading):
1. IBWorker queue poisoning — timed-out request still runs, blocks queue (see CONCURRENCY_ARCHITECTURE.md P1)
2. app.py still God Object — needs analyze_service.py extraction before ≤150 lines
3. strategy_ranker returns `right=None` in top_strategies output (investigation needed)
4. Pre-market: 0% quote completion (expected — IBKR options data only live during market hours)

High:
5. No IBWorker request expiry — queued requests don't expire when caller already timed out
6. Dual circuit breakers (app.py legacy + DataService) — inconsistent state possible
7. No connection heartbeat — silent TCP drops not detected
8. mock_provider still partially hardcoded AME structure (low priority)

---

## Session Log

| Day | Date | What Happened |
|-----|------|--------------|
| Day 1 | Mar 5, 2026 | Project scaffolded. Phase 0 docs created. Codex files ported. |
| Day 2 | Mar 5, 2026 | GOLDEN_RULES enhanced. Research Plan reviewed, code conflicts documented. Full frontend UI redesign (8 files). |
| Day 3 | Mar 6, 2026 | Phase 1+2 complete. constants.py, bs_calculator.py, ib_worker.py, yfinance_provider.py, data_service.py all created. ibkr_provider.py: direction-aware fetch + structure cache + live market data type fixed. Threading violation fixed (_extract_iv_data → IBWorker). gate_engine None crash fixed. Empty-string parsing fixed. Live IBKR confirmed: account U11574928, AMD/AAPL chains fetched. CONCURRENCY_ARCHITECTURE.md research plan written. |

---

## Next Session Priorities (Day 4)

### P1 — Fix queue poisoning (must do before live paper trading)
1. Add `expires_at` to IBWorker `_Request` — worker discards expired requests
2. Set `ib.RequestTimeout` around `reqTickers` in IBKRProvider
3. Remove legacy circuit breaker from app.py (`_ib_chain_*` variables + functions)

### P2 — Phase 3: analyze_service.py
4. Extract business logic from app.py into `analyze_service.py`
5. app.py becomes routes-only ≤150 lines (Rule 4)

### P3 — Debug + polish
6. Investigate `right=None` in strategy_ranker output
7. Background heartbeat in IBWorker (connection health)
8. Test full flow during market hours (9:30am-4pm ET) for live quote data

### Reference
- See `docs/stable/CONCURRENCY_ARCHITECTURE.md` for full thread/concurrency research plan
