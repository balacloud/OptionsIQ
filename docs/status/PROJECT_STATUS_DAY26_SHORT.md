# OptionsIQ — Project Status Day 26
> **Date:** April 20, 2026
> **Version:** v0.18.0
> **Session type:** Data infrastructure + UX fixes + FOMC gate fix

---

## What Happened This Session

**Theme:** Close the real data gaps. Three fixes that directly improve gate accuracy.

### Backend Changes
| Change | File | Impact |
|--------|------|--------|
| `_days_until_next_fomc()` helper | `analyze_service.py` | FOMC gate now real (was 999) |
| `FOMC_DATES` imported | `analyze_service.py` | STA offline → constants fallback |
| `_seed_iv_for_ticker()` extracted | `app.py` | Shared helper for single + batch seeding |
| `POST /api/admin/seed-iv/all` | `app.py` | Batch IV seeding for all 15 ETFs |
| `seed_iv_nightly.sh` | project root | Cron-ready shell script |

### Frontend Changes
| Change | File | Impact |
|--------|------|--------|
| `↓ Seed IV` button | `App.jsx` | Manual IV seeding from UI |
| Strike zone label overlap fixed | `TradeExplainer.jsx` | Labels in clean key table, not chart |
| Passed gates now visible | `MasterVerdict.jsx` | Green chip row: "✓ Passed: DTE · IVR ..." |

### Data
- 7,492 IV rows seeded into `iv_history.db` across 20 tickers
- All 15 ETFs now have 365–443 days of IBKR daily IV history
- IVR percentile gate is now reliable from day 1

### Research
- `docs/Research/Data_Strategy_Day26.md` created — 3-option data plan (Nightly IB pull, Tradier, EODHD)
- Tradier API reviewed: Lite (free) account gives full options data API with OI, volume, Greeks
- EODHD tested: free tier paywalls options endpoint — verify format before paying

---

## Build Health
- Backend: **import clean** — no errors
- Frontend: **Compiled successfully** — zero warnings
- Tests: **27 passing** (unchanged)
- FOMC check: `_days_until_next_fomc()` returns 16 (May 6) ✅

---

## Open Issues
- **KI-067** (MEDIUM): QQQ sell_put ITM strikes — not addressed
- **KI-075** (MEDIUM): GateExplainer GATE_KB drift — scheduled for Day 27 audit
- **KI-044** (MEDIUM): API_CONTRACTS.md — partially updated, ETF fields still stale

---

## Next Session (Day 27) Priorities

1. **P0 — Run MASTER_AUDIT_FRAMEWORK** (all 9 categories) — user confirmed this is Day 27 start
2. **P1 — Tradier integration** — open Lite account, wire OI/volume into Liquidity gate, fix last data gap
3. **P2 — KI-067** QQQ sell_put ITM strike fix
4. **P3 — KI-044** API_CONTRACTS.md full sync (ETF-only fields, remove POST /api/orders/stage)
