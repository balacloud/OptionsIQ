# OptionsIQ — Known Issues Day 20
> **Last Updated:** Day 20 (March 28, 2026)
> **Previous:** KNOWN_ISSUES_DAY19.md

---

## Resolved This Session (Day 20)

### ETF Liquidity Gate — OTM spread too strict (MEDIUM → RESOLVED)
ETF OTM legs (e.g. XLK 136C at 4.4% OTM) had bid-ask spread of ~24%, which triggered `SPREAD_BLOCK_PCT=15%` hard block — stopping all strategies from surfacing.
Fix: ETF post-processing in `app.py` — when liquidity gate blocks solely on "Spread too wide" for an ETF ticker, downgrade from BLOCK/fail to warn. Same Rule 5 pattern as events/pivot/DTE.

### Strategy ranker narrow-chain fallback (MEDIUM → RESOLVED)
For ETFs with narrow option chains (e.g. XLK Apr 2026 max strike 136 at $130.25 underlying), all three delta targets (0.30, 0.20, 0.15) resolved to the same highest OTM strike. Both bear_call_spread conditions failed (`short_30.strike == protection_15.strike`), leaving only a naked short call strategy.
Fix: `strategy_ranker.py` — after finding `short_30`, look for strikes strictly ABOVE it for the protection leg. If none exist, fall back to 2nd-highest OTM as short and highest OTM as protection (e.g. 135/136 Bear Call, net_credit=$0.52).

### Session protocol documentation gaps (MEDIUM → RESOLVED)
Session startup protocol existed in 3 locations with inconsistent step counts. `memory/MEMORY.md` had only 3 steps (missing ROADMAP, PROJECT_STATUS, KNOWN_ISSUES). Root cause: model reads MEMORY.md first (loaded into context) and follows its abbreviated list.
Fix: Updated MEMORY.md to full 6-step list with `← DO NOT SKIP` annotation on ROADMAP. Updated GOLDEN_RULES.md SESSION STARTUP CHECKLIST to explicitly list all 6 files. Updated Rule 9 (close checklist) to include all 8 items.

---

## Still Open

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Sector ETF bear directions (bear_call_spread/sell_call) now tested ✅ for XLK/XLY/XLF.
Single-stock buy_put and sell_call still need market-hours live test with a bearish stock.
**Next:** Test Monday when market opens.

### KI-067: QQQ chain too narrow for current price (MEDIUM — NEW)
QQQ underlying at $563.79 but IBKR chain maxes at strike $562. All available calls are ITM.
`strike_otm` gate correctly blocks ("Strike is ITM — call selling into immediate loss").
Root cause: direction-aware chain fetch window (-2% to +8%) should reach ~$609 for sell_call, but IBKR struct_cache was built at a lower price level. Cache drift threshold (15%) not exceeded, so no auto-refresh.
**Fix needed:** Investigate why sell_call fetch isn't reaching OTM strikes for QQQ. Check struct_cache drift logic vs current price.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
L2 sector analyze shows IVR 97.22% (ATM contract IV → iv_store percentile).
L3 gate analysis shows IVR 21.43 (average of all contracts' impliedVol).
Different aggregation methods produce different values. Needs investigation to align.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
Sector scan `market_regime` field, `bear_call_spread` direction, `ivr_bear_warning` not documented.

### KI-001/KI-023: app.py still ~650+ lines (MEDIUM)
analyze_service.py not yet created. Added more code this session (liquidity ETF post-processing).

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)
QQQ returns 0 contracts. Related to KI-067.

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 30 (LOW)

### KI-013/KI-050: API URL hardcoded in JS files (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059 single-stock bear) |
| Medium | 6 (KI-067 new, KI-064, KI-044, KI-001, KI-022, KI-025) |
| Low | 5 |
| **Total** | **12** |
| **Resolved Day 20** | **3** (ETF liquidity gate block, ranker narrow-chain fallback, session protocol doc gaps) |
