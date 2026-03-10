# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (chain_cache.db + iv_store.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 5 → Day 6)
All concurrency problems resolved. Day 6 = market hours detection (KI-024) + analyze_service.py + paper trade test.

## Session Protocol (REQUIRED at start of every session)
1. Read `CLAUDE_CONTEXT.md` — check Current State, Known Issues, Next Session Priorities
2. Read `docs/stable/GOLDEN_RULES.md`
3. Verify state before writing any code

## Key Source Files
```
backend/
  app.py              558 lines — routes + helpers. Needs analyze_service.py split (Day 6 P1).
  constants.py        DONE — all thresholds, direction-aware DTE/strike windows
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at, heartbeat (30s idle)
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE — provider cascade + SQLite cache + AUTHORITATIVE circuit breaker
  ibkr_provider.py    DONE — direction-aware fetch, struct cache (drift-aware), broad retry
  mock_provider.py    LOW PRIORITY — partially hardcoded AME still
  gate_engine.py      FROZEN — math correct. Coerce None→0.0 in gate_payload before calling.
  strategy_ranker.py  FROZEN — math correct. right field populated.
  pnl_calculator.py   FROZEN — math correct
  iv_store.py         FROZEN — math correct

  # TO CREATE (Day 6 P1):
  analyze_service.py  — extract _merge_swing, _extract_iv_data, _behavioral_checks from app.py
```

## IBWorker Threading Rules (CRITICAL)
- ALL IBKRProvider calls MUST go through `_ib_worker.submit(fn, *args, timeout=N)`
- NEVER call ibkr_provider methods directly from Flask thread — asyncio event loop conflict → hang
- gate_engine requires float for all keys — coerce `ivr_data` None values to 0.0 before gate_payload
- Heartbeat: `reqCurrentTime()` every 30s idle, `_last_heartbeat` staleness check (>75s = disconnected)

## Queue Poisoning Fix (KI-016 — Day 4)
- `_Request` stores `expires_at = time.monotonic() + timeout`
- Worker discards expired requests before executing

## RequestTimeout Fix (KI-017 — Day 4)
- `self.ib.RequestTimeout = 15` before each `reqTickers` batch, restored to 0 in `finally`

## IBWorker Heartbeat (KI-019 — Day 5)
- `queue.get(timeout=30.0)` — on Empty: `ib.reqCurrentTime()`, update `_last_heartbeat`
- `is_connected()`: checks ib flag AND `time.monotonic() - _last_heartbeat < 75.0`

## STA API Field Mapping (verified Day 5 — CRITICAL)
STA /api/sr/{ticker} uses camelCase TOP-LEVEL fields, no nested "levels" object:
- `suggestedEntry` → entry_pullback
- `suggestedStop` → stop_loss
- `suggestedTarget` → target1
- `riskReward` → risk_reward
- `meta.adx.adx` → adx
- `meta.tradeViability.viable == "YES"` → swing_signal = "BUY" else "SELL"
- `support[-1]` → s1_support (nearest support level)
STA /api/stock/{ticker}: `currentPrice` → last_close + entry_momentum
STA /api/patterns/{ticker}: `patterns.vcp.confidence` → vcp_confidence, `patterns.vcp.pivot_price` → vcp_pivot
STA /api/earnings/{ticker}: `days_until` → earnings_days_away (NOT `days_away`)
STA /api/context/SPY: `cycles.cards[name=FOMC Proximity].raw_value` → fomc_days_away
yfinance SPY (computed in backend): spy_above_200sma (close > 200-day SMA), spy_5day_return

## spy_above_200sma Fix (Day 5)
- STA doesn't expose this field — was returning None → bool(None)=False → Market Regime always FAIL
- Fix: computed from yfinance SPY history in sta_fetch(). Fails safe to True if yfinance unavailable.
- Payload parser: `bool(v if v is not None else True)` — explicit None check

## Direction Locking (Day 5)
- BUY signal → locks ['sell_call', 'buy_put']
- SELL signal → locks ['buy_call', 'sell_put']
- No signal → nothing locked

## Struct Cache Drift Invalidation (Day 5)
- `_StructCacheEntry` now stores `underlying_at_cache`
- Cache invalidates if `abs(current - cached) / cached > 0.15` (>15% drift)
- Fixes scenario: NVDA cached at $47.69, actual price $179 → old strikes selected → all fail qualification

## Strike Qualification (Day 5)
- `SMART_MAX_EXPIRIES = 2` (was 1)
- `SMART_MAX_STRIKES = 6` (was 4)
- `SMART_MAX_CONTRACTS = 12` (was 8)
- Broad retry: if len(qual) < 3 → retry with ±15% ATM window across 3 expiries
- Note: for NVDA deep ITM on weekends, only 2 contracts may qualify (market closed = no data)

## Market Hours Behavior (CRITICAL TO UNDERSTAND)
Regular session: 9:30am–4:00pm ET, Mon–Fri
- OPEN: reqTickers returns live bid/ask/greeks → all gates work
- CLOSED: reqTickers returns zero → greeks_pct=0%, liquidity FAIL, theta=999%, ibkr_stale
- KI-024: market hours detection not yet implemented → off-hours analysis is misleading
- FIX PLAN: detect ET market hours → skip reqTickers → use BS greeks from bs_calculator

## AMD → NVDA Workflow (per-ticker cache)
- Cache is PER TICKER — no waiting between different tickers
- AMD then NVDA immediately: two separate 8-12s IBKR fetches, no interference
- Same ticker within 2min: uses SQLite cache (instant)
- Same ticker after 2min: fresh IBKR fetch triggered automatically
- Direction switch same ticker: uses cached chain (ok for most cases)

## Golden Rules (critical)
1. Live data default — reqMarketDataType(1). Mock only for pytest/CI.
2. One IB() instance in IBWorker thread. Flask routes NEVER touch ib_insync directly.
3. No magic numbers — everything in constants.py.
4. app.py routes only (≤150 lines). Target not met yet — 558 lines.
5. gate_engine.py math is frozen. Coerce None→0.0 in gate_payload.
6. STA offline → Manual mode. Never crash.
7. ACCOUNT_SIZE must be in .env — no default in code.
8. Quality banners mandatory when data tier < live.
9. Session close: update CLAUDE_CONTEXT.md, KNOWN_ISSUES, ROADMAP, API_CONTRACTS, PROJECT_STATUS.
10. Read CLAUDE_CONTEXT.md first every session.
12. Single circuit breaker — DataService CB is authoritative.

## Data Provider Hierarchy
1. IBKR Live (reqMarketDataType=1) — default
2. IBKR Cache (SQLite, TTL 2 min, persistent) — "Using cached chain" banner
3. yfinance (emergency fallback) — "Live data unavailable" banner
4. Mock (dev/CI ONLY) — "MOCK DATA" banner, never for paper trades

## Four Directions
| Direction | View | Gate Track | Strike |
|-----------|------|-----------|--------|
| buy_call | Bullish | A | ITM delta ~0.68 |
| sell_call | Neutral/Bearish | A | ATM/OTM |
| buy_put | Bearish | B | ITM delta ~-0.68 |
| sell_put | Neutral/Bullish | B | ATM/OTM |

DTE window: 14-120 days. Buyer sweet spot: 45-90 DTE. Seller sweet spot: 21-45 DTE.

## Day 6 Priorities
1. **KI-024: Market hours detection** — detect ET market hours, use BS greeks when closed
2. **Create analyze_service.py** — extract _merge_swing, _extract_iv_data, _behavioral_checks
3. **Paper trade end-to-end test** — record trade + verify mark-to-market P&L (weekday)
4. **Verify NVDA weekday** — confirm broad retry gets proper contracts with live greeks
5. **KI-022: Synthetic swing defaults warning** — amber banner when stop/target are fabricated

## Frontend Status (Day 2 + Day 4+5 fixes)
- App.jsx: ticker override fixed, SELL direction locking added
- DirectionSelector.jsx: SELL signal locking, correct tooltip per signal
- SwingImportStrip.jsx: STA offline detection fixed (json?.status === 'ok')
- All other components: stable

## Git Status
- Local repo only — no remote origin configured yet

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/CONCURRENCY_ARCHITECTURE.md` — all 5 problems resolved, market hours next
- `docs/versioned/KNOWN_ISSUES_DAY5.md`
- `docs/status/PROJECT_STATUS_DAY5_SHORT.md`
