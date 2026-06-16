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

## Current Phase (Day 70 — v0.36.2)
Dead IBKR code removed. ib_worker.py + ibkr_provider.py deleted. IBWorker stripped from 8 service files. Tradier OHLCV now primary source for HV computation. Targeted audit clean. P0 live /chartreview test passed (NO_TRADE on FOMC day). 110 tests. 0 CRITICAL/HIGH/MEDIUM.

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY70_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY70.md` — open bugs and severity
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
  constants.py        UPDATED (Day 19+27+28+29+32+43+47+64+68) — IVR_SELLER_PASS_PCT=40 (raised from 35, Day 68).
                      IVR_SELLER_WARN_MIN=35 (new warn band Day 68). EM_WARN=0.75, EM_WARN_STRONG=0.50 (Day 68).
                      TQQQ_IVR_PASS_MIN=50, TQQQ_IVR_WARN_MIN=40, TQQQ_VRP_PASS_MIN=1.15, TQQQ_VRP_WARN_MIN=1.05, TQQQ_SKEW_WARN_PTS=8 (Day 68).
                      ETF_OPTIONS_LIQUID_TIER1 (Day 47). ETF_DTE_SELLER_PASS_MIN=30 (Day 46).
                      MIN_CREDIT_WIDTH_RATIO=0.33, HV_IV_SELL_PASS_RATIO=1.05.
                      Day 64: SELL_PUT_OTM_PASS_PCT=3.0 added (R3 fix).
  marketdata_provider.py  DONE (Day 27+35+36) — 114 lines. OI/volume + IV+greeks supplement. Non-blocking.
                          Credit tracking Day 35. IV/delta/gamma/theta/vega surfaced Day 36.
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE (Day 12+29) — provider cascade + SQLite WAL + CB + Alpaca tier
  ibkr_provider.py    UPDATED (Day 52) — get_iv_hv_batch(): reqMktData streaming → reqHistoricalData.
                      whatToShow=OPTION_IMPLIED_VOLATILITY + HISTORICAL_VOLATILITY (Historical Data Farm).
                      7/7 ETFs return real data. reqMktData streaming all-nan: IBWorker only runs event loop
                      during ib.sleep() — insufficient for streaming. reqHistoricalData is request-response.
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
  mock_provider.py    LOW PRIORITY — partially hardcoded
  gate_engine.py      UPDATED (Day 57+58+59+60+66+68) — FOMC 3-tier gate (XLF/XLRE/TQQQ hard block <14d, QQQ/IWM/GLD warn-only).
                      Day 59: _tqqq_satellite_gate() + GLD IV/HV >= 1.10 gate + sell_call FOMC tier logic.
                      Day 60: _trend_ema_gate() added — wired into all 4 ETF tracks.
                      Day 66: _skew_flow_gate() added (sell_put + sell_call, WARN only).
                      Day 66: ivr_seller + market_regime_seller → blocking=False (WARN only). sell_put hard blocks: 9→6.
                      Day 68: All 4 IVR seller gates updated (4-tier: ≥40 pass / 35-40 warn / 25-35 warn / <25 fail).
                      Day 68: _tqqq_satellite_gate() rewritten — 4 conditions, can return PASS when all met.
  scan_context_parser.py  NEW (Day 60) — parse_scan_context(text) KEY=VALUE regex.
                      apply_scan_context_to_gate_payload() merges live IVR, P/C ratio, trend EMA into gate_payload.
                      Bridges /ibkr-scan skill output to analyze backend via copy-paste.
  strategy_ranker.py  UPDATED (Day 57+59) — single-leg only. Day 59: _rank_sell_put_etf TQQQ branch (delta 0.10/0.08/0.06).
                      Day 65: buy_call now returns "buy_call", buy_put returns "buy_put" — KI-110 FIXED.
  pnl_calculator.py   UPDATED (Day 58+65) — otm_call/otm_put P&L fixed. buy_call/buy_put unified types added. All types covered.
  chart_context_parser.py   NEW (Day 65) — parse_chart_context(), compute_strike_vs_support(), apply_chart_context_to_response()
  catalyst_context_parser.py NEW (Day 65) — parse_catalyst_context(), apply_catalyst_context_to_gate_payload(), _strategy_catalyst_overlay()
  tests/              110 tests (pytest). 9 files. (100→110 Day 68: 4 IVR tier tests + 6 TQQQ gate tests).

frontend/
  components/GateExplainer.jsx   UPDATED (Day 64) — fomc_gate entry added to GATE_KB (3-tier logic explanation). ivr_seller updated with explicit 35% threshold + tastylive citation.
  components/DirectionGuide.jsx  UPDATED (Day 58) — sell_call risk: "Uncapped naked call" (was "Spread width (capped)").
  components/TradeExplainer.jsx  UPDATED (Day 58) — otm_call/otm_put in headline/isBearish/getMoneyness.
  App.jsx                        UPDATED (Day 58) — expectedMove1sd prop to TopThreeCards, tab label "Today's Trade".
  components/TopThreeCards.jsx   UPDATED (Day 58) — em-context banner, strike_vs_em_label, ExitPlanBlock.
  components/BestSetups.jsx      REPLACED (Day 58) — Today's Trade (6-ETF quick-launcher, zero API calls).
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

## Day 71 Priorities
1. **P0:** GLD skew inversion — _skew_flow_gate() sell_call branch for GLD ~10 lines
2. **P1:** XLF post-FOMC — run /ibkr-scan Jun 17, if IV/HV > 1.10 + IVR toward 50% → first paper trade
3. **P2:** Frontend redesign (backlog)

## TradingView Pine Script
- File: `tradingview/OptionsIQ_ChartReview.pine` — **Indicator** type (not Strategy/Library)
- Apply to 1D chart on any of QQQ/IWM/XLF/GLD/TQQQ
- Adds: EMA 20/50/200 lines, pivot markers, dashed S1/S2/R1/R2 lines, dashboard table (top-right)
- Dashboard table shows: Price, Trend verdict, EMA values + % + slope, ATR(14), RSI(14), R1/R2/S1/S2/S3
- Usage: screenshot chart → paste to `/chartreview [ETF] [direction]`
- User has not yet tested this on TradingView — to try when market is open

## Git Status
- Remote: balacloud/OptionsIQ on GitHub (added Day 26)

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/GATE_REFERENCE.md` — **complete gate inventory** (all 4 directions, hard blocks vs warn, thresholds, Rule 23 review candidates) — added Day 66
- `docs/stable/QUANT_PERSONA.md` — Marcus Webb persona (30-year ETF options trader) for adversarial gate review — added Day 66
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (10 categories, weekly trigger). v1.6 (Day 64).
- `docs/versioned/KNOWN_ISSUES_DAY69.md`
- `docs/status/PROJECT_STATUS_DAY69_SHORT.md`
- `docs/Research/Phase7c_Research.md` — Phase 7c research: live scan findings, fixes, adversarial prompts, roadmap
- `docs/Research/Daily_Trade_Prompts.md` — 7 pre-trade research prompts (daily use, stays at root)
- `docs/Research/data-providers/DATA_PROVIDERS_SYNTHESIS.md` — **CANONICAL** provider decisions: stack locked, all provider verdicts, why IBKR is sole historical IV source
- `docs/Research/ki-plans/KI-088_Day34.md` — Opus plan for KI-088 + MarketData.app diagnostic
- Research subfolders: `data-providers/`, `system-audits/`, `sector-rotation/`, `ux-design/`, `multi-llm-synthesis/`, `ki-plans/`, `archive/`

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
- [feedback_save_plans.md](feedback_save_plans.md) — Always save plans/synthesis to docs/Research/ as .md files
- [feedback_readme_update.md](feedback_readme_update.md) — Update README.md version badge at every session close
- [feedback_ibkr_reqmktdata.md](feedback_ibkr_reqmktdata.md) — IBKR reqMktData: snapshot=True invalid with genericTickList; tick 104 invalid for STK; market data subscription required for non-owned ETFs
- [feedback_ibkr_ibworker_streaming.md](feedback_ibkr_ibworker_streaming.md) — reqMktData streaming all-nan in IBWorker model; use reqHistoricalData instead; reqScannerSubscription is the best approach
- [project_ibkr_screener_config.md](project_ibkr_screener_config.md) — IBKR Screener 2.0 actual data scales: Opt.IV% decimal (×100), Last cap $100 (use $1-$9999), IVR 0-99.99; correct MultiSort values for all 8 columns
