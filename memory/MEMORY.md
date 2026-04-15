# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (chain_cache.db + iv_store.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 24)
v0.16.0. First GO signals confirmed (XLF + XLV bear_call_spread). bull_put_spread built.
ExecutionCard.jsx + POST /api/orders/stage + ibkr_provider.stage_spread_order() done but
NOT yet wired into App.jsx (KI-071). ibkr_provider now readonly=False.
Next: wire ExecutionCard + CSS into App.jsx, live test stage order at market open (KI-070).

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY23_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY23.md` — open bugs and severity
6. Read `docs/stable/API_CONTRACTS.md` — ONLY if touching API endpoints
After reading: state current version, top priority, any blockers. Ask "What would you like to focus on today?"

## Key Source Files
```
backend/
  app.py              ~660 lines — ETF-only enforcement, _etf_payload(), direction_locked=[],
                                   ETF behavioral checks, fomc_days_away default=999.
                                   Still needs analyze_service.py split (KI-001/KI-023).
  constants.py        DONE (Day 19) — all thresholds + Phase 7b bear constants + DIRECTION_TO_CHAIN_DIR
  bs_calculator.py    DONE — Black-Scholes greeks + price (scipy)
  ib_worker.py        DONE — single IB() thread, submit() queue, expires_at queue poisoning fix
  yfinance_provider.py DONE — middle tier, BS greeks fill
  data_service.py     DONE (Day 12) — provider cascade + SQLite WAL + CB + Alpaca tier
  ibkr_provider.py    DONE (Day 12) — try-finally cancelMktData. OI confirmed unavailable (platform).
  alpaca_provider.py  DONE (Day 10) — REST fallback, greeks ✅, NO OI/volume (model limitation)
  mock_provider.py    LOW PRIORITY — partially hardcoded
  gate_engine.py      UPDATED (Day 21) — ETF gate tracks added: _run_etf_buy_call/put/sell_put.
                                         etf_mode: bool param on run(). Math still frozen.
                                         Callers must coerce ivr_data None→0.0 before gate_payload.
  strategy_ranker.py  UPDATED (Day 23) — _rank_sell_put_spread() added (bull_put_spread, delta 0.30/0.15).
                                         ETF sell_put now routes to spread builder (not naked put).
                                         All 4 ETF directions return defined-risk strategies.
  pnl_calculator.py   UPDATED (Day 21) — ETF: price-relative scenarios (-10% to +15%).
                                          Stock: explicit None guards on all swing fields.
  iv_store.py         FROZEN — math correct

  sector_scan_service.py  DONE (Day 19) — STA consumer + L1 scan + L2 analyze + Phase 7b bear logic.

  # TO CREATE:
  marketdata_provider.py  DEFERRED — MarketData.app no historical IV (confirmed), low priority
  analyze_service.py      P3 — extract _merge_swing, _extract_iv_data, _behavioral_checks
```

## IBWorker Threading Rules (CRITICAL)
- ALL IBKRProvider calls MUST go through `_ib_worker.submit(fn, *args, timeout=N)`
- NEVER call ibkr_provider methods directly from Flask thread — asyncio event loop conflict → hang
- gate_engine requires float for all keys — coerce `ivr_data` None values to 0.0 before gate_payload

## ETF-Only Mode (Day 21)
- 16 ETFs: XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, SCHB, QQQ, TQQQ
- Non-ETF tickers → HTTP 400 with `etf_universe` list
- `_etf_payload()` returns: real SPY regime data, all swing fields = None, `swing_data_quality: "etf"`, `signal: None`
- `direction_locked: []` for all ETFs — direction from regime, not swing signal
- Gate engine called with `etf_mode=True` → routes to ETF-specific gate tracks
- Behavioral checks: IVR context, SPY regime warning, delta discipline (no VCP references)

## Direction-Aware Chain Fetch (implemented Day 3)
```
buy_call  → DTE 45-90 + strikes 8-20% ITM below underlying (delta ~0.68)
buy_put   → DTE 45-90 + strikes 8-20% ITM above underlying (delta ~-0.68)
sell_call → DTE 21-45 + strikes ATM ±6% (sell_call: -2% to +8%)
sell_put  → DTE 21-45 + strikes ATM ±6% (sell_put: -8% to +2%)
Fallback: if direction window yields <3 strikes, supplement from ±15% broad window
```
Structure cache: `IBKRProvider._struct_cache` — in-memory, 4h TTL, keyed by ticker.

## Phase 7b: Sector Bear Market (Day 19)
- bear_call_spread for Lagging ETFs: RS < 98 AND momentum < -0.5
- DIRECTION_TO_CHAIN_DIR: maps display hints (bear_call_spread) → core directions (sell_call)
- Broad Selloff: >50% sectors Weakening/Lagging AND SPY < 200 SMA
- IVR < 40% → L2 soft warning (premium thin for credit spreads)

## Four Directions
| Direction | View | Gate Track | Strike |
|-----------|------|-----------|--------|
| buy_call | Bullish | A | ITM delta ~0.68 |
| sell_call | Neutral/Bearish | A | ATM/OTM |
| buy_put | Bearish | B | ITM delta ~-0.68 |
| sell_put | Neutral/Bullish | B | ATM/OTM |

DTE window: 14-120 days. Buyer sweet spot: 45-90 DTE. Seller sweet spot: 21-45 DTE.

## Day 24 Priorities
1. **P0:** KI-071 — Wire ExecutionCard into App.jsx AnalysisPanel + add CSS to index.css
2. **P0:** KI-070 — Live test stage_spread_order at market open (transmit=False → TWS blotter)
3. **P1:** KI-067 — QQQ sell_put returns ITM puts, fix strike window or struct_cache
4. **P2:** KI-044 — API_CONTRACTS.md: add POST /api/orders/stage + ETF-only fields

## Git Status
- Local repo only — no remote origin configured yet

## Docs Location
- `CLAUDE_CONTEXT.md` — root (master reference)
- `docs/stable/GOLDEN_RULES.md`
- `docs/stable/ROADMAP.md`
- `docs/stable/API_CONTRACTS.md`
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — consolidated audit (8 categories, weekly trigger)
- `docs/versioned/KNOWN_ISSUES_DAY21.md`
- `docs/status/PROJECT_STATUS_DAY21_SHORT.md`
- `docs/Research/Sector_Bear_Market_Day19.md`
- `docs/Research/Sector_Behavioral_Audit_Day15.md`

## Memory Index
- [feedback_test_before_plan.md](feedback_test_before_plan.md) — Always test APIs with live calls before making claims or planning
