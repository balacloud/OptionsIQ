# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (chain_cache.db + iv_store.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 17)
v0.13.1. First full audit (MASTER_AUDIT_FRAMEWORK, 8 categories). All 8 claims VERIFIED. Threading SAFE.
KI-060 FIXED: SPY regime None→0.0 masking in all 4 gate tracks — now returns non-blocking warn.
KI-061 CLOSED: iv_store IVR formula verified correct (percentile: count(hist_iv≤iv)/total×100).
Audit health: 0 CRITICAL, 2 HIGH (KI-059 bear untested — needs market hours, KI-044 API docs stale).
Next: Day 18 = bear market live test P0 (IB Gateway + market hours) + API_CONTRACTS sync.

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
  gate_engine.py      DONE (Day 17) — Rule 3 fixed, math frozen. KI-060: SPY gate None masking fixed.
                                     Callers must coerce ivr_data None→0.0 before gate_payload.
                                     spy_5day_return: do NOT coerce — gate now handles None internally.
  strategy_ranker.py  UPDATED (Day 12) — sell_put naked warning on all 3 strategies.
                                        sell_call → bear_call_spread ✓. buy_put → ITM+spread+ATM ✓.
  pnl_calculator.py   FIXED (Day 9) — None guard + 4 strategy type handlers
  iv_store.py         FROZEN — math correct

  sector_scan_service.py  DONE (Day 15+16) — STA consumer, L1+L2, SPY regime via STA (Day 16)

  # TO CREATE:
  marketdata_provider.py  DEFERRED — MarketData.app no historical IV (confirmed), low priority
  analyze_service.py      P3 — extract _merge_swing, _extract_iv_data, _behavioral_checks
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
STA /api/stock/SPY: `priceHistory[-1].close > mean(priceHistory[-200:].close)` → spy_above_200sma
                    `(priceHistory[-1].close - priceHistory[-6].close) / priceHistory[-6].close × 100` → spy_5day_return
NOTE: yfinance SPY for spy regime REMOVED Day 16 (rate limiting). Now uses STA exclusively.

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

## Day 18 Priorities
1. **P0:** Bear market live test — buy_put + sell_call with real bearish setup (KI-059, Rule 13) — needs IB Gateway + market hours
2. **P1:** API_CONTRACTS.md full sync (KI-044)
3. **P2:** Phase 7 research — sector bear plays (multi-LLM research required before coding)
4. **P3:** analyze_service.py extraction (app.py ≤ 150 lines)

## Frontend Status (Day 16)
- Tab switcher: Analyze | Sectors (App.jsx)
- Analyze tab: full gate analysis, strategies, P&L table, behavioral checks, swing import, paper trade
- Sectors tab: SectorRotation.jsx + ETFCard.jsx + useSectorData.js — L1 scan + L2 detail + L3 deep dive
- All quality banners: ibkr_live/cache/stale/closed/alpaca/yfinance/mock

## Git Status
- Local repo only — no remote origin configured yet

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/versioned/KNOWN_ISSUES_DAY17.md`
- `docs/status/PROJECT_STATUS_DAY17_SHORT.md`
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (8 categories, weekly trigger)
- `docs/Research/System_Coherence_Audit_Day11.md`
- `docs/Research/Sector_Rotation_ETF_Module_Day11.md`
- `docs/Research/Sector_Behavioral_Audit_Day15.md`

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
