# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (iv_history.db + chain_cache.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 26)
v0.18.0. Data infrastructure complete. FOMC gate fixed (_days_until_next_fomc() from constants.py). IVR seeded: 7,492 rows across 20 tickers from IBKR. ↓ Seed IV button in UI. Strike zone label overlap fixed. Tradier Lite (free) confirmed as OI/volume solution.
Next: Master Audit Framework (all 9 categories, Day 27 P0), then Tradier integration.

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY26_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY26.md` — open bugs and severity
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
  gate_engine.py      UPDATED (Day 21) — ETF gate tracks. etf_mode param. Math frozen.
  strategy_ranker.py  UPDATED (Day 23) — bull_put_spread. All 4 ETF spreads defined-risk.
  pnl_calculator.py   UPDATED (Day 21) — ETF price-relative scenarios. Stock None guards.
  iv_store.py         FROZEN — math correct. DB: backend/data/iv_history.db (7,492 rows seeded Day 26)
  sector_scan_service.py  DONE (Day 19) — STA consumer + L1 scan + L2 analyze + Phase 7b bear logic.
  tests/              DONE (Day 24) — 27 tests (pytest). 5 files.
  seed_iv_nightly.sh  NEW (Day 26) — cron script: curl POST /api/admin/seed-iv/all nightly 4:30pm ET

  # TO CREATE:
  tradier_provider.py  P1 Day 27 — OI/volume supplement for Liquidity gate (Lite account = free)
  marketdata_provider.py  DEFERRED — MarketData.app no historical IV (confirmed), low priority
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

## Day 27 Priorities
1. **P0:** Run MASTER_AUDIT_FRAMEWORK — all 9 categories (user confirmed)
2. **P1:** Tradier integration — open Lite (free), wire OI/volume → Liquidity gate
3. **P2:** KI-067 — QQQ sell_put ITM strike fix
4. **P3:** KI-044 — API_CONTRACTS.md full sync

## Git Status
- Remote: https://github.com/balacloud/OptionsIQ.git (configured Day 26)
- All 26 days of commits pushed. Push after every session close.

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (9 categories, weekly trigger). v1.2.
- `docs/versioned/KNOWN_ISSUES_DAY26.md`
- `docs/status/PROJECT_STATUS_DAY26_SHORT.md`
- `docs/Research/Data_Strategy_Day26.md` — 3-option data plan (Nightly IB, Tradier, EODHD)
- `docs/Research/Options_Data_Provider_Research_Day10.md` — evidence base (live-tested providers)
- `docs/Research/UX_Research_Synthesis_Day25.md` — Phase 8 LLM research synthesis

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
- [feedback_save_plans.md](feedback_save_plans.md) — Always save plans/synthesis to docs/Research/ as .md files
- [feedback_readme_update.md](feedback_readme_update.md) — Update README.md version badge at every session close
