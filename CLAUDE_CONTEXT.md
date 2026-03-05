# OptionsIQ — Claude Context
> **Last Updated:** Day 1 (March 5, 2026)
> **Current Version:** v0.1 (scaffold only — no working code yet)
> **Project Phase:** Phase 0 complete → Phase 1 starting

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
| Backend | Scaffold only | Codex files copied, not yet refactored |
| Frontend | Scaffold only | Codex files copied, not yet refactored |
| IBKR connection | Not working | app.py still the God Object |
| Gate logic | Correct (keep) | gate_engine.py verified correct |
| P&L math | Correct (keep) | pnl_calculator.py verified correct |
| Strategy ranking | Correct (keep) | strategy_ranker.py verified correct |
| IV store | Correct (keep) | iv_store.py verified correct |
| constants.py | Not created yet | Phase 1 task |
| bs_calculator.py | Not created yet | Phase 1 task |
| data_service.py | Not created yet | Phase 2 task |
| IB worker thread | Not created yet | Phase 2 task |
| yfinance_provider | Not created yet | Phase 2 task |
| analyze_service.py | Not created yet | Phase 3 task |

---

## Architecture

**Backend:** Flask on port 5051
**Frontend:** React on port 3050
**IB Gateway:** 127.0.0.1:4001
**Database:** SQLite at `backend/data/cache.db`

### Data Provider Hierarchy (live-first)
```
[1] IBKR Live (reqMarketDataType=1)  ← DEFAULT FOR ALL OPERATIONS
[2] IBKR Cache (SQLite, TTL 2 min)  ← shows "Using cached chain" banner
[3] yfinance (emergency fallback)    ← shows "Live data unavailable" banner
[4] Mock (dev/CI testing ONLY)       ← NEVER used for paper trades
```

### Key Files (target state after refactor)
```
backend/
  app.py              Routes only (~120 lines)
  constants.py        All thresholds and defaults
  data_service.py     Provider selection + cache + IB worker thread
  analyze_service.py  Analysis assembly + STA fetch
  bs_calculator.py    Black-Scholes greeks fallback
  ibkr_provider.py    Chain fetch (wrapped in worker thread)
  yfinance_provider.py Middle tier
  mock_provider.py    Dynamic mock (not hardcoded AME)
  gate_engine.py      KEEP AS-IS
  strategy_ranker.py  KEEP AS-IS
  pnl_calculator.py   KEEP AS-IS
  iv_store.py         KEEP AS-IS
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

---

## Known Issues (Day 1)

Full list: `docs/versioned/KNOWN_ISSUES_DAY1.md`

Critical (blocks paper trading):
1. app.py God Object — must split before anything works
2. mock_provider hardcoded to AME — breaks any other ticker
3. In-memory cache lost on restart

High:
4. No yfinance middle tier
5. QUICK_ANALYZE_MODE silently uses fake HV20
6. _merge_swing() fabricates missing fields silently

---

## Session Log

| Day | Date | What Happened |
|-----|------|--------------|
| Day 1 | Mar 5, 2026 | Project scaffolded. Phase 0 docs created. Codex files ported. |

---

## Next Session Priorities

1. Phase 1: Create `constants.py` (all thresholds from build plan)
2. Phase 1: Create `bs_calculator.py` (Black-Scholes greeks)
3. Phase 1: Fix `mock_provider.py` (dynamic pricing per ticker)
4. Phase 2: Wrap `ibkr_provider.py` in dedicated IB worker thread
5. Phase 2: Create `data_service.py`
