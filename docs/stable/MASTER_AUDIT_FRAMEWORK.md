# OptionsIQ — Master Audit Framework
> **Last Updated:** Day 45 (May 6, 2026)
> **Version:** v1.4
> **When to run:** Weekly (Monday before market open) OR triggered by: "run audit", "audit now", major feature completion
> **Time estimate:** 30-45 mins for Categories 1-9. Category 10 (effectiveness) runs monthly or when setups are dry.

---

## What This Framework Is

A single, consolidated audit process that replaces all ad-hoc audits.
Previously: System Coherence Audit (Day 11, 47 findings), Behavioral Audit (Day 11, 17 claims),
Sector Behavioral Audit (Day 15, 21 claims) — all separate, inconsistent, incomplete.

This framework consolidates all three into a repeatable, principle-grounded process.
Every finding gets severity: **CRITICAL / HIGH / MEDIUM / LOW**
Every finding gets verdict: **VERIFIED / PLAUSIBLE / MISLEADING / BROKEN / FALSE**

---

## Principles This Audit Is Grounded In

### From Golden Rules (hard constraints):
| # | Principle | What the audit checks |
|---|-----------|----------------------|
| R1 | Live data is always the default | Tradier REST is primary live source; no silent mock fallback; IBKR only for EOD IV batch |
| R2 | One IBWorker, one IB() instance | No ib_insync calls from Flask thread, ever |
| R3 | No magic numbers | All thresholds in constants.py, none inline |
| R4 | app.py is routes only (≤150 lines) | Line count, no business logic in routes |
| R5 | gate_engine math is frozen | No math changes, only constant imports |
| R7 | ACCOUNT_SIZE must be explicit | Startup raises if missing, no default in code |
| R8 | Quality banners mandatory | Every data tier below live has a visible banner |
| R11 | Return null, not a plausible fake | No hardcoded fallback values for missing data |
| R12 | Verify data contracts before coding | Producer defines API, consumer adapts |
| R13 | All 4 directions tested before "frozen" | buy_call + sell_call + buy_put + sell_put all exercised |
| R14 | Swing field defaults forbidden | Missing fields → null + SKIP gate, never fabricated |
| R15 | Code is source of truth, docs are debt | Code vs docs contradictions = doc is wrong |
| R16-gate | Gate track must be explicit per direction | No direction-agnostic routing |
| R16-restart | Restart backend after ANY Python change | Flask debug=False — no auto-reload; kill+restart+health-check required |
| R18 | Liquidity gates must be direction-aware | ATM nearness filter can't apply to ITM buyer strikes |
| R21 | Think like a quant trader, not a developer | Would this cost money if wrong? |

### From LLM Research (external validation):
- **Historical IV is uniquely IBKR** — no other affordable provider has it. IVR requires IBKR EOD batch (not live chain).
- **IVR = percentile** (what % of past year was lower than today), not count-rank
- **High IVR → sell premium, not buy** — IVR 100% on buy_call is a critical block, not a warning
- **IVR seller threshold = 35%** (tastylive empirical, Day 29) — not 50%. Higher threshold sacrifices 60-70% of trade frequency.
- **Multi-LLM consensus before implementing financial logic** — one model can hallucinate options theory
- **Sector quadrant interpretation requires research** — Weakening ≠ ANALYZE (it means WAIT)
- **Lagging ≠ bearish opportunity without further conditions** — mean-reversion timing matters
- **ETF options have different liquidity profiles** — can't apply single-stock thresholds to ETFs
- **Tradier REST = real-time data with brokerage account** — free, OI + volume + greeks included, 200 req/min

### From Coding Experience (learned the hard way):
- **Zero is not null** — `0` scores as real data, corrupts gate logic silently
- **Spread order precedence** — `{ ...obj, field }` overwrites; `{ field, ...obj }` gets overwritten
- **IB.RequestTimeout=0 means unlimited** — always set before reqTickers
- **Queue poisoning** — timed-out requests stay in queue; expires_at prevents stale execution
- **reqTickers() does NOT fire tickOptionComputation** — must use reqMktData(snapshot=False)
- **Docs always diverge from code** — they were written before code, never synced back
- **Direction-specific logic needs direction-specific tests** — 1 passing direction ≠ 4 correct
- **Silent fallbacks are worse than crashes** — phantom data that looks correct corrupts decisions
- **`_f(x) or None` is dangerous for valid 0.0 values** — `0.0 or None` evaluates to `None` in Python. Deep-OTM options legitimately have delta=0.0. Use `float(g[k]) if g.get(k) is not None else None` instead (KI-090 lesson).
- **Data source labels must reflect actual source** — if Tradier fills the BOD cache, call it "bod_cache" not "ibkr_cache". Lying labels corrupt the DataProvenance UI and iv_provider selection downstream (KI-092/093 lesson).
- **SQLite CURRENT_TIMESTAMP is UTC** — when parsing in JavaScript, always append 'Z' before `new Date(...)`. Without 'Z', Chrome treats the string as local time → 4-hour offset in EDT. Use `.replace(' ', 'T') + 'Z'` consistently.

---

## The 8 Audit Categories

---

### Category 1: Claim Verification Audit
**Principle:** Rule 15 (code is truth), Rule 20 (behavioral audit first), Rule 21 (quant filter)
**Format:** State the claim → read the code → assign verdict

#### Verdict Labels:
- `[VERIFIED]` — code does exactly what we claim
- `[PLAUSIBLE]` — logic looks right but not directly tested
- `[MISLEADING]` — claim is partially true but omits an important caveat
- `[BROKEN]` — claim is true in theory but code path is dead or wrong
- `[FALSE]` — code does the opposite of what we claim

#### Claims Checklist (run each session):
```
[ ] "Tradier is the primary live chain source — IB Gateway not needed for analysis"
    → Read: data_service.py get_chain() — is tradier_provider called before ibkr_stale?
    → Confirm: IBKR provider no longer in live path (only EOD batch)

[ ] "BOD batch uses Tradier (not IBKR) — runs successfully without IB Gateway"
    → Read: batch_service.run_bod_batch() — does it call data_svc.get_chain() (Tradier cascade)?
    → Confirm: no ib_worker calls inside run_bod_batch()

[ ] "Direction-aware OTM filter prevents ITM puts on sell_put"
    → Read: tradier_provider.get_options_chain() — does `strike > underlying` skip for sell_put?
    → Read: ibkr_provider.py — same filter present?

[ ] "Skew computation is non-blocking — analyze returns skew:null if Tradier unavailable"
    → Read: analyze_service.analyze_etf() — is compute_skew() in a try/except?
    → Confirm: tradier_provider=None path returns skew:null, not an exception

[ ] "sell_call builds a bear_call_spread (ranks 1+2); rank 3 is a far-OTM naked call with UNLIMITED RISK warning"
    → Read: strategy_ranker._rank_sell_call() — verify ranks 1+2 have two legs, rank 3 has warning field

[ ] "buy_put builds ITM put + bear put spread"
    → Read: strategy_ranker._rank_buy_put() — verify all 3 strategy types

[ ] "SPY regime gates bullish calls correctly"
    → Read: gate_engine._run_track_a() SPY gate. Does spy_5day_return=-3% → FAIL?

[ ] "IVR seller threshold is 35% (not 50%)"
    → Read: constants.py IVR_SELLER_PASS_PCT — should be 35, not 50
    → Read: gate_engine seller gate — does it use IVR_SELLER_PASS_PCT?

[ ] "sell_put warns about naked risk"
    → Read: strategy_ranker._rank_track_b() — warning field on all 3 strategies

[ ] "ACCOUNT_SIZE raises at startup if missing"
    → Read: app.py startup block. Is there an explicit raise or just a default?

[ ] "iv_provider maps tradier/alpaca to yf_provider (not mock)"
    → Read: analyze_service.analyze_etf() iv_provider selection block
    → Confirm: data_source="tradier" → yf_provider, not mock_provider

[ ] "Quality banner shows when data is below live"
    → Read: frontend QualityBanner.jsx — does it cover: bod_cache, tradier, ibkr_stale, alpaca, yfinance, mock?
```

---

### Category 2: Golden Rule Compliance
**Principle:** All 21 rules — check each has not been violated since last audit

```
[ ] R1: Tradier in DataService live chain path (before ibkr_stale). IBKR NOT in live path.
    → grep data_service.py for tradier_provider call in get_chain()
[ ] R2: grep app.py for direct ib. calls → should be zero outside ib_worker.py
[ ] R3: grep gate_engine.py + strategy_ranker.py + tradier_provider.py for raw numbers
    → skew thresholds: SKEW_TARGET_DELTA, SKEW_DTE_MIN, SKEW_DTE_MAX must be in constants.py ✓
[ ] R4: wc -l backend/app.py → should be ≤150 (currently ~475 — known violation, tracked KI-086 partial)
[ ] R5: gate_engine.py math functions untouched since Day 12
[ ] R6: STA offline path — analyze_etf() works with STA down? (underlying_hint fallback)
[ ] R7: grep app.py + analyze_service for ACCOUNT_SIZE default → must be None/raise
[ ] R8: every data tier in QualityBanner.jsx — bod_cache/tradier/ibkr_stale/alpaca/yfinance/mock
[ ] R11: grep all providers for hardcoded numeric fallbacks (e.g., iv=25, hv=15)
    → Special check: _f(x) or None pattern → dangerous for delta=0.0 (KI-090 lesson)
[ ] R13: all 4 directions live tested via Tradier? (Day 40 BOD smoke test: sell_put ✓ via Tradier)
[ ] R14: _merge_swing → grep for default= with a number
[ ] R16-gate: gate_engine.run() routes by direction string — verify 4 branches exist
[ ] R16-restart: After this audit session, any Python changes must trigger kill+restart+health-check
[ ] R18: liquidity gate strike nearness uses direction-aware threshold
[ ] R21: last analysis result — does it pass quant filter? (is IVR actually flowing? is skew returning?)
```

---

### Category 3: Quant Correctness Audit
**Principle:** Rule 21 (think like a quant trader) — would wrong code cost money?

```
[ ] IVR calculation: iv_store.get_ivr() → percentile formula correct?
    Formula: count(hist_iv ≤ current_iv) / len(hist_iv) * 100
    NOT: (current_iv - min) / (max - min) * 100  ← that's IV percentile by range, not rank

[ ] IVR threshold interpretation (updated Day 29):
    buy_call gate → IVR < 30% = PASS (cheap IV, good time to buy)
    sell_put gate → IVR > 35% = PASS (tastylive empirical; was 50% pre-Day 29 — verify constants.py)
    Are these thresholds in constants.py (IVR_BUYER_PASS_PCT, IVR_SELLER_PASS_PCT) and applied correctly?

[ ] Direction-DTE mapping:
    buy_call / buy_put → 45-90 DTE sweet spot enforced?
    sell_call / sell_put → 21-45 DTE sweet spot enforced?

[ ] Strike direction mapping:
    buy_call → strikes 8-20% BELOW underlying (ITM calls, delta ~0.68)
    buy_put  → strikes 8-20% ABOVE underlying (ITM puts, delta ~-0.68)
    sell_call → ATM ±6% (slight OTM preferred)
    sell_put  → ATM ±6% (slight OTM preferred, below support)

[ ] Theta burn calculation:
    burn = abs(theta * hold_days) / premium * 100
    Is hold_days from user input (planned_hold_days) not a hardcoded default?

[ ] HV/IV ratio interpretation:
    ratio = IV / HV20
    ratio < 1.0 = options cheap vs realized vol → PASS for buyers
    ratio > 1.3 = options overpriced → FAIL for buyers
    Direction: this gate is different for sellers (want high IV, not low)

[ ] Bear call spread math:
    premium = short_call_premium - long_call_premium (net credit)
    max_loss = (long_strike - short_strike) * 100 - net_credit
    Is this what pnl_calculator computes?

[ ] SPY regime direction-awareness:
    buy_call: SPY 5d return < -3% → FAIL. < -1% → WARN
    sell_put: SPY 5d return < -3% → FAIL (neutral/bull bias broken)
    buy_put: SPY 5d return < -3% → PASS (bearish confirmed)
    sell_call: SPY down → PASS (neutral/bear bias confirmed)
    Are all 4 directions handled with different thresholds?

[ ] IVR → direction adjustment:
    IVR > 50% + buy_call → should suggest bull_call_spread instead
    Is this adjustment in sector_scan_service._analyze_etf()?
    Does it actually change the suggested_direction field?

[ ] Skew computation (added Day 42):
    skew = put_iv_30d - call_iv_30d from nearest 20-50 DTE Tradier chain
    Positive skew = puts richer = downside tail risk priced in (normal market condition)
    Skew is informational only — not yet wired into gate logic
    → Read: analyze_etf() return dict — does "skew" key exist?
    → Confirm: compute_skew() is inside try/except (non-blocking)
    → Confirm: SKEW_TARGET_DELTA=0.30, SKEW_DTE_MIN=20, SKEW_DTE_MAX=50 in constants.py
```

---

### Category 4: Data Integrity Audit
**Principle:** R11 (null not fake), R8 (quality banners), R15 (code is truth)

```
[ ] Provider cascade order (updated Day 39):
    BOD Cache (bod_cache) → Tradier (tradier) → Stale Cache (ibkr_stale) → Alpaca (alpaca) → yfinance (yfinance) → Mock (mock)
    Read data_service.py get_chain() — does fallback order match exactly?
    IBKR LIVE IS REMOVED from this cascade. "ibkr_cache" label must NOT appear anywhere.

[ ] Data source labels — no "ibkr_cache" anywhere (renamed to "bod_cache" Day 40):
    grep data_service.py + data_health_service.py + analyze_service.py for "ibkr_cache" → should be zero

[ ] BOD cache TTL: chain_cache.db SQLite cache. Is TTL constant in constants.py?
    Read data_service._cache_get() — how long is a cached chain considered fresh?

[ ] iv_provider selection covers all data_source values (updated Day 40):
    "ibkr_live", "ibkr_closed", "bod_cache", "ibkr_stale" → ib_worker.provider
    "yfinance", "tradier", "alpaca" → yf_provider
    anything else → mock_provider
    Read analyze_service.py iv_provider block — verify all 5+ source labels are handled

[ ] Zero vs null discipline:
    grep tradier_provider.py for "or None" patterns → dangerous for 0.0 delta (KI-090)
    OK: `float(g[k]) if g.get(k) is not None else None` ← correct form
    NOT OK: `_f(g.get("delta")) or None` ← 0.0 becomes None

[ ] Historical IV data: only IBKR EOD batch provides it.
    Tradier: provides chain greeks but NOT historical IV (no get_historical_iv method)
    yf_provider: provides get_historical_iv() via yfinance (used as IV fallback when Tradier is data_source)
    grep tradier_provider.py for get_historical_iv → should NOT exist

[ ] SPY regime source: sector_scan_service._spy_regime() → uses STA, not yfinance (Day 16 fix)
    Read the function. Is STA_BASE_URL used? No yfinance import?

[ ] All provider tiers in QualityBanner (updated for Tradier primary):
    bod_cache → "Using BOD cache — pre-warmed this morning"
    tradier   → no banner (live real-time = best available)
    ibkr_stale → "Stale cache..."
    alpaca → "Alpaca fallback — 15-min delay, no OI/volume"
    yfinance → "Emergency fallback — estimated greeks only"
    mock → "MOCK DATA — do not trade"
```

---

### Category 5: Threading Safety Audit
**Principle:** R2 (IBWorker owns IB()), concurrency architecture docs

```
[ ] All IBKR calls in ibkr_provider.py go through IBWorker.submit()
    grep app.py + sector_scan_service.py + any _service.py for ib. calls
    Should find zero direct ib. calls outside of ib_worker.py + ibkr_provider.py

[ ] IBWorker expires_at implemented:
    grep ib_worker.py for expires_at — should be in _Request dataclass
    Worker checks expiry before executing: if time.monotonic() > req.expires_at → discard

[ ] IBWorker heartbeat:
    grep ib_worker.py for reqCurrentTime — heartbeat every 30s idle?
    is_connected() checks both ib.isConnected() AND last_heartbeat < 75s

[ ] reqMktData try-finally pattern:
    grep ibkr_provider.py for cancelMktData — should be in finally block
    Ensures no zombie subscriptions if exception during greek read

[ ] Single DataService circuit breaker:
    grep app.py for any CB-related code → should be zero
    DataService is the ONLY place with circuit breaker logic (Rule 12)
```

---

### Category 6: API Contract Sync
**Principle:** R15 (code is truth), R9 (session close protocol)

```
[ ] Count @app.route/@app.get/@app.post/@app.patch/@app.delete in app.py:
    grep -c "@app\." backend/app.py

[ ] Count endpoints in API_CONTRACTS.md:
    Count ## POST / ## GET / ## PATCH / ## DELETE headers in the doc

[ ] For each key endpoint, verify response structure:
    /api/options/analyze → verdict, gates, strategies, pnl_table, behavioral_checks, skew (Day 42)
    /api/health → status, ibkr_connected, mock_mode, tradier_ok, tradier_error (Day 41)
    /api/sectors/scan → etfs[], spy_regime, scan_time
    /api/admin/batch-status → recent_runs[], next_bod, next_eod (Day 35)
    /api/admin/warm-cache (POST) → status, tickers_ok, tickers_failed, duration_sec (BOD)
    /api/admin/seed-iv/all (POST) → status, tickers_ok, tickers_failed (EOD)
    /api/best-setups → as_of, candidates_scanned, setups[], all_results[] (Day 29)

[ ] Verify field names match between code and docs:
    "skew" field in analyze response — is it in API_CONTRACTS.md?
    "tradier_ok", "tradier_error" in health response — is it in API_CONTRACTS.md? ✓ (added Day 41)
    "bod_cache" as data_source — is API_CONTRACTS.md updated from "ibkr_cache"?

[ ] Verify STA field mappings still match STA's actual response:
    Key ones that have burned us: days_until vs days_away, suggestedEntry vs levels.entry
```

---

### Category 7: Direction Coverage Audit
**Principle:** R13 (all 4 directions tested), R16 (explicit gate routing)

```
[ ] gate_engine.py has 4 distinct branches:
    _run_track_a (buy_call), _run_sell_call, _run_buy_put, _run_track_b (sell_put)
    Each uses direction-specific thresholds from constants.py

[ ] strategy_ranker.py has 4 distinct builders:
    _rank_track_a, _rank_sell_call, _rank_buy_put, _rank_track_b
    Each returns 3 strategies with correct strategy_type

[ ] pnl_calculator.py handles all strategy types:
    itm_call, atm_call, bear_call_spread, sell_call (direction C)
    itm_put, atm_put, bear_put_spread
    naked_put

[ ] Live test coverage (update this table each audit):
    | Direction  | Live Tested? | Last Test | Provider | Bugs Found |
    |------------|-------------|-----------|----------|------------|
    | buy_call   | YES ✅      | Day 21 (XLU ETF) | IBKR | none active |
    | sell_put   | YES ✅      | Day 40 BOD smoke (5 ETFs) | Tradier | KI-091 fixed (ITM put filter) |
    | sell_call  | YES ✅      | Day 21 (XLU ETF) | IBKR | none active |
    | buy_put    | YES ✅      | Day 21 (XLU ETF) | IBKR | none active |
    Note: buy_call, sell_call, buy_put not yet live-tested with Tradier as primary source.

[ ] IVR direction adjustment in sector_scan_service:
    IVR > 50% + buy_call → bull_call_spread (verified Day 16 ✅)
    IVR > 50% + buy_put → bear_put_spread (not verified)
    IVR < 30% + sell_put → flag (not verified)
```

---

### Category 8: Error Handling Audit
**Principle:** R11 (null not fake), Session Rules (no bare excepts)

```
[ ] No bare except: in Python files:
    grep -n "except:" backend/*.py
    Every except must name the exception and log it

[ ] No silent None swallowing:
    grep -n "except.*pass" backend/*.py → each one is a hidden failure

[ ] STA offline graceful:
    Kill localhost:5001, run analyze → should return Manual mode, not crash

[ ] IBKR offline graceful:
    Disconnect IB Gateway, run analyze → should cascade to Alpaca, not 500 error

[ ] DB connection failure:
    If chain_cache.db locked/missing → DataService should log and continue, not crash

[ ] Sector scan with 0 ETFs returning:
    If STA /api/sectors/rotation returns empty → scan returns empty list, not crash

[ ] SPY regime STA offline:
    If STA is down → spy_regime returns {spy_above_200sma: null, spy_5day_return: null}
    Does the frontend render this gracefully (no exception, no null crash)?
```

---

## Audit Scoring

After running all 8 categories, tally findings:

| Severity | Definition | Response |
|----------|-----------|----------|
| CRITICAL | Would cause wrong trade or system crash | Fix before next market open |
| HIGH | Silently wrong data or blocked feature | Fix within 2 sessions |
| MEDIUM | Feature incomplete or misleading UI | Schedule next session |
| LOW | Docs stale, minor edge case | Track in KNOWN_ISSUES |

**Audit health score:**
- 0 CRITICAL + 0 HIGH = ✅ Healthy
- 0 CRITICAL + 1-3 HIGH = ⚠️ Monitor
- Any CRITICAL = 🔴 Do not paper trade until resolved

---

## How to Run

**Full audit (Categories 1-9):**
> "Run the full audit"
Claude reads all 9 categories against the current codebase, produces findings table.

**Targeted audit:**
> "Run Category 3 — quant correctness"
> "Audit direction coverage"
> "Check threading safety"
> "Run Category 10 — trading effectiveness"

**Weekly trigger (Monday before market open):**
> "Weekly audit"
Claude runs Category 1 (claims), Category 3 (quant), Category 7 (direction coverage), Category 6 (API sync) — the 4 highest-value categories for trading safety.

**Monthly trigger OR when "I can't find any setups":**
> "Run trading effectiveness audit" or "Run Category 10"
Claude runs Check 10.1 (gate pass rate) and 10.2 (always one direction) live. Produces gate blocker diagnosis.
Checks 10.3 (DTE calibration), 10.4 (unbiased evaluation), 10.5 (expected value) are review/research — Claude summarizes current state.

---

## Audit Log

| Audit | Date | Category | Findings | CRITICALs | HIGHs | Notes |
|-------|------|----------|----------|-----------|-------|-------|
| Day 11 System Coherence | Mar 13, 2026 | 1,2,4,5,8 | 47 | 6 | 8 | First full audit |
| Day 11 Behavioral | Mar 13, 2026 | 1 | 17 claims | 3 FALSE | 5 MISLEADING | Behavioral claims only |
| Day 15 Sector Behavioral | Mar 20, 2026 | 1,3,7 | 21 claims | 0 | 0 after fixes | Sector module specific |
| Day 16 Quant Spot Check | Mar 20, 2026 | 3,7 | 2 findings | 0 | 1 (KI-059) | IVR adj confirmed, bear untested |
| Day 17 Full Audit | Mar 22, 2026 | 1-8 | 10 checks | 0 | 2 found+fixed | KI-060 SPY None masking fixed, KI-061 IVR formula verified. Post-fix: 0C/2H remaining (KI-059, KI-044) |
| Day 25 Category 9 Added | Apr 17, 2026 | 9 | New category | 0 | 0 | Frontend UX Accuracy audit added. Phase 8 UX overhaul introduced hardcoded GATE_KB + isBearish() zone logic — needs sync audit trigger. |
| Day 27 Full Audit | Apr 21, 2026 | 1-9 | 5 findings | 0 | 1 found+fixed | bull_put_spread missing in pnl_calculator (P&L table all zeros for ETF sell_put) — FIXED. API_CONTRACTS updated (seed fields, OI source, ETF enforcement note). Direction table corrected (all 4 directions live tested Day 21+27). Post-fix: 0C/0H. |
| Day 42 Full Audit | May 6, 2026 | 1-9 | 0 CRITICAL · 2 HIGH · 3 MEDIUM | 2 HIGH + 1 MEDIUM fixed same session | 2 MEDIUM fixed end of session | First audit with Tradier as primary. Framework updated to v1.3 before run. All findings resolved. |
| Day 45 Framework Update | May 6, 2026 | 10 (new) | Category 10 added — Trading Effectiveness | 0 | 0 | Gate pass rate, "always one direction" claim, DTE calibration, adversarial LLM review, expected value sanity. v1.4. Not yet run against live data. |

---

---

### Category 9: Frontend UX Accuracy Audit
**Added:** Day 25 (April 17, 2026)
**Principle:** R15 (code is truth), R21 (quant filter) — wrong plain English descriptions mislead a beginner into making a wrong trade.

**Why this matters:** The Day 25 UX overhaul added hardcoded knowledge to the frontend — gate Q&A text, profit/loss zone directions, strategy type templates. These can silently drift from backend logic when the backend changes, showing "Profit Zone" where the math says loss.

**When to run:** Whenever gate_engine.py or strategy_ranker.py changes, OR monthly as part of weekly audit rotation.

```
[ ] TradeExplainer isBearish() classification:
    Open TradeExplainer.jsx — function isBearish(strategy_type)
    Should return true ONLY for: bear_call_spread, sell_call, buy_put, itm_put, atm_put
    For these, profit zone is LEFT of breakeven (price stays below)
    For all others (bull_put_spread, buy_call, sell_put, itm_call, atm_call): profit zone RIGHT
    Verify against gate_engine.py gate tracks — bearish gates = tracks where PRICE FALLING = profit

[ ] TradeExplainer getTradeHeadline() templates:
    For each strategy_type, verify the headline is correct:
    bear_call_spread → "profit if stays below ${breakeven}" ✓ (short call above)
    bull_put_spread  → "profit if stays above ${breakeven}" ✓ (short put below)
    itm_call/atm_call → "profit if rises above ${breakeven}" ✓
    itm_put/atm_put  → "profit if drops below ${breakeven}" ✓
    sell_call        → "profit if stays below ${strike}" — note: unlimited risk without spread
    sell_put         → "profit if stays above ${strike}"

[ ] GateExplainer GATE_KB accuracy:
    Open GateExplainer.jsx — GATE_KB object
    For each gate ID, verify the question and pass/fail answers match gate_engine.py logic:
    ivr_seller → PASS answer should say "IV is expensive" (IVR > 50% for sellers)
    ivr        → PASS answer should say "IV is cheap" (IVR < 30% for buyers)
    market_regime_seller → different from market_regime (seller bias = up OR flat = pass)
    strike_otm → PASS = strike is X% above/below current price (check SELL_CALL_OTM_PASS_PCT)
    risk_defined → PASS only when spread is present (bear_call_spread, bull_put_spread) — NOT sell_call naked

[ ] GateExplainer category assignment:
    All gate IDs are assigned to one of: market, pricing, risk
    No gate shows in wrong category (e.g., market_regime_seller must be in 'market', not 'risk')
    Gates without GATE_KB entry → fallback renders gate.id + raw reason (no crash)

[ ] DirectionGuide descriptions match actual system behavior:
    buy_call card: "I think price will RISE significantly" — matches Track A, ITM calls ✓
    sell_put card: "I think price will STAY or rise slowly" — matches Track B, sell premium ✓
    sell_call card: "I think price will STAY or drop slowly" — matches Track A, sell premium ✓
    buy_put card: "I think price will DROP significantly" — matches Track B, ITM puts ✓
    Risk labels: sell_call and sell_put show "Risk: Spread width (capped)" — correct only when spread built
    (sell_put can still be naked per strategy_ranker — DirectionGuide says spread, may be misleading for sell_put)

[ ] LearnTab educational content accuracy:
    LessonStrikes: ITM/ATM/OTM zones flip correctly for puts vs calls (call slider = OTM right, put = OTM left)
    LessonDirections: 4 P&L SVG lines show correct shapes (call = up-sloping right, put = up-sloping left)
    LessonSpreads: bear call spread example numbers match typical XLF scenario (credit < spread width)
    LessonGates: gate descriptions consistent with GATE_KB in GateExplainer (no contradictions)

[ ] Strategy type coverage:
    GateExplainer and TradeExplainer handle all strategy_types returned by strategy_ranker:
    bear_call_spread ✓, bull_put_spread ✓, itm_call ✓, atm_call ✓, itm_put ✓, atm_put ✓
    sell_call ✓, sell_put ✓, naked_put (if returned — does TradeExplainer handle this?)
    If strategy_type is unknown → TradeExplainer renders gracefully (fallback template, not crash)
```

**Severity mapping:**
- `isBearish()` wrong for any type → **CRITICAL** (green shown where loss zone is)
- `GATE_KB` text contradicts gate_engine logic → **HIGH** (wrong advice for beginner)
- Category misassignment in GATE_KB → **MEDIUM** (confusing but not dangerous)
- LearnTab text inconsistency → **LOW** (educational, not trading decision)

---

---

### Category 10: Trading Effectiveness Audit
**Added:** Day 45 (May 6, 2026)
**Principle:** R21 (think like a quant trader) — correctness is necessary but not sufficient. A system that never finds trades, or whose gate pass rate is near zero, is useless regardless of how correct the code is.

**Why this matters:** Categories 1-9 verify that the code does what we claim. Category 10 verifies that what we claim is actually useful — that the system surfaces actionable setups at a reasonable rate, that the DTE/threshold choices are empirically grounded, and that we have a method for knowing when the system is wrong.

**When to run:** Monthly, OR whenever the user says "I can't find any setups" or "everything is blocked."

---

#### Check 10.1 — Gate Pass Rate (measurable, run today)
```
[ ] Trigger Best Setups scan (or run 15 ETFs × 4 directions manually).
    Count: how many ETF/direction combinations return non-BLOCKED verdict?

    Target calibration:
      < 2 setups surfaced   → gates are OVER-TUNED. Find the single biggest blocker.
      3-6 setups surfaced   → HEALTHY. Market has some opportunity.
      > 10 setups surfaced  → gates are UNDER-TUNED. Standards are too loose.

    If blocked: identify the gate blocking the most ETFs.
    Is it: events (CPI/FOMC window)? liquidity (bid-ask too wide)? IVR? DTE?
    One gate causing >50% of blocks = recalibration candidate.
```

#### Check 10.2 — "Always One Direction" Claim (verifiable)
```
[ ] Claim: given a clear VIX regime (VIX 12-20 = normal, VIX 20-30 = elevated, VIX>30 = stress),
    at least one of the 15 ETFs should surface a CAUTION or GO verdict in at least one direction.

    Verify today: is the claim true?
      YES → system is functioning. Blocked setups are legitimately blocked.
      NO (all 15 ETFs blocked in all 4 directions) → gate miscalibration.
        Diagnosis: which gate is unanimously failing?
        Action: check if that gate's threshold is empirically justified or was set conservatively
                and never recalibrated.
```

#### Check 10.3 — DTE Calibration (research-grounded, run quarterly)
```
[ ] Current config: buyers = 45-90 DTE, sellers = 21-45 DTE.
    Tastylive framework: open at 45 DTE, manage/close at 21 DTE (theta inflection point).

    Questions to answer with Perplexity/tastylive data before changing:
      Q1: Does the 45 DTE → 21 DTE exit framework hold for ETF sector options specifically?
          (Lower OI than SPY/QQQ — does the theta curve behave the same?)
      Q2: What is the empirical win-rate difference between opening at 45 DTE vs 21 DTE?
          (21 DTE = more theta acceleration but less buffer if trade goes against you)
      Q3: Is the events gate (CPI/FOMC within DTE window) causing most blocks for sellers?
          If yes: lowering DTE to 21 doesn't fix it — CPI is still inside 21 days.

    Only change DTE thresholds after answering Q1-Q3 with sourced data.
    Do NOT change based on intuition — wrong DTE calibration affects every trade.
```

#### Check 10.4 — Unbiased Evaluation (three methods)
```
[ ] Method A — Paper Trade Prediction Test (30-trade sample):
    For every setup with GO verdict: record the predicted outcome
    (e.g., "profit if XLF stays above $50.63 by May 29").
    After 30 closed trades:
      Win rate < 50% → gates are passing wrong setups. Tighten thresholds.
      Win rate > 70% → gates may be too conservative. Are we blocking good setups?
      Win rate 55-65% → reasonable for defined-risk premium selling.

[ ] Method B — Adversarial LLM Review (per trade, already in Daily_Trade_Prompts.md):
    Paste best setup into Perplexity or ChatGPT with this prompt:
    "I am considering this options trade: [full setup details].
     Act as an adversarial options risk manager. List every reason NOT to take this trade,
     ranked by severity. Do not soften your objections. Be specific about the numbers."
    If the LLM finds a gate that our system missed → add that gate.
    If the LLM objects to something our gates already caught → our gates are working.

[ ] Method C — Weekly Gate Pass Rate Log (track over time):
    Each week, record: {date, etfs_scanned, setups_surfaced, top_blocker_gate}.
    After 4 weeks:
      Consistently 0-1 setups/week → structural gate problem or permanently unfavorable market.
      Consistently 4-8 setups/week → system is healthy.
      Setups cluster around same 2-3 ETFs always → sector coverage bias (check RS quadrant data).
```

#### Check 10.5 — Expected Value Sanity (quant filter)
```
[ ] For the top recommended setup, verify:
    credit_to_width_ratio ≥ 33% (MIN_CREDIT_WIDTH_RATIO enforced by strategy_ranker) ✓
    breakeven is outside the expected 1-sigma move for the DTE:
      expected_move ≈ underlying_price × IV × sqrt(DTE/365)
      short strike should be beyond expected_move for sellers
      (e.g., sell_put at $50.63 breakeven on XLF $51.59 = only $0.96 buffer on $51 underlying.
       With IV=18%, 23 DTE: expected move ≈ 51.59 × 0.18 × sqrt(23/365) ≈ $2.46.
       Short strike is INSIDE the 1-sigma move → high assignment risk despite passing other gates.)
    If short strike is inside expected move → stress_check gate should WARN. Verify it does.
```

**Severity mapping:**
- Gate pass rate = 0 for >2 consecutive weeks → **HIGH** (system not surfacing trades)
- Short strike inside expected move with no warning → **HIGH** (quant blind spot)
- DTE thresholds not sourced from empirical research → **MEDIUM** (assumption not validated)
- Paper trade win rate < 45% over 30 trades → **CRITICAL** (gates are selecting losers)

---

## What's Not Yet Audited (Future Categories)

- **Performance Audit** — deepcopy cost in scan cache, struct_cache LRU eviction
- **Paper Trade Audit** — mark-to-market math, entry price accuracy
- **Sector Quadrant Logic Audit** — needs Phase 7 research first (bear plays)
- **Test Coverage Audit** — pytest coverage per module (currently minimal)

---

*Location: `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — stable reference, updated when new principles are learned*
*Trigger with: "run audit", "weekly audit", or specific category name*
