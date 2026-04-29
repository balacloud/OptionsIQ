# OptionsIQ — Roadmap
> **Last Updated:** Day 31 (April 29, 2026)
> **Current Version:** v0.23.0

---

## Phase 0 — Documentation (Day 1) ✅ COMPLETE
- [x] CLAUDE_CONTEXT.md, GOLDEN_RULES.md, ROADMAP.md, API_CONTRACTS.md
- [x] Codex source files ported, .gitignore, .env.example, requirements.txt, start.sh, stop.sh
- [x] CLAUDE.md created + session startup/close checklists added to CLAUDE_CONTEXT.md (Day 8)

## Phase 1 — Backend Foundation (Day 3) ✅ COMPLETE
- [x] `constants.py`, `bs_calculator.py`, `ibkr_provider.py` market_data_type=1

## Phase 2 — Data Layer (Day 3) ✅ COMPLETE
- [x] `ib_worker.py`, `yfinance_provider.py`, `data_service.py`
- [x] Direction-aware chain fetch + 4h structure cache + threading violation fixed

## Phase 3 — Fix Concurrency + Analyze Service (Day 4) ✅ P1 COMPLETE

### P1 ✅ ALL DONE
- [x] `expires_at` on IBWorker `_Request` — queue poisoning fix (KI-016)
- [x] `ib.RequestTimeout = 15` around reqTickers (KI-017)
- [x] Legacy circuit breaker removed from app.py (KI-018)
- [x] `right=None` in strategy_ranker fixed (KI-020)
- [x] Ticker override bug fixed — App.jsx spread order
- [x] STA offline detection fixed — `json?.status === 'ok'`

### P2 — Day 6
- [x] Create `analyze_service.py` — extracted all helpers + orchestrator (Day 24) ✅
- [x] app.py to ≤350 lines (965→320, KI-023) ✅ Day 24
- [ ] Synthetic-default warning when swing fields null (KI-022)
- [ ] FOMC days auto-compute from constants.FOMC_DATES in manual mode

### P3 ✅ DONE (Day 5)
- [x] IBWorker background heartbeat (KI-019) — `reqCurrentTime()` every 30s, staleness check

## Phase 3 Additional Fixes (Day 5) ✅ COMPLETE
- [x] STA field mapping fixed — `suggestedEntry/Stop/Target/riskReward` (was `levels.*`)
- [x] `spy_above_200sma` computed from yfinance — no more false Market Regime FAILs
- [x] Direction locking fixed for SELL signal
- [x] Struct cache drift invalidation (>15% price move clears cache)
- [x] `SMART_MAX_STRIKES` 4→6, `SMART_MAX_EXPIRIES` 1→2, broad-window retry when <3 qualify
- [x] `start.sh` `.env` path fix + venv creation fix

## Phase 4 — Market Hours + Analyze Service (Day 6–8)
- [x] Market hours detection — BS greeks when market closed (KI-024) ✅ Day 6
- [x] ibkr_closed data source tier — no stale-quote caching ✅ Day 6
- [x] Frontend: amber banner + "IB Closed" header label ✅ Day 6
- [x] Strategy ranker: explicit builders for all 4 directions (KI-021) ✅ Day 7
- [x] reqMktData(snapshot=False) replaces reqTickers — modelGreeks fix (KI-027) ✅ Day 7
- [x] KI-026 VERIFIED Day 9 — live greeks 100% during market hours, usopt lazy connect confirmed ✅
- [x] pnl_calculator: None guard + itm_put/atm_put/bear_call_spread/sell_call handlers ✅ Day 9
- [x] sell_call direction-aware sort + SMART_MAX_STRIKES 6→12 → bear_call_spread building ✅ Day 9
- [x] KI-035: OI always 0 — genericTickList="101" fix applied (verify market hours Day 11) ✅ Day 10
- [x] Create alpaca_provider.py — REST fallback with greeks (NO OI/volume) ✅ Day 10
- [ ] Synthetic swing default warning banner (KI-022)
- [ ] Create marketdata_provider.py — MarketData.app REST provider ($12/mo, pending support ticket)
- [ ] Create analyze_service.py — extract from app.py (KI-001/023, Day 11 P2)

## Phase 4c — Data Infrastructure (Day 26–27) ✅ COMPLETE
- [x] Nightly IV seeding: `POST /api/admin/seed-iv/all` + `↓ Seed IV` button ✅ Day 26
- [x] FOMC gate fix: `_days_until_next_fomc()` from constants fallback ✅ Day 26
- [x] 7,492 IV rows seeded from IBKR — IVR gate reliable from day 1 ✅ Day 26
- [x] TradeExplainer strike zone overlap fixed ✅ Day 26
- [x] MasterVerdict passed gates visible as chips ✅ Day 26
- [x] MarketData.app OI/volume supplement: `marketdata_provider.py` wired ✅ Day 27
- [x] FOMC calendar corrected: Apr 29 (was missing, had May 6) ✅ Day 27
- [x] bull_put_spread P&L handler added (HIGH audit finding) ✅ Day 27
- [x] Pre-trade research workflow: Daily_Trade_Prompts.md + CopyForChatGPT button ✅ Day 27

## Phase 4b — System Audit + Hardening (Day 11-12) ✅ PHASE A+D COMPLETE
- [x] Behavioral audit: 17 claims verified against code ✅ Day 11
- [x] Phase A critical fixes (logger, QualityBanner, WAL, bare excepts, missing banners) ✅ Day 12
- [x] Phase D error handling (subscription cleanup, ticker validation, outer try-except) ✅ Day 12
- [x] gate_engine Rule 3 fix: 60+ hardcoded literals → constants.py imports ✅ Day 12
- [x] KI-035 OI: confirmed platform limitation, graceful degradation shipped ✅ Day 12
- [x] sell_put naked warning, ACCOUNT_SIZE startup guard ✅ Day 12
- [ ] Phase B API contract sync (update API_CONTRACTS.md to match code) — Day 13 P0
- [ ] Phase C provider consistency (None vs 0, bs_greeks flag)
- [ ] Phase E performance (deepcopy, struct_cache LRU, startup health check)
- [ ] Phase F documentation sync

## Phase 5 — Paper Trading Ready
- [ ] Paper trade record + mark-to-market verified end-to-end
- [ ] IV history seeded for AMD, NVDA, PLTR, RKLB, AMZN
- [ ] git tag v1.0 — paper trading begins

## Phase 6 — Sector Rotation ETF Module (STA-powered)
STA already provides: RS Ratio, quadrants, cap-size rotation, sector→ETF mapping.
OptionsIQ consumes `GET localhost:5001/api/sectors/rotation` — zero RS computation needed.
- [x] Research: RS methodology, strategy-per-quadrant, ETF liquidity ✅ Day 11
- [x] RS formula verified against STA source ✅ Day 11 (6-mo closes, midpoint normalize, 10-day delta)
- [x] Multi-LLM research audit (Gemini+GPT-4o+Perplexity): 7 questions, 3 design corrections ✅ Day 13
- [x] ~~`sector_rotation.py`~~ NOT NEEDED — STA provides all rotation data ✅
- [x] `sector_scan_service.py` — STA consumer + research-verified quadrant→direction + catalyst warnings ✅ Day 13
- [x] Backend: `GET /api/sectors/scan` (L1) + `GET /api/sectors/analyze/{ticker}` (L2) ✅ Day 13
- [x] Level 3 reuses existing `POST /api/options/analyze` (zero new code) ✅
- [x] TQQQ rules: max 45 DTE, no covered calls, decay warning ✅ Day 13
- [x] ETF constants in constants.py (tickers, gate overrides, FOMC, dividend) ✅ Day 13
- [x] Frontend: SectorRotation.jsx + ETFCard.jsx + useSectorData.js + tab switcher ✅ Day 14
- [x] L2 pipeline fix: get_chain tuple, IVR wiring, SPY regime, scan cache, behavioral audit ✅ Day 15
- [x] L2 IV overlay live test with IBKR during market hours ✅ Day 16 (6/7 ETFs pass)
- [x] SPY regime: yfinance → STA /api/stock/SPY priceHistory ✅ Day 16 (rate limit fix)
- [x] IVR-tiered direction in scan_sectors() — sell_put (IVR>50%), buy_call (IVR<30%) ✅ Day 22
- [ ] ETF-specific gate overrides in gate_engine (premium $0.50, spread 0.10%)
See: `docs/Research/Sector_Rotation_ETF_Module_Day11.md`

## Phase 7 — Bear Market Workflows (P0 for Day 17)
The system currently earns in bull + neutral markets only. Bear directions (buy_put, sell_call) are
code-complete but untested. Phase 7 closes this gap across both single-stock and sector modules.

### 7a — Single Stock Bear Directions (KI-059 — DEFERRED: ETF-only pivot)
- [ ] ~~Live test buy_put~~ — stocks no longer accepted (ETF-only mode returns 400)
- [x] ETF buy_put + sell_call tested ✅ Day 21 (XLU all 4 directions confirmed)
- [ ] If stocks re-enabled later: gate track B fires, ITM put + bear put spread strategy returns

### 7b — Sector Bear Market Strategies ✅ COMPLETE (Day 19)
- [x] Research: Lagging ETF → bear_call_spread conditions (RS<98, momentum<-0.5) ✅ Day 19
- [x] Research: Dropped Weakening→sell_call (defensive sectors get bid up in selloffs) ✅ Day 19
- [x] Implement bearish quadrant→direction mapping (Lagging + bear thresholds → bear_call_spread) ✅ Day 19
- [x] Add regime detector: "BROAD_SELLOFF" banner (>50% Weakening/Lagging + SPY<200SMA) ✅ Day 19
- [x] Frontend: bear badges (red), selloff banner, IVR bear warning ✅ Day 19
- [x] IVR as L2 soft warning (not L1 hard gate — L1 never has IVR) ✅ Day 19
- [x] ETF gate post-processing: events/pivot/DTE auto-pass for ETFs ✅ Day 19
- [x] Bug fixes: KI-062/063/065/066 + L2 None→buy_call ✅ Day 19
- See: `docs/Research/Sector_Bear_Market_Day19.md`

### 7c — Weakening → sell_call for Cyclical Sectors (deferred, needs research)
- [ ] Research: distinguish cyclical (XLI, XLY, XLB) vs defensive (XLU, XLP) sectors
- [ ] Research: conditions for selling calls on weakening cyclicals (avoid defensive inflows)
- [ ] Backtesting: validate sell_call on Weakening ETFs doesn't get squeezed by rotation

## Phase 8 — Options Explainer Page ("Learn" Tab) ✅ COMPLETE (Day 25, enhanced Day 31)
Interactive education page — no backend, pure frontend with mock data.
- [x] "Learn" tab added to App.jsx (alongside Signal Board) ✅ Day 25
- [x] 4 interactive lessons: Strikes, Directions, Spreads, Gates ✅ Day 25
- [x] Strike zone visualization (ITM/ATM/OTM number line with price slider) ✅ Day 25
- [x] P&L profile SVG diagrams per direction (4 directions + spreads payoff) ✅ Day 25
- [x] Interactive: stock price slider → moneyness update in Strikes lesson ✅ Day 25
- [x] Covers: when to buy vs sell premium, spreads, gates, strike selection ✅ Day 25
- [x] Inline TradeExplainer in analysis panel — context-sensitive per trade ✅ Day 25
- [x] GateExplainer replaces GatesGrid — plain English Q&A accordion ✅ Day 25
- [x] DirectionGuide replaces DirectionSelector — educational 2×2 cards ✅ Day 25
- [x] MasterVerdict + TopThreeCards enhanced with plain English descriptions ✅ Day 25
- [x] Multi-LLM research synthesis: GPT-4o + Gemini + Perplexity ✅ Day 25
- [ ] Links back to Analyze tab from Learn ("this is what OptionsIQ does when you pick buy_call") — deferred
- [ ] Live test all 4 directions to verify TradeExplainer zone colors (KI-076) — Day 26 P0
See: `docs/Research/UX_Research_Synthesis_Day25.md`

## Phase 9 — Track Record + Daily Workflow (Day 28+)
- [x] ETF holdings earnings gate (KI-079) — ETF_KEY_HOLDINGS + COMPANY_EARNINGS + _etf_holdings_earnings_gate() ✅ Day 28
- [x] Liquidity gate hard-fail on bid-ask >20% (KI-080) — SPREAD_DATA_FAIL_PCT + spread_pct on gate dict ✅ Day 28
- [x] FOMC gate: warn when FOMC inside DTE window (fomc_days < dte), not just when imminent ✅ Day 28
- [x] Pre-analysis prompts in UI — PreAnalysisPrompts.jsx copyable panel in analyze tab ✅ Day 29
- [x] Paper trade P&L dashboard — PaperTradeDashboard.jsx, SQLite-backed, win rate + equity curve ✅ Day 29
- [x] Credit-to-width ratio gate (KI-082) — MIN_CREDIT_WIDTH_RATIO=0.33, _credit_width() in strategy_ranker ✅ Day 29
- [x] Best Setups page — BestSetups.jsx, parallel ETF scan, manual Run Scan button, watchlist ✅ Day 29
- [x] HV/IV VRP seller gate — _etf_hv_iv_seller_gate(), Sinclair volatility risk premium ✅ Day 29
- [x] VIX regime gate — _vix_regime_gate(), <15 warn, >30 warn, >40 fail ✅ Day 29
- [x] Data Health tab — DataProvenance.jsx + GET /api/data-health, field-level provenance ✅ Day 29
- [x] Tab state retention — always-mount pattern (display:none vs unmount) ✅ Day 29
- [x] Fix XLE OHLCV corruption (KI-083) — deleted 18 rows (close > 80.0), HV-20 now 16.96% ✅ Day 30
- [x] Fix IWM OHLCV corruption — deleted 17 rows (close < 150), worst_dd now 9.2% (was 65%) ✅ Day 30
- [x] McMillan Rolling Stress Check — compute_max_21d_move() + _historical_stress_gate() on sell tracks ✅ Day 30
- [x] Fix XLC + XLRE + SCHB OHLCV gap (KI-084/087) — _seed_iv_for_ticker() enhanced to also seed OHLCV ✅ Day 31
- [x] VIX display in RegimeBar (KI-085) — color-coded badge: green/orange/red/grey ✅ Day 31
- [x] LearnTab Perplexity redesign — 5-panel trade education panel, context-aware real ETF data ✅ Day 31
- [x] Best Setups as home screen — default tab, auto-scan on mount, clickable cards → analysis ✅ Day 31
- [x] Paper trade workflow rebuilt — PaperTradeBanner + PATCH/DELETE endpoints + PaperTradeDashboard ✅ Day 31
- [ ] Skew computation — put_iv_30delta - call_iv_30delta from existing IBKR chain data
- [ ] app.py size violation (KI-086) — move _seed_iv_for_ticker + _run_one to service modules

## Phase 10 — Order Execution (Day 23, deferred)
Place spread orders directly into TWS via IB Gateway — analysis → execution in one UI.

- [x] Research IBKR TWS API: transmit=False safety, BAG contract, ComboLeg structure ✅ Day 23
- [x] `ibkr_provider.stage_spread_order()` — qualifies legs, builds BAG, placeOrder(transmit=False) ✅ Day 23
- [x] `POST /api/orders/stage` — validates spread params, calls IBWorker ✅ Day 23
- [x] `ExecutionCard.jsx` — shows legs, net credit, max profit/loss, Stage button ✅ Day 23
- [x] Wire ExecutionCard into App.jsx AnalysisPanel + CSS styles (KI-071) ✅ Day 24
- [x] ExecutionCard redesigned as visual IBKR Client Portal guide (no API staging) ✅ Day 24
- [x] TWS staging code reverted (readonly=True, stage_spread_order removed) ✅ Day 24
- [ ] (Future) whatIf commission estimate before staging

## Backtesting — Research Deferred (Day 29)

Explicitly researched and deferred. Rationale documented here to avoid re-asking.

**Why full options backtesting is not on the roadmap:**
1. **No historical chain data** — backtesting requires full chain snapshots (strikes + IVs + bid/ask) at historical timestamps. IBKR has it per contract but pulling 16 ETFs × 365 days × full chains = enormous quota + storage. yfinance has no historical chain data. MarketData.app has some but at additional cost.
2. **Path dependency** — options P&L depends on *when* you exit, not just entry/expiry. A sell_put closed at 50% profit at 14 DTE is radically different from holding to expiry. Any backtest ignoring intraday management gives misleading win rates.
3. **IV regime dependency** — the same gate rules produce opposite results in 2022 (VIX 35, high IV) vs 2024 (VIX 13, suppressed IV). A backtest without regime labels is noise, not signal.

**Better alternatives already in the system:**
- **Paper Trade Dashboard** — forward paper trading from today using the exact live gate logic. More honest than a backtest: no look-ahead, real fills, real IV regime.
- **Gate pass rate history** — `iv_history.db` has 7,492 rows of historical IV per ETF + OHLCV. Computable: "when IVR>35 + HV/IV<1.05, what was the ETF's 21-day return?" — no options chain needed.

**Decision:** Let the paper trade dashboard accumulate 30-60 real trades. That win rate data is worth more than a backtest on imperfect historical chains.

**If reconsidered later:** Start with `gate_pass_rate_history` using existing iv_history.db + ohlcv_daily. No new data source needed. Scope: ~2 days. Do NOT attempt full options chain backtesting without a paid historical data subscription.

---

## Post-v1.0 (Backlog)
- [ ] Real-time chain refresh, P&L history chart, multi-ticker watchlist, CSV export
- [ ] Persistent structure cache in SQLite
- [ ] Request deduplication for simultaneous analyze calls (P4 from concurrency arch)
- [ ] MCP server: expose gate_engine, sector_scan, paper_trade as MCP tools for conversational analysis
- [ ] audit_quick.sh: automate mechanical grep-based audit checks (Category 2, 4, 5, 8 partials)

---

## Version Log

| Version | Day | Notes |
|---------|-----|-------|
| v0.1 | Day 1 | Scaffold — Codex files ported, Phase 0 docs complete |
| v0.2 | Day 2 | Frontend redesigned — two-panel layout, verdict hero, collapsible sections |
| v0.3 | Day 3 | Data layer complete — IBWorker, DataService, direction-aware fetch, live IBKR confirmed |
| v0.4 | Day 4 | Concurrency P1 fixes (KI-016/017/018), ticker override + STA offline detection fixed |
| v0.5 | Day 5 | KI-019 heartbeat done, STA field mapping fixed, SPY/200SMA from yfinance, direction lock SELL, struct cache drift, broader strike qualification |
| v0.6 | Day 6 | KI-024 market hours detection — BS greeks when closed, ibkr_closed tier, frontend banner |
| v0.7 | Day 7 | KI-021 strategy routing all 4 directions, KI-027 reqMktData fix for modelGreeks, Phase 4e BS fallback |
| v0.7 | Day 8 | Process session — CLAUDE.md created, session startup/close checklists formalized in CLAUDE_CONTEXT.md |
| v0.8 | Day 9 | KI-026 verified live. KI-030 hv_20 fix. KI-031 pnl_calculator fixed. KI-033 sell_call spread fixed (sort + SMART_MAX). Alpaca researched as REST fallback. |
| v0.9 | Day 10 | KI-035 OI fix applied. alpaca_provider.py created + wired. MarketData.app tested (hist IV=None). Provider research doc. Golden Rule 19. |
| v0.9.1 | Day 11 | KI-037 confirmed (MarketData.app no historical IV — platform limitation). System coherence audit: 47 findings (6 critical, 8 high). Audit doc created. |
| v0.9.2 | Day 12 | All Phase A+D audit fixes shipped. gate_engine Rule 3 fixed (60+ literals → constants.py). KI-035 OI platform limitation confirmed + graceful degradation. SQLite WAL. reqMktData try-finally. ACCOUNT_SIZE guard. sell_put naked warning. System usable for live analysis. |
| v0.10.0 | Day 13 | Sector Rotation ETF module: multi-LLM research (3 models, 7 questions, 3 corrections). sector_scan_service.py (L1+L2). 15 ETFs live-tested. Research-verified: Weakening=WAIT, Lagging=SKIP, Risk-Off=QQQ calls. |
| v0.11.0 | Day 14 | Sector Rotation frontend: SectorRotation.jsx + ETFCard.jsx + useSectorData.js. Tab switcher (Analyze/Sectors). Filter bar, L2 detail panel, deep dive → analyze flow. |
| v0.12.0 | Day 15 | Sector L2 pipeline fixed: get_chain tuple unpack, IVR/HV wiring, SPY regime, scan cache. Behavioral audit (21 claims, 0 BROKEN after fixes). Golden Rule 21. |
| v0.13.0 | Day 16 | L2 live test PASSED (6/7 ETFs). SPY regime: yfinance → STA priceHistory. Massive.com: no historical IV confirmed. Bear market gap identified (buy_put + sell_call untested, Lagging = no bear plays). User manual written. |
| v0.13.1 | Day 17 | First full audit (MASTER_AUDIT_FRAMEWORK, 8 categories). KI-060: SPY gate None→0.0 masking fixed in all 4 directions. KI-061: IVR formula verified correct. All 8 behavioral claims VERIFIED. Threading SAFE. Zero bare excepts. |
| v0.13.1 | Day 18 | Review + planning session (no code changes). Audit framework reviewed (5 improvements, Cat 3 IVR typo fixed). Options Explainer "Learn" tab designed (Phase 8). |
| v0.14.0 | Day 19 | Phase 7b: Sector Bear Market Strategies. Lagging→bear_call_spread, broad selloff detection, ETF gate auto-pass (events/pivot/DTE). 5 bugs fixed (KI-062/063/065/066 + L2 direction). Research doc created. |
| v0.14.1 | Day 20 | ETF liquidity gate BLOCK→WARN, narrow-chain bear_call_spread fallback, session protocol docs fixed. |
| v0.15.0 | Day 21 | **ETF-Only Pivot.** 16-ETF universe enforced (400 for non-ETFs). Signal Board UI (RegimeBar + Scanner + Analysis Panel). ETF gate tracks: _run_etf_buy_call/put/sell_put. _etf_payload() (zero fabrication). Delta-based spread legs. Price-relative P&L scenarios. All 4 directions tested live on XLU. |
| v0.15.1 | Day 22 | Live smoke test. 5 fixes: market_regime_seller ETF blocking, liquidity non-blocking red, spy_above None→False, IVR scan wiring (sell_put when IVR>50%), gate visibility (MasterVerdict inline detail). KI-068/KI-069 identified: strategy.type=None + CAUTION verdict structural issue (OI=0 platform limit always warns). |
| v0.16.0 | Day 23 | First GO signals (XLF, XLV bear_call_spread). bull_put_spread. 6 bugs fixed. ExecutionCard + POST /api/orders/stage (later reverted Day 24). |
| v0.16.1 | Day 24 | Structural cleanup: analyze_service.py extraction (app.py 965→320). 27 tests (5 files). ExecutionCard rewritten as IBKR Client Portal visual guide. TWS staging code reverted. README.md comprehensive rewrite. |
| v0.17.0 | Day 25 | **Phase 8 UX Overhaul** — beginner-friendly frontend. DirectionGuide, TradeExplainer (number line + risk/reward bar), GateExplainer (plain English Q&A accordion), LearnTab (4 interactive lessons: Strikes/Directions/Spreads/Gates). MasterVerdict + TopThreeCards enhanced with plain English. MASTER_AUDIT_FRAMEWORK v1.2: Category 9 (Frontend UX Accuracy) added. Zero backend changes. |
| v0.18.0 | Day 26 | **Data infrastructure + gate fixes.** Nightly IV seeding (POST /api/admin/seed-iv/all + UI button). FOMC gate fixed (_days_until_next_fomc() from constants.py). 7,492 IV rows seeded. TradeExplainer strike zone overlap fixed. MasterVerdict passed gates visible. Tradier API reviewed (Lite free = full data API). Data_Strategy_Day26.md. |
| v0.19.0 | Day 27 | **Full audit + pre-trade workflow.** Full audit (0C/0H): bull_put_spread P&L fixed (HIGH), API_CONTRACTS.md synced (MEDIUM), audit framework corrected (LOW). MarketData.app OI/volume supplement (marketdata_provider.py, load_dotenv ordering fix). FOMC calendar corrected (Apr 29 missing). CopyForChatGPT.jsx button. Daily_Trade_Prompts.md. start/stop script PID fixes. ChatGPT live test caught 3 gaps: KI-079 (ETF holdings earnings), KI-080 (bid-ask hard fail), KI-081 (CPI calendar). |
| v0.20.0 | Day 28 | **Gate robustness — ChatGPT-driven fixes.** KI-079 resolved: ETF_KEY_HOLDINGS + COMPANY_EARNINGS (52 companies) + _etf_holdings_earnings_gate() wired into all 4 directions. KI-080 resolved: SPREAD_DATA_FAIL_PCT=20%, spread_pct exposed on gate dict, blocking kept at >20%. FOMC gate: now warns when fomc_days < dte (inside holding window) not just when imminent. KI-082 logged: credit-to-width ratio gap. Tests: 27→29. Two ChatGPT stress tests validated fixes live (XLK + XLY). Pre-analysis prompts in UI proposed for Day 29. |
| v0.21.0 | Day 29 | **Data observability + gate hardening.** KI-082 resolved: MIN_CREDIT_WIDTH_RATIO=0.33 (tastylive empirical), _credit_width() in strategy_ranker, bear_call/bull_put R1/R2 wired. HV/IV VRP gate: _etf_hv_iv_seller_gate() (Sinclair — sell only when IV>HV). VIX regime gate: <15 warn, >30 warn, >40 fail. IVR thresholds: 50→35 (tastylive 60-70% frequency improvement). FOMC imminent fix (<5 days now warns, was falling through). Data Health tab: GET /api/data-health with field-level provenance per ETF (7 fields × 15 ETFs). Best Setups tab: parallel scan, manual trigger, IVR watchlist. Pre-analysis prompts + Paper Trade Dashboard shipped. Tab state retention (display:none vs unmount). IVR key mismatch fixed (was always null). Signal board display:grid override fixed. KI-083/084 discovered via data health (XLE OHLCV corrupted, XLC/XLRE missing). |
| v0.23.0 | Day 31 | **LearnTab Perplexity redesign + UX polish + KI-084/085 resolved.** LearnTab: complete rewrite as 5-panel Perplexity-style trade education panel (Risk/Reward, Strike Zones, Breakeven, Timing/DTE, Safety Gates). Context-aware: real ETF price/strike/premium/expiry from analysis; XLF bear call defaults otherwise. SVG number line with staggered markers (no overlap regardless of proximity). VIX badge in RegimeBar — color-coded per regime (KI-085 resolved). XLRE/SCHB OHLCV seeded (KI-084/087 resolved). Paper trade workflow rebuilt: PaperTradeBanner (strategy picker + confirmation), PaperTradeDashboard (mark/close/delete), PATCH + DELETE endpoints. Best Setups as home screen: default tab 'setups', auto-scan on mount, clickable SetupCards → handleSelectFromSetups → analysis panel + tab switch. |
| v0.22.0 | Day 30 | **McMillan Stress Check + OHLCV data cleanup.** Gemini/McMillan book-audit driven. compute_max_21d_move() in iv_store.py — worst 21-day drawdown + best 21-day rally from OHLCV history. _historical_stress_gate() in gate_engine.py — WARN (non-blocking) if sell_put short strike inside historical worst-drawdown zone; sell_call if inside worst-rally zone. Wired into _run_etf_sell_put and _run_sell_call. Stress fields (max_21d_drawdown_pct, max_21d_rally_pct, stress_bars_available) added to gate_payload in analyze_service.py. Data cleanup: deleted 18 corrupted XLE rows (close>80, ~2x real price) — HV-20 went 413%→17%. Deleted 17 corrupted IWM rows (close<150) — worst_dd went 65%→9.2%. Tests: 29→33. KI-087 logged (XLRE/SCHB 0 OHLCV). |
