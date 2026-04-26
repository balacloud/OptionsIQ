# OptionsIQ — Project Status Day 28
> **Date:** April 22–26, 2026
> **Version:** v0.20.0
> **Session type:** Gate robustness — ChatGPT stress-test driven fixes

---

## What Shipped Today

### KI-079 RESOLVED — ETF Holdings Earnings Gate
ChatGPT stress test on XLY caught: TSLA (18%) + AMZN (25%) both report before expiry but gate said "no conflict."
- `constants.py` — added `ETF_KEY_HOLDINGS` dict (16 ETFs → top moveable holdings) + `COMPANY_EARNINGS` dict (52 companies, Q2–Q4 2026 dates)
- `analyze_service.py` — new `_etf_holdings_at_risk()` helper: returns holdings reporting before option expiry
- `gate_engine.py` — new `_etf_holdings_earnings_gate()`: warns when any key holding reports inside DTE window
- Wired into all 4 ETF direction tracks (buy_call, buy_put, sell_put, sell_call)
- Verified live: XLK/May22 → AMD (6d), MSFT (7d), AAPL (9d) all correctly flagged; XLY/May22 → TSLA (0d), AMZN (7d), MCD (7d), HD (21d)

### KI-080 RESOLVED — Liquidity Gate Hard-Fail on Extreme Spread
XLY analysis had 27.52% bid-ask → delta was -0.046 for near-ATM put (should be ~-0.45) → strategy selected ATM instead of OTM. Root cause: `apply_etf_gate_adjustments()` was unconditionally downgrading all ETF spread-fails to warn + blocking=False.
- `constants.py` — added `SPREAD_DATA_FAIL_PCT = 20.0`
- `gate_engine.py` — `_liquidity_gate()` now exposes raw `spread_pct` on gate dict
- `analyze_service.py` — only downgrades to warn when `spread_pct ≤ 20%`; above 20% keeps `blocking=True` with "data unreliable" reason
- Tests: 27 → 29 (2 new: spread 15% → warn, spread 27% → blocking fail)

### FOMC Gate Logic Fix
Root cause: `_etf_fomc_gate()` only warned when `5 ≤ fomc_days ≤ 10`. If FOMC was 20 days away but DTE was 30, the gate passed silently. ChatGPT caught this on XLK sell_put (FOMC April 29, DTE 30).
- Now warns whenever `fomc_days < dte` (FOMC before option expiry) regardless of absolute proximity
- Reason string shows both FOMC days and DTE for transparency
- Verified: FOMC 7d/DTE 30 → warn, FOMC 20d/DTE 30 → warn, FOMC 35d/DTE 30 → pass

### KI-082 Logged — Credit-to-Width Ratio Gate
Two separate ChatGPT stress tests caught: $0.05 credit on $1-wide XLK spread (5% of width), $0.32 on $1-wide XLY spread (32%). Industry minimum is ~20% of width. No gate exists for this. Logged as MEDIUM. Fix path in KNOWN_ISSUES_DAY28.md.

---

## Pre-Analysis Prompts in UI — Day 29 Candidate

Currently the pre-trade research workflow requires the user to:
1. Go to `docs/Research/Daily_Trade_Prompts.md`
2. Copy Prompt 1 (macro regime) → Perplexity
3. Copy Prompt 2 (sector setup) → ChatGPT
4. Then run OptionsIQ
5. Then use CopyForChatGPT button for post-analysis stress test

**Proposed improvement:** Show Prompts 1–2 directly in the OptionsIQ UI as a "Pre-Analysis" panel with copy buttons, pre-filled with today's date and selected ETF. Completes the full loop: pre-research → analysis → post-stress test — all without leaving the app. Low-effort frontend addition, high workflow friction reduction.

---

## Real-World Validation (Day 28)

Two ChatGPT stress tests on live trades:
1. **XLK sell_put (May 22 expiry)** — GPT caught: FOMC April 29 inside holding window, AAPL + MSFT reporting inside DTE, $0.05 credit on $1-wide spread too weak. All 3 points now addressed (FOMC gate fixed, KI-079 fixed, KI-082 logged).
2. **XLY sell_put (May 22 expiry)** — confirmed same issues. Post-fix: TSLA (0d), AMZN (7d) flagged correctly; FOMC warns. Credit-to-width still not gated (KI-082 next).

---

## Current System Health

| Area | Status |
|------|--------|
| IBKR live data | Working — account U11574928 |
| IV seeding | 7,492 rows across all 16 ETFs (seeded Day 26) |
| OI/volume | MarketData.app supplement wired (Day 27) |
| Gate engine | Holdings earnings gate live. FOMC window gate fixed. Spread hard-block live. |
| P&L table | All 6 strategy types handled correctly |
| Tests | 29 passing |
| Pre-trade workflow | CopyForChatGPT + Daily_Trade_Prompts.md |
| Audit health | 0 Critical, 1 High (KI-059 deferred), 6 Medium |

---

## Next Session Priorities

### P0 — Pre-Analysis Prompts in UI (Day 29 candidate)
Show Prompts 1–2 from Daily_Trade_Prompts.md in a "Pre-Analysis" panel inside the app. Pre-fill with ticker and date. Copy buttons. Completes the full research loop without leaving OptionsIQ.

### P1 — Paper Trade P&L Dashboard
Backend: `GET /api/options/paper-trades/summary` — win rate by verdict, direction, ETF.
Frontend: Dashboard tab — equity curve, win rate by GO/WAIT/BLOCK. Converts paper trade history into evidence-based confidence for real money.

### P2 — Credit-to-Width Ratio Gate (KI-082)
Add `MIN_CREDIT_WIDTH_RATIO = 0.20` to constants. Gate fails sell_put/sell_call when credit < 20% of spread width. Requires strategy_ranker to pass spread_width and credit_received to gate_payload.

### P3 — Daily Best Setups Page
Auto-scan → surface top 2-3 setups in one view. One button: "Refresh setups."

### Deferred
- KI-067: QQQ sell_put ITM strike fix
- KI-081: CPI/NFP macro events calendar (LOW)
- KI-077: DirectionGuide sell_put "capped" label (LOW)
