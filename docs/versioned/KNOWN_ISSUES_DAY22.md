# OptionsIQ — Known Issues Day 22
> **Last Updated:** Day 22 (April 14, 2026)
> **Previous:** KNOWN_ISSUES_DAY21.md

---

## Resolved This Session (Day 22)

### market_regime_seller blocking ETF sell_call in bull market (HIGH → RESOLVED)
ETF post-process in `app.py` only covered buy_call/put/sell_put. When sell_call (bear_call_spread)
was run on Lagging sectors (XLV, XLF) with SPY above 200SMA, `market_regime_seller` gate fired
blocking=True — preventing sector-relative shorts in bull market. Fixed: ETF sell_call post-process
sets `blocking=False` with reason "sector RS/momentum weakness overrides SPY trend".

### Liquidity showing ❌ red when non-blocking for ETFs (MEDIUM → RESOLVED)
ETF liquidity post-process condition was `g.get("blocking")` — only fired for blocking gates.
When gate was already non-blocking (DayN code), the `status="fail"` persisted as red dot.
Fixed: condition changed to `g["status"] == "fail"` regardless of blocking flag.

### spy_above_200sma None→False bug (MEDIUM → RESOLVED)
`bool(spy_regime.get("spy_above_200sma", True))` returns `False` when key exists with value None
(Python dict.get default only substitutes if key MISSING). Fixed: explicit `if _spy_above_raw is not None`
check — defaults to `True` (safe for buy_call/sell_put) only when value is actually missing.

### MasterVerdict gate details invisible (HIGH → RESOLVED)
UI showed "3/8 pass · 2 warn · 1 fail" with colored dots but no labels — user couldn't know
which gate failed or why. Fixed: `MasterVerdict.jsx` now renders blocking fails + warn gates
inline with name, computed_value, and reason. `GatesGrid.jsx` now auto-opens when any fail/warn present.

### IVR not wired into scan_sectors() direction mapping (MEDIUM → RESOLVED)
`quadrant_to_direction()` was updated with IVR tiers (Day 22) but `scan_sectors()` called it
without `ivr=` — so all Leading/Improving sectors got `buy_call` regardless of IVR.
Fixed: `scan_sectors(iv_store=None)` parameter added, `_get_ivr()` helper looks up latest
stored IV for each ETF and passes percentile to `quadrant_to_direction()`.
Result: XLI, XLK, QQQ, MDY → `sell_put` (IVR >50%); IWM → `buy_call` (IVR <30%).

---

## Still Open

### KI-068: strategy.type = None for ETF sell_call (NEW — MEDIUM)
`top_strategies` entries for XLF/XLV sell_call have `type: None`. The `_rank_sell_call`
or ETF ranker path does not set the type field. Frontend may not render strategy header
or type label correctly.
**Fix needed:** Trace `strategy_ranker._rank_sell_call()` → ensure `type` field set on
bear_call_spread dict. Likely missing in ETF mode path.

### KI-069: CAUTION verdict suppresses GO for all-non-blocking gate sets (NEW — MEDIUM)
When all blocking gates pass but 2+ warn gates fire (e.g. liquidity OI=0 + DTE warn),
verdict is CAUTION (amber) not GO (green). Since OI=0 is a known platform limitation
(not a real liquidity issue for SPDR ETFs), it should NOT lower verdict to CAUTION.
In practice, the best available trade in any market condition appears as CAUTION — user
expects a GREEN signal to mean "trade this" but never sees one.
**Fix needed:** Audit verdict logic. OI=0 warn for ETFs should be demoted to `status="info"`
or excluded from verdict downgrade. ETF-specific verdict threshold may be appropriate.

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Lower priority — ETF-only mode means stocks return 400. Deferred.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_call direction for QQQ returns fractional weekly-expiry strikes (602.5, 604.78) → ITM
for current price $614. QQQ scan now suggests `sell_put` (IVR >50%) not `sell_call`,
so this is lower priority. Test when QQQ sell_put is run at market open.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
L2 sector analyze shows IVR ~97% (ATM contract IV → iv_store percentile).
L3 gate analysis shows IVR ~76% (average of all contracts' impliedVol). ~5pp gap.
Data-specific from IV spike, not systematic. Low impact.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
ETF-only enforcement, Signal Board, `_etf_payload` fields not documented.

### KI-001/KI-023: app.py still ~680+ lines (MEDIUM)

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 999 (LOW)

### KI-013/KI-050: API URL hardcoded in JS files (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059, deferred) |
| Medium | 6 (KI-067, KI-064, KI-044, KI-001, KI-068, KI-069) |
| Low | 5 |
| **Total** | **12** |
| **Resolved Day 22** | **5** (market_regime_seller, liquidity red, spy_above None, gate visibility, IVR scan wiring) |
