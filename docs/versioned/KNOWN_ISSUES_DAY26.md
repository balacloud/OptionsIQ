# OptionsIQ — Known Issues Day 26
> **Last Updated:** Day 26 (April 20, 2026)
> **Previous:** KNOWN_ISSUES_DAY25.md

---

## Resolved This Session (Day 26)

### KI-008: fomc_days_away always 999 — FIXED ✅
`_days_until_next_fomc()` helper added to `analyze_service.py`. Reads `FOMC_DATES` from `constants.py` (2026–2027 already defined). ETF analysis now always has real FOMC days: STA online → STA's value, STA offline → computed from constants. Today: 16 days to May 6, 2026. Events gate now fires correctly within 3 days of a Fed meeting.

### IVR cold-start — FIXED ✅ (not formally a KI but a known data gap)
`POST /api/admin/seed-iv/all` route built. `↓ Seed IV` button added to frontend scanner header. 7,492 IV rows seeded across 20 tickers (15 ETFs + 5 prior stocks) from IBKR `reqHistoricalData`. IVR percentile now meaningful from day 1. Nightly cron script `seed_iv_nightly.sh` created as automated backup.

### KI-076: TradeExplainer strike zone label overlap — FIXED ✅
Strike zone labels removed from chart (no more overlapping "$147.00 / BE $147.70 / $148.00" crammed into 10px). Replaced with clean "Strike Key" card below the number line — each marker shown as colored dot + price + sublabel. Readable at any strike spacing.

### MasterVerdict passed gates invisible — FIXED ✅ (not formally a KI)
MasterVerdict now shows a compact "✓ Passed: DTE · Market Regime · IVR Seller ..." chip row below the warn/fail detail. Previously the 6 green dots had tooltip-only information.

---

## New Issues This Session (Day 26)

None.

---

## Still Open (Carried Forward)

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Deferred — ETF-only mode returns 400 for non-ETFs.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put direction for QQQ returns ITM put strikes. struct_cache issue. Not addressed Day 26.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
~5pp gap. May self-correct now that IVR data is seeded from consistent IBKR source.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
Partially addressed Day 26 (seed-iv routes updated). ETF-only enforcement and Signal Board fields still not fully documented.

### KI-075: GateExplainer GATE_KB may drift from gate_engine.py (MEDIUM)
Audit trigger: Category 9. Scheduled for Day 27 Master Audit.

### KI-077: DirectionGuide sell_put "capped" label may mislead (LOW)
Unchanged.

### KI-038: Alpaca OI/volume missing (LOW)
### KI-034: OHLCV temporal gap not validated (LOW)
### KI-013/KI-050: API URL hardcoded in JS files (LOW)
### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)
### KI-072: deepcopy() on every cache hit (LOW)
### KI-073: _struct_cache grows unbounded (LOW)
### KI-074: No IBWorker health check at startup (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059 deferred) |
| Medium | 4 (KI-067, KI-064, KI-044, KI-075) |
| Low | 8 (KI-038, KI-034, KI-013/050, KI-049, KI-072, KI-073, KI-074, KI-077) |
| **Total** | **13** |
| **Resolved Day 26** | **3** (KI-008, KI-076, IVR cold-start) |
| **Added Day 26** | **0** |
