# OptionsIQ — Master Audit Framework
> **Last Updated:** Day 69 (Jun 16, 2026)
> **Version:** v1.7
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
- **Historical IV is uniquely IBKR** — no other affordable provider has it. During market hours, IBKR watchlist `52wk IV Rank` is authoritative and real-time. iv_history.db EOD batch is now redundant for daily decisions but kept for paper trade audit trail.
- **IVR = percentile** (what % of past year was lower than today), not count-rank
- **High IVR → sell premium, not buy** — IVR 100% on buy_call is a critical block, not a warning
- **IVR seller threshold = 40%** (raised from 35% Day 68 peer review — Perplexity/Gemini/ChatGPT consensus). Warn band 35–40% added. IVR_SELLER_WARN_MIN=35 is the new floor for the warn tier.
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
- **Pre-filter tools own their checks — don't double-gate** — If `/ibkr-scan` already validated IVR/IV_HV/market_regime, the backend gate for that same condition must be advisory WARN only (Rule 23 lesson, Day 62). Hard-blocking contradicts a pre-filter the user already ran.
- **scan_context_parser overrides are the bridge** — `parse_scan_context()` extracts KEY=VALUE pairs from SCAN CONTEXT block; `apply_scan_context_to_gate_payload()` injects live IVR, IV_HV, P/C ratio directly into the gate payload before gate_engine runs. This is how `/ibkr-scan` data flows into the backend without a direct API call (Day 60 lesson).
- **Trend gate is the ONE hard block that pre-filter cannot own** — `_trend_ema_gate()` is direction-aware: blocks sell_put + buy_call when below 200EMA, blocks buy_put when above 200EMA (warns sell_call). Too subtle for watchlist scan; backend enforces. All other trend/regime checks are advisory only per Rule 23.

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
[ ] "Tradier is the primary live chain source — IB Gateway API is dead"
    → Read: data_service.py get_chain() — is tradier_provider called before ibkr_stale?
    → Confirm: IBKR provider no longer in live path at all (IB Gateway dead as of Day 56)

[ ] "BOD batch is dead — batch_service.py exists but is not called"
    → Read: app.py — is run_bod_batch() called anywhere? Should be zero.
    → Confirm: no scheduled batch calls at startup

[ ] "Direction-aware OTM filter prevents ITM puts on sell_put"
    → Read: tradier_provider.get_options_chain() — does `strike > underlying` skip for sell_put?
    → Also: Tradier chain sorted by |abs(delta)-0.22| for sell_put/sell_call (delta-centered)
    → Confirm: delta-centered sort is present, not ATM-proximity sort

[ ] "Skew computation is non-blocking — analyze returns skew:null if Tradier unavailable"
    → Read: analyze_service.analyze_etf() — is compute_skew() in a try/except?
    → Confirm: tradier_provider=None path returns skew:null, not an exception

[ ] "sell_call returns single-leg sell_call — R1 delta 0.20, R2 delta 0.15, R3 delta 0.25 (no spreads)"
    → Read: strategy_ranker._rank_sell_call() — verify all 3 are single-leg, no bear_call_spread
    → Confirm: strategy_type field is 'sell_call' (not 'bear_call_spread') on all 3

[ ] "buy_put returns single-leg buy_put — R1 delta 0.68 ITM, R2 delta 0.50 ATM, R3 delta 0.30 OTM (no spreads)"
    → Read: strategy_ranker._rank_buy_put() — verify all 3 are single-leg
    → Confirm: strategy_type field is 'buy_put' on all 3

[ ] "buy_call returns single-leg buy_call — R1 delta 0.68 ITM, R2 delta 0.50 ATM, R3 delta 0.30 OTM"
    → Read: strategy_ranker._rank_buy_call() — verify all 3 are single-leg buy_call

[ ] "sell_put returns single-leg sell_put — R1 delta 0.20, R2 delta 0.15, R3 delta 0.28"
    → Read: strategy_ranker._rank_sell_put_etf() — verify R1/R2/R3 delta targets

[ ] "expected_move_1sd in every analyze response"
    → Read: analyze_service.analyze_etf() return dict — does 'expected_move_1sd' key exist?
    → Formula: (iv/100) × sqrt(dte/365) × underlying_price

[ ] "exit_plan in every strategy object"
    → Read: analyze_service._enrich_strategies() or strategy_ranker — is exit_plan dict built?
    → Verify fields: rule, profit_target_pct, profit_target_credit, dte_exit, exit_date
    → TQQQ: 25%/14 DTE. Standard: 50%/21 DTE. Buys: 100% gain / -50% stop.

[ ] "strike_vs_em_label correctly classifies OTM relative to 1σ expected move"
    → Read: analyze_service — is (underlying-strike)/expected_move computed?
    → ≥1.0σ = ✅ Outside 1σ, 0.8-1.0σ = ⚠️ Near 1σ, <0.8σ = ❌ INSIDE expected move

[ ] "FOMC 3-tier gate: BLOCK XLF/XLRE/TQQQ within 14d, WARN QQQ/IWM/GLD within 7d — never block buys"
    → Read: gate_engine — FOMC gate tiers. Do TQQQ + XLF block within 14d for sellers?
    → Confirm: buy_call and buy_put are excluded from the FOMC block (WARN only)

[ ] "trend_ema gate is direction-aware — hard-blocks any direction fighting the 200EMA trend"
    → sell_put: P/EMA200 < 0 → blocking=True (downtrend structural risk for put sellers)
    → buy_call: P/EMA200 < 0 → blocking=True (downtrend structural headwind for call buyers)
    → buy_put: P/EMA200 > 0 → blocking=True (uptrend structural headwind for put buyers)
    → sell_call: P/EMA200 > 0 → blocking=False WARN only
    → Read: gate_engine._trend_ema_gate() — verify all 4 branches and blocking flags
    → Confirm: all 4 ETF tracks call _trend_ema_gate()

[ ] "scan_context_parser.py parses IBKR SCAN CONTEXT block and overrides gate payload"
    → Read: scan_context_parser.parse_scan_context() — extracts IVR, IV_HV, P/C from KEY=VALUE block
    → Read: scan_context_parser.apply_scan_context_to_gate_payload() — merges overrides into payload
    → Read: App.jsx — is there a SCAN CONTEXT textarea? Does it send scan_context in the analyze payload?
    → Read: analyze_service — does it call apply_scan_context_to_gate_payload() before gate_engine?

[ ] "5 advisory-only gates (Rule 23 — Day 62): ivr_buyer, hv_iv_buyer, market_regime, max_loss, VRP (non-GLD)"
    → Read: gate_engine — do these 5 gates return blocking=False even when conditions fail?
    → Confirm: GLD IV/HV < 1.10 is the EXCEPTION — remains a hard block (gate_engine._hv_iv_vrp_gate for GLD)
    → GLD hard block wired since Day 59 (KI-108 resolved)

[ ] "TQQQ delta cap implemented: strategy_ranker uses delta 0.10/0.08/0.06 for sell_put"
    → Read: strategy_ranker._rank_sell_put_etf() for TQQQ — verify delta targets are 0.10/0.08/0.06
    → Confirm: TQQQ_MAX_DELTA = 0.10 in constants.py (KI-107 resolved Day 59)

[ ] "ETF universe is exactly 6 tickers: QQQ, IWM, XLF, GLD, TQQQ, SPY"
    → Read: constants.py ETF_TICKERS — verify exact set. SPY is regime anchor only (no trades).

[ ] "/api/best-setups, /api/sectors/scan, /api/sectors/analyze return 410 Gone"
    → Read: app.py — do these routes exist? Do they return 410, not 404?

[ ] "SPY regime gates use STA (not IB Gateway or yfinance)"
    → Read: sector_scan_service._spy_regime() — STA_BASE_URL still used?

[ ] "IVR seller threshold is 40% with warn band 35–40% (not 50%, not 35%)"
    → Read: constants.py IVR_SELLER_PASS_PCT — should be 40 (raised from 35 Day 68)
    → Read: constants.py IVR_SELLER_WARN_MIN — should be 35 (new warn band floor Day 68)
    → Read: gate_engine seller gate — does it use 4-tier logic (≥40 pass / 35-40 warn / 25-35 warn / <25 fail)?

[ ] "TQQQ_MAX_DELTA = 0.10 in constants.py"
    → Read: constants.py — TQQQ_MAX_DELTA value. Must be 0.10 (not 0.15).

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
[ ] R1: Tradier in DataService live chain path (before ibkr_stale). IB Gateway is dead — no ibkr_provider in live path.
    → grep data_service.py for tradier_provider call in get_chain()
[ ] R2: IB Gateway dead. No IBWorker, no IB() instance. Verify no ib_insync imports remain active in any service file.
    → grep -r "ib_insync\|IBWorker\|ib_worker" backend/*.py (ib_worker.py + ibkr_provider.py only — none from services)
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
[ ] R23: advisory-only gates — IVR, IV/HV, market_regime, max_loss, VRP (non-GLD) are all blocking=False
    → grep gate_engine.py for each: confirm blocking=False (or no hard block) for these 5
    → Exception: GLD hv_iv gate stays blocking=True. trend_ema gate stays blocking=True for sellers.
    → Confirm scan_context_parser.py exists and apply_scan_context_to_gate_payload() is called in analyze_service
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
    sell_put gate → IVR ≥ 40% = PASS, 35–40% = WARN, 25–35% = WARN (floor), <25% = FAIL (raised from 35% Day 68 peer review)
    Are these thresholds in constants.py (IVR_BUYER_PASS_PCT, IVR_SELLER_PASS_PCT) and applied correctly?

[ ] Direction-DTE mapping:
    buy_call / buy_put → 45-90 DTE sweet spot enforced?
    sell_call / sell_put → 21-45 DTE sweet spot enforced?

[ ] Strike direction mapping (single-leg only — Day 57):
    buy_call → ITM delta ~0.68 (R1), ATM delta ~0.50 (R2), OTM delta ~0.30 (R3)
    buy_put  → ITM delta ~0.68 (R1), ATM delta ~0.50 (R2), OTM delta ~0.30 (R3)
    sell_call → delta ~0.20 OTM (R1), delta ~0.15 (R2), delta ~0.25 (R3) — all single-leg
    sell_put  → delta ~0.20 OTM (R1), delta ~0.15 (R2), delta ~0.28 (R3) — all single-leg
    TQQQ sell_put: delta capped at 0.10 by TQQQ_MAX_DELTA (NOT 0.15 or 0.20)

[ ] Expected move formula (new Day 57):
    expected_move = (iv_pct / 100) × sqrt(dte / 365) × underlying_price
    strike_vs_em = (underlying - strike) / expected_move  [for puts]
    strike_vs_em = (strike - underlying) / expected_move  [for calls]
    ≥1.0σ = ✅ Outside 1σ, 0.8-1.0σ = ⚠️ Near 1σ, <0.8σ = ❌ INSIDE

[ ] Exit plan correctness (new Day 57):
    sell_put / sell_call (non-TQQQ): profit_target_pct=50%, dte_exit=21
    TQQQ sell_put:                   profit_target_pct=25%, dte_exit=14
    buy_call / buy_put:              profit_target_pct=100%, stop_loss_pct=50%

[ ] FOMC gate tier correctness (new Day 57):
    Tier 1 BLOCK: XLF, XLRE, TQQQ — seller directions blocked within 14 days of FOMC
    Tier 2 WARN:  QQQ, IWM, GLD — WARN only (never block) within 7 days of FOMC
    Buy directions (buy_call, buy_put): WARN only regardless of ticker, never block

[ ] GLD gate: IV/HV ≥ 1.10 required for sellers — IMPLEMENTED Day 59 (KI-108 resolved)
    → Read: gate_engine — verify _hv_iv_vrp_gate (or _tqqq_satellite_gate / GLD path) hard-blocks when IV/HV < 1.10
    → Confirm: this is a HARD BLOCK (blocking=True), NOT advisory warn — per Rule 23 GLD exception
    → Cross-check: all other hv_iv gates for non-GLD are now advisory WARN only (Day 62)

[ ] TQQQ delta enforcement: _tqqq_satellite_gate() wired — IMPLEMENTED Day 59 (KI-107 resolved)
    → Read: gate_engine._tqqq_satellite_gate() — wired into sell_put AND sell_call for TQQQ?
    → Read: strategy_ranker._rank_sell_put_etf() — TQQQ uses delta 0.10/0.08/0.06 (not 0.20/0.15/0.28)
    → Confirm: TQQQ_MAX_DELTA = 0.10 in constants.py

[ ] Theta burn calculation:
    burn = abs(theta * hold_days) / premium * 100
    Is hold_days from user input (planned_hold_days) not a hardcoded default?

[ ] HV/IV ratio interpretation:
    ratio = IV / HV20
    ratio < 1.0 = options cheap vs realized vol → PASS for buyers
    ratio > 1.3 = options overpriced → FAIL for buyers
    Direction: this gate is different for sellers (want high IV, not low)

[ ] SPY regime direction-awareness:
    buy_call: SPY 5d return < -3% → FAIL. < -1% → WARN
    sell_put: SPY 5d return < -3% → FAIL (neutral/bull bias broken)
    buy_put: SPY 5d return < -3% → PASS (bearish confirmed)
    sell_call: SPY down → PASS (neutral/bear bias confirmed)
    Are all 4 directions handled with different thresholds?

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
    /api/options/analyze → verdict, gates, strategies, pnl_table, behavioral_checks, skew, expected_move_1sd (Day 57)
    /api/health → status, ibkr_connected, mock_mode, tradier_ok, tradier_error (Day 41)
    /api/admin/batch-status → recent_runs[], next_bod, next_eod (Day 35 — BOD batch dead but endpoint may exist)
    DEPRECATED (410): /api/sectors/scan, /api/sectors/analyze/{ticker}, /api/best-setups

[ ] Verify new Day 57 analyze fields in API_CONTRACTS.md:
    "expected_move_1sd" at top level — is it documented?
    Per-strategy: "expected_move", "strike_vs_expected_move", "strike_vs_em_label" — documented?
    Per-strategy: "exit_plan" dict with rule/profit_target_pct/profit_target_credit/dte_exit/exit_date — documented?

[ ] Verify field names match between code and docs:
    "skew" field in analyze response — is it in API_CONTRACTS.md? ✓
    "tradier_ok", "tradier_error" in health response — is it in API_CONTRACTS.md? ✓ (added Day 41)
    "bod_cache" as data_source — is API_CONTRACTS.md updated from "ibkr_cache"? ✓

[ ] Deprecated endpoints documented in API_CONTRACTS.md:
    /api/best-setups → 410 Gone (replaced by /ibkr-scan skill)
    /api/sectors/scan → 410 Gone
    /api/sectors/analyze/{ticker} → 410 Gone

[ ] Verify STA field mappings still match STA's actual response:
    Key ones that have burned us: days_until vs days_away, suggestedEntry vs levels.entry
```

---

### Category 7: Direction Coverage Audit
**Principle:** R13 (all 4 directions tested), R16 (explicit gate routing)

```
[ ] gate_engine.py has 4 distinct branches (verify function names):
    _run_track_a or similar (buy_call), _run_sell_call, _run_buy_put, _run_track_b or _run_sell_put
    Each uses direction-specific thresholds from constants.py
    FOMC gate applied differently per direction (block sellers, warn buyers)

[ ] strategy_ranker.py has 4 distinct builders (Day 57 — verify actual function names):
    _rank_sell_put_etf (sell_put), _rank_sell_call (sell_call)
    _rank_buy_call (buy_call), _rank_buy_put (buy_put)
    Each returns 3 strategies with correct strategy_type (ALL SINGLE-LEG, no spreads)
    Strategy types returned: ONLY 'sell_put', 'sell_call', 'buy_call', 'buy_put'
    STALE types (must NOT appear): 'bear_call_spread', 'bull_put_spread', 'itm_call', 'atm_call', 'naked_put'

[ ] pnl_calculator.py handles all current strategy types (Day 57 — single-leg only):
    sell_put — is P&L table computed for this type? (formerly naked_put)
    sell_call — is P&L table computed?
    buy_call — is P&L table computed?
    buy_put — is P&L table computed?
    STALE types (itm_call, atm_call, bear_call_spread, itm_put, atm_put, bear_put_spread, naked_put)
      → should be harmless dead code, but verify no KeyError if they appear

[ ] Live test coverage (update this table each audit):
    | Direction  | Live Tested? | Last Test | Provider | Bugs Found |
    |------------|-------------|-----------|----------|------------|
    | buy_call   | YES ✅      | Day 21 (XLU ETF) | IBKR | IBKR dead — Tradier untested for this direction |
    | sell_put   | YES ✅      | Day 61/62 (QQQ/XLF) | Tradier+SCAN CONTEXT | trend_ema gate end-to-end confirmed |
    | sell_call  | PARTIAL ⚠️ | Day 59 (FOMC gate fix) | Tradier | Single-leg FOMC gate fix confirmed; full chain path unverified |
    | buy_put    | NO ❌       | Day 21 (XLU ETF) | IBKR | Not tested with Tradier + single-leg |
    Note: buy_put not verified with current Tradier+single-leg+scan_context architecture. buy_call Tradier path untested.
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
| Day 58 Framework Update | May 29, 2026 | All | v1.5 — reflect Day 57-58 architecture pivot | TBD | TBD | Single-leg only, 6-ETF universe, expected_move/exit_plan fields, FOMC 3-tier gate, Today's Trade tab. Full audit run follows update. |
| Day 58 Full Audit | May 29, 2026 | 1-9 | 0 CRITICAL · 4 HIGH · 3 MEDIUM · 2 LOW | 0 | 4 HIGH fixed same session | HIGH: otm_call/otm_put in pnl_calculator (zero P&L for R3), TradeExplainer isBearish/getMoneyness missing otm_put, sell_call DirectionGuide risk label stale ("Spread width"), FOMC gate blocked buyers. All 4 HIGH fixed. MEDIUM open: KI-107 (TQQQ delta guard), KI-108 (GLD IV/HV gate), sell_call FOMC tier not using _etf_fomc_gate. |
| Day 59 KI Resolution | May 29, 2026 | 3,7 | KI-107+108+109 resolved | 0 | 0 | TQQQ _tqqq_satellite_gate() + sell_put delta 0.10/0.08/0.06. GLD IV/HV < 1.10 hard block in gate_engine. sell_call FOMC gate → _etf_fomc_gate(). 37 tests pass. All MEDIUM open issues resolved. |
| Day 60 Framework Update | May 30, 2026 | 1,2,7 | scan_context_parser + trend_ema_gate shipped | 0 | 0 | New: parse_scan_context(), apply_scan_context_to_gate_payload(), _trend_ema_gate() wired all 4 tracks. App.jsx SCAN CONTEXT textarea. 52 tests. ibkr-scan SCAN CONTEXT block added. |
| Day 62 Gate Recalibration | Jun 1, 2026 | 2,3 | 5 gates advisory-only per Rule 23 | 0 | 0 (intentional design change) | ivr_buyer, hv_iv_buyer, market_regime, max_loss, VRP (non-GLD) changed hard-block → advisory warn. GLD IV/HV exception kept. Rule 23 added to GOLDEN_RULES. ETF Signal Scanner removed from App.jsx. 52 tests pass. |
| Day 63 MCP Integration | Jun 2, 2026 | 1 | /ibkr-scan rewritten — MCP replaces screenshot | 0 | 0 | ibkr-scan.md: 12 MCP calls for all 6 ETFs. Three-input architecture (CHART+CATALYST+SCAN) designed. chart_context_parser.py + catalyst_context_parser.py created (not yet wired). Workflow split: browser (flat rate) vs Claude Code (dev). |
| Day 64 Full Audit | Jun 3, 2026 | 1-9 | 0 CRITICAL · 0 HIGH · 3 MEDIUM · 2 LOW | 0 | 0 HIGH fixed (none found) | MEDIUM: R3 magic 3.0 in gate_engine → SELL_PUT_OTM_PASS_PCT constant added; fomc_gate missing from GATE_KB → added; trend_ema gate description too narrow → corrected (blocks all 4 dirs direction-aware). LOW: KI-110 (buy_call stale type names), R4 app.py 360 lines. All MEDIUM fixed same session. |
| Day 69 Targeted Audit | Jun 16, 2026 | 1,2,3,7,9 | 0 CRITICAL · 1 HIGH · 1 MEDIUM · 1 LOW | 0 | 1 HIGH fixed same session | HIGH: GateExplainer.jsx ivr_seller GATE_KB showed "IVR ≥ 35%" — contradicts backend gate (40% after Day 68) → fixed to 40% + warn band explanation. MEDIUM: MASTER_AUDIT_FRAMEWORK 5 stale IVR=35% references → updated to 40%. LOW: app.py debug endpoint "ibkr_cache" label → replaced with "bod_cache". All 3 fixed same session. Framework updated to v1.7. 110 tests pass. |

---

---

### Category 9: Frontend UX Accuracy Audit
**Added:** Day 25 (April 17, 2026)
**Principle:** R15 (code is truth), R21 (quant filter) — wrong plain English descriptions mislead a beginner into making a wrong trade.

**Why this matters:** The Day 25 UX overhaul added hardcoded knowledge to the frontend — gate Q&A text, profit/loss zone directions, strategy type templates. These can silently drift from backend logic when the backend changes, showing "Profit Zone" where the math says loss.

**When to run:** Whenever gate_engine.py or strategy_ranker.py changes, OR monthly as part of weekly audit rotation.

```
[ ] TradeExplainer isBearish() classification (Day 57 — single-leg only):
    Open TradeExplainer.jsx — function isBearish(strategy_type)
    Should return true for: sell_call, buy_put (profit from price staying flat/falling)
    Should return false for: buy_call, sell_put (profit from price rising/staying above)
    STALE types no longer returned by backend: bear_call_spread, itm_put, atm_put, bull_put_spread
    → If isBearish() still lists these, it's dead code (OK) but must NOT MISS sell_call or buy_put

[ ] TradeExplainer getTradeHeadline() templates (Day 57 — verify current types):
    sell_put  → "profit if stays above ${strike}" ✓
    sell_call → "profit if stays below ${strike}" ✓
    buy_call  → "profit if rises above ${breakeven}" ✓
    buy_put   → "profit if drops below ${breakeven}" ✓
    Stale types (bear_call_spread, itm_call, etc.) may still exist — verify no crash if encountered

[ ] TopThreeCards.jsx displays new Day 57-58 fields correctly:
    expectedMove1sd prop wired from App.jsx: <TopThreeCards expectedMove1sd={data?.expected_move_1sd} ...>
    em-context banner shows: "±$X.XX expected move (1σ, Nd)"
    strike_vs_em_label appears in detail grid for rank1 and alt strategies
    ExitPlanBlock renders: rule text + green target chip + date chip (stop chip for buys only)
    When gatedOut: exit plan and P&L chips are hidden (GATED OUT overlay instead)

[ ] BestSetups.jsx → Today's Trade (Day 58 — replaced, scanner removed Day 62):
    No API calls on mount (zero STA/backend fetches — was causing "STA offline" error)
    Shows 6-ETF grid: QQQ, IWM, XLF, GLD, TQQQ (satellite), SPY (regimeOnly/disabled)
    After ETF selection: shows 4-direction picker + TQQQ rules (blue) or GLD rules (amber)
    Analyze button calls onSelect(ticker, direction) → App.jsx handleSelectFromSetups
    ETF Signal Scanner tab: REMOVED Day 62 (was causing 410 on scan click — dead endpoint)
    Verify: no "Scan" button or scanner import remains in App.jsx or BestSetups.jsx

[ ] GateExplainer GATE_KB accuracy:
    Open GateExplainer.jsx — GATE_KB object
    ivr_seller → PASS answer should say "IVR ≥ 40% = PASS" (raised from 35% Day 68); WARN band 35–40% should appear for borderline IVR
    ivr        → PASS answer should say "IV is cheap" (IVR < 30% for buyers)
    market_regime_seller → different from market_regime (seller bias = up OR flat = pass)
    fomc_gate (new Day 57) → is this gate ID in GATE_KB? Or does it render as raw gate.id?
    risk_defined → if present, may be stale (spreads removed Day 57) — verify no misleading text

[ ] GateExplainer category assignment:
    All gate IDs are assigned to one of: market, pricing, risk
    fomc_gate should be in 'market' (not 'risk')
    Gates without GATE_KB entry → fallback renders gate.id + raw reason (no crash)

[ ] DirectionGuide descriptions match actual system behavior (Day 57 — single-leg):
    buy_call card: "I think price will RISE significantly" ✓
    sell_put card: "I think price will STAY or rise slowly" ✓
    sell_call card: "I think price will STAY or drop slowly" ✓
    buy_put card: "I think price will DROP significantly" ✓
    Risk labels: sell_call and sell_put must NOT say "Spread width (capped)" — they are naked now
    SHOULD SAY: "Risk: Uncapped (naked premium)" or similar — verify this was updated

[ ] LearnTab educational content accuracy:
    LessonStrikes: ITM/ATM/OTM zones flip correctly for puts vs calls ✓
    LessonDirections: 4 P&L SVG lines show correct shapes ✓
    LessonSpreads: bear call spread content is now educational-only (no longer a live strategy)
    LessonGates: gate descriptions consistent with GATE_KB (fomc_gate may be missing)

[ ] Strategy type coverage (Day 57 — current types only):
    GateExplainer and TradeExplainer handle all strategy_types NOW returned by strategy_ranker:
    sell_put ✓, sell_call ✓, buy_call ✓, buy_put ✓
    Stale types (bear_call_spread, bull_put_spread, itm_call, atm_call, itm_put, atm_put, naked_put):
    → These are NO LONGER returned by backend. Frontend handlers for them are dead code.
    → Verify: no crash if one appears (defensive fallback), but they should not appear.
    If strategy_type is unknown → TradeExplainer renders gracefully (fallback template, not crash)
```

**Severity mapping:**
- `isBearish()` wrong for any active type (sell_call or buy_put) → **CRITICAL** (green shown where loss zone is)
- `GATE_KB` text contradicts gate_engine logic → **HIGH** (wrong advice for beginner)
- DirectionGuide "Spread width" risk label for naked strategies → **HIGH** (misleads on risk)
- fomc_gate not in GATE_KB → **MEDIUM** (shows raw ID, not helpful)
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
[ ] Run /api/options/analyze for the 5 tradeable ETFs × 4 directions = 20 combinations.
    (SPY is regime anchor only — skip. Use: QQQ, IWM, XLF, GLD, TQQQ)
    Count: how many ETF/direction combinations return non-BLOCKED verdict?

    Target calibration:
      < 1 setup surfaced    → gates are OVER-TUNED or FOMC blocks all sellers. Diagnose.
      2-5 setups surfaced   → HEALTHY. Market has some opportunity.
      > 8 setups surfaced   → gates are UNDER-TUNED. Standards are too loose.

    If blocked: identify the gate blocking the most ETFs.
    Is it: FOMC (XLF/TQQQ sell blocked?)? IVR (< 40% for sellers — raised from 35% Day 68)? DTE? IV/HV?
    One gate causing >50% of blocks = recalibration candidate.
```

#### Check 10.2 — "Always One Direction" Claim (verifiable)
```
[ ] Claim: given a clear VIX regime (VIX 12-20 = normal, VIX 20-30 = elevated, VIX>30 = stress),
    at least one of the 5 tradeable ETFs should surface a CAUTION or GO verdict in at least one direction.

    Verify today: is the claim true?
      YES → system is functioning. Blocked setups are legitimately blocked.
      NO (all 5 ETFs blocked in all 4 directions) → gate miscalibration.
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
