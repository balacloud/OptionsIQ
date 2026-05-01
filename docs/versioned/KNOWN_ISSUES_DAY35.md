# OptionsIQ — Known Issues Day 35
> **Last Updated:** Day 35 (May 1, 2026)
> **Previous:** KNOWN_ISSUES_DAY34.md

---

## Resolved This Session (Day 35)

None — Day 35 was infrastructure and architecture work, not bug fixes.

---

## Updated This Session (Day 35)

### KI-089: MarketData.app chain provider — APPROACH CHANGED
**Previous plan:** Subscribe to Starter ($12/mo), wire as primary chain provider.
**Revised decision (Day 35):**
- Full Greeks confirmed at ALL tiers (including Free) via docs scrape
- `get_oi_volume()` uses `limit=1` → 1 credit/call → ~33 credits/day actual usage
- Free plan (100/day) has 3× headroom — no upgrade needed yet
- Stay on Free tier, monitor for a few days, upgrade only if credit usage or 24h delay causes a real gate problem
- Architecture: Alpaca Free (chain + Greeks) + MarketData.app Free (OI supplement, 24h delayed OK for ETF liquidity gate)
**Status:** MONITORING — not a bug, an architecture decision.

### KI-086: app.py size violation — PARTIALLY RESOLVED
- `_seed_iv_for_ticker` extracted to `batch_service.py` (Day 35)
- app.py: 536 → 492 lines
- Still above Rule 4 target (150 lines) — `_run_one` closure in `best_setups()` still inline
- Remaining work: move `_run_one` to best_setups_service.py

---

## New Issues This Session (Day 35)

None found.

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — 492 lines (Rule 4 max = 150) (MEDIUM)
`_run_one()` closure in `best_setups()` route still inline — move to best_setups_service.py.

### KI-067: QQQ sell_put returns ITM strikes (MEDIUM)
Chain too narrow for current QQQ price (~$658) — sell_put picks up ITM puts.

### KI-064: IVR mismatch L2 vs L3 (~5pp gap) (MEDIUM)

### KI-075: GateExplainer GATE_KB may drift (MEDIUM)

### KI-076: TradeExplainer isBearish() not live-tested (LOW)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)

---

## Resolved History (recent)
- KI-088: L3 stale banner — STA underlying price fallback in analyze_etf() ✅ Day 34
- KI-CB-FRAGILE, KI-STALE-HARDBLOCK, KI-VERDICT-NULL, KI-AMBER-YELLOW, KI-VIX-RATELIMIT, KI-OHLCV-EVERY-CALL, KI-UNDERLYING-IBKR, KI-PARALLEL-EXPIRY ✅ Day 33
- KI-VRP-INVERT ✅ Day 32
- KI-084/087: XLRE OHLCV seeded ✅ Day 31
- KI-085: VIX badge in RegimeBar ✅ Day 31
