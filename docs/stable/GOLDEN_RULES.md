# OptionsIQ — Golden Rules

> **Purpose:** Stable reference document for all session rules
> **Location:** `docs/stable/GOLDEN_RULES.md` (rarely changes)
> **Last Updated:** Day 42 (May 6, 2026)

---

## DOMAIN RULES (OptionsIQ-Specific)

### Rule 1: Live Data Is the Default. Always.
`reqMarketDataType(1)` is hardcoded as the startup call.
Paper trading uses the same live data path as production.
Mock data is for `pytest` and CI only — never for paper trades.
If IBKR is offline, show a banner. Never silently fall back to stale/fake data without telling the user.

### Rule 2: One IB() Instance. One Worker Thread.
The IB() instance lives in `IBWorker` — a single dedicated thread started at app startup.
Flask routes NEVER create IB() instances directly.
Flask routes NEVER call ib_insync methods directly.
All IBKR requests go through `data_service.request_chain(ticker)` which queues to IBWorker.

### Rule 3: No Magic Numbers.
Every threshold lives in `constants.py`. No raw numbers in gate_engine, ranker, or route handlers.
If you need a new threshold, add it to `constants.py` first, then import it.

### Rule 4: app.py Is Routes Only.
`app.py` max 150 lines. Routes only — validate input, call service, return JSON.
Business logic goes in `analyze_service.py`.
Data access goes in `data_service.py`.
If app.py grows past 150 lines, something is wrong.

### Rule 5: Gate Math Is Frozen.
`gate_engine.py` is verified correct. Do not touch the math.
Only allowed changes: import constants from `constants.py` instead of inline numbers.
New gates must be added as new functions — never modify existing gate functions.

### Rule 6: STA Integration Is Optional, Never Required.
OptionsIQ works standalone. If STA is offline: Manual mode.
Never crash or block if `localhost:5001` is unreachable.
`fetch_sta_data()` returns `None` on connection error — UI handles this gracefully.

### Rule 7: ACCOUNT_SIZE Must Be Explicit.
ACCOUNT_SIZE is a required `.env` variable. App raises at startup if not set.
No default value in code. User must be conscious of their account size for position sizing.

### Rule 8: Quality Banners Are Mandatory.
When data quality is below "live", the frontend MUST show a banner.
- Tier 2 (cached): "Using cached chain from X minutes ago"
- Tier 3 (yfinance): "Live data unavailable — using yfinance (greeks estimated)"
- Tier 4 (mock): "MOCK DATA — testing only. Do not paper trade."

### Rule 9: Session Close Protocol.
At every session close, update ALL of the following (Claude does this — no manual user action):
- `CLAUDE_CONTEXT.md` — Current State table + Session Log + Next Session Priorities + Last Updated
- `docs/versioned/KNOWN_ISSUES_DAY[N].md` — mark resolved, add new (create new file each day)
- `docs/stable/ROADMAP.md` — tick completed items, add new ones
- `docs/status/PROJECT_STATUS_DAY[N]_SHORT.md` — create new status snapshot
- `docs/stable/API_CONTRACTS.md` — if any endpoint added or changed
- `docs/stable/GOLDEN_RULES.md` — if new rule or process lesson learned
- `memory/MEMORY.md` — update phase, priorities, file statuses
- Git commit (skip push — no remote configured)

### Rule 10: Read CLAUDE_CONTEXT.md First.
At the start of every session: read `CLAUDE_CONTEXT.md` before writing a single line of code.
Check Current State table. Check Known Issues. Check Next Session Priorities.
Do not assume state from memory — verify from the doc.

### Rule 11: Return null, Not a Plausible Fake.
A hardcoded fallback value is worse than an error. Never return fake defaults (e.g., IV=25, HV20=15) when a data source fails. Return `null` and let the frontend show "unavailable" honestly. Silent fallbacks corrupt paper trade decisions.

### Rule 12: Verify Data Contracts Before Writing Code.
Check actual return structures from each module before writing consuming code. The producer (e.g., `data_service`) defines the API structure; consumers adapt to it. Never double-calculate a field — if `data_service` computed IV, don't recompute it in `analyze_service`.

### Rule 13: No Module Is "Frozen" Until All 4 Directions Are Tested.
`gate_engine.py`, `strategy_ranker.py`, and any direction-aware module CANNOT be declared frozen or "verified correct" until all four directions (`buy_call`, `sell_call`, `buy_put`, `sell_put`) have been explicitly exercised end-to-end with real or realistic data.
Marking a module frozen after testing only 1 direction creates a false safety guarantee. The freeze label means: "tested, correct, do not touch." Until all paths are covered, the label is a lie.

### Rule 14: Swing Field Defaults Are Forbidden. (Extension of Rule 11)
`_merge_swing` (and any swing-merging code) MUST NOT fabricate plausible values for missing fields.
- `vcp_confidence` missing → `None`, never `70`
- `adx` missing → `None`, never `35`
- `volume_ratio` missing → `None`, never `1.0`
Any behavioral check that receives `None` for a field it needs must emit a `SKIP` result with a human-readable reason string, not a pass or fail based on phantom data.
Adding a `swing_data_quality: "full" | "partial" | "manual"` flag is mandatory when any field is filled with a default.

### Rule 15: Code Is the Source of Truth. Docs Are the Debt.
If README, API_CONTRACTS.md, or any doc contradicts the actual code behavior — the doc is wrong, not the code.
When you discover a contradiction:
1. Verify code behavior with a diagnostic first (don't assume docs are right)
2. Fix the doc immediately — do not defer
3. If the code behavior is itself wrong (e.g., cache-first when live-first is required), fix the code AND the doc together

Common contradictions to audit every 5 sessions:
- IVR formula (percentile vs rank)
- Gate Track routing per direction
- Data provider hierarchy order
- ACCOUNT_SIZE startup enforcement
- Verdict logic (pass count thresholds)

### Rule 16: Gate Track Assignment Must Be Explicit Per Direction.
Gate engine MUST receive explicit direction context and apply the correct track:
- `buy_call` → Track A (buyer gates: momentum, breakout, HV/IV, trend)
- `sell_call` → Track A-Seller (seller gates: premium decay, range-bound, IV rank)
- `buy_put` → Track B (put-buyer gates: breakdown, bearish momentum)
- `sell_put` → Track B-Seller (put-seller gates: support hold, elevated IV, cash-secured)
If a function accepts `direction` but ignores it and routes by some other heuristic, it is a bug. Audit gate routing every time a new direction is enabled.

### Rule 17: Never Claim Enforcement You Haven't Implemented.
If ACCOUNT_SIZE has a default value in code (`25000`), you CANNOT document it as "required — app raises at startup if not set." The documentation must match the actual runtime behavior.
Before writing "app raises if X is missing," verify the raise exists in the startup path with a code read. If it doesn't exist, either implement it or document the actual behavior (default used, warning logged).

### Rule 19: Research and Decision Sessions Get a Markdown Doc.
Any session involving external research (API comparison, library evaluation, architecture decisions) MUST produce a `.md` file in `docs/Research/` before the session closes.
Format: `docs/Research/<Topic>_Day[N].md`
Include: the question asked, options evaluated, conclusions, and action items.
This prevents re-doing the same research in future sessions and keeps decision history auditable.

### Rule 20: Behavioral Audit Before Code Fixes.
Before fixing surface-level bugs from a coherence audit, run a behavioral audit first.
A behavioral audit asks: "does the system actually do what we claim it does?"
Use the structured audit prompt with verdict labels:
`[VERIFIED]`, `[PLAUSIBLE]`, `[MISLEADING]`, `[UNVERIFIED]`, `[HALLUCINATED]`
This prevents wasting time fixing cosmetic issues while fundamental logic is wrong.
Audit covers: gate logic claims, strategy builder claims, data flow claims, Golden Rules enforcement.

### Rule 22: Two Personas. Always Active. Non-Negotiable.

Every decision in OptionsIQ — architecture, gate logic, code structure, UI, data handling — must pass through two internal lenses before being acted on. These are not aspirational; they are required filters.

---

#### Persona A — The 30-Year Systems Architect

**Who they are:**
Built trading infrastructure at scale. Has seen systems fail in production during the 2008 crash, the 2020 COVID gap, and the 2022 vol crush. Has ripped out elegant code that looked correct but was wrong under real market stress. Does not trust "it works in dev." Does not trust "it worked last week."

**How they think:**
- "What happens when this is called 50 times in a row during a fast market? Does IBWorker queue back up? Does SQLite WAL handle concurrent reads?"
- "What is the blast radius if this function throws? Does it corrupt the paper trade record, or does it fail cleanly with a logged error?"
- "This module is 604 lines. Can I reason about the full state at line 450 without reading from the top? If not, it needs splitting."
- "Is this threshold in constants.py or is it a magic number waiting to be forgotten? Rule 3."
- "If I change this gate, do all 4 directions still work? Or do I break buy_put because I only tested sell_put?"
- "Is this actually tested, or is it 'looks correct'? Rule 13."

**What they veto:**
- Silent fallbacks — Rule 11. A system that fabricates plausible data and keeps running is more dangerous than one that crashes loudly.
- God objects — Rule 4. One file that does everything is untestable and unmaintainable.
- Undocumented thresholds — Rule 3. If a number is not in constants.py with a comment, it doesn't exist.
- "It's a personal project, close enough" — This mindset causes real money losses. Personal does not mean sloppy.

---

#### Persona B — The 30-Year Quant Trader

**Who they are:**
Has traded defined-risk spreads through every major vol regime. Has blown up small accounts with strategies that looked good on paper. Has seen IV Rank lie (high IV can keep going higher), seen regime signals lag by weeks, seen liquidity disappear when you need it most. Does not care if the code is elegant. Cares if the trade makes money.

**How they think:**
- "Is the IV environment right for this direction, or am I forcing a trade because the tool says GO?"
- "What is the expected move for this expiry? Is my short strike outside it? If the market makes a 1-sigma move, where am I?"
- "This spread pays $0.05 on $1 wide. After commissions, I'm taking on $95.50 of risk to make $4.50. That's not a trade, that's a lottery ticket."
- "FOMC is in 7 days and this expires in 30. That's not 'no event conflict' — that's the biggest event of the month sitting inside my holding window."
- "The bid-ask spread is 16%. My fill is going to be at least 8% worse than mid. Does the trade still make sense after realistic execution cost?"
- "Win rate matters. But expectancy is what pays the bills. A 70% win rate with a 3:1 loser destroys your account. What's the actual expectancy here?"
- "Am I taking this trade because it's a good trade, or because I've been staring at the screen for two hours and need to do something?"

**What they demand:**
- Credit-to-width ratio gate — $0.05 on $1 wide is not a trade (KI-082).
- Expected move context — is the short strike outside the expected move? Surface this.
- Regime check before any GO — SPY regime + VIX level, not just one.
- Honest liquidity — if OI is zero and the spread is 15%, say so loudly, not in a footnote.
- Trade management baked in — what's the profit target, stop level, and exit rule at 21 DTE?

---

#### How to Apply These Personas

Before writing any code, before proposing any architecture, before declaring any gate "done", run both filters:

1. **Architect filter:** "Would this hold up under real load, real market stress, and adversarial data? Is it testable, auditable, and maintainable?"
2. **Quant filter:** "Would this lose me money? Does it produce actionable, honest, risk-aware output — or does it produce confident-looking output that masks real risk?"

If either persona would object, **stop and redesign** before writing a line.

This rule supersedes comfort, speed, and "good enough for a personal project."

---

### Rule 21: Think Like a Quant Trader, Not a Developer.
Every code review and audit must pass the **quant filter**: "Would this cost me money?"
- A developer asks: "Does it compile? Does it crash?" A quant asks: "Is the DTE wrong? Is IVR actually flowing? Can the trader get in and out?"
- Dead code paths that look correct but never execute (e.g., IVR-based DTE when IVR is always `None`) are **critical bugs** — they silently degrade every recommendation.
- Every data field shown to the trader must trace back to a real computation. If a field shows "—" because the pipeline never populates it, that's not a display bug — it's a missing feature disguised as working code.
- Liquidity (bid-ask spread, OI) must be surfaced before any "Analyze" recommendation. Directing a trader toward an illiquid chain without warning is a system failure.
- Market regime (SPY trend, VIX level) must gate bullish recommendations. RS momentum is a lagging indicator — it takes weeks to rotate. The market can crash 10% before quadrants catch up.
- **Audit priority order**: P&L impact first, data integrity second, UX third, code style last.

### Rule 18: Liquidity Gate Thresholds Must Be Direction-Aware.
The "strike nearness" sub-check in the liquidity gate (contract within N% of underlying) WILL always fail for ITM buyer strategies by design — that's what ITM means. Applying an ATM nearness filter to a delta-0.68 ITM call is a structural mismatch.
Liquidity gate must either:
(a) Disable strike-nearness for ITM buyer tracks (replace with delta-range check), or
(b) Use direction-aware nearness thresholds (±20% for buyers, ±6% for sellers)
Document which approach is used. Never apply a single nearness threshold across all 4 directions.

---

## SESSION RULES

### The 16 Process Rules:
1. **START of session:** Read `CLAUDE_CONTEXT.md` first — always
2. **BEFORE modifying any file:** READ it first using Read tool — never assume structure
3. **NEVER assume code structure** — always verify with actual file
4. **END of session:** Create updated `PROJECT_STATUS_DAY[N+1]_SHORT.md`
5. **User will say "session ending"** to trigger session close protocol
6. **NEVER HALLUCINATE** — Don't claim behavior without running diagnostics
7. **THINK THROUGH** — Pause and reason carefully before suggesting solutions
8. **ALWAYS VALIDATE** — Fact-check answers against actual code
9. **GENERATE FILES ONE AT A TIME** — Wait for user confirmation before next file
10. **FOLLOW CODE ARCHITECTURE RULES** — See section below
11. **DEBUG APIs PROPERLY** — Run diagnostic queries FIRST before writing fixes
12. **LOCAL FILES FIRST, THEN GIT** — Update files locally using Edit/Write tools FIRST, then commit and push
13. **EXHAUSTIVE VERIFICATION** — When testing artifacts, check EVERY item, not a sample
14. **UPDATE "LAST UPDATED" DATES** — When modifying any file in `docs/stable/`, update the `Last Updated` header
15. **NEVER IMPLEMENT WITHOUT VALIDATION** — Don't implement features based on assumptions. Require verified behavior from actual code or explicit user direction
16. **RESTART BACKEND AFTER PYTHON CHANGES** — Flask runs with `debug=False` (no auto-reload). After ANY edit to `.py` files, immediately kill and restart the backend (`lsof -ti:5051 | xargs kill -9` then `nohup python3 app.py > backend.log 2>&1 &`). Verify with `curl /api/health` before declaring the feature done. Do NOT leave the user running stale code.

---

## SESSION STARTUP CHECKLIST

**Read ALL 6 files IN ORDER. Do not skip or reorder. Authoritative source: `CLAUDE_CONTEXT.md` → Session Protocol.**

1. `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. `docs/stable/ROADMAP.md` — phase status, done vs pending ← COMMONLY SKIPPED, DO NOT SKIP
4. `docs/status/PROJECT_STATUS_DAY{N}_SHORT.md` — latest day status snapshot
5. `docs/versioned/KNOWN_ISSUES_DAY{N}.md` — open bugs and severity
6. `docs/stable/API_CONTRACTS.md` — ONLY if touching API endpoints

Behavioral rules (non-negotiable):
- Do NOT ask user to re-explain the project
- Do NOT ask for files unless you need to modify them
- Do NOT jump to fixing — understand the problem first
- After reading all startup docs: state current version, top priority, blockers, then ask "What would you like to focus on today?"

---

## SESSION CLOSE CHECKLIST

**Authoritative update list is in `CLAUDE_CONTEXT.md` → Session Protocol → Close Checklist.**

Key reminders:
- Ask before updating: bugs fixed? APIs changed? new rule learned?
- Claude does ALL file updates — no manual user action
- Git commit AND push (skip push if no remote configured)
- Note deferred tasks in Next Session Priorities

---

## API SYNC VERIFICATION

### When to Verify API_CONTRACTS.md:
- After adding new endpoints
- After modifying existing endpoints
- Periodically (every 5 sessions) as a health check

### How to Verify (Claude runs this):
```bash
grep -n "@app.route" backend/app.py
```

### Verification Checklist:
1. Count routes in `app.py`
2. Count routes documented in `API_CONTRACTS.md`
3. If mismatch -> update `API_CONTRACTS.md`
4. Check response structures are still accurate

> **Every `@app.route` in app.py MUST have a corresponding entry in API_CONTRACTS.md**

---

## CODE ARCHITECTURE RULES

### Best Practices for Code Generation:
1. **Verify data contracts BEFORE writing code** — Check actual return structures before writing consuming code
2. **Document API contracts** — Each module's input/output should be documented in comments
3. **Producer defines API** — Data producer (e.g., `data_service`) defines the structure; consumer adapts to it
4. **Don't double-calculate** — If `data_service` computes IV, don't recompute it in `analyze_service`
5. **Test incrementally** — Verify each change works before proceeding to next
6. **Clean separation of concerns** — Routes don't touch business logic; business logic doesn't touch IBKR
7. **Flat API structures preferred** — `chain.calls` is better than `data.options.chain.calls.list`
8. **Zero is not null** — Use `null` for missing data, never `0`. Zero scores as real data and corrupts gate logic.

### Why These Rules Exist:
- Silent fallbacks (IV=0, HV=0) cause gate logic to pass or fail incorrectly
- Hardcoded mock data (AME) breaks analysis for any other ticker
- God Object app.py mixes IBKR, analysis, and route logic — impossible to test or debug

---

## DEBUGGING RULES

### When Fixing Bugs:
1. **ALWAYS run diagnostic queries FIRST** before writing fixes
2. **Never assume library behavior** — verify actual return values
3. **If fix fails, STOP** — diagnose root cause, don't chain guesses
4. **Test in isolation** — verify the fix works standalone before integrating

### Debugging Workflow:
```
1. Understand the symptom
2. Form hypothesis about cause
3. Write diagnostic query to TEST hypothesis
4. Run diagnostic, analyze results
5. Only THEN write the fix
6. Test fix incrementally
7. If fix fails, go back to step 2 — don't guess again
```

---

## COMMON MISTAKES TO AVOID

### Don't Do This:
- [ ] Jump to writing code without understanding the problem
- [ ] Assume file structure without seeing the actual file
- [ ] Chain multiple guesses when the first fix fails
- [ ] Write long code blocks without user testing in between
- [ ] Create PROJECT_STATUS that loses cumulative context
- [ ] Return fake numeric defaults when a data source fails
- [ ] Mix IBKR threading with Flask route handlers

### Do This Instead:
- [x] Ask clarifying questions first
- [x] Read the current file before modifying
- [x] Run diagnostic queries to understand actual behavior
- [x] Test each change before moving to the next
- [x] Stop and diagnose when something fails
- [x] Return `null` for missing data, never a fake plausible value
- [x] Keep PROJECT_STATUS focused but reference stable docs

---

## KEY LEARNINGS (Cumulative)

### Day 2: UI Design for Emotional Intelligence
- **Verdict before evidence** — GO/PAUSE/BLOCK is the dominant hero element. Users need the conclusion before the proof. Burying the verdict mid-page forces anxiety and second-guessing.
- **Quality banner is first-class** — If data tier < live, sticky banner appears before ANY analysis data. A trader who doesn't notice cached/mock data can make a wrong paper trade decision.
- **Progressive disclosure** — Secondary sections collapsed by default. Show summary indicators (dot-bar, count) in headers so users can decide whether to expand.
- **Human-readable labels in UI** — Never expose internal field names (`entry_pullback`) to users. Labels are the interface; field names are implementation details.
- **Desktop two-panel: left sticky** — Verdict and controls always visible while results scroll on the right.

### Day 6: Critical Audit Findings — Systematic Gaps
- **"Frozen" ≠ "Correct for all directions."** `gate_engine.py` and `strategy_ranker.py` were declared frozen after testing one direction. Both had routing bugs for `sell_call` and `buy_put`. Freeze label must require all-directions test coverage.
- **`_merge_swing` violated Rule 11 silently.** Fabricated `vcp_confidence=70`, `adx=35` as defaults. Gate logic ran on phantom data and no one noticed because the output looked plausible. Silent fabrication is worse than a crash — it looks correct.
- **Docs diverged from code in 4 places simultaneously.** IVR formula (percentile vs rank), data hierarchy (cache-first vs live-first), ACCOUNT_SIZE enforcement (code has default, docs say "raises"), verdict logic (thresholds mismatch). The common cause: docs written ahead of code and never sync'd back after implementation changed.
- **Direction-specific logic needs direction-specific tests.** A system with 4 directions needs 4 test paths per module. One passing direction gives false confidence the other 3 are correct.
- **Liquidity gates designed for sellers break buyers by construction.** Strike-nearness filters are an ATM-centric concept. Applying them to delta-0.68 ITM contracts is a category error.

### Day 4: Spread Order, Detection Patterns, Legacy Cleanup
- **Spread order determines precedence in JS.** `{ ticker: "MEOH", ...swing }` — if swing has `ticker: "AMD"`, AMD wins. Always put explicit override fields AFTER the spread: `{ ...swing, ticker: "MEOH" }`. This applies to any field that should never be overridden by a previous state import.
- **`!json.error` is a weak offline check.** An offline response using `status: "offline"` (no `error` field) passes `!json.error` as true. Always check the affirmative: `json?.status === 'ok'`.
- **Remove legacy code the moment the replacement is confirmed working.** Two circuit breakers (app.py legacy + DataService) diverged silently across sessions. The moment DataService CB was confirmed working on Day 3, the app.py CB should have been removed. It wasn't — and it added confusion for two sessions.
- **app.py line count is a real health metric.** Every business logic function in app.py is untestable in isolation. 821 lines = significant tech debt. Target ≤150 is not aesthetic — it's testability.

### Day 3: Concurrency and Threading
- **IBWorker owns the IB() instance — no exceptions.** Even helper methods like get_historical_iv() and get_ohlcv_daily() must go through IBWorker.submit(). Calling ib_insync methods from any other thread causes asyncio event-loop conflicts that hang indefinitely with no error message.
- **Queue poisoning is a real threat.** When submit(timeout=24s) times out, the worker keeps running. Every subsequent request waits for the hung call to finish. Fix: add `expires_at` to each `_Request` so the worker discards stale requests.
- **ib.RequestTimeout=0 means unlimited.** Always set `ib.RequestTimeout = N` before any reqTickers call. Otherwise a slow IBKR response blocks the worker indefinitely.
- **Frozen files can be worked around.** gate_engine.py is frozen (math correct). But it calls float() on all keys directly — if a value is None (not missing), float(None) crashes. Fix: coerce None → 0.0 in gate_payload construction before passing to gate_engine. Never modify the gate math; adapt the inputs.
- **Direction-aware fetching is mandatory for performance.** Fetching 12 generic ATM contracts when the user wants ITM delta-0.68 calls wastes IBKR quota and time. Always target the direction's DTE sweet spot (buyers 45-90, sellers 21-45) and strike zone (buyers 8-20% ITM, sellers ATM ±6%).
- **Structure cache (reqSecDefOptParams) is free speed.** Chain structure (strikes + expiries) is stable for 4+ hours intraday. Cache it in memory. First call populates; subsequent calls skip the round-trip entirely.

### Day 1: Scaffold Lessons
- **Read frozen files before touching them** — `gate_engine.py`, `pnl_calculator.py`, `strategy_ranker.py`, `iv_store.py` are verified correct; the only allowed change is importing from `constants.py`
- **God Object pattern blocks everything** — app.py mixing IBKR + analysis + routes means nothing can be tested independently; split first
- **Mock data tied to one ticker breaks all others** — `mock_provider.py` hardcoded to AME must be dynamic before any multi-ticker work

### General: Silent Fallbacks — The Invisible Lie
- **A hardcoded fallback value is worse than an error.** Returning IV=25 when IBKR fails, or HV20=15 when calculation fails — the system makes gate decisions on phantom data and the trader never knows.
- **Return null, not a plausible fake.** Let gate logic handle missing data honestly (gate = FAIL or SKIP).
- **Audit the WHOLE path.** Backend → data_service → analyze_service → gate_engine → API → frontend. A silent fallback at any layer corrupts all layers downstream.

### General: Data Contract Bugs
- Verify data contracts BEFORE writing UI or service code
- Don't double-calculate — producer defines API, consumer adapts
- Check for field name mismatches between layers
- Flat structures are easier to validate than nested ones

### General: Debugging Discipline
- **Debug before coding** — Run diagnostic queries first
- **Don't chain failed attempts** — Stop, think, verify
- **Library behavior != assumptions** — Always verify actual return values (especially ib_insync async patterns)

### General: Local Files First, Then Git
- **Update files locally FIRST** — Use Edit/Write tools to modify filesystem
- **Then commit and push** — Git is version control, not the primary update mechanism
- **Claude commits AND pushes** — Don't provide commands for the user to run

### General: Exhaustive Verification
- **Don't spot-check — verify EVERYTHING** — This is Claude's computational advantage
- **When given test artifacts:** Read EVERY file, check EVERY field, document EVERY finding
- **Don't take human shortcuts** — Value is in thoroughness, not speed

### General: Auto-Update Everything — Don't Ask, Just Do
- **Never ask the user to manually update files** — Claude updates all docs directly
- **Never provide git commands** — Claude commits AND pushes
- **Always update timestamps** on every doc touched
- **Session close = Claude does everything** — update docs, commit, push. User just says "close session."

---

## SESSION REMINDER

```
OPTIONSIQ SESSION REMINDER:
1. STOP before coding — understand the problem first
2. READ the current file before modifying anything
3. RUN diagnostic queries before writing fixes
4. TEST incrementally — one change at a time
5. If something fails, STOP and diagnose — don't guess again
6. At end, run session close checklist — Claude does all updates
```

---

*This file lives in `docs/stable/` — stable reference, rarely changes*
