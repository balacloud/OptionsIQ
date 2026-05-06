# OptionsIQ — Project Status Day 42
> **Date:** May 6, 2026
> **Version:** v0.29.0
> **Tests:** 36 (all pass)

---

## What Shipped

### Skew Computation (NEW FEATURE)
- `compute_skew()` added to `tradier_provider.py` — 2 extra Tradier API calls (expirations + full neutral chain fetch)
- Picks nearest expiry in SKEW_DTE_MIN=20 to SKEW_DTE_MAX=50 window; finds nearest-to-SKEW_TARGET_DELTA=0.30 call and put
- Returns `put_iv_30d - call_iv_30d` as `skew` field (positive = puts more expensive = normal downside fear)
- Wired non-blocking into `analyze_service.analyze_etf()` — logged and skipped on error
- `/api/options/analyze` response now includes `skew` dict with 8 fields
- **Root cause for design:** `get_options_chain()` is direction-filtered (sell_put → puts only), so skew needs separate fetch of both sides

### Rule 16: Restart Backend After Python Changes
- Golden Rule 16 added to GOLDEN_RULES.md — kill port 5051, restart, verify `/api/health` before declaring done
- **Root cause:** Flask `debug=False` has no auto-reload; stale Python code ran silently after changes

### MASTER_AUDIT_FRAMEWORK v1.2 → v1.3
- Updated for Tradier-era architecture, new IVR thresholds, skew, new R16
- New "From Coding Experience" section: `_f() or None` trap, label-source integrity, SQLite UTC caveat
- Category 1 Claims completely rewritten (12 new Tradier-era claims)
- Day 42 full audit run: 0 CRITICAL · 2 HIGH · 3 MEDIUM — all resolved same session

### Audit Fixes (Day 42)
| Finding | Severity | Fix | File |
|---------|----------|-----|------|
| QualityBanner dead `ibkr_cache` key (KI-094) | HIGH | Renamed to `bod_cache`, added `tradier` to no-banner early-return | `frontend/src/App.jsx` |
| API_CONTRACTS.md missing `skew` field | HIGH | Documented full `skew` response block | `docs/stable/API_CONTRACTS.md` |
| BatchStatusPanel UTC timestamp (KI-095) | MEDIUM | `fmtTime()` normalizes SQLite timestamp before `new Date()` | `frontend/src/components/DataProvenance.jsx` |
| data_service.py stale docstring `ibkr_cache` | MEDIUM | Updated to `bod_cache` | `backend/data_service.py` |
| ACCOUNT_SIZE silent default 25000 | MEDIUM | Removed default, relies on startup validation | `backend/app.py` |
| Missing route in API_CONTRACTS.md | MEDIUM | Added `GET /api/options/paper-trades/summary` | `docs/stable/API_CONTRACTS.md` |

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (DEFERRED) | Single-stock bear untested — ETF-only mode |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift from gate_engine |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested all 4 directions |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |

---

## Next Session Priorities

| Priority | Item | Effort | Notes |
|----------|------|--------|-------|
| P0 | KI-064: IVR mismatch L2 vs L3 investigation | 30 min | Root cause unknown — diff chain profile vs time delta vs IV source? |
| P1 | KI-075: GateExplainer GATE_KB drift audit | 30 min | Category 9 sweep — seller gates changed since Day 25 |
| P2 | KI-077: DirectionGuide sell_put "capped" label | 15 min | Label or tooltip fix |
| P3 | KI-081: CPI/NFP/PCE macro calendar | 30 min | Add to constants.py, surface as soft WARN in gate |
| P4 | Category 7 live tests — buy_call/sell_call/buy_put via Tradier | 45 min | Only sell_put tested Day 40 |
