# OptionsIQ — Known Issues Day 34
> **Last Updated:** Day 34 (April 30, 2026)
> **Previous:** KNOWN_ISSUES_DAY33.md

---

## Resolved This Session (Day 34)

### KI-088: L3 "Run Analysis" stale banner ✅ RESOLVED Day 34
Added `_resolve_underlying_hint(ticker, payload)` helper to `analyze_service.py`.
Precedence: `payload["last_close"]` → STA `/api/stock/{ticker}` currentPrice → None (IBKR fallback).
Called at top of `analyze_etf()` — bypasses `ibkr_provider`'s internal `reqMktData(snapshot=True)` call
which was returning None for bid/ask/last in the 1.2s window. Result: `data_source: ibkr_live` on L3.
`_run_one` in `app.py` simplified — inline STA fetch removed (now handled centrally).
Data Provenance updated: `underlying_price` field added to `field_resolution` (source: "sta").
3 new unit tests added (test_resolve_underlying_hint.py). Tests: 33 → 36.

---

## New Issues This Session (Day 34)

### KI-089: MarketData.app as primary chain provider (OPPORTUNITY — Day 35)
**Context:** MarketData.app live chain test confirmed full data — IV, delta, theta, gamma, vega,
bid/ask, OI, volume per contract. All fields gate_engine needs. $12/mo subscription.
**Gap:** Historical IV (for IVR seeding) not available via their chain endpoint — returns 0 contracts
for past dates. IVR endpoint returns `no_data`.
**Proposed split:**
- Daily analysis (chain fetch): MarketData.app REST → eliminates IBKR dependency during trading hours
- Nightly IV seed (once/day, already works): Keep IBKR/yfinance — no time pressure, reliable
- Underlying price, VIX, SPY regime: Already on STA ✅
**Priority:** MEDIUM. Current IBKR pain is resolved (Days 33–34). This is an upgrade, not a fix.
**Research doc:** docs/Research/KI-088_Plan_Day34.md (§MarketData diagnostic)

---

## Still Open (Carried Forward)

### KI-086: app.py size violation — 536 lines (Rule 4 max = 150) (MEDIUM)
`_seed_iv_for_ticker()` (~50 lines) + `seed_iv_all()` route + `_run_one()` closure belong in service modules.

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
- KI-VRP-INVERT: VRP gate inverted since Day 29 ✅ Day 32
- LearnTab zones SVG overlap ✅ Day 32
- KI-084/087: XLRE, SCHB OHLCV seeded ✅ Day 31
- KI-085: VIX badge in RegimeBar ✅ Day 31
