# OptionsIQ — Project Status Day 50
> **Date:** May 21, 2026 | **Version:** v0.33.0 | **Tests:** 44

## What Shipped

### IBKR Live IV/HV Batch Integration (KI-101 CLOSED)

**The data gap audit:** With Tradier as primary chain source and IBKR for EOD batch, the system is actually data-rich. The main remaining gap was IV/HV ratio showing `—` in the Best Setups watchlist when Tradier returned no IV for the ATM contract.

**Fix — two-layer redundancy:**

**Layer 1 — Live IBKR batch fetch:**
- `ibkr_provider.get_iv_hv_batch(tickers)` — new method. Uses existing IBWorker + IB Gateway connection. Calls `reqMktData` with `genericTickList="104,106,29,30"` (histVol, impliedVol, callVol, putVol). Batch-qualifies all ETF contracts, fires all 15 reqMktData calls, single `ib.sleep(4.0)` covers all. Returns `dict[ticker → {iv, hv, iv_hv_pct, iv_hv_ratio, opt_volume}]`.
- `scanner_service.fetch_live_iv_hv_batch(tickers, ib_worker)` — IBWorker wrapper. Returns `{}` gracefully when IB Gateway offline (no blast radius).
- `app.py` — calls batch fetch ONCE before the 15-ETF scan loop. One 4-second IBKR round-trip replaces 0 previous calls. Result passed as `live_scanner` dict to each `run_one_setup()`.
- `best_setups_service.run_one_setup()` — new `live_scanner` param (default `None`). Priority: live IBKR → file cache → null (never fabricated — Rule 11).

**Layer 2 — Screenshot file cache fallback:**
- `/etf-scan` Claude command (`.claude/commands/etf-scan.md`) — user pastes IBKR Market Screener ETF screenshot, Claude reads it, applies IVR/VRP/liquidity gate criteria, outputs ranked analysis, writes `backend/data/scanner_cache.json` (4h TTL).
- `scanner_service.get_scanner_data(ticker)` — reads file cache. Used when IB Gateway is offline.
- `scanner_service.scanner_cache_age_hours()` — utility for monitoring.
- Setup doc: `docs/Research/IBKR_ETF_Scanner_Day50.md` — exact IBKR ETF screener column/MultiSort config.

**Data gap audit conclusion:** Tradier + IBKR + STA covers all critical gate fields. Remaining gaps: (1) 30-day avg option volume still uses MarketData.app for Tier 2 ETFs; (2) put/call ratio (ticks 29/30) now flows through batch but not yet wired into any gate — available when ready.

## Test Count
44 (unchanged — no new gate logic, pure data plumbing)

## Open Issues
| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH | Single-stock bear untested — deferred by design (ETF-only mode) |
| KI-099 | LOW | bull_call_spread direction for Leading/Improving + IVR 30–50% |

## Next Session Priorities
1. **P0 — Test scanner integration live** — start backend, run Best Setups with IB Gateway connected, verify IV/HV column populates. ~15 min.
2. **P1 — Paper trade logging** — still 0/30. Log next XLF or QQQ setup. Cannot calibrate gates without 30-trade sample.
3. **P2 — MASTER_AUDIT_FRAMEWORK sweep** — overdue since Day 42 (8 sessions). All 10 categories.
4. **P3 — Put/call ratio gate** — IBKR ticks 29/30 now flow through batch. Simple sentiment overlay in sector_scan or gate_engine. ~20 lines.
5. **P4 — KI-099** — bull_call_spread for Leading/Improving ETFs. High complexity, plan before touching.
