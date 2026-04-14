# OptionsIQ — Claude Memory

## Project Overview
Personal options analysis tool. NOT a broker. Analysis only.
- Backend: Flask on port **5051**
- Frontend: React on port **3050**
- IB Gateway: 127.0.0.1:4001 (live account U11574928)
- Database: SQLite at `backend/data/` (chain_cache.db + iv_store.db)
- STA (separate repo): `localhost:5001` — integration HTTP only, optional

## Current Phase (Day 23)
v0.15.1. Live smoke test complete. IVR-tiered scan wiring done. Gate visibility fixed.
Two structural issues block GO signal: (1) OI=0 platform limitation always creates liquidity
warn → verdict always CAUTION (KI-069). (2) sell_put only builds naked puts → max_loss
blocks on any ETF. Need bull_put_spread. strategy.type=None in ETF sell_call (KI-068).
Next: fix KI-069 verdict logic + KI-068 type field + bull_put_spread → get first GO signal.

## Session Protocol (REQUIRED at start of every session — read ALL 6 files IN ORDER)
1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints and process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending ← DO NOT SKIP
4. Read `docs/status/PROJECT_STATUS_DAY22_SHORT.md` — latest day status snapshot
5. Read `docs/versioned/KNOWN_ISSUES_DAY22.md` — open bugs and severity
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
  strategy_ranker.py  UPDATED (Day 21) — ETF mode: delta-based spread legs (delta 0.30/0.15).
                                         Detected via swing_data_quality == "etf".
                                         sell_call → bear_call_spread ✓. buy_put → ITM+spread+ATM ✓.
                                         KI-068: strategy.type=None for ETF sell_call (unfixed).
                                         NEEDS: bull_put_spread for sell_put (naked blocks max_loss).
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

## Day 23 Priorities
1. **P0:** KI-069 — Fix verdict logic: ETF OI=0 should be `info` not `warn` (stops CAUTION block)
2. **P0:** KI-068 — Fix strategy.type=None for ETF sell_call path in strategy_ranker.py
3. **P1:** bull_put_spread for sell_put (like bear_call_spread for sell_call) — defined risk
4. **P2:** Verify GO signal: XLF sell_call + XLI sell_put should show green after fixes
5. **P3:** KI-044 API_CONTRACTS.md ETF-only fields sync

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
