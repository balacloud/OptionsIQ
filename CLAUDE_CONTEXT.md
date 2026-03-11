# OptionsIQ — Claude Context
> **Last Updated:** Day 9 (March 11, 2026)
> **Current Version:** v0.8 (live greeks confirmed, sell_call spread fixed, pnl_calculator fixed, Alpaca planned)
> **Project Phase:** Phase 4 complete — Alpaca integration + analyze_service.py next

---

## Session Protocol

### Startup Checklist (read IN THIS ORDER before any code or plan)
1. `CLAUDE_CONTEXT.md` ← this file — current state, known issues, next priorities
2. `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. `docs/stable/ROADMAP.md` — phase status, done vs pending
4. `docs/status/PROJECT_STATUS_DAY9_SHORT.md` — latest day status (update filename each day)
5. `docs/versioned/KNOWN_ISSUES_DAY9.md` — open bugs and severity (update filename each day)
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
| Backend | Phase 4 complete | Live greeks confirmed, sell_call spread working |
| Frontend | Done + Day 4+5+6 fixes | Market closed banner + IB Closed label |
| IBKR connection | WORKING | Live confirmed: AMD/NVDA, greeks_pct 100%, account U11574928 |
| Gate logic | Correct (frozen) | gate_engine.py verified correct |
| P&L math | Fixed Day 9 | pnl_calculator.py — None guard + 4 new strategy type handlers |
| Strategy ranking | Updated Day 9 | sell_call: bear_call_spread building (225/230 AMD). sell_put: naked only |
| IV store | Correct (frozen) | iv_store.py verified correct |
| constants.py | DONE (Day 9) | SMART_MAX_STRIKES 6→12, SMART_MAX_CONTRACTS 12→26, sell windows fixed |
| bs_calculator.py | DONE | Black-Scholes greeks fallback |
| ib_worker.py | DONE (Day 5) | Queue poisoning + heartbeat + RequestTimeout |
| yfinance_provider.py | DONE | Middle tier, BS greeks fill (NO greeks — computed via BS only) |
| data_service.py | DONE | Provider cascade + SQLite cache + single circuit breaker |
| ibkr_provider.py | DONE (Day 9) | reqMktData sort fix + OI field fix (KI-035 pending) |
| alpaca_provider.py | NOT CREATED | Day 10 P1 — REST fallback with real greeks |
| analyze_service.py | NOT CREATED | Day 10 P2 — extract from app.py |
| app.py | Partial refactor | 558 lines. Still needs analyze_service.py split. |

### Backend Files (current state)
```
backend/
  app.py              558 lines — routes + helpers. Needs analyze_service.py split (P2).
  constants.py        DONE (Day 9) — SMART_MAX_STRIKES 12, SMART_MAX_CONTRACTS 26,
                                     SELL_CALL_STRIKE_HIGH_PCT 0.15, SELL_PUT_STRIKE_LOW_PCT 0.15
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single thread, submit() queue, expires_at, heartbeat (30s idle)
  yfinance_provider.py DONE — emergency fallback (no greeks — computed via BS)
  data_service.py     DONE — provider cascade + SQLite cache + AUTHORITATIVE CB + ibkr_closed tier
  ibkr_provider.py    DONE (Day 9) — direction-aware strike sort (sell_call ascending, sell_put desc)
                                     OI field: optOpenInterest (was callOpenInterest — wrong field)
                                     KI-035: genericTickList="" → needs "101" for OI tick 22
                                     Phase 4e: BS fallback if usopt still no greeks after wait
  mock_provider.py    PARTIAL — still partially hardcoded (low priority)
  gate_engine.py      FROZEN — math correct. Coerce None→0.0 before passing gate_payload.
  strategy_ranker.py  UPDATED (Day 7+9) — explicit builder per direction:
                                        _rank_sell_call → bear_call_spread (delta 0.30/0.15) ✓
                                        _rank_buy_put   → ITM put + bear put spread + ATM put ✓
                                        _rank_track_b (sell_put) → naked sell_put (no spread yet)
  pnl_calculator.py   FIXED (Day 9) — None guard, handlers for itm_put/atm_put/bear_call_spread/sell_call
                                       spread handler direction-aware via right field
  iv_store.py         FROZEN — math correct

  # TO CREATE:
  alpaca_provider.py  Day 10 P1 — REST fallback with real greeks (needs APLACA_SECRET in .env)
  analyze_service.py  Day 10 P2 — extract _merge_swing, _extract_iv_data, _behavioral_checks
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
[2.5] Alpaca indicative/opra (PLANNED)     ← REST fallback WITH greeks — better than yfinance
[3] yfinance (emergency fallback)          ← NO real greeks (BS computed from HV)
[4] Mock (dev/CI testing ONLY)             ← NEVER for paper trades
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

Full list: `docs/versioned/KNOWN_ISSUES_DAY8.md`

Open (HIGH — Day 10 P0):
1. **OI always 0 via reqMktData** — `genericTickList=""` doesn't include tick 22. Need `"101"`. Liquidity gate always fails (KI-035)

Open (MEDIUM):
2. **NVDA buy_put sparse** — only 3 contracts qualify, DTE gate fails. SMART_MAX_STRIKES increase may help (KI-025)
3. **analyze_service.py missing** — app.py still 558 lines, target ≤150 (KI-001/KI-023)
4. **Synthetic swing defaults silent** — no banner when stop/target are fabricated (KI-022/KI-005)

Open (Planned — Day 10):
5. **alpaca_provider.py missing** — REST fallback with real greeks (KI-036). Needs APLACA_SECRET in .env.

Open (Low priority):
6. OHLCV temporal gap validation at write time (KI-034)
7. fomc_days_away manual mode defaults to 30 (KI-008)
8. API URL hardcoded in useOptionsData.js (KI-013)

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

---

## Next Session Priorities (Day 10)

### P0 — Fix KI-035: OI always 0 (FIRST THING)
1. Change `genericTickList=""` → `genericTickList="101"` in ibkr_provider.py reqMktData for options
2. Test AMD sell_call → verify OI > 0 → liquidity gate should pass for liquid strikes
3. This unblocks paper trade E2E testing

### P1 — Create alpaca_provider.py
4. User MUST first add `APLACA_SECRET=<secret>` to backend/.env (get from Alpaca dashboard)
5. Create `backend/alpaca_provider.py`:
   - REST client for `GET /v1beta1/options/snapshots/{symbol}?feed=indicative`
   - Parse OCC symbol for strike/expiry/right
   - Map to same contract dict format as ibkr_provider output
   - Returns: bid, ask, delta, gamma, theta, vega, IV, OI, volume
6. Register in DataService cascade between IBKR cache and yfinance (tier 2.5)
7. Add `ALPACA_FEED=indicative` to .env (switch to `opra` if subscribing)

### P2 — Create analyze_service.py
8. Extract `_merge_swing()`, `_extract_iv_data()`, `_behavioral_checks()` from app.py
9. app.py → routes-only ≤150 lines

### P3 — bull_put_spread for sell_put (after OI fix and Alpaca done)
10. `_rank_track_b` currently builds naked sell_puts — upgrade to bull put spread
    Short put delta ~0.30 (OTM) + long put delta ~0.15 (protection)

### P4 — Paper trade E2E
11. Once OI gate passes, record AMD or CTRA paper trade
12. Verify mark-to-market P&L in `GET /api/options/paper-trades`

### Reference
- `docs/stable/CONCURRENCY_ARCHITECTURE.md` — all 5 problems resolved + market hours
- `docs/versioned/KNOWN_ISSUES_DAY9.md` — current issue list
