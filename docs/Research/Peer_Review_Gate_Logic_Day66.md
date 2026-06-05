# External Peer Review — OptionsIQ Gate Logic
> **Day 66 (Jun 5, 2026)**
> **Purpose:** Multi-LLM review of gate thresholds and missing gates, after Marcus Webb internal review
> **Context:** Marcus Webb review → 2 gates downgraded (ivr_seller, market_regime_seller). Hard blocks: sell_put 9→6, sell_call 7→5.
> **Rule 19:** Research session → results go back here as findings per model.

---

## What we already know (don't re-derive)

- `trend_ema` (200 EMA hard block for sellers) — CONFIRMED correct, keep
- `hv_iv_vrp` (VRP gate, GLD hard block) — CONFIRMED correct, keep
- `events` (FOMC block for XLF/XLRE/TQQQ) — CONFIRMED correct, keep
- `liquidity` (20% spread block) — CONFIRMED correct, keep
- `ivr_seller` — DOWNGRADED to WARN (double-gatekeeping with pre-filter scan)
- `market_regime_seller` — DOWNGRADED to WARN (trend_ema owns structural case)

---

## The 3 questions for peer review

### Q1 — Are the threshold numbers right for ETF options specifically?

We're trading 6 ETFs only: **QQQ, IWM, XLF, GLD, TQQQ, SPY** (SPY regime-anchor only).

Current thresholds:
- IVR seller pass: **35%** (tastylive: IVR > 35 = elevated premium)
- IVR buyer pass: **30%** (IVR < 30 = cheap IV)
- VIX crisis block: **40** (tastylive 21-year study)
- VIX low warn: **15** (thin premium)
- GLD IV/HV hard block: **< 1.10** (gold options need stronger VRP)
- Non-GLD VRP warn: **< 1.05** (Sinclair minimum)
- Skew elevated warn: **7 pts** (30-delta put/call IV spread)
- Skew heavy warn: **10 pts**
- DTE seller sweet spot: **30–45 days** (tastylive)
- DTE buyer sweet spot: **45–90 days**
- Bid-ask spread block: **> 20%**

**Ask each model:** "For a systematic ETF options seller trading QQQ, IWM, XLF, GLD, and TQQQ — are these thresholds correct? Which would you change and why? Reference specific academic or empirical sources."

---

### Q2 — Is the missing 'expected move' gate the right addition?

Marcus Webb flagged: when a short put strike is **inside the 1-SD expected move**, probability of profit is below 50%. We display expected_move per strategy but don't gate on it.

Proposed gate:
```
expected_move_1sd = IV × underlying × sqrt(DTE/365)
if short_strike > (underlying - expected_move_1sd):
    WARN: "Strike inside 1-SD expected move — POP < 50%"
```

**Ask each model:** "Is strike-vs-expected-move the right gate to add? How do professional options desks actually use expected move in pre-trade screening? Is there a better formulation?"

---

### Q3 — What are we not checking that a professional ETF options desk would check?

Current gate inventory (all WARN unless noted):
- IVR environment, VRP (IV/HV), VIX regime
- 200 EMA trend (HARD BLOCK for sellers)
- FOMC calendar (HARD BLOCK rate-sensitive within 14d)
- ETF holdings earnings, event density
- Strike OTM check, DTE window
- Bid-ask liquidity (HARD BLOCK > 20%)
- McMillan historical stress
- Put/call sentiment ratio
- 30-delta IV skew (institutional flow)
- Position sizing

**Ask each model:** "What are the top 3 things a professional ETF options desk checks before entering a short-premium position that are NOT in this list? Focus on signals that are computable from publicly available data (options chain, price history, macro calendar)."

---

## Where to paste these prompts

### Perplexity (academic / research citations)
Best for: Q1 (threshold calibration) — Perplexity will cite Sinclair, Natenberg, tastylive research papers.

Paste prompt for Q1 with the threshold list. Ask for academic sources.

### ChatGPT-4o (practical trading review)
Best for: Q3 (what's missing) — GPT-4o tends to give practitioner-level answers with real trading context.

Paste prompt for Q3 with the full gate inventory. Ask "what would a professional desk check that isn't here?"

### Gemini (quantitative challenge)
Best for: Q2 (expected move gate formulation) — Gemini is strong on math and options pricing theory.

Paste prompt for Q2 with the proposed gate formula. Ask for a better formulation if one exists.

---

## How to run

1. Copy each question block + context above into the relevant model
2. Paste results back into this file under "Findings" below
3. Synthesize into action items at the bottom
4. Per Rule 19: session close creates final research doc

---

## Findings

*(paste model responses here)*

### Perplexity — Q1: Threshold calibration
```
[paste response]
```

### ChatGPT — Q3: What's missing
```
[paste response]
```

### Gemini — Q2: Expected move gate
```
[paste response]
```

---

## Synthesis (fill after all 3 responses)

| Finding | Source | Action |
|---------|--------|--------|
| | | |

---

## Context to paste with every prompt

> "OptionsIQ is a personal options analysis tool for trading 6 ETFs: QQQ, IWM, XLF, GLD, TQQQ (and SPY as regime anchor). It's a short-premium, single-leg, systematic approach — sell_put or sell_call based on pre-scan signals from IBKR. The system runs a pre-trade gate engine before recommending strikes. I'm reviewing whether the gates and thresholds are correct."
