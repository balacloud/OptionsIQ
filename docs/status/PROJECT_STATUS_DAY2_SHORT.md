# OptionsIQ — Project Status Day 2
> **Date:** March 5, 2026
> **Version:** v0.2
> **Phase:** Phase 1 (Backend Foundation) — starting

---

## What Was Done Day 2

### Documentation
- `GOLDEN_RULES.md` — expanded with STA process/discipline layer (session startup/close checklists, API sync, debugging rules, code architecture rules, common mistakes, key learnings)
- `docs/Research/Options_Research_Plan` — reviewed, code conflicts documented, key decisions locked
- Data architecture principles established (tiered TTL, delta-triggered invalidation, IBWorker queue pattern)

### Frontend Redesign (all 8 components + CSS)
- `index.css` — two-panel desktop grid, collapsible system, verdict hero styles, sticky quality banner, responsive breakpoints
- `App.jsx` — two-panel layout, `QualityBanner` component inline, no hardcoded AME defaults, deep-link support preserved
- `MasterVerdict.jsx` — hero card: GO/PAUSE/BLOCK label, colored background, gate dot-bar + count
- `GatesGrid.jsx` — collapsible with dot-bar summary in header; expands to 3-column gate grid
- `SwingImportStrip.jsx` — human-readable labels, sectioned (Entry/Risk/Pattern/Calendar/Market), real STA endpoint `/api/integrate/sta-fetch/{ticker}`, FOMC field added
- `TopThreeCards.jsx` — Rank 1 dominant (blue hero card + P&L at target/stop inline), Ranks 2-3 collapsible
- `PnLTable.jsx` — collapsible, cleaner row highlighting
- `BehavioralChecks.jsx` — collapsible, block/warn count in header
- `Header.jsx` — simplified, IB modal triggered via prop

---

## Current State

| Area | Status |
|------|--------|
| Backend | Scaffold only — Phase 1 not started |
| Frontend | DONE — desktop two-panel, all sections collapsible |
| IBKR connection | Not working (God Object, threading bugs) |
| constants.py | Not created — next priority |
| bs_calculator.py | Not created |
| data_service.py | Not created |
| IBWorker thread | Not created |
| yfinance_provider | Not created |
| analyze_service.py | Not created |
| /api/integrate/sta-fetch/{ticker} | Missing from backend — frontend calls it |

---

## New Issues Found Day 2

- **KI-014** (Critical): `ibkr_provider.py:22` market_data_type=3 (delayed) — must be 1 (live)
- **KI-015** (High): `/api/integrate/sta-fetch/{ticker}` missing from backend — 404 on STA connect

Total open issues: 15 (was 13)

---

## Day 3 Priorities

1. Create `constants.py` — authoritative values from Research Plan Section 4F
2. Fix `ibkr_provider.py:22` — market_data_type 3 → 1
3. Create `bs_calculator.py` — Black-Scholes via scipy
4. Fix `mock_provider.py` — dynamic pricing (not hardcoded AME)
5. Fix `iv_store.py` — add entry_price, mark_price columns
6. Remove `QUICK_ANALYZE_MODE` from app.py
7. Add `/api/integrate/sta-fetch/{ticker}` to backend

**Done when:** `python -c "from backend import constants, bs_calculator"` runs clean

---

## Key Decisions Locked In (from Research Plan)

- All 4 directions: buy_call, sell_call, buy_put, sell_put
- DTE window: 14-120 days
- ib_insync pinned at 0.9.86 (archived but stable)
- IBWorker: single thread, queue pattern
- Cache: persistent SQLite (not in-memory)
- Greeks fallback: Black-Scholes when modelGreeks is None
- FOMC calendar: hardcoded 2026-2027 in constants.py, pull from STA when connected
- DEFAULT_ACCOUNT_SIZE: $25,000
