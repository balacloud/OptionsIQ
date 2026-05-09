# OptionsIQ — Claude Context
> **Last Updated:** Day 49 (May 8, 2026)
> **Current Version:** v0.32.0
> **Project Phase:** Phase 7c KI sweep complete. KI-096/097/098/100 all implemented. 44 tests. Next: paper trade logging (0/30) + KI-099 scoping.

---

## Session Protocol

### Startup Checklist (read IN THIS ORDER before any code or plan)
1. `CLAUDE_CONTEXT.md` ← this file — current state, known issues, next priorities
2. `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. `docs/stable/ROADMAP.md` — phase status, done vs pending
4. `docs/status/PROJECT_STATUS_DAY49_SHORT.md` — latest day status (update filename each day)
5. `docs/versioned/KNOWN_ISSUES_DAY49.md` — open bugs and severity (update filename each day)
6. `docs/stable/API_CONTRACTS.md` — only if touching API endpoints

After reading, state: current version, current day's top priority, any blockers. Then ask: "What would you like to focus on today?"

Behavioral rules (do not skip):
- Do NOT ask user to re-explain the project
- Do NOT ask for files unless you need to modify them
- Do NOT jump to fixing — understand the problem first

### Close Checklist (end of every session — Golden Rule 9)

**Step 1 — Ask before updating:**
- "Did any bugs get fixed or found this session?" → drives KNOWN_ISSUES update
- "Did any APIs change?" → drives API_CONTRACTS update
- "Did we learn a new rule or process lesson?" → drives GOLDEN_RULES update

**Step 2 — Update all docs (Claude does this, no manual user action needed):**
- [ ] `CLAUDE_CONTEXT.md` — Last Updated, Current State table, Session Log, Next Session Priorities
- [ ] `docs/versioned/KNOWN_ISSUES_DAY{N}.md` — create new file, mark resolved, add new
- [ ] `docs/stable/ROADMAP.md` — tick completed items, add new ones
- [ ] `docs/status/PROJECT_STATUS_DAY{N}_SHORT.md` — create new status snapshot
- [ ] `docs/stable/API_CONTRACTS.md` — if any endpoint added or changed
- [ ] `docs/stable/GOLDEN_RULES.md` — if new rule or process lesson learned
- [ ] `README.md` — update version badge (`> **vX.Y.Z** — Day N`)
- [ ] `memory/MEMORY.md` — update phase, file statuses, priorities
- [ ] Git commit and push

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
| Backend | Defect sweep (Day 43) | KI-064: ATM contract IV in _extract_iv_data() (was averaging). KI-081: MACRO_DATES + _days_until_next_macro() + macro events in gate. fomc_days_away silent 999 bug fixed. Tests: 36. |
| Frontend | GateExplainer + DirectionGuide fixes (Day 43) | hv_iv_vrp + vix_regime GATE_KB entries added. events entry updated for CPI/NFP/PCE. sell_put risk label fix (KI-077). |
| IBKR connection | WORKING | Best Setups + L3 both live. KI-088 resolved (Day 34) — _resolve_underlying_hint() pre-fetches STA price, bypasses unreliable reqMktData snapshot. |
| Gate logic | Hardened Day 28 | Holdings earnings gate live. FOMC window gate fixed. Spread >20% blocks. 29 tests. |
| P&L math | Fixed Day 9 | pnl_calculator.py — None guard + 4 new strategy type handlers |
| Strategy ranking | Updated Day 9+12 | sell_call: bear_call_spread ✓. sell_put: naked + warning label. |
| IV store | Correct (frozen) | iv_store.py verified correct |
| constants.py | DONE (Day 19) | ETF module + Phase 7b bear thresholds: RS_LAGGING_BEAR_RS/MOM, DIRECTION_TO_CHAIN_DIR |
| bs_calculator.py | DONE | Black-Scholes greeks fallback |
| ib_worker.py | DONE (Day 5) | Queue poisoning + heartbeat + RequestTimeout |
| yfinance_provider.py | DONE | Middle tier, BS greeks fill (NO greeks — computed via BS only) |
| data_service.py | DONE (Day 12) | Provider cascade + SQLite WAL + CB + Alpaca tier |
| ibkr_provider.py | DONE (Day 12) | try-finally cancelMktData. OI via reqMktData confirmed unavailable (platform limit) |
| alpaca_provider.py | DONE (Day 10) | REST fallback, greeks ✅, NO OI/volume (model limitation) |
| analyze_service.py | DONE (Day 43) | KI-064: _extract_iv_data() uses ATM contract IV. KI-081: _days_until_next_macro() helper. _fomc_days computed once (fixes fomc_days_away=999 silent bug). |
| app.py | 402 lines (Day 46) | sta_fetch logic extracted to sta_service.py (KI-086 closed). Rule 4 still technically violated (>150) but all business logic is now in service modules. |
| batch_service.py | NEW (Day 35) | 148 lines — seed_iv_for_ticker(), run_bod_batch(), run_eod_batch(). APScheduler target functions. |

### Backend Files (current state)
```
backend/
  app.py              497 lines — startup catch-up wired (Day 37). load_dotenv() MUST be first import.
                                   KI-086: still above Rule 4 (150). _run_one closure still inline.
  batch_service.py    UPDATED (Day 37) — 231 lines. seed_iv_for_ticker(), run_bod_batch(), run_eod_batch().
                                   run_startup_catchup() daemon (Day 37) — fires missed BOD/EOD on startup.
                                   yfinance IV fallback REMOVED (Day 37) — HV≠IV, contaminates IVR.
                                   OHLCV yfinance fallback kept (price data correct from both).
  constants.py        DONE (Day 12) — 19 new thresholds: IV abs fallback, DTE signal quality,
                                      SPY regime per direction, STRIKE_SAFETY_RATIO, SELL_CALL_OTM_PASS_PCT
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single thread, submit() queue, expires_at, heartbeat (30s idle)
  yfinance_provider.py DONE — emergency fallback (no greeks — computed via BS)
  data_service.py     DONE (Day 12) — provider cascade + SQLite WAL + timeout + CB + Alpaca tier
  ibkr_provider.py    DONE (Day 12) — try-finally cancelMktData (no zombie subs).
                                     OI via reqMktData CONFIRMED unavailable (platform limitation).
                                     direction-aware strike sort (sell_call asc, sell_put desc)
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
                                     alpaca-py SDK, OCC parsing, direction-aware DTE/strike windows
                                     Tier 4 in cascade (between stale cache and yfinance)
  mock_provider.py    PARTIAL — still partially hardcoded (low priority)
  gate_engine.py      DONE (Day 12+28) — Rule 3 fixed (60+ literals → constants.py).
                                     Liquidity gate: OI=0+Vol>0 → WARN. spread_pct on gate dict.
                                     _etf_holdings_earnings_gate() wired all 4 tracks (Day 28).
                                     FOMC gate: fomc_days < dte (inside window) not just imminent (Day 28).
  strategy_ranker.py  UPDATED (Day 20) — narrow-chain fallback: when all delta targets cluster to same strike,
                                        uses 2nd-highest OTM as short + highest OTM as protection.
                                        sell_put naked put warning added to all 3 strategies.
                                        _rank_sell_call → bear_call_spread (delta 0.30/0.15) ✓
                                        _rank_buy_put   → ITM put + bear put spread + ATM put ✓
                                        _rank_track_b   → naked sell_put + naked warning
  pnl_calculator.py   FIXED (Day 9) — None guard, handlers for itm_put/atm_put/bear_call_spread/sell_call
                                       spread handler direction-aware via right field
  iv_store.py         FROZEN — math correct

  sector_scan_service.py  DONE (Day 19) — STA consumer + quadrant→direction + catalyst warnings.
                                       L1 scan (15 ETFs + SPY regime) + L2 analyze (IV/IVR/HV/liquidity).
                                       Day 19: Phase 7b bear logic (Lagging→bear_call_spread), _detect_regime(),
                                       L2 chain fix (DIRECTION_TO_CHAIN_DIR), IVR bear warning.

  analyze_service.py  DONE (Day 24+28+36) — 835 lines. _etf_holdings_at_risk() added (Day 28).
                                   Day 36: IV patching from MD.app when chain IV=null + md_supplement in response.

  tests/               DONE (Day 24+28+30+34) — 36 tests (pytest). 6 files: bs_calculator, spread_math,
                                   direction_routing, gate_engine_etf, etf_gate_postprocess, resolve_underlying_hint.

  constants.py         DONE (Day 19+27+28) — ETF_KEY_HOLDINGS (16 ETFs), COMPANY_EARNINGS (52 cos,
                                   Q2–Q4 2026). SPREAD_DATA_FAIL_PCT=20.0. FOMC_DATES correct.

  marketdata_provider.py  DONE (Day 27+35+36) — OI/volume + greeks supplement from MarketData.app REST API.
                                          Non-blocking (5s timeout). Wired into analyze_etf().
                                          Day 35: credit tracking (X-Api-Ratelimit-Remaining/Consumed headers).
                                          Day 36: IV, delta, gamma, theta, vega now parsed and returned.
                                          Free tier (100/day) confirmed sufficient — ~33 credits/day actual usage.
```

---

## Architecture

**Backend:** Flask on port 5051
**Frontend:** React on port 3050
**IB Gateway:** 127.0.0.1:4001 (live account U11574928)
**Database:** SQLite at `backend/data/` (chain_cache.db + iv_store.db)

### Data Provider Hierarchy — DataService.get_chain() (Day 39)
```
[1] BOD Cache (SQLite, pre-warmed 9:31 AM)   ← "bod_cache" — fastest, no network call
[2] Tradier REST (real-time, brokerage acct) ← "tradier" — PRIMARY live source, no IB Gateway needed
[3] Stale BOD Cache                          ← "ibkr_stale" — last known-good if Tradier fails
[4] Alpaca (15-min delayed REST)             ← "alpaca" — greeks+IV, no OI
[5] yfinance (emergency fallback)            ← "yfinance" — NO real greeks (BS computed)
[6] Mock (dev/CI testing ONLY)              ← NEVER for paper trades

IBKR LIVE REMOVED from DataService (Day 39). See ARCH_DECISION_TRADIER_PRIMARY.md.
IBKR only called by: run_eod_batch() → ib_worker.submit(get_historical_iv) for IV seeding.
MarketData.app: OI/volume supplement for Liquidity gate (~33 credits/day, Free tier).
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

### Market Hours Behavior (KI-024 resolved Day 6)
```
MARKET OPEN (9:30am–4:00pm ET, Mon–Fri):
  reqMktData(snapshot=False) → tickOptionComputation fires → live modelGreeks
  data_source = "ibkr_live", greeks_pct ~80-100% (pending verification Day 8)

MARKET CLOSED (evenings, weekends, pre-market):
  IBKRProvider._market_is_open() → False → skip reqTickers
  Calls _get_hv_estimate(ticker) via yfinance → 20-day HV as IV proxy
  Computes BS greeks for all qualified contracts
  data_source = "ibkr_closed" (new tier in data_service)
  Frontend: amber banner "Market closed — using estimated greeks"
  Liquidity gate still FAILs (OI=0 expected), but theta/delta/vega are real
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

Full list: `docs/versioned/KNOWN_ISSUES_DAY48.md`

Open (HIGH):
1. **KI-059: single-stock bear untested** — DEFERRED. Stocks return 400. ETF all 4 directions ✅ Day 21.

Open (MEDIUM):
2. **KI-101:** Best Setups watchlist IV/HV ratio shows `—` when chain IV null but OHLCV/HV data is available

Open (LOW):
3. **KI-099:** bull_call_spread missing as direction for Leading/Improving + IVR 30–50% (deferred, high complexity)

Resolved (Day 49): KI-096 ✅ (IVR null→unknown confidence), KI-097 ✅ (event density gate), KI-098 ✅ (weekChange tape-fight gate), KI-100 ✅ (Tier 1 GO rate reporting). 8 new tests (36→44).
Resolved (Day 48): No code resolutions — research session only. 5 new design gaps logged.
Resolved (Day 47): No new KI resolutions. All code issues closed.
Resolved (Day 46): KI-086 ✅ CLOSED (sta_service.py extracted — sta_fetch 74 lines → 2 lines). ETF sell_call DTE bug fixed (pre-existing: was using stock DTE constants, now uses _run_etf_sell_call with ETF_DTE_SELLER_PASS_MIN=30). ETF_DTE_SELLER_PASS_MIN 21→30.
Resolved (Day 44): KI-076 (TradeExplainer isBearish() — no bug, all 4 directions verified correct via live API). Tradier all 4 directions confirmed (Category 7).
Resolved (Day 43): KI-064 (IVR mismatch ATM IV fix), KI-075 (GATE_KB drift + DTE constants), KI-077 (sell_put label), KI-081 (macro events CPI/NFP/PCE). Bonus: fomc_days_away silent 999 bug.
Resolved (Day 42): KI-094 (QualityBanner ibkr_cache key), KI-095 (BatchStatusPanel UTC timestamp). Plus 4 audit MEDIUM fixes same session.
Resolved (Day 40): KI-090/091/092/093 — Tradier delta coercion, direction-aware strike window, bod_cache rename, iv_provider tradier mapping.
Resolved (Day 39): KI-086 (best_setups_service.py extracted), KI-067 (QQQ sell_put ITM fix).
Resolved (Day 34): KI-088 (L3 stale banner).
Resolved (Day 32): KI-VRP-INVERT, LearnTab zones overlap.
Resolved (Day 31): KI-084/087, KI-085.
Resolved (Day 30): KI-083, KI-IWM-OHLCV.
Resolved (Day 29): KI-082, IVR key mismatch, signal board fix.
Resolved (Day 28): KI-079, KI-080, FOMC window gate.
Resolved (Day 27): KI-078, bull_put_spread P&L.
Resolved (Day 26): KI-008, IVR cold-start.
Resolved (Day 24): KI-071/KI-070/KI-001/KI-023.

---

## Session Log

| Day | Date | What Happened |
|-----|------|--------------|
| Day 1 | Mar 5, 2026 | Project scaffolded. Phase 0 docs created. Codex files ported. |
| Day 2 | Mar 5, 2026 | GOLDEN_RULES enhanced. Full frontend UI redesign (8 files). |
| Day 3 | Mar 6, 2026 | Phase 1+2 complete. IBWorker, DataService, direction-aware fetch. Live IBKR confirmed. |
| Day 4 | Mar 7, 2026 | KI-016 queue poisoning (expires_at). KI-017 RequestTimeout=15. KI-018 legacy CB removed (821→527). KI-020 strategy_ranker right=None. Ticker override + STA offline fixed. MEOH confirmed live. |
| Day 5 | Mar 10, 2026 | KI-019 heartbeat done. STA field mapping fixed (suggestedEntry/Stop/Target). spy_above_200sma from yfinance. Direction lock SELL. Struct cache drift invalidation (15%). SMART_MAX_EXPIRIES 1→2, SMART_MAX_STRIKES 4→6, broad retry <3 contracts. start.sh .env fix. CTRA+NVDA tested. Market-closed behavior diagnosed (KI-024 new). |
| Day 6 | Mar 10, 2026 | KI-024 market hours detection. ibkr_provider: _market_is_open() (ET TZ), _get_hv_estimate() (20-day HV). BS greeks when closed. ibkr_closed tier in data_service. Frontend amber banner + "IB Closed" header. Fixed logger import + broad retry variable scope bug. |
| Day 7 | Mar 10, 2026 | Strategy ranker: explicit builders for sell_call (bear call spread) + buy_put (long put + bear put spread) — KI-021 fixed. Root cause of modelGreeks=None found: reqTickers() doesn't fire tickOptionComputation. Replaced with reqMktData(snapshot=False) throughout. Phase 4d extended wait (sleep 3+5). Phase 4e BS fallback if usopt still silent. Confirmed OPRA subscription adequate (no new subscription needed). Stale AMD chain cache cleared (strike mismatch at ~182 vs live ~205). |
| Day 8 | Mar 11, 2026 | Process session — no code changes. Created CLAUDE.md (session pointer). Added startup + close checklists to CLAUDE_CONTEXT.md. Enforced ordered priming: CLAUDE_CONTEXT → GOLDEN_RULES → ROADMAP → PROJECT_STATUS → KNOWN_ISSUES → API_CONTRACTS. |
| Day 9 | Mar 11, 2026 | KI-026 live greeks CONFIRMED (100% greeks_pct, ibkr_live, Phase 4e never fired). KI-030 AMD hv_20 corruption fixed (deleted 20 bad ohlcv rows). KI-031 pnl_calculator None crash fixed + 4 strategy type handlers added. KI-033 sell_call bear_call_spread fixed: direction-aware sort + SMART_MAX_STRIKES 6→12 + MAX_CONTRACTS 12→26. OI field fix: optOpenInterest. Alpaca researched: great REST fallback, needs alpaca_provider.py + API secret. |
| Day 10 | Mar 12, 2026 | KI-035 OI fix applied (genericTickList="101"). alpaca_provider.py CREATED + wired into DataService+app.py. .env syntax fix. Alpaca live-tested: greeks ✅, OI/volume ❌ (model limitation). MarketData.app live-tested: current greeks ✅, historical IV=None (unknown if trial/platform). Perplexity research: 9 providers compared, none under $30/mo has historical IV. Research doc created (docs/Research/). Golden Rule 19 added. |
| Day 11 | Mar 13, 2026 | KI-037 CONFIRMED (MarketData.app no historical IV — platform limitation). System coherence audit: 47 findings. Behavioral audit: 17 claims, 8 verified, 3 misleading, 5 false. Key findings: liquidity gate permanently broken (OI=0), gate_engine 60+ hardcoded thresholds (Rule 3 violated), 2 missing quality banners, sell_put naked with no warning, DTE buyer sweet spot not enforced, ACCOUNT_SIZE silently defaults. Sector rotation ETF module researched. |
| Day 12 | Mar 17, 2026 | All Phase A+D critical/high audit fixes shipped during market hours. KI-035 OI confirmed platform limitation — graceful degradation added (WARN not BLOCK). gate_engine Rule 3 fixed (60+ literals → constants.py). SQLite WAL. reqMktData try-finally. Startup guard for ACCOUNT_SIZE. sell_put naked warning. QualityBanner fixed. alpaca+ibkr_stale banners added. System now usable for live analysis. |
| Day 13 | Mar 19, 2026 | Sector Rotation ETF module: multi-LLM research (Gemini+GPT-4o+Perplexity), 7 questions audited, 3 design corrections (Weakening→WAIT, Lagging→SKIP, Risk-Off→QQQ calls). sector_scan_service.py created (L1 scan + L2 analyze). ETF constants added. L1 tested live with STA: 15 ETFs, correct quadrant→direction mapping, catalyst warnings working. |
| Day 14 | Mar 19, 2026 | Sector Rotation frontend: SectorRotation.jsx + ETFCard.jsx + useSectorData.js. Tab switcher (Analyze/Sectors) in App.jsx. Filter bar (All/Analyze/Watch/Skip), L2 detail panel, cap-size signal banner, deep dive → analyze flow. Build passes clean. |
| Day 15 | Mar 20, 2026 | Sector L2 pipeline completely fixed. Coherence audit: C1-C2 (bull_call_spread), C3 (scan cache), H1-H4, M1-M7, L1-L5. Quant audit: Q1 (IVR wiring), Q2 (liquidity), Q3 (SPY regime), Q4 (cache safety), Q5 (0→None). Behavioral audit: 21 claims — 3 BROKEN/3 FALSE found+fixed. get_chain tuple fix (showstopper). Golden Rule 21 added. |
| Day 16 | Mar 20, 2026 | P0 live test PASSED (6/7 ETFs): XLE/XLU/XLK/MDY/IWM/TQQQ all return live IV/IVR. QQQ still 0 contracts (KI-025). IVR direction adjustment confirmed (buy_call→bull_call_spread). L3 deep dive confirmed (XLE BLOCK, live greeks). SPY regime: yfinance → STA priceHistory (rate limit fix). Massive.com: no historical IV = IBKR still required. User manual written. Bear market gap identified (buy_put + sell_call not live tested, Lagging sector = no bear plays). |
| Day 17 | Mar 22, 2026 | First full audit using MASTER_AUDIT_FRAMEWORK (8 categories). All 8 claims VERIFIED. Threading SAFE. Zero bare excepts. KI-060 FIXED: spy_5day_return None→0.0 silent masking in all 4 gate tracks — now returns non-blocking warn. KI-061 CLOSED: iv_store IVR formula verified correct (percentile). Audit health: 0 CRITICAL, 2 HIGH (KI-059 bear untested, KI-044 API docs). No market hours today. |
| Day 18 | Mar 23, 2026 | Review + planning session (no code changes). Audit framework reviewed: 5 improvements identified (regression gate, Cat 3 IVR typo fixed, Cat 9 smoke test proposed, delta tracking, automation). Options Explainer "Learn" tab concept designed (Phase 8). MCP servers discussed. Audit health unchanged: 0C/2H. |
| Day 19 | Mar 24, 2026 | Phase 7b: Sector Bear Market Strategies shipped. Lagging→bear_call_spread (RS<98, mom<-0.5). Broad selloff detection. 5 bugs fixed: KI-062 (earnings fabricated), KI-063 (SPY regime fabricated + unit mismatch), KI-065 (Deep Dive direction), KI-066 (DTE gate ETF). ETF gate post-processing: events/pivot/DTE auto-pass. Research doc created. Live tested: XLV+XLY bear_call_spread, QQQ SKIP, BROAD_SELLOFF fires. |
| Day 20 | Mar 28, 2026 | Sector options pipeline unblocked: ETF liquidity gate BLOCK→WARN (OTM spread too strict), strategy_ranker narrow-chain fallback (135/136 Bear Call for XLK). Session startup protocol fixed across 3 docs (MEMORY.md 3-step→6-step). KI-067 NEW: QQQ chain too narrow for current price. XLK/XLY/XLF all return bear_call_spread strategies. QQQ still blocked. |
| Day 21 | Apr 9, 2026 | **ETF-Only Pivot (v0.15.0).** 16-ETF universe enforced. Signal Board UI (RegimeBar+Scanner+Analysis Panel). ETF gate tracks (_run_etf_buy_call/put/sell_put). _etf_payload() zero-fabrication. Delta-based spread legs. Price-relative P&L. All 4 directions tested live XLU. 3 bugs fixed: pnl TypeError, IBKR clientId conflict, React STA-offline crash. |
| Day 22 | Apr 14, 2026 | **Live smoke test + 5 fixes (v0.15.1).** market_regime_seller ETF blocking fixed. Liquidity non-blocking red fixed. spy_above_200sma None→False fixed. IVR scan wiring complete (sell_put when IVR>50%). MasterVerdict gate detail inline. GatesGrid auto-open. KI-068/KI-069 identified: strategy.type=None + CAUTION always (OI=0 platform limit). |
| Day 23 | Apr 15, 2026 | **First GO signals + ExecutionCard (v0.16.0).** KI-069 fixed (OI=0→pass for ETFs). KI-068 fixed (direction normalization bear_call_spread→sell_call). bull_put_spread built (_rank_sell_put_spread). ETF sell_put max_loss re-evaluated using spread. ETF DTE seller 21-45→pass. PnLTable auto-open. MasterVerdict all fails inline. ExecutionCard.jsx + POST /api/orders/stage + ibkr_provider.stage_spread_order() — NOT yet wired into App.jsx (KI-071). |
| Day 24 | Apr 15, 2026 | **Structural cleanup (v0.16.1).** analyze_service.py extracted (app.py 965→320 lines, analyze_service 604 lines). TWS staging code reverted (readonly=True, stage_spread_order removed, POST /api/orders/stage removed). 27 tests created (5 files: BS greeks, spread math, direction routing, gate engine, ETF post-processing). ExecutionCard rewritten as IBKR Client Portal visual guide (no API calls). KI-071/KI-070/KI-001 resolved. README.md comprehensively rewritten. |
| Day 26 | Apr 20, 2026 | **Data infrastructure + gate fixes (v0.18.0).** FOMC gate fixed: _days_until_next_fomc() from constants.py — no longer 999 when STA offline (16 days to May 6). IVR seeding: POST /api/admin/seed-iv/all + ↓ Seed IV UI button — 7,492 rows across 20 tickers seeded from IBKR reqHistoricalData. seed_iv_nightly.sh cron script. Strike zone label overlap fixed (key table below chart). MasterVerdict passed gates visible as green chips. Data_Strategy_Day26.md created (3-option data plan). Tradier API reviewed: Lite free account = full options data API with OI, volume, Greeks (120 req/min). EODHD tested: paywalled on free tier — verify before paying. KI-008 resolved, 3 issues fixed total. |
| Day 27 | Apr 21, 2026 | **Full audit + pre-trade workflow + bug fixes (v0.19.0).** Full MASTER_AUDIT_FRAMEWORK run (all 9 categories): 0C/0H. HIGH fixed: bull_put_spread P&L handler missing since Day 23 (all sell_put P&L rows were 0). MEDIUM fixed: API_CONTRACTS.md synced (pacing_warning, sources_used, alpaca, ETF enforcement, OI note). LOW fixed: MASTER_AUDIT_FRAMEWORK direction table + sell_call claim. MarketData.app integration: marketdata_provider.py + load_dotenv() ordering bug fixed. Pre-trade research: Daily_Trade_Prompts.md (7 prompts for Perplexity/ChatGPT/Gemini) + CopyForChatGPT.jsx button (pre-fills Prompt 4 from live analysis data). start/stop script reliability: -sTCP:LISTEN flag, webpack PID capture. ChatGPT live test of XLY trade caught: FOMC gate false negative (corrected constants.py Apr 29 date), ETF holdings earnings gap (new KI-079), liquidity hard-fail gap (new KI-080). MCP ecosystem researched — Perplexity + FMP MCPs recommended, no options-specific MCPs exist yet. |
| Day 28 | Apr 22–26, 2026 | **Gate robustness — ChatGPT-driven fixes (v0.20.0).** KI-079 resolved: ETF_KEY_HOLDINGS (16 ETFs) + COMPANY_EARNINGS (52 companies, Q2–Q4 2026) + _etf_holdings_at_risk() + _etf_holdings_earnings_gate() wired into all 4 ETF direction tracks. KI-080 resolved: SPREAD_DATA_FAIL_PCT=20.0 in constants, spread_pct exposed on liquidity gate dict, apply_etf_gate_adjustments() now keeps blocking=True above 20%. FOMC gate fixed: now warns whenever fomc_days < dte (inside holding window) not just ≤10 days imminent — caught by ChatGPT on XLK sell_put (FOMC April 29, DTE 30, gate was passing). KI-082 logged: credit-to-width ratio ($0.05 on $1-wide = 5%, industry min ~20%). Tests: 27→29. Two ChatGPT stress tests (XLK + XLY) validated all gate fixes live. Feature idea logged: pre-analysis prompts in UI for Day 29. |
| Day 29 | Apr 27, 2026 | **Data observability + gate hardening (v0.21.0).** KI-082 resolved: MIN_CREDIT_WIDTH_RATIO=0.33 (tastylive/Sinclair empirical), _credit_width() in strategy_ranker, wired into bear_call/bull_put R1/R2, 4 tests. HV/IV VRP gate: _etf_hv_iv_seller_gate() — sell only when IV>HV (Sinclair volatility risk premium). VIX regime gate: <15 warn, >30 warn, >40 fail, wired into seller tracks. IVR seller threshold: 50→35 (tastylive: IVR>50 sacrifices 60-70% frequency). FOMC imminent fix: <5 days now warns (was falling through). Multi-LLM synthesis doc created. Best Setups tab: parallel ETF scan, manual Run Scan, watchlist with IVR (fixed key mismatch iv_data→ivr_data). Data Health tab: GET /api/data-health — source health + IV history + chain cache + field-level resolution (7 fields × 15 ETFs). DataProvenance.jsx built. Pre-analysis prompts + Paper Trade Dashboard shipped (SQLite-backed). Tab state retention: display:none pattern (preserves scan state across switches). Signal board display:grid fix (was overridden by display:block). KI-083 (XLE HV=413% from corrupted OHLCV) + KI-084 (XLC/XLRE no OHLCV) discovered via data health tab. FOMC confirmed 2 days away (Apr 29) — explains all Best Setups blocked. |
| Day 30 | Apr 28, 2026 | **McMillan Stress Check + OHLCV cleanup (v0.22.0).** Gemini book-audit driven. compute_max_21d_move(ticker) in iv_store.py — worst 21-day drawdown + best 21-day rally. _historical_stress_gate(p, direction) in gate_engine — WARN (non-blocking) if sell_put strike inside historical worst-drawdown zone; sell_call if inside worst-rally zone. gate_payload gets stress fields. OHLCV cleanup: XLE 18 rows deleted (close>80, HV 413%→17%). IWM 17 rows deleted (close<150, worst_dd 65%→9.2%). Tests: 29→33. KI-083 + KI-IWM resolved. KI-087 logged (XLRE/SCHB 0 OHLCV). |
| Day 49 | May 8, 2026 | **Phase 7c KI sweep + `/ki` slash command (v0.32.0).** KI-096/097/098/100 all resolved (36→44 tests). 3/3 LLM audit consensus confirmed before implementing. KI-098: weekChange tape-fight gate. KI-096: ivr_confidence flag (WARN not FAIL on no history). KI-097: _etf_event_density_gate() weighted event count. KI-100: tier1_summary in best-setups + Tier 1 pills UI. New: `/ki` command (.claude/commands/ki.md) — type `/ki "description"` to instantly log a numbered KI entry. KI-101 found: IV/HV shows `—` in watchlist when chain IV null. |
| Day 48 | May 8, 2026 | **Phase 7c external audit + STA code review (v0.31.0 — no code changes).** STA backend.py reviewed — RS ratio = midpoint normalization (swing-trading RRG variant), weekChange computed and returned but unused by quadrant_to_direction(). Phase7c two-file redundancy eliminated → Phase7c_Research.md (single consolidated doc). ChatGPT 4-question audit stored: 5 design gaps logged as KI-096–100 (IVR null coercion, event density, absolute trend gate, bull_call_spread direction, Tier 1 GO rate reporting). Awaiting Gemini/Perplexity results before implementing. |
| Day 47 | May 7, 2026 | **README full rewrite + Phase 7c code improvements (v0.31.0).** README rewritten — 9+ stale sections fixed (Tradier as primary, 15 ETFs not 16, all 21 backend files, 22 frontend components, API table 10→21 endpoints, version history through v0.30.1). Phase 7c: ETF_OPTIONS_LIQUID_TIER1 in constants, _is_early_market_session() helper, ticker in gate_payload, actionable liquidity messages (Tier2 ETF → "try QQQ/XLF", early session → "rescan after 10 AM"). Phase7c_Research.md created (merged from Day46+47 docs). |
| Day 46 | May 7, 2026 | **KI-086 closed + DTE calibration (v0.30.1).** sta_service.py extracted (sta_fetch 74 lines → 2 lines, app.py 472→402). ETF sell_call DTE bug fixed: _run_etf_sell_call() added (was using stock DTE constants 14-21, now ETF 30-45). ETF_DTE_SELLER_PASS_MIN 21→30 (tastylive 200k+ trade research). Category 10 live research: 2/11 CAUTION today, Liquidity Proxy dominant blocker, vol gates all pass at VIX=17.39. |
| Day 44 | May 6, 2026 | **Verification session (v0.30.0).** KI-076: TradeExplainer isBearish() verified correct (no bug). Tradier all 4 directions live-confirmed. Data requirements audit: BOD=zero IBKR, EOD=hard IBKR. No code changes. |
| Day 43 | May 6, 2026 | **Defect sweep (v0.30.0).** KI-064: ATM contract IV in _extract_iv_data() — IVR L2/L3 gap eliminated. KI-075: GATE_KB hv_iv_vrp+vix_regime entries added; ETF sell_put DTE gate fixed to use ETF_DTE_SELLER_PASS_MIN/MAX (was using wrong single-stock VCP constants). KI-077: sell_put risk label. KI-081: MACRO_DATES (CPI/NFP/PCE 2026-2027) + _days_until_next_macro() + macro events in gate + fomc_days_away silent 999 bug fixed. |
| Day 42 | May 6, 2026 | **Skew + full audit (v0.29.0).** `compute_skew()` shipped (Tradier 2-call fetch, put_iv_30d − call_iv_30d, 8-field response). Day 42 full audit (MASTER_AUDIT_FRAMEWORK v1.3): 0C · 2H · 3M — all resolved. QualityBanner ibkr_cache key fixed (KI-094). BatchStatusPanel UTC timestamp fixed (KI-095). ACCOUNT_SIZE silent default removed. Rule 16 added (restart backend after .py edits). |
| Day 41 | May 6, 2026 | **Polish + observability (v0.28.2).** DataFlowDiagram SVG: Tradier as PRIMARY LIVE (dark green), IBKR demoted to EOD-only, cascade subtext added. FOMC 2026 dates verified correct (no code changes needed). Tradier startup health ping: `_tradier_ok` + `_tradier_error` on startup, surfaced in `/api/health`. No bug fixes. 36 tests. |
| Day 40 | May 5, 2026 | **Tradier production-ready — KI-090/091/092/093 resolved (v0.28.1).** KI-090: Tradier delta=0.0 coercion fixed (`_f(...) or None` → `float(g[key]) if g.get(key) is not None else None`). KI-091: Direction-aware strike window added to tradier_provider (sell_put OTM filter, sell_call OTM filter). KI-092: "ibkr_cache" renamed to "bod_cache" in data_service + data_health_service. KI-093: iv_provider now maps "tradier"+"alpaca" → yf_provider. End-to-end smoke test passed: IB Gateway OFF, 5/5 Best Setups = data_source=tradier, 0 ITM puts, all deltas non-null. |
| Day 39 | May 5, 2026 | **Tradier primary + KI-086/KI-067 resolved (v0.28.0).** tradier_provider.py created + wired into DataService. IBKR removed from DataService live chain path — IB Gateway now only needed for EOD batch (4:05 PM ET). Cascade: BOD cache → Tradier → stale cache → Alpaca → yfinance → Mock. KI-086: best_setups_service.py extracted (app.py 497→449 lines). KI-067: ibkr_provider OTM filter for sell_put + strategy_ranker fallback → return [] (no more ITM strikes). Manual BOD/EOD trigger buttons with idempotency check. Startup catchup delay 10s→30s + _ran_on() min_duration=1.0. ARCH_DECISION_TRADIER_PRIMARY.md + backup created. |
| Day 38 | May 5, 2026 | **DataFlowDiagram + doc corrections (v0.27.1).** DataFlowDiagram SVG component added and wired into DataProvenance tab — always visible, two-section architecture diagram (Live Analysis + Batch/Nightly). MD.app confirmed FREE tier (100 credits/day, was incorrectly documented as Starter $12/mo). Tradier support confirmed: no subscription needed for API access. |
| Day 37 | May 4, 2026 | **Startup catch-up + IV integrity (v0.27.0).** run_startup_catchup() daemon thread fires missed BOD/EOD jobs on startup (checks batch_run_log for prev-day EOD, today's BOD/EOD). yfinance HV removed from IV seeding pipeline — HV≠IV, storing HV in iv_history.db contaminates IVR percentile. docs/Research/ reorganized (18 files→6 subdirs) with DATA_PROVIDERS_SYNTHESIS.md. Tradier: confirmed free with brokerage account, ORATS greeks hourly. Massive.com: final verdict don't buy. |
| Day 36 | May 4, 2026 | **MarketData.app greeks pipeline (v0.26.1).** marketdata_provider.get_oi_volume() now returns IV+greeks (delta/gamma/theta/vega) alongside OI/volume. analyze_etf() patches current_iv from MD.app when Alpaca chain IV=null — recomputes IVR percentile + hv_iv_ratio, sets iv_source="marketdata". md_supplement dict added to analyze response. |
| Day 35 | May 1, 2026 | **Batch infrastructure + architecture decisions (v0.26.0).** APScheduler wired: BOD 9:31 AM + EOD 4:05 PM ET auto-fire Mon-Fri. batch_service.py extracted (148 lines) — seed_iv_for_ticker, run_bod_batch, run_eod_batch. app.py 536→492 lines (KI-086 partial). Batch status dashboard in DataProvenance (BatchStatusPanel + IVCoverageGrid). MarketData.app credit tracking live (~33 credits/day vs 100 limit — stay on Free). Full Greeks at all MD tiers confirmed via docs scrape. Two-arch design locked: Alpaca+MD live hours / IBKR batch-only. 15 ETFs confirmed (SCHB not in app). New routes: GET /api/admin/batch-status, POST /api/admin/warm-cache. |
| Day 34 | Apr 30, 2026 | **KI-088 resolved (v0.25.1).** _resolve_underlying_hint() helper added to analyze_service.py — STA canonical source for underlying price. L3 "Run Analysis" now returns ibkr_live (was ibkr_stale). _run_one simplified. Data Provenance: underlying_price field added. MarketData.app diagnostic: full chain data confirmed (IV+greeks+bid/ask+OI), no historical IV. KI-089 logged for Day 35 ($12/mo subscription plan). 36 tests pass. |
| Day 33 | Apr 30, 2026 | **Best Setups scan infrastructure overhaul (v0.25.0).** 8 root-cause fixes: CB threshold 2→5, stale spread WARN not BLOCK (data_source param added to apply_etf_gate_adjustments), verdict_label null fix (headline key), amber→yellow normalization + data_source added to _run_one, VIX from STA (rate-limit fix + threading.Lock), OHLCV reqHistoricalData skipped when SQLite ≤2 days fresh, STA underlying price pre-fetch in _run_one bypasses get_underlying_price() IBKR call, max_workers=1 (sequential, eliminates queue expiry). Result: 6 CAUTION setups confirmed live (XLF 9/11, XLK 9/11, XLC 8/11, XLY, XLV, XLP). VIX=17.59 from STA. 33 tests pass. KI-088 new: L3 stale banner — same STA price fix needed in analyze_etf() main path. |
| Day 32 | Apr 29, 2026 | **VRP gate fix + IV/HV watchlist + zones fix (v0.24.0).** Critical bug found: `_etf_hv_iv_seller_gate()` inverted since Day 29 — compared IV/HV ratio against HV/IV thresholds, blocking sellers when IV > HV (should PASS). Fixed comparison operators, removed HV_IV_SELL_WARN_RATIO constant, updated display label. IV/HV column added to Best Setups watchlist (green ≥1.05, amber 1.0–1.05, red <1.0). LearnTab zones: zone text moved to edge-anchored corners (no more overlap with strike labels), BE label gets collision-aware horizontal offset when near short strike, TOTAL_H 102→116. API: best-setups results now include iv_hv_ratio, hv_20, current_iv. 33 tests pass. |
| Day 31 | Apr 29, 2026 | **LearnTab redesign + UX polish + KI-084/085 resolved (v0.23.0).** LearnTab: Perplexity-style 5-panel trade education panel (Risk/Reward, Strike Zones, Breakeven, Timing/DTE, Safety Gates) replacing generic 4-lesson format. Context-aware: uses real ETF price/strike/premium/expiry from analysis when available; XLF defaults otherwise. SVG number line (staggered markers, no overlap). VIX badge added to RegimeBar with color coding (KI-085). XLRE/SCHB OHLCV seeded via _seed_iv_for_ticker() enhancement (KI-084/087). Paper trade workflow rebuilt: PaperTradeBanner (strategy picker), PaperTradeDashboard (mark/close/delete per trade), PATCH + DELETE endpoints. Best Setups as home screen: default tab 'setups', auto-scan on mount, clickable SetupCards → analysis + tab switch. |
| Day 25 | Apr 17, 2026 | **Phase 8 UX Overhaul (v0.17.0).** Research-first: 3 multi-LLM prompts (GPT-4o + Gemini + Perplexity) synthesized before coding. New: DirectionGuide.jsx (educational 2×2 direction cards), TradeExplainer.jsx (percentage-based number line + risk/reward bar + ITM/ATM/OTM zones), GateExplainer.jsx (accordion Q&A, readiness bar, gate meters), LearnTab.jsx (4 interactive lessons: Strikes/Directions/Spreads/Gates). Enhanced: MasterVerdict (plain English subtitle), TopThreeCards (plain English per strategy). App.jsx wired with tab nav (Signal Board / Learn Options). 600 lines new CSS. Build clean (0 warnings, 0 errors). MASTER_AUDIT_FRAMEWORK v1.2: Category 9 (Frontend UX Accuracy) added. 3 new KIs: KI-075 (GATE_KB drift), KI-076 (isBearish() untested live), KI-077 (sell_put capped label). Zero backend changes. |

---

## Next Session Priorities (Day 50)

### P0 — Paper trade logging (user action)
Log next XLF or QQQ CAUTION setup to Paper Trade Dashboard. Need 30 trades for win rate data. Still at 0.

### P1 — KI-101: IV/HV ratio null in watchlist
Best Setups watchlist shows `—` for IV/HV when Tradier chain returns no IV. Should fall back to HV-20 only display or mark as "HV only". MEDIUM effort.

### P2 — KI-099: bull_call_spread direction for Leading/Improving
For Leading/Improving ETFs + IVR 30–50%, add `bull_call_spread` as suggested direction. High complexity — read existing direction track code first, plan before touching.

### P3 — MASTER_AUDIT_FRAMEWORK sweep
Overdue since Day 42. Run all 10 categories. Focus on Category 10 (Trading Effectiveness) and gate calibration (are 3–5 GO/CAUTION setups surfacing per week?).

### Deferred
- **Backtesting** — explicitly deferred. Full rationale in ROADMAP.md.

### Reference
- `docs/versioned/KNOWN_ISSUES_DAY49.md` — current issue list
- `docs/status/PROJECT_STATUS_DAY49_SHORT.md` — Day 49 summary
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (10 categories, weekly trigger) v1.4
- `docs/Research/Phase7c_Research.md` — Phase 7c research: live scan findings, fixes, adversarial prompts, roadmap
- `docs/Research/Daily_Trade_Prompts.md` — 7 prompts for Perplexity/ChatGPT/Gemini pre-trade research
