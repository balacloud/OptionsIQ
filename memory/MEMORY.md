# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (iv_history.db + chain_cache.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 30)
v0.22.0. McMillan Rolling Stress Check shipped (Gemini book-audit inspired). compute_max_21d_move() + _historical_stress_gate() on sell_put and sell_call tracks. OHLCV corruption fixed: XLE (18 bad rows deleted, HV 413%→17%) + IWM (17 bad rows deleted, worst_dd 65%→9.2%). Tests: 33.
Next: Seed OHLCV for XLRE/SCHB (KI-084/087), VIX in RegimeBar (KI-085), skew gate.

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY30_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY30.md` — open bugs and severity
6. Read `docs/stable/API_CONTRACTS.md` — ONLY if touching API endpoints
After reading: state current version, top priority, any blockers. Ask "What would you like to focus on today?"

## Key Source Files
```
backend/
  app.py              320 lines — THIN WRAPPERS (Day 24). Routes only, imports from analyze_service.py.
                                   New Day 26: _seed_iv_for_ticker() helper, POST /api/admin/seed-iv/all.
  analyze_service.py  DONE (Day 24+26) — 610+ lines. analyze_etf(), _days_until_next_fomc(),
                                     _etf_payload(), apply_etf_gate_adjustments(), all helpers.
                                     FOMC now computed from FOMC_DATES when payload missing.
  constants.py        DONE (Day 19+26) — all thresholds + FOMC_DATES 2026-2027 (already present)
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier, BS greeks fill. get_historical_iv() returns HV20 proxy.
  data_service.py     DONE (Day 12) — provider cascade + SQLite WAL + CB + Alpaca tier
  ibkr_provider.py    DONE (Day 12) — try-finally cancelMktData. OI confirmed unavailable (platform).
                                     get_historical_iv() confirmed working — returns daily IV bars.
                                     readonly=True (Day 24: staging code reverted).
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
  mock_provider.py    LOW PRIORITY — partially hardcoded
  gate_engine.py      DONE (Day 21+28+30) — ETF gate tracks. FOMC gate. Holdings earnings gate. McMillan stress gate.
  strategy_ranker.py  DONE (Day 23+29) — bull_put_spread. Credit-to-width ratio gate (MIN_CREDIT_WIDTH_RATIO=0.33).
  pnl_calculator.py   DONE (Day 27) — bull_put_spread handler added. All 6 strategy types covered.
  iv_store.py         DONE (Day 30) — get_iv_stats(), get_ohlcv_stats(), compute_max_21d_move() added.
  sector_scan_service.py  DONE (Day 19) — STA consumer + L1 scan + L2 analyze + Phase 7b bear logic.
  marketdata_provider.py  DONE (Day 27) — OI/volume supplement from MarketData.app. Non-blocking.
  data_health_service.py  DONE (Day 29) — GET /api/data-health, field-level provenance per ETF.
  tests/              DONE (Day 24+28+30) — 33 tests (pytest). 5 files.
```

## IBWorker Threading Rules (CRITICAL)
- ALL IBKRProvider calls MUST go through `_ib_worker.submit(fn, *args, timeout=N)`
- NEVER call ibkr_provider methods directly from Flask thread — asyncio event loop conflict → hang
- gate_engine requires float for all keys — coerce `ivr_data` None values to 0.0 before gate_payload
- Nightly seed job: must route through Flask → IBWorker.submit() (not direct cron → ib_insync)

## ETF-Only Mode (Day 21)
- 15 ETFs in constants.py ETF_TICKERS: XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, QQQ, TQQQ
- Non-ETF tickers → HTTP 400 with `etf_universe` list
- `_etf_payload()` returns: real SPY regime data, all swing fields = None, `swing_data_quality: "etf"`
- Gate engine called with `etf_mode=True` → routes to ETF-specific gate tracks

## Data Gaps Status (post Day 26)
| Gap | Status |
|-----|--------|
| IVR cold-start | ✅ FIXED — 7,492 rows seeded, all ETFs 365+ days |
| FOMC = 999 | ✅ FIXED — _days_until_next_fomc() from constants.py |
| OI always 0 | ❌ OPEN — Tradier Lite (free) is the fix, P1 Day 27 |
| EODHD backfill | ⏸ PAUSED — free tier paywalls options endpoint, verify before paying |

## Four Directions
| Direction | View | Gate Track | Strike |
|-----------|------|-----------|--------|
| buy_call | Bullish | A | ITM delta ~0.68 |
| sell_call | Neutral/Bearish | A | ATM/OTM |
| buy_put | Bearish | B | ITM delta ~-0.68 |
| sell_put | Neutral/Bullish | B | ATM/OTM |

DTE window: 14-120 days. Buyer sweet spot: 45-90 DTE. Seller sweet spot: 21-45 DTE.

## Day 31 Priorities
1. **P1:** Seed OHLCV for XLC, XLRE, SCHB (KI-084/087) — run analyze with IBKR to trigger OHLCV seeding
2. **P2:** VIX in RegimeBar (KI-085) — small badge showing live VIX with color coding
3. **P3:** Skew gate — put_iv_30delta - call_iv_30delta from existing chain data
4. **P4:** app.py cleanup (KI-086) — move _seed_iv_for_ticker + _run_one to service modules

## Git Status
- Remote: https://github.com/balacloud/OptionsIQ.git (configured Day 26)
- All 26 days of commits pushed. Push after every session close.

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (9 categories, weekly trigger). v1.2.
- `docs/versioned/KNOWN_ISSUES_DAY30.md`
- `docs/status/PROJECT_STATUS_DAY30_SHORT.md`
- `docs/Research/Daily_Trade_Prompts.md` — 7 pre-trade research prompts (new Day 27)
- `docs/Research/Options_Book_Based_Review.md` — Gemini: Natenberg/Sinclair/Taleb/McMillan audit of OptionsIQ (Day 30)

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
- [feedback_save_plans.md](feedback_save_plans.md) — Always save plans/synthesis to docs/Research/ as .md files
- [feedback_readme_update.md](feedback_readme_update.md) — Update README.md version badge at every session close
