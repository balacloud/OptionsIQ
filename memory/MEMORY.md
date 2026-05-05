# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (iv_history.db + chain_cache.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, always running (user's own system)
- MarketData.app: **FREE tier** (100 credits/day, ~33/day used). NOT on Starter $12/mo. Upgrade only if credits saturate.
- Tradier: signing up soon (free account, no subscription needed — confirmed by support)

## Current Phase (Day 38)
v0.27.1. DataFlowDiagram SVG added to Data Provenance tab — always-visible two-section architecture diagram (Live Analysis + Batch/Nightly). MD.app confirmed FREE tier (was incorrectly documented as Starter $12/mo). Tradier: open account imminent, no subscription needed (support confirmed).

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY38_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY38.md` — open bugs and severity
6. Read `docs/stable/API_CONTRACTS.md` — ONLY if touching API endpoints
After reading: state current version, top priority, any blockers. Ask "What would you like to focus on today?"

## Key Source Files
```
backend/
  app.py              492 lines — Rule 4 violation (max 150). _seed_iv_for_ticker moved to batch_service.py (Day 35). _run_one still inline.
  batch_service.py    UPDATED (Day 37) — 231 lines. seed_iv_for_ticker(), run_bod_batch(), run_eod_batch().
                      run_startup_catchup() daemon (Day 37). yfinance IV fallback REMOVED (HV≠IV).
  analyze_service.py  DONE (Day 24+28+29+33+34+36) — 841 lines. _resolve_underlying_hint() (Day 34).
                      Day 36: IV patching from MD.app + md_supplement. Day 37: MD.app IV stored daily.
  constants.py        DONE (Day 19+27+28+29+32) — MIN_CREDIT_WIDTH_RATIO=0.33, IVR_SELLER_PASS_PCT=35,
                      HV_IV_SELL_PASS_RATIO=1.05 (IV/HV). VIX_LOW_VOL=15, VIX_STRESS=30, VIX_CRISIS=40.
  marketdata_provider.py  DONE (Day 27+35+36) — 114 lines. OI/volume + IV+greeks supplement. Non-blocking.
                          Credit tracking Day 35. IV/delta/gamma/theta/vega surfaced Day 36.
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE (Day 12+29) — provider cascade + SQLite WAL + CB + Alpaca tier
  ibkr_provider.py    DONE (Day 12) — try-finally cancelMktData. OI unavailable (platform). readonly=True.
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
  mock_provider.py    LOW PRIORITY — partially hardcoded
  gate_engine.py      DONE (Day 21+27+28+29+32) — all 4 tracks with VRP + VIX gates for sellers.
  strategy_ranker.py  DONE (Day 23+29) — credit_to_width_ratio on bear_call/bull_put R1/R2.
  pnl_calculator.py   DONE (Day 27) — bull_put_spread handler. All 6 strategy types covered.
  iv_store.py         DONE (Day 29+35) — get_iv_stats(), get_ohlcv_stats(), compute_max_21d_move(). batch_run_log table + log_batch_run() + get_batch_runs() added Day 35.
  data_health_service.py  DONE (Day 29+34) — 8 fields now (underlying_price added Day 34).
  sector_scan_service.py  DONE (Day 19) — STA consumer + L1 scan + L2 analyze + Phase 7b bear logic.
  tests/              DONE (Day 24+28+30+34) — 36 tests (pytest). 6 files.
                      New: test_resolve_underlying_hint.py (3 tests, KI-088).

frontend/
  components/DataProvenance.jsx  DONE (Day 29+34+35+38) — DataFlowDiagram SVG added Day 38 (always visible). BatchStatusPanel + IVCoverageGrid added Day 35.
  components/BestSetups.jsx      DONE (Day 31+32) — IV/HV ratio column, 7-col grid.
```

## STA Architectural Role (updated Day 34)
STA is the canonical source for:
- **Underlying spot price**: `_resolve_underlying_hint()` → STA `/api/stock/{ticker}` currentPrice
- **VIX**: `_fetch_vix()` → STA `/api/stock/%5EVIX` (rate-limit safe, no stampede)
- **SPY Regime**: `_spy_regime()` → STA `/api/context/SPY`
IBKR remains source for: option chain (strikes, IVs, greeks, bid/ask) + nightly IV seeding.
STA is user's own system — always running. Rule 6 (STA optional) preserved via graceful fallback.

## IBWorker Threading Rules (CRITICAL)
- ALL IBKRProvider calls MUST go through `_ib_worker.submit(fn, *args, timeout=N)`
- NEVER call ibkr_provider methods directly from Flask thread — asyncio event loop conflict → hang
- gate_engine requires float for all keys — coerce `ivr_data` None values to 0.0 before gate_payload
- load_dotenv() in app.py MUST come before ALL project imports — module-level os.getenv() runs at import time

## ETF-Only Mode (Day 21)
- 15 ETFs: XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, QQQ, TQQQ
- SCHB is NOT in the app — confirmed from UI and constants.py (memory docs were wrong)
- Non-ETF tickers → HTTP 400 with `etf_universe` list
- Gate engine called with `etf_mode=True` → routes to ETF-specific gate tracks

## Day 39 Priorities
1. **P0:** Tradier integration — open brokerage account, test live chain call, implement `tradier_provider.py`.
2. **P1:** KI-086 — move `_run_one` to `best_setups_service.py` (app.py 497→~420 lines).
3. **P2:** KI-067 — QQQ sell_put ITM strike fix.
4. **P3:** Check backend.log for "Startup catch-up" entries (backend restarted Day 38 with IB Gateway live).
5. **P4:** FOMC dates audit — verify 2026 dates in constants.py complete (next: Jun 18, Jul 30).

## Git Status
- Remote: balacloud/OptionsIQ on GitHub (added Day 26)

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (9 categories, weekly trigger). v1.2.
- `docs/versioned/KNOWN_ISSUES_DAY36.md`
- `docs/status/PROJECT_STATUS_DAY36_SHORT.md`
- `docs/Research/Daily_Trade_Prompts.md` — 7 pre-trade research prompts (daily use, stays at root)
- `docs/Research/data-providers/DATA_PROVIDERS_SYNTHESIS.md` — **CANONICAL** provider decisions: stack locked, all provider verdicts, why IBKR is sole historical IV source
- `docs/Research/ki-plans/KI-088_Day34.md` — Opus plan for KI-088 + MarketData.app diagnostic
- Research subfolders: `data-providers/`, `system-audits/`, `sector-rotation/`, `ux-design/`, `multi-llm-synthesis/`, `ki-plans/`, `archive/`

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
- [feedback_save_plans.md](feedback_save_plans.md) — Always save plans/synthesis to docs/Research/ as .md files
- [feedback_readme_update.md](feedback_readme_update.md) — Update README.md version badge at every session close
