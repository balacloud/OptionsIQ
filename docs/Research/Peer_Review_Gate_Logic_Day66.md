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

## Findings — Day 67 (Jun 6, 2026)

### Perplexity — Q1: Threshold calibration

**IVR seller pass 35% → ADJUST to 40–45%.** Tastylive's IVR > 35 is their minimum baseline, not optimized for systematic ETF-only sellers. A 4-year SPY analysis found elevated-IVR environments (filtered at higher cutoffs) produced materially better P/L per day. Tastylive's 2018 IVR-DTE interaction study showed best risk-adjusted outcomes at IVR > 40 using 30 DTE. Recommendation: raise hard pass to IVR > 40, retain WARN band 35–40%.

**VIX crisis block 40 → CONFIRM.** Tastylive 21-year study: VIX > 38 occurred only 3.4% of the time since 1995. Setting block at 40 adds buffer against false positives. No change needed.

**GLD IV/HV block 1.10 → CLARIFY tenor.** 1.10x ratio is directionally correct — GLD IV mean-reverts slowly and skew inverts during rallies (call demand surges). Critical question: which IV tenor vs which HV tenor? Current live data shows GLD 20-day HV ~22.6% vs IV ~20.8% = ratio 0.92, which would trigger hard block. Standard: 30-day IV / 20-day HV ≥ 1.10. Accept that GLD frequently fails this gate in trending low-vol gold regimes.

**TQQQ → CRITICAL STRUCTURAL WARNING.** TQQQ options cannot share the same IVR/VRP/DTE thresholds as non-leveraged ETFs. Specific risks: (1) IVR structurally appears elevated more often than QQQ even in identical conditions; (2) a "normal" VRP of 1.05x on TQQQ masks compressed real edge; (3) skew of 7-10 pts is qualitatively different from SPY/QQQ; (4) DTE 30-45 carries substantially higher gamma/gap risk. Recommendation: TQQQ-specific thresholds (IVR > 50%, VRP > 1.15, DTE floor 35, skew heavy at 8 pts).

**GLD skew interpretation inverted.** GLD skew goes NEGATIVE during gold rallies (calls get bid above puts). A skew WARN based on put richness misses the elevated-risk regime for GLD call-sellers. Separate GLD-specific skew gate warranted.

**DTE ↔ IVR co-dependence.** Tastylive finding: IVR > 40 warrants 30 DTE; IVR < 30 warrants 60 DTE. Static DTE gate should be co-dependent with IVR level (MEDIUM priority).

---

### Gemini — Q2: Expected move gate

**Drop the log-normal formula. Use delta proxy.** The standard formula (S × σ × √(DTE/365)) assumes symmetrical distribution — equities have significant downside skew. It also assumes constant volatility and ignores the smile. Professional desks use two methods:

**Method 1 — Delta Proxy (most efficient):** A 1-SD move covers ~68.2% of occurrences, leaving ~15.9% on each side. A 16-delta option represents the 1-SD boundary. Because market makers price skew into delta, a 16-delta put is naturally further OTM than a 16-delta call on QQQ. Gate: `if abs(short_leg_delta) > 0.16: WARN "Strike inside 1-SD expected move"`.

**Method 2 — Straddle approximation:** `expected_move_1sd = (atm_call_ask + atm_put_ask) × 0.85`. ATM straddle directly prices the 1-SD expected move with skew embedded.

**Gemini verdict for OptionsIQ:** Use delta proxy. Delta already flows through the system. Gating at abs(delta) > 0.16 automatically accounts for the volatility smile and downside skew.

---

### ChatGPT — Q2+Q3: Expected move gate + what's missing

**Critical correction on expected move framing:** "Inside 1-SD = POP < 50%" is WRONG. A 1-SD range = 68% confidence. At the 1-SD strike, POP is still ~84% OTM. The real risk is margin of safety and gamma exposure, not probability crossing 50%. Gate should be framed as strike proximity, not POP.

**Better formulation — distance ratio:**
```python
em_1sd = expiry_iv * forward_price * sqrt(dte / 365)
distance_ratio = (forward_price - short_put_strike) / em_1sd  # sell_put

# Tiers:
# < 0      → HARD BLOCK (strike ITM)
# 0–0.35x  → STRONG WARN (too close, high gamma risk)
# 0.35–0.75x → WARN (inside preferred buffer)
# 0.75–1.25x → PASS
# > 1.25x  → PASS + warn low credit
```

**Top 3 missing professional gates:**

1. **Delta / probability ITM gate** — target 0.15–0.30 delta for short options; WARN > 0.35; HARD BLOCK > 0.45. More precise than "OTM check."

2. **Term-structure / front-vol stress gate** — WARN if front IV > back IV by > 10–15%, or if VIX9D > VIX > VIX3M stress stack. Data source needed (VIX9D not currently pulled).

3. **Portfolio-level beta/gamma concentration gate** — selling QQQ + IWM + TQQQ simultaneously = one correlated equity-vol bet. SPY beta-weighted delta + max loss under -3/-5/-8% gap. Not currently tracked.

**Bid-ask 20% too loose for liquid ETFs:** SPY/QQQ should block > 10–12%; IWM/GLD/XLF > 15%; TQQQ max 20%.

---

## Synthesis

| Finding | Source | Priority | Action |
|---------|--------|----------|--------|
| Raise IVR seller pass 35% → 40%, WARN band 35–40% | Perplexity | HIGH | `constants.py` IVR_SELLER_PASS_MIN=40, add IVR_SELLER_WARN_MIN=35 |
| GLD IV/HV tenor — standardize 30d IV / 20d HV | Perplexity | HIGH | Audit gate_engine.py, document in GATE_REFERENCE.md |
| TQQQ separate thresholds (IVR>50, VRP>1.15, skew 8pts) | Perplexity | CRITICAL | Add to `_tqqq_satellite_gate()` |
| Expected move gate — use distance ratio, not formula | Gemini + ChatGPT | HIGH | Add `_add_em_check()` in analyze_service.py |
| "POP <50% inside 1-SD" framing is WRONG | ChatGPT | HIGH | Fix gate message: "high gamma risk" not "POP <50%" |
| GLD skew inverted — calls > puts during gold rallies | Perplexity | MEDIUM | Flag in `skew_flow` gate when GLD call IV > put IV |
| DTE ↔ IVR co-dependence | Perplexity | MEDIUM | Defer — requires IVR-conditional DTE logic |
| VIX 40 block — CONFIRMED | All models | — | No action |
| Bid-ask 20% too loose for SPY/QQQ | ChatGPT | LOW | Defer — ticker-specific tiers not in scope yet |
| Term-structure stress gate (VIX9D) | ChatGPT | LOW | Defer — VIX9D not currently available |
| Portfolio beta/gamma concentration gate | ChatGPT | LOW | Defer — no portfolio tracking in system |

---

## Context to paste with every prompt

> "OptionsIQ is a personal options analysis tool for trading 6 ETFs: QQQ, IWM, XLF, GLD, TQQQ (and SPY as regime anchor). It's a short-premium, single-leg, systematic approach — sell_put or sell_call based on pre-scan signals from IBKR. The system runs a pre-trade gate engine before recommending strikes. I'm reviewing whether the gates and thresholds are correct."
