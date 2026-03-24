# OptionsIQ — Project Status Day 19
> **Date:** March 24, 2026
> **Version:** v0.14.0
> **Phase:** Day 19 — Phase 7b: Sector Bear Market Strategies (implemented + live tested)

---

## What Was Done Today

### Phase 7b: Sector Bear Market Strategies (COMPLETE)
Researched and implemented bearish options plays for sector ETFs in bear markets.

**New features:**
- **Lagging → bear_call_spread**: RS < 98 AND momentum < -0.5 → bearish credit spread recommendation
- **Broad Selloff detection**: >50% sectors Weakening/Lagging AND SPY < 200 SMA → regime banner
- **IVR bear warning**: L2 soft warning when IVR < 40% (premium may be thin for credit spreads)
- **Frontend**: bear badges (red), selloff banner, IVR warning display

**Research doc:** `docs/Research/Sector_Bear_Market_Day19.md`
- Dropped: Weakening → sell_call (defensive sectors get bid up in selloffs)
- Changed: IVR from L1 hard gate to L2 soft warning (L1 never has IVR)

### Bug Fixes (5 resolved)
1. **KI-062**: ETF earnings_days_away fabricated (45 → None) — Rule 11 violation
2. **KI-063**: SPY regime fabricated defaults → real STA data with 2-min cache
3. **KI-063b**: spy_5day_return unit mismatch (STA % vs gate decimal) → normalization
4. **KI-065**: Frontend Deep Dive sent buy_call for bear_call_spread ETFs → fixed mapping
5. **KI-066**: DTE Selection gate false FAIL for ETFs (VCP not applicable) → auto-pass
6. **L2 None→buy_call**: SKIP ETFs silently fetched buy_call chain → fixed with direction mapping

### ETF Gate Post-Processing (Rule 5 compliant)
Three ETF-specific gates now handled via post-processing (gate math frozen):
- Event Calendar: "earn N/A (ETF)" instead of fabricated "earn 45d"
- Pivot Confirm: "ETF: auto-pass" (VCP pivots don't apply to ETFs)
- DTE Selection: "ETF: auto-pass" (VCP/ADX signals don't apply to ETFs)

### Live Test Results
- L1 Scan: BROAD_SELLOFF detected, XLV + XLY → bear_call_spread, QQQ → SKIP ✅
- L2 Analysis: sell_call chain fetched correctly, IVR working ✅
- L3 Gates (sell_call track): IVR PASS, Market Regime Seller PASS, Events PASS ✅
- L3 Gates (buy_call track): all 3 ETF auto-passes working, Market Regime correctly FAIL ✅

---

## Files Changed

| File | Change |
|------|--------|
| `backend/constants.py` | +RS_LAGGING_BEAR_RS, RS_LAGGING_BEAR_MOM, BROAD_SELLOFF_SECTOR_PCT, IVR_BEAR_SPREAD_WARN, DIRECTION_TO_CHAIN_DIR |
| `backend/sector_scan_service.py` | quadrant_to_direction bear logic, _detect_regime(), L2 chain fix, IVR soft warning |
| `backend/app.py` | SPY regime helpers (_fetch_spy_regime, _spy_above_200, _spy_5d_return), earnings None fix, ETF gate post-processing (events + pivot + DTE) |
| `frontend/src/App.jsx` | bear_call_spread added to SECTOR_DIR_TO_CORE mapping |
| `frontend/src/components/ETFCard.jsx` | bear_call_spread in DIR_LABELS, BEAR_DIRECTIONS set, badge-bear styling |
| `frontend/src/components/SectorRotation.jsx` | Broad selloff banner, IVR bear warning display |
| `frontend/src/index.css` | .badge-bear, .sector-selloff-banner, .etf-warning-bear styles |
| `docs/Research/Sector_Bear_Market_Day19.md` | Research doc (Rule 19) |

---

## Audit Health
- 0 CRITICAL
- 1 HIGH: KI-059 (single-stock bear directions untested)
- 5 MEDIUM: KI-064, KI-044, KI-001, KI-022, KI-025
- Down from 2 HIGH → 1 HIGH (sector bear now tested)

---

## Next (Day 20)
1. **P0: KI-059** — single-stock buy_put + sell_call live test (needs market hours + IB Gateway + bearish stock)
2. **P1: KI-064** — IVR mismatch investigation (L2 percentile vs L3 average)
3. **P2: KI-044** — API_CONTRACTS.md full sync
4. **P3: KI-001** — analyze_service.py extraction (app.py ~650 lines)
5. **P4: Phase 8** — Options Explainer "Learn" tab
