# Project Status — Day 46 (May 7, 2026)
> **Version:** v0.30.1
> **Tests:** 36 (unchanged)

---

## What Shipped

### KI-086 CLOSED — sta_service.py extracted (Rule 4 compliance)
**Root cause:** `sta_fetch` route had 74 lines of inline STA HTTP calls + SPY 200SMA/5d computation directly in app.py. `_run_one` had already been extracted on Day 39 (docs stale).
**Fix:** `backend/sta_service.py` created with `fetch_sta_swing_data(symbol)`. Route reduced to 2 lines. Removed unused `import requests as _requests`. app.py: 472 → 402 lines.
**Verification:** 36 tests pass. `/api/integrate/sta-fetch/QQQ` behavior unchanged.

### ETF sell_call DTE gate fix — _run_etf_sell_call (pre-existing bug)
**Root cause:** ETF sell_call/bear_call_spread was routing through `_run_sell_call()` (stock function) which uses `DTE_REC_HIGH_SIGNAL=21` as the pass ceiling. DTE=22 was showing "Tradable, but slower decay" (stock message) — wrong constants for ETF track.
**Fix:** Created `_run_etf_sell_call()` per Rule 5 (new function, no modification to `_run_sell_call`). Uses `ETF_DTE_SELLER_PASS_MIN/MAX`. Updated routing: ETF sell_call → `_run_etf_sell_call()`.
**Verification:** XLF bear_call_spread DTE=22 now shows `[warn] DTE (Seller) — Below ETF entry floor (30 DTE) — gamma risk elevated`.

### DTE calibration hardened — ETF_DTE_SELLER_PASS_MIN 21→30
**Research basis:** tastylive 200k+ credit spread trade analysis (daystoexpiry.com synthesis). Opening at 21 DTE enters gamma acceleration zone (4-10x daily decay, amplified delta risk). The 45→21 DTE window captures 46% of profit at 2x higher Sharpe ratio. 21 DTE = management EXIT rule, not entry floor.
**Fix:** `constants.py` — `ETF_DTE_SELLER_PASS_MIN = 30`. Applies to both sell_put (`_run_etf_sell_put`) and sell_call (`_run_etf_sell_call`).
**Trade-off:** Today's XLF/XLV at DTE=22 now get DTE warn (was pass). This is the correct call per research.

### Category 10 Live Research — Phase7c_Trading_Effectiveness_Day46.md
**Research run:** Live Best Setups scan + detailed gate analysis on XLF and XLV.
**Key findings:**
- Check 10.1: 2/11 CAUTION today (below 3-6 target). Dominant blocker = Liquidity Proxy (bid-ask >20%), NOT vol miscalibration. Vol gates all PASS at VIX=17.39.
- Check 10.2: "Always one direction" principle MET — XLF + QQQ surface CAUTION.
- Check 10.3: DTE gap found → fixed (ETF_DTE_SELLER_PASS_MIN 21→30).
- Check 10.4: Weekly gate pass rate log started. Paper trade log not yet running. Adversarial LLM prompt defined.
- Check 10.5: McMillan Stress Check firing correctly (XLF short call inside 1-sigma).

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (DEFERRED) | Single-stock bear tracks untested — ETF-only mode (400) |

---

## Next Session Priorities (Day 47)

| Priority | Issue | Effort |
|----------|-------|--------|
| P0 | README full rewrite — KI-086 closed, KI-059 deferred = all code issues done. Conditions met. | 45 min |
| P1 | Adversarial LLM review: paste XLF/QQQ setup to ChatGPT (Check 10.4 method b) | 15 min |
| P2 | Start paper trade logging (Check 10.4 method a — need 30 trades for win rate) | ongoing |
| P3 | MASTER_AUDIT_FRAMEWORK weekly sweep (skip until Day 49+) | — |
| P4 | Phase 7c cyclical vs defensive split (needs Weakening cyclicals in ANALYZE mode) | deferred |
