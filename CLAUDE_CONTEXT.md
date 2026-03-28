# OptionsIQ — Claude Context
> **Last Updated:** Day 20 (March 28, 2026)
> **Current Version:** v0.14.1
> **Project Phase:** Phase 7b complete + sector options pipeline unblocked. Single-stock bear test (KI-059) next Monday. Phase 8 (Options Explainer) planned.

---

## Session Protocol

### Startup Checklist (read IN THIS ORDER before any code or plan)
1. `CLAUDE_CONTEXT.md` ← this file — current state, known issues, next priorities
2. `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. `docs/stable/ROADMAP.md` — phase status, done vs pending
4. `docs/status/PROJECT_STATUS_DAY20_SHORT.md` — latest day status (update filename each day)
5. `docs/versioned/KNOWN_ISSUES_DAY20.md` — open bugs and severity (update filename each day)
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
- [ ] `memory/MEMORY.md` — update phase, file statuses, priorities
- [ ] Git commit and push (skip push if no remote configured yet)

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
| Backend | Phase 7b complete + pipeline fixes | Sector options pipeline unblocked: ETF liquidity gate BLOCK→WARN, narrow-chain bear_call_spread fallback. app.py + strategy_ranker.py updated. |
| Frontend | Done + Day 19 bear UI | Bear badges, selloff banner, IVR bear warning, Deep Dive direction fix. UI smoke test pending (Monday). |
| IBKR connection | WORKING | Live confirmed: AMD, XLE, XLK, IWM, TQQQ greeks live. account U11574928 |
| Gate logic | Correct + Rule 3 fixed | gate_engine.py imports from constants.py — 60+ literals replaced |
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
| analyze_service.py | NOT CREATED | Day 13 P2 — extract from app.py |
| app.py | Hardened + Day 20 | ~660 lines. SPY regime helpers, earnings None fix, ETF gate post-processing (events/pivot/DTE/liquidity). |

### Backend Files (current state)
```
backend/
  app.py              ~600 lines — HARDENED (Day 12): logger defined, ACCOUNT_SIZE guard,
                                   outer try-except on analyze, bare excepts named+logged.
                                   Still needs analyze_service.py split (Day 13 P2).
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
  gate_engine.py      DONE (Day 12) — Rule 3 fixed: imports from constants.py (60+ literals replaced).
                                     Liquidity gate: OI=0+Vol>0 → WARN not BLOCK.
                                     Still math-frozen — coerce None→0.0 before gate_payload.
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

  # TO CREATE:
  marketdata_provider.py  — MarketData.app REST provider ($12/mo — pending)
  analyze_service.py      — extract _merge_swing, _extract_iv_data, _behavioral_checks
```

---

## Architecture

**Backend:** Flask on port 5051
**Frontend:** React on port 3050
**IB Gateway:** 127.0.0.1:4001 (live account U11574928)
**Database:** SQLite at `backend/data/` (chain_cache.db + iv_store.db)

### Data Provider Hierarchy (live-first)
```
[1] IBKR Live (reqMktData snapshot=False)  ← DEFAULT (greeks confirmed Day 9)
[2] IBKR Cache (SQLite, TTL 2 min)         ← "Using cached chain" banner
[2.5] MarketData.app (PLANNED, $12/mo)    ← greeks+IV+OI+volume, 15-min delayed
[3] Alpaca indicative (DONE, free)         ← greeks+IV but NO OI/volume
[4] yfinance (emergency fallback)          ← NO real greeks (BS computed from HV)
[5] Mock (dev/CI testing ONLY)             ← NEVER for paper trades
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

Full list: `docs/versioned/KNOWN_ISSUES_DAY20.md`

Open (HIGH):
1. **KI-059: single-stock buy_put + sell_call not live tested** — sector bear ETFs ✅ (XLK/XLY/XLF). Individual stocks still need market-hours test (Monday).

Open (MEDIUM):
2. **KI-067: QQQ chain too narrow** — underlying $563.79, chain max strike $562. All calls ITM, strike_otm gate blocks. Struct_cache drift not triggering refresh. NEW Day 20.
3. **KI-064: IVR mismatch L2 vs L3** — L2 percentile vs L3 average aggregation
4. **KI-044: API_CONTRACTS.md partially stale** — market_regime added, full sync still pending
5. **analyze_service.py missing** — app.py ~660 lines (KI-001/KI-023)
6. **Synthetic swing defaults silent** (KI-022/KI-005)
7. **QQQ 0 contracts** — large-cap sparse strikes (KI-025, related to KI-067)

Open (LOW):
7. **Alpaca OI/volume missing** (KI-038)
8. OHLCV temporal gap validation (KI-034)
9. fomc_days_away defaults to 30 (KI-008)
10. API URL hardcoded (KI-013/KI-050)
11. account_size hardcoded in PaperTradeBanner.jsx (KI-049)

Resolved (Day 20):
- ETF liquidity gate BLOCK→WARN: OTM spread too strict for ETFs (app.py ETF post-processing, Rule 5)
- Narrow-chain bear_call_spread fallback: strategy_ranker uses 2nd-highest/highest OTM when chain too narrow
- Session protocol doc gaps fixed: MEMORY.md + GOLDEN_RULES.md aligned to CLAUDE_CONTEXT.md authoritative 6-step list

Resolved (Day 19):
- KI-062: ETF earnings_days_away fabricated 45 → None (Rule 11 fix)
- KI-063: SPY regime fabricated defaults → real STA data + unit mismatch fix
- KI-065: Deep Dive bear_call_spread → buy_call frontend mapping fix
- KI-066: DTE Selection gate false FAIL for ETFs → auto-pass
- L2 None→buy_call: SKIP ETFs silently fetched buy_call chain → direction mapping fix

Resolved (Day 17):
- KI-060: spy_5day_return None → 0.0 silent masking in all 4 gate tracks (HIGH)
- KI-061: iv_store.py IVR formula verified correct — percentile-based (HIGH)

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

---

## Next Session Priorities (Day 21)

### P0 — Frontend Smoke Test + Single-Stock Bear (KI-059) — MARKET OPEN REQUIRED
1. Open UI → Sectors tab → verify L1 loads → click XLK → L2 IV/IVR shows → Deep Dive → L3 bear_call_spread renders
2. Find bearish individual stock → run buy_put + sell_call → verify gate track B fires, ITM put surfaces, P&L math works

### P1 — QQQ Chain Width (KI-067)
QQQ underlying $563.79 but chain maxes at $562. Investigate struct_cache drift logic — why isn't sell_call fetch reaching +8% OTM (~$609)?

### P1 — IVR Mismatch (KI-064)
L2 shows IVR 97%, L3 shows IVR 21%. Trace both code paths with live data. Align on one truth.

### P2 — API_CONTRACTS.md full sync (KI-044)

### P3 — analyze_service.py extraction (KI-001/023)
app.py ~660 lines. Rule 4 target: ≤150 lines.

### Deferred
- Phase 7c: Weakening → sell_call for cyclical sectors
- bull_put_spread for sell_put (strategy_ranker.py)
- ETF-specific gate overrides (ETF_MIN_PREMIUM, ETF_SPREAD_BLOCK constants — defined but unused)
- Phase C/E/F audit items
- Audit framework improvements: regression gate, Cat 9 smoke test, delta tracking
- Phase 8: Options Explainer "Learn" tab (~300 lines React, frontend-only)

### Reference
- `docs/versioned/KNOWN_ISSUES_DAY20.md` — current issue list
- `docs/status/PROJECT_STATUS_DAY20_SHORT.md` — Day 20 summary
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (8 categories, weekly trigger)
- `docs/Research/Sector_Bear_Market_Day19.md` — Phase 7b research + thresholds
- `docs/Research/Sector_Behavioral_Audit_Day15.md` — 21-claim sector audit
