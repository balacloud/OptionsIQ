# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (iv_history.db + chain_cache.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, always running (user's own system)
- MarketData.app: **FREE tier** (100 credits/day, ~33/day used). NOT on Starter $12/mo. Upgrade only if credits saturate.
- Tradier: LIVE (free brokerage account, no subscription needed). Primary chain source since Day 39.

## Current Phase (Day 48)
v0.31.0. Phase 7c external audit (Day 48): ChatGPT 4-question audit complete — 5 design gaps found (KI-096 IVR null coercion, KI-097 event density, KI-098 absolute trend gate, KI-099 bull_call_spread direction, KI-100 Tier 1 GO rate). STA backend.py reviewed: RS midpoint normalization confirmed, weekChange returned but unused. Phase7c files consolidated into Phase7c_Research.md. Awaiting Gemini/Perplexity before implementing. 36 tests.

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY48_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY48.md` — open bugs and severity
6. Read `docs/stable/API_CONTRACTS.md` — ONLY if touching API endpoints
After reading: state current version, top priority, any blockers. Ask "What would you like to focus on today?"

## Key Source Files
```
backend/
  app.py              402 lines. sta_fetch extracted to sta_service.py (Day 46, KI-086 closed). Rule 4 technically violated but all business logic in service modules.
  sta_service.py      NEW (Day 46) — fetch_sta_swing_data(symbol). sta_fetch route 74→2 lines.
  batch_service.py    UPDATED (Day 37+39) — 239 lines. seed_iv_for_ticker(), run_bod_batch(), run_eod_batch().
                      run_startup_catchup() daemon. _ran_on() min_duration=1.0 (Day 39). startup delay 10s→30s.
  tradier_provider.py UPDATED (Day 39+40+42) — 346 lines. Primary live chain source. TRADIER_KEY env var.
                      compute_skew() (Day 42): 30-delta put/call IV spread. Direction-aware OTM filter (Day 40).
  best_setups_service.py NEW (Day 39) — run_one_setup() extracted from app.py _run_one closure.
  analyze_service.py  DONE (Day 24+28+29+33+34+36+40+43+47) — ~900 lines. _resolve_underlying_hint() (Day 34).
                      Day 43: _extract_iv_data() ATM IV, _days_until_next_macro(), fomc_days_away fix.
                      Day 47: ETF_OPTIONS_LIQUID_TIER1 imported, _is_early_market_session() helper,
                      "ticker" in gate_payload, actionable liquidity gate messages in apply_etf_gate_adjustments.
  constants.py        DONE (Day 19+27+28+29+32+43+47) — ETF_OPTIONS_LIQUID_TIER1 (Day 47).
                      ETF_DTE_SELLER_PASS_MIN=30 (Day 46, tastylive 200k+ trade research).
                      MIN_CREDIT_WIDTH_RATIO=0.33, IVR_SELLER_PASS_PCT=35, HV_IV_SELL_PASS_RATIO=1.05.
  marketdata_provider.py  DONE (Day 27+35+36) — 114 lines. OI/volume + IV+greeks supplement. Non-blocking.
                          Credit tracking Day 35. IV/delta/gamma/theta/vega surfaced Day 36.
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE (Day 12+29) — provider cascade + SQLite WAL + CB + Alpaca tier
  ibkr_provider.py    DONE (Day 12) — try-finally cancelMktData. OI unavailable (platform). readonly=True.
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
  mock_provider.py    LOW PRIORITY — partially hardcoded
  gate_engine.py      DONE (Day 21+27+28+29+32+43) — all 4 tracks with VRP + VIX gates for sellers.
                      Day 43: _etf_fomc_gate() extended to check macro events (CPI/NFP/PCE). _run_sell_call gate 4 same.
                      ETF_DTE_SELLER_PASS_MIN/MAX imported and used correctly (was using wrong VCP constants).
  strategy_ranker.py  DONE (Day 23+29) — credit_to_width_ratio on bear_call/bull_put R1/R2.
  pnl_calculator.py   DONE (Day 27) — bull_put_spread handler. All 6 strategy types covered.
  iv_store.py         DONE (Day 29+35) — get_iv_stats(), get_ohlcv_stats(), compute_max_21d_move(). batch_run_log table + log_batch_run() + get_batch_runs() added Day 35.
  data_health_service.py  DONE (Day 29+34) — 8 fields now (underlying_price added Day 34).
  sector_scan_service.py  DONE (Day 19) — STA consumer + L1 scan + L2 analyze + Phase 7b bear logic.
  tests/              DONE (Day 24+28+30+34) — 36 tests (pytest). 6 files.
                      New: test_resolve_underlying_hint.py (3 tests, KI-088).

frontend/
  components/DataProvenance.jsx  DONE (Day 29+34+35+38+39+41+42) — ManualBatchTriggers added Day 39. DataFlowDiagram SVG updated Day 41. fmtTime() UTC fix Day 42.
  components/GateExplainer.jsx   DONE (Day 25+43) — hv_iv_vrp + vix_regime GATE_KB entries added Day 43. events entry updated for CPI/NFP/PCE.
  components/DirectionGuide.jsx  DONE (Day 25+43) — sell_put risk label fix Day 43 (KI-077).
  App.jsx                        DONE (Day 21+25+29+31+42) — QualityBanner ibkr_cache→bod_cache (Day 42), tradier added to no-banner early-return.
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

## Day 49 Priorities
1. **P0:** Consolidate Gemini/Perplexity audit results into Phase7c_Research.md — compare with ChatGPT findings.
2. **P1:** Implement KI-098 — absolute trend gate: `weekChange ≤ 0` required for `bear_call_spread` in `quadrant_to_direction()`. 3-line change + 2 call sites + 1 test.
3. **P2:** Implement KI-096 — IVR null handling: treat None as "unknown confidence", not 0.0.
4. **P3:** Implement KI-097 — event density gate: count events in DTE window, escalate at 3+.
5. **P4:** Paper trade logging — log next XLF/QQQ CAUTION setup (user action, 0/30 logged).

## Git Status
- Remote: balacloud/OptionsIQ on GitHub (added Day 26)

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (9 categories, weekly trigger). v1.3 (Day 42).
- `docs/versioned/KNOWN_ISSUES_DAY47.md`
- `docs/status/PROJECT_STATUS_DAY47_SHORT.md`
- `docs/Research/Phase7c_Research.md` — Phase 7c research: live scan findings, fixes, adversarial prompts, roadmap
- `docs/Research/Daily_Trade_Prompts.md` — 7 pre-trade research prompts (daily use, stays at root)
- `docs/Research/data-providers/DATA_PROVIDERS_SYNTHESIS.md` — **CANONICAL** provider decisions: stack locked, all provider verdicts, why IBKR is sole historical IV source
- `docs/Research/ki-plans/KI-088_Day34.md` — Opus plan for KI-088 + MarketData.app diagnostic
- Research subfolders: `data-providers/`, `system-audits/`, `sector-rotation/`, `ux-design/`, `multi-llm-synthesis/`, `ki-plans/`, `archive/`

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
- [feedback_save_plans.md](feedback_save_plans.md) — Always save plans/synthesis to docs/Research/ as .md files
- [feedback_readme_update.md](feedback_readme_update.md) — Update README.md version badge at every session close
