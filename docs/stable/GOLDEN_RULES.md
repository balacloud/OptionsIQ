# OptionsIQ — Golden Rules

> **Purpose:** Stable reference document for all session rules
> **Location:** `docs/stable/GOLDEN_RULES.md` (rarely changes)
> **Last Updated:** Day 3 (March 6, 2026)

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
At every session close, update:
- `CLAUDE_CONTEXT.md`: Current State table + Session Log + Next Session Priorities + Last Updated
- `docs/versioned/KNOWN_ISSUES_DAY[N].md`: Mark resolved, add new
- `docs/stable/ROADMAP.md`: Mark completed phases
- `docs/stable/API_CONTRACTS.md`: If any endpoint added or changed
- `docs/status/PROJECT_STATUS_DAY[N]_SHORT.md`: New status doc

### Rule 10: Read CLAUDE_CONTEXT.md First.
At the start of every session: read `CLAUDE_CONTEXT.md` before writing a single line of code.
Check Current State table. Check Known Issues. Check Next Session Priorities.
Do not assume state from memory — verify from the doc.

### Rule 11: Return null, Not a Plausible Fake.
A hardcoded fallback value is worse than an error. Never return fake defaults (e.g., IV=25, HV20=15) when a data source fails. Return `null` and let the frontend show "unavailable" honestly. Silent fallbacks corrupt paper trade decisions.

### Rule 12: Verify Data Contracts Before Writing Code.
Check actual return structures from each module before writing consuming code. The producer (e.g., `data_service`) defines the API structure; consumers adapt to it. Never double-calculate a field — if `data_service` computed IV, don't recompute it in `analyze_service`.

---

## SESSION RULES

### The 15 Process Rules:
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

---

## SESSION STARTUP CHECKLIST

When user starts a new session:
1. [x] Read `CLAUDE_CONTEXT.md` FIRST (master reference)
2. [x] Read `docs/status/PROJECT_STATUS_DAY[N]_SHORT.md`
3. [x] Verify context by summarizing current state to user
4. [x] Ask: "What would you like to focus on today?"
5. [ ] Do NOT ask user to re-explain the project
6. [ ] Do NOT ask for files unless you need to modify them
7. [ ] Do NOT jump to fixing — understand the problem first

---

## SESSION CLOSE CHECKLIST

When user says "session ending" or "close session":
1. [x] Create `docs/status/PROJECT_STATUS_DAY[N+1]_SHORT.md`
2. [x] Ask: "Did any bugs get fixed or found?" -> Update `KNOWN_ISSUES_DAY[N].md`
3. [x] Ask: "Did any APIs change?" -> Update `API_CONTRACTS.md`
4. [x] Ask: "Did we learn a new rule?" -> Update `GOLDEN_RULES.md`
5. [x] **UPDATE `CLAUDE_CONTEXT.md`** — Current Day, Version, Last Updated, State table, Session Log, Next Session Priorities
6. [x] Update auto memory (`~/.claude/projects/.../memory/MEMORY.md`) if significant learnings
7. [x] Git commit AND PUSH (don't forget push!)
8. [x] Note any deferred tasks for next session

### How Updates Work (Claude Code):
- Claude uses Edit/Write tools to update files directly in the filesystem
- No manual user action needed for local file updates
- Claude commits AND pushes to git — don't provide commands for user to run

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
