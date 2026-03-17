# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (chain_cache.db + iv_store.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 12)
Phase 4b audit hardening complete. All critical/high bugs fixed. System usable for live analysis.
KI-035 OI confirmed IBKR platform limitation — graceful degradation (WARN not BLOCK) is permanent.
gate_engine Rule 3 fixed: imports from constants.py (60+ literals replaced). SQLite WAL added.
Next: Day 13 = API_CONTRACTS.md sync (P0) + sector rotation backend (P1).

## Session Protocol (REQUIRED at start of every session)
1. Read `CLAUDE_CONTEXT.md` — check Current State, Known Issues, Next Session Priorities
2. Read `docs/stable/GOLDEN_RULES.md`
3. Verify state before writing any code

## Key Source Files
```
backend/
  app.py              ~600 lines — HARDENED (Day 12): logger, ACCOUNT_SIZE guard, outer try-except.
                                   Needs analyze_service.py split (Day 13 P2).
  constants.py        DONE (Day 12) — 19 new thresholds added (IV abs, DTE signal, SPY regime per dir)
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE (Day 12) — provider cascade + SQLite WAL + CB + Alpaca tier
  ibkr_provider.py    DONE (Day 12) — try-finally cancelMktData. OI via reqMktData confirmed unavailable.
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
  mock_provider.py    LOW PRIORITY — partially hardcoded
  gate_engine.py      DONE (Day 12) — Rule 3 fixed: imports from constants.py. Liquidity: OI=0+Vol>0 → WARN.
                                     Math is FROZEN — coerce None→0.0 in gate_payload before calling.
  strategy_ranker.py  UPDATED (Day 12) — sell_put naked warning on all 3 strategies.
                                        sell_call → bear_call_spread ✓. buy_put → ITM+spread+ATM ✓.
  pnl_calculator.py   FIXED (Day 9) — None guard + 4 strategy type handlers
  iv_store.py         FROZEN — math correct

  # TO CREATE:
  marketdata_provider.py  Day 13 — MarketData.app REST ($12/mo — pending)
  analyze_service.py      Day 13 P2 — extract _merge_swing, _extract_iv_data, _behavioral_checks
```

## IBWorker Threading Rules (CRITICAL)
- ALL IBKRProvider calls MUST go through `_ib_worker.submit(fn, *args, timeout=N)`
- NEVER call ibkr_provider methods directly from Flask thread — asyncio event loop conflict → hang
- `_extract_iv_data` uses `_call_provider()` helper to route IBKR calls through IBWorker
- gate_engine requires float for all keys — coerce `ivr_data` None values to 0.0 before gate_payload

## Queue Poisoning Fix (KI-016 — RESOLVED Day 4)
- `_Request` stores `expires_at = time.monotonic() + timeout`
- Worker checks expiry BEFORE executing: if expired → put TimeoutError in result_q → continue
- submit() timeout and worker expiry both use same `timeout` value — synchronized

## reqMktData Fix (KI-027 — RESOLVED Day 7, verified Day 9)
- `reqTickers()` does NOT fire `tickOptionComputation` (tick type 13 = modelGreeks)
- Must use `reqMktData(contract, genericTickList="", snapshot=False)` then `ib.sleep(3+)`
- Subscribe all contracts, sleep, read Ticker.modelGreeks, cancelMktData(contract) in try-finally
- Live greeks confirmed 100% during market hours (ibkr_live, usopt lazy connect confirmed)

## KI-035 OI — CONFIRMED PLATFORM LIMITATION (Day 12)
- `genericTickList="101"` does NOT deliver per-contract OI via reqMktData
- Volume IS available (Vol > 0 confirmed live). OI is simply not available from IBKR this way.
- Resolution: graceful degradation in `_liquidity_gate()`:
  - OI=0 with Vol>0 → WARN not BLOCK
  - `spread_fail_block` (spread > 15%) is the only hard liquidity block
  - Note in gate result: `OI 0 [OI unavailable]`

## STA API Field Mapping (verified Day 5 — CRITICAL)
STA /api/sr/{ticker}: `suggestedEntry` → entry_pullback, `suggestedStop` → stop_loss,
                      `suggestedTarget` → target1, `riskReward` → risk_reward,
                      `meta.adx.adx` → adx, `support[-1]` → s1_support
STA /api/stock/{ticker}: `currentPrice` → last_close + entry_momentum
STA /api/patterns/{ticker}: `patterns.vcp.confidence` → vcp_confidence, `patterns.vcp.pivot_price` → vcp_pivot
STA /api/earnings/{ticker}: `days_until` → earnings_days_away (NOT days_away)
STA /api/context/SPY: `cycles.cards[FOMC].raw_value` → fomc_days_away
yfinance SPY: computed in backend → spy_above_200sma, spy_5day_return

## Direction-Aware Chain Fetch (implemented Day 3)
```
buy_call  → DTE 45-90 + strikes 8-20% ITM below underlying (delta ~0.68)
buy_put   → DTE 45-90 + strikes 8-20% ITM above underlying (delta ~-0.68)
sell_call → DTE 21-45 + strikes ATM ±6% (sell_call: -2% to +8%)
sell_put  → DTE 21-45 + strikes ATM ±6% (sell_put: -8% to +2%)
Fallback: if direction window yields <3 strikes, supplement from ±15% broad window
```

## Golden Rules (critical)
1. Live data default — reqMarketDataType(1). Mock only for pytest/CI.
2. One IB() instance in IBWorker thread. Flask routes NEVER touch ib_insync directly.
3. No magic numbers — everything in constants.py.
4. app.py routes only (≤150 lines). Target not met yet — ~600 lines.
5. gate_engine.py math is frozen. Coerce None→0.0 in gate_payload.
6. STA offline → Manual mode. Never crash.
7. ACCOUNT_SIZE must be in .env — no default in code. Startup raises if missing.
8. Quality banners mandatory when data tier < live.
9. Session close: update CLAUDE_CONTEXT.md, KNOWN_ISSUES, ROADMAP, PROJECT_STATUS, MEMORY.md.
10. Read CLAUDE_CONTEXT.md first every session.
12. Single circuit breaker — DataService CB is authoritative. No CB logic in app.py.

## Data Provider Hierarchy (updated Day 12)
1. IBKR Live (reqMktData snapshot=False) — default, greeks confirmed 100% Day 9
2. IBKR Cache (SQLite WAL, TTL 2 min, persistent) — "Using cached chain" banner
2.5. MarketData.app (PLANNED, $12/mo) — greeks+IV+OI+volume, 15-min delayed
3. Alpaca (DONE, free) — greeks+IV but NO OI/volume (model limitation)
4. yfinance (emergency fallback) — NO real greeks (BS computed from HV)
5. Mock (dev/CI ONLY) — "MOCK DATA" banner, never for paper trades

## Four Directions
| Direction | View | Gate Track | Strike |
|-----------|------|-----------|--------|
| buy_call | Bullish | A | ITM delta ~0.68 |
| sell_call | Neutral/Bearish | A | ATM/OTM |
| buy_put | Bearish | B | ITM delta ~-0.68 |
| sell_put | Neutral/Bullish | B | ATM/OTM |

DTE window: 14-120 days. Buyer sweet spot: 45-90 DTE. Seller sweet spot: 21-45 DTE.

## Day 13 Priorities
1. **P0:** API_CONTRACTS.md sync — update spec to match code (5 mismatches, KI-044)
2. **P1:** Sector rotation backend — sector_scan_service.py + 2 endpoints
3. **P2:** analyze_service.py extraction (app.py ≤ 150 lines)
4. **P3:** bull_put_spread for sell_put direction

## Frontend Status (Day 2 + Day 4+5+6+12 fixes)
- App.jsx: ticker override fixed, QualityBanner fixed (ibkr_live), alpaca+ibkr_stale banners added
- Header.jsx: alpaca added to sourceLabel map
- strategy_ranker.py: sell_put naked warning on all strategy cards
- All other components: stable

## Git Status
- Local repo only — no remote origin configured yet

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/versioned/KNOWN_ISSUES_DAY12.md`
- `docs/status/PROJECT_STATUS_DAY12_SHORT.md`
- `docs/Research/System_Coherence_Audit_Day11.md`
- `docs/Research/Behavioral_Audit_Day11.md`
- `docs/Research/Sector_Rotation_ETF_Module_Day11.md`

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
