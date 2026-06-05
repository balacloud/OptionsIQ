# Project Status — Day 67 (Jun 6, 2026)
> **Version:** v0.35.9
> **Session type:** Research synthesis + skill enhancement

---

## What Shipped

### 3-Model Peer Review Synthesis
External review complete. Perplexity (Q1 thresholds), Gemini (Q2 expected move), ChatGPT (Q2+Q3 missing gates). All findings saved to `docs/Research/Peer_Review_Gate_Logic_Day66.md`.

Key verdicts:
- IVR 35 → raise to 40, WARN band 35–40% (HIGH — implement Day 68)
- TQQQ structural incompatibility — CRITICAL — needs separate thresholds in `_tqqq_satellite_gate()` (Day 68)
- Expected move gate: use distance ratio not log-normal; "POP <50% inside 1-SD" framing was wrong (HIGH — Day 68)
- GLD skew inverted: calls get bid above puts during gold rallies — add flag to `skew_flow` gate (MEDIUM)
- VIX 40 block: CONFIRMED, no change
- Bid-ask 20% too loose for SPY/QQQ: LOW, defer (data-available but low impact)

### chartreview.md — Blended Skill (3-in-1)
`skills/chartreview.md` rewritten to combine chartreview + catalyst-check + direction verdict:

**Input:** TradingView screenshot + pasted SCAN CONTEXT from /ibkr-scan
**Output (single /chartreview call):**
1. CHART REVIEW — full technical analysis (EMA, S/R, verdict per direction)
2. CATALYST CHECK — FOMC/CPI/NFP/earnings in window, live search, strike survival
3. DIRECTION VERDICT — all 4 directions scored (0–6), winner selected with edge + risk summary

**Scoring system:**
- Chart fit (BLOCK=0, WAIT=1, GO=2)
- IV fit: IVR>40+IV_HV>1.05 → sellers 2 / buyers 0; IVR<30 → buyers 2 / sellers 0; P/C>1.5 → sell_put IV=0
- Catalyst fit: sellers (clean=2, caution=1, abort=0); buyers (catalyst in window=2, clean=1, wrong-dir=0)

**3 machine blocks emitted:**
- `CHART CONTEXT` — for OptionsIQ
- `CATALYST CONTEXT` — for OptionsIQ
- `DIRECTION_WINNER` — ticker, winner direction, score/6

**Morning workflow is now 2 steps, not 3:**
```
Step 1: /ibkr-scan                     → SCAN CONTEXT
Step 2: /chartreview (screenshot +     → CHART REVIEW + CATALYST CHECK
         paste SCAN CONTEXT)             + DIRECTION VERDICT
```

Catalyst-check.md remains unchanged as standalone skill.

---

## Test Count
**100 tests** — no backend changes this session.

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

## Next Session Priorities (Day 68)

### P0 — Live end-to-end test with blended /chartreview
Run morning workflow: /ibkr-scan → /chartreview (new blended skill, paste screenshot + SCAN CONTEXT) → paste 3 context blocks into OptionsIQ → verify direction verdict matches backend recommendation.

### P1 — IVR 35→40 + WARN band
`constants.py`: IVR_SELLER_PASS_MIN=40, add IVR_SELLER_WARN_MIN=35. `gate_engine.py`: sell_put/sell_call ivr gate emits WARN for 35-40 range. ~15 lines.

### P2 — Expected move distance ratio gate
`analyze_service.py`: `_add_em_check()` on each strategy post-ranking. distance_ratio = (underlying - strike) / expected_move_1sd. Thresholds: <0.50 STRONG WARN, <0.75 WARN, ≥0.75 PASS. Add EM_WARN_STRONG=0.50, EM_WARN=0.75 to constants.py. ~20 lines.

### P3 — TQQQ separate thresholds in _tqqq_satellite_gate()
Add: IVR > 50 required (WARN if 40-50), VRP > 1.15 required (WARN if 1.05-1.15), skew heavy WARN at 8pts (not 10). ~15 lines.

### P4 — GLD IV/HV tenor audit
Read gate_engine.py `_etf_hv_iv_seller_gate()` — verify which HV and IV tenors are compared. Document in GATE_REFERENCE.md. No code change unless mixed tenors confirmed.
