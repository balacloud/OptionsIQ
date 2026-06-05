# Project Status — Day 66 (Jun 5, 2026)
> **Version:** v0.35.8
> **Session type:** Gate philosophy + skew gate + Marcus Webb review + Pine Script fix

---

## What Shipped

### Skew Flow Gate (institutional flow signal)
- `backend/gate_engine.py` — `_skew_flow_gate()` added. Advisory WARN only (Rule 23).
  - sell_put: skew >= 7 pts → WARN; >= 10 pts → strong WARN
  - sell_call: skew <= 2 pts → WARN (call momentum / squeeze risk)
- `backend/constants.py` — SKEW_PUT_WARN_PTS=7.0, SKEW_PUT_STRONG_PTS=10.0, SKEW_CALL_WARN_PTS=2.0
- `backend/analyze_service.py` — compute_skew() moved BEFORE engine.run(), skew_value added to gate_payload
- `backend/tests/test_skew_gate.py` — 7 new tests (93→100 total)
- `frontend/src/components/LearnTab.jsx` — skew_flow GATE_KB entry added

### Marcus Webb Gate Review — 2 gates downgraded
- `ivr_seller` (sell_put + sell_call) → WARN only. Was blocking when IVR < 25%. Reason: double-gatekeeping with /ibkr-scan pre-filter (Rule 23).
- `market_regime_seller` (sell_put) → WARN only. Was blocking when SPY strongly down. Reason: trend_ema gate owns structural case; already WARN for sell_call — asymmetry unjustified.
- **Result:** sell_put hard blocks: 9→6. sell_call hard blocks: 7→5.
- Remaining 6 hard blocks are all immutable laws: trend_ema, FOMC rate-sensitive, GLD VRP, liquidity >20%, VIX >40, strike_otm.

### New Stable Docs
- `docs/stable/GATE_REFERENCE.md` — complete gate inventory: all 4 directions, thresholds, block vs warn, Rule 23 review candidates
- `docs/stable/QUANT_PERSONA.md` — Marcus Webb persona (30-year ETF options trader) for adversarial gate review

### New Research Docs
- `docs/Research/Marcus_Webb_Gate_Review_Day66.md` — gate-by-gate verdicts: KEEP/DOWNGRADE/REMOVE/MISSING
- `docs/Research/Peer_Review_Gate_Logic_Day66.md` — 3 questions ready for Perplexity/ChatGPT/Gemini

### Pine Script Fixed + Enhanced
- `tradingview/OptionsIQ_ChartReview.pine` — upgraded to v6, pure ASCII (zero non-ASCII bytes), direction-aware gate verdicts section (sell_put/sell_call/buy_call/buy_put [GO]/[WARN]/[BLOCK]), volume vs 20-day average row added.
- /chartreview skill tested live on QQQ — dashboard read correctly, CHART CONTEXT generated.

---

## Test Count
**100 tests** (was 93, +7 new: test_skew_gate.py)

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear untested — ETF-only going forward |
| KI-099 | LOW | buy_call for Leading/Improving ETFs — single-leg only, deferred |

---

## Audit Health
**0 CRITICAL / 0 HIGH / 0 MEDIUM** — Safe to paper trade.

---

## Next Session Priorities (Day 67)

### P0 — Live end-to-end test with all 3 contexts
Run a real morning scan: /ibkr-scan → /chartreview (paste screenshot) → /catalyst-check → paste all 3 contexts into OptionsIQ → verify strike_vs_support and catalyst_overlay display correctly in TopThreeCards.

### P1 — External peer review (bring back results)
Paste prompts from `docs/Research/Peer_Review_Gate_Logic_Day66.md` to Perplexity (Q1 thresholds), ChatGPT (Q3 missing gates), Gemini (Q2 expected move gate). Bring results back and synthesize.

### P2 — Add expected_move_check gate (Marcus MISSING gate #1)
Strike vs 1-SD expected move → WARN if short strike is inside expected move ("POP < 50%"). ~20 lines in gate_engine.py, already have expected_move_1sd in analyze response.

### P3 — Frontend redesign
Warnings-only gate display (hide PASS gates by default), one trade per screen, cleaner aesthetic.

### P4 — DTE-event routing
Surface "expiry exits before FOMC" vs "expiry holds through FOMC" at DTE gate level, not just in catalyst_overlay per-strategy.
