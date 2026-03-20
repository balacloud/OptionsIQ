# OptionsIQ — Known Issues Day 15
> **Last Updated:** Day 15 (March 20, 2026)
> **Previous:** KNOWN_ISSUES_DAY14.md

---

## Resolved This Session (Day 15)

### KI-051: get_chain tuple not unpacked in sector L2 (CRITICAL — FIXED)
`data_service.get_chain()` returns `tuple[dict, str]` but sector L2 did `chain = data_service.get_chain(...)` then `chain.get(...)` → AttributeError silently caught. **All L2 IV/liquidity fields were always None.** Fix: `chain, data_source = data_service.get_chain(...)`.

### KI-052: IVR/HV dead code in sector L2 (HIGH — FIXED)
`iv_store` was never passed to `analyze_sector_etf()`. IVR always None → DTE always 45 (default), direction never IVR-adjusted. Fix: wired `iv_store` param through app.py route.

### KI-053: impliedVol vs iv field name (HIGH — FIXED)
Sector L2 used `c.get("iv")` but all providers use `impliedVol`. ATM IV extraction always returned None. Fix: changed to `atm.get("impliedVol")`.

### KI-054: Timestamp +00:00Z invalid ISO (MEDIUM — FIXED)
Backend `datetime.now(timezone.utc).isoformat()` produces `+00:00`. Frontend appended `Z` → `+00:00Z` (invalid). Fix: removed `+ 'Z'` in SectorRotation.jsx.

### KI-055: Null spread renders green (MEDIUM — FIXED)
`null > 5` is false → falls to green class. Trader sees green "—" implying good liquidity when no data exists. Fix: null check before color ternary.

### KI-056: Deep dive no auto-trigger (MEDIUM — FIXED)
`handleSectorDeepDive` only set state, didn't call `analyze()`. User clicked "Full Gate Analysis" → nothing happened. Fix: call `analyze()` with direct values (React state is async).

### KI-057: rs_ratio/rs_momentum default 0 (LOW — FIXED)
RS normalized around 100. Default 0 = "catastrophically weak". Inconsistent with cap-size ETFs defaulting to 100. Fix: default to `None` (no default).

---

## Still Open

### KI-044: API_CONTRACTS.md stale — 5+ mismatches vs code (HIGH)
Now includes 2 new sector endpoints partially documented. Full sync still needed.

### KI-001/KI-023: app.py still ~620 lines (MEDIUM)
`analyze_service.py` not yet created. Added ~20 lines for sector routes.

### KI-022/KI-005: Synthetic swing defaults silent (MEDIUM)

### KI-025: Sparse strike qualification for large-cap stocks (MEDIUM)

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 30 (LOW)

### KI-013: API URL hardcoded in useOptionsData.js (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

### KI-050: API URL hardcoded in useSectorData.js (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-044) |
| Medium | 3 |
| Low | 5 |
| **Total** | **9** |
| **Resolved Day 15** | **7** (KI-051 through KI-057) |
