# Phase 7c — Trading Effectiveness Research
> **Started:** Day 46 (2026-05-07) | **Last updated:** Day 49 (2026-05-08)
> **Framework:** MASTER_AUDIT_FRAMEWORK v1.4, Category 10

---

## Check 10.1 — Gate Pass Rate

### Live Scan (Day 46, 2026-05-07T14:21Z)

**VIX:** 17.39 | **SPY regime:** Above 200SMA (bull) | **Candidates:** 11/15 ETFs

| ETF | Direction | Verdict | Pass% | Blocking Gate |
|-----|-----------|---------|-------|---------------|
| XLF | bear_call_spread | CAUTION | 64% | None blocking |
| QQQ | sell_put | CAUTION | 55% | None blocking |
| XLK | sell_put | BLOCKED | 64% | Liquidity Proxy (spread >20%) |
| XLV | bear_call_spread | BLOCKED | 64% | Liquidity Proxy (spread 39.2%) |
| MDY | bear_call_spread | BLOCKED | 64% | Liquidity Proxy |
| XLI | bear_call_spread | BLOCKED | 55% | Vol Risk Premium + Liquidity Proxy |
| XLY | bear_call_spread | BLOCKED | 55% | Liquidity Proxy |
| XLC | bear_call_spread | BLOCKED | 55% | Liquidity Proxy |
| XLP | bear_call_spread | BLOCKED | 55% | Liquidity Proxy |
| XLB | bear_call_spread | BLOCKED | 45% | Vol Risk Premium + Liquidity Proxy |
| IWM | bull_call_spread | BLOCKED | 22% | HV/IV Ratio + Theta Burn + Liquidity Proxy |

**Result: 2/11 actionable (CAUTION). Target = 3-6. Currently BELOW target.**

### Root Cause — The Liquidity Tier Problem

All volatility gates PASSED (verified on XLV): IV Rank, Vol Risk Premium, VIX Regime, DTE, Earnings. The sole blocker in 9/11 cases is **Liquidity Proxy (bid-ask spread >20%)**.

The 15 ETFs fall into two distinct options liquidity classes:

**Tier 1 — Tight OTM spreads (typically <5% at 0.30 delta):**
QQQ (~3M contracts/day), IWM (~600k), XLF (~500k), XLK (~400k), XLY (~200k)

**Tier 2 — Wide OTM spreads (commonly 10-40% at 0.30 delta):**
XLV, XLI, XLC, XLB, XLP, MDY — lower options volume, market makers need larger edge

The 20% hard-block threshold is correct: a 39% spread on XLV = ~$0.20 edge per contract = $2,000 slippage at 100 contracts before the trade starts.

**Conclusion:** System is NOT over-tuned on volatility parameters. Blocking is correct. Low actionable count reflects genuine market conditions.

### Weekly Gate Pass Rate Log

| Date | Candidates | GO | CAUTION | BLOCKED | Dominant Blocker |
|------|-----------|----|---------|---------|--------------------|
| 2026-05-07 | 11 | 0 | 2 | 9 | Liquidity Proxy (bid-ask >20%) |
| 2026-05-08 | 12 | 0 | TBD | TBD | Run Best Setups scan to complete |

---

## Check 10.2 — Always One Direction

**VIX = 17.39, SPY above 200SMA, 9/15 sectors Lagging.**

- XLF CAUTION (bear_call_spread) ✅
- QQQ CAUTION (sell_put) ✅

**Principle MET.** The system correctly surfaces liquid ETFs (QQQ, XLF) with tight spreads even when sector ETFs are all blocked. Simultaneous all-11-blocked with no liquidity reason = gate miscalibration signal. Today: 9/11 blocked due to Liquidity Proxy = market condition, not calibration problem.

---

## Check 10.3 — DTE Calibration

**Gap found (Day 46) → Fixed (Day 46).**

**Research (tastylive + daystoexpiry.com, 200k+ trades):**
- 45→21 DTE: daily decay 1-2%, Sharpe ~2x higher (stable gamma) — captures ~46% of max profit
- 21→0 DTE: daily decay 4-10%, gamma risk 4-5x higher
- Tastylive "close at 21 DTE" = management EXIT rule, not entry floor
- Opening AT 21 DTE = entering gamma acceleration zone immediately, foregoing all high-Sharpe theta

**Fix:** `ETF_DTE_SELLER_PASS_MIN` raised 21 → 30 (Day 46) ✅

---

## Check 10.4 — Unbiased Evaluation

### Method (a): Paper trade log

- Infrastructure: PaperTradeDashboard.jsx live
- Action: Log next XLF or QQQ CAUTION setup
- Target: 30 trades before checking win rate
- Current: **0 trades logged**

### Method (b): Adversarial trade review (monthly — specific setup)

Paste into ChatGPT or Claude Opus with a live setup:

```
Act as an adversarial options risk manager. I am considering selling an XLF bear_call_spread
with strike $57/$58, expiry 22 DTE, credit $0.22, IVR=51, IV/HV=1.53. VIX=17.4, SPY above 200SMA.
List every reason NOT to take this trade, ranked by severity. Be harsh.
```

**Result (Day 48, XLF $57/$58, 22 DTE, $0.22 credit, IVR=51, IV/HV=1.53, VIX=17.4):**

| Severity | Finding |
|----------|---------|
| 1 — Critical | Macro-event cluster: NFP May 8, CPI May 12, FOMC minutes May 20, PCE May 28 — 4 rate-sensitive events within 22 DTE |
| 2 — High | Direction fights tape: SPY above 200SMA + VIX 17 = risk-on. Bear_call_spread on rising financials punishes short calls |
| 3 — Medium | XLF concentration: top 10 holdings = 56% (BRK, JPM, V, MA, BAC). Idiosyncratic event risk higher than ETF label implies |
| Verdict | WAIT — structure acceptable, but event stack + tape make this the wrong window |

**Gaps found:**
1. **Event density:** System uses single-next-event logic (`_days_until_next_macro()`). Adversarial LLM found 4 events in 22 DTE. Gate should count events-in-window, not just proximity to next event.
2. **Absolute trend:** System maps Lagging quadrant → bear_call_spread using RS ratio only. A sector can be Lagging vs SPY while rising in absolute terms (tape-fighting). `weekChange` is already in the STA response but unused by `quadrant_to_direction()`.

### Method (c): Weekly gate pass rate log

See Check 10.1 table above.

### Method (d): System-level effectiveness audit (monthly — feed README + this file as context)

> **Setup:** Paste `README.md` + this file into ChatGPT or Claude Opus, then ask each prompt below.
> These audit the *system design*, not a single trade.

**Prompt D1 — Direction logic / tape-fighting:**
```
You are an adversarial quant reviewing an options signal system.
The system maps sector RS-Momentum quadrants to options directions:
  Lagging (RS<100, RS-Mom<0) → bear_call_spread if rs_ratio < 98 AND rs_momentum < -0.5
The RS ratio is normalized to 100 at the midpoint of a 6-month window.
Problem: a sector can be "Lagging" (underperforming SPY relatively) while rising in absolute
terms in a broad bull market. SPY above 200SMA + VIX 17 = risk-on.
Q: Does this direction logic recommend bear_call_spread on sectors that are rising in
absolute price terms? What gate would you add to prevent tape-fighting directions?
```

**Prompt D2 — Event density:**
```
The system has a macro event gate that checks days-until-NEXT-event (NFP/CPI/PCE/FOMC).
It blocks trades if the next event is within 7 days, warns if within 14 days.
Problem: for a 22 DTE trade, there can be 4 separate macro events within the window
(NFP May 8, CPI May 12, FOMC May 20, PCE May 28).
The single-next-event logic treats "1 event in 22 days" identically to "4 events in 22 days."
Q: What is the right framework for event density risk? At what event count should the gate
escalate from WARN to BLOCK? How should DTE interact with event count?
```

**Prompt D3 — Gate calibration:**
```
An options signal system scans 15 ETFs and currently returns:
  0 GO verdicts, 2-3 CAUTION, 9-12 BLOCKED
Dominant blocker: bid-ask spread >20% on OTM options (liquidity gate).
Secondary blockers: IVR null (no IV history → fails 35% threshold), HV/IV <1.05.
Q: Is a system producing 0 GO verdicts out of 15 ETFs correctly calibrated for a
VIX=17, SPY-above-200SMA environment? What win rate would you expect from CAUTION setups
if the system is well-calibrated? What is the minimum acceptable GO rate per week?
```

**Prompt D4 — Buy vs sell structure:**
```
The system defaults to credit spreads (bear_call_spread, sell_put) when IVR > 35% and IV/HV > 1.05.
It never recommends buy_call unless IVR < 30%. Current market: VIX=17, SPY above 200SMA,
most sectors "Lagging" with IVR null (no history → coerced to 0.0 → fails seller threshold).
Q: In a low-VIX, SPY bull-trend environment with unknown IVR, what options structures
have the highest probability-weighted expected value? Is IVR<30% threshold for buy_call
too restrictive when most IVRs are null/unknown?
```

---

## External Audit — ChatGPT (Day 48, 2026-05-08)

> **Context fed:** README.md + Phase7c_Research.md. All 4 prompts in one conversation.

### Q1 — Direction logic / tape-fighting

**Verdict: Yes — the system recommends bear_call_spread on sectors that are rising in absolute price. Serious blind spot.**

> "The system risks confusing 'not the best sector' with 'safe to short calls.' Relative strength is useful for ranking sectors. It is not enough to choose an options direction by itself."

Key finding: `rs_ratio < 98 AND rs_momentum < -0.5` = relative underperformance only. A sector can be Lagging while SPY+5%, sector+2% — still bullish in absolute terms.

**Recommended gate (minimum viable):**
```
bear_call_spread only if: rs_ratio < 98 AND rs_momentum < -0.5 AND weekChange <= 0
```

**Recommended gate (better):**

| Scenario | Action |
|----------|--------|
| Lagging RS + ETF down on week | bear_call_spread allowed |
| Lagging RS + ETF flat | CAUTION only |
| Lagging RS + ETF up on week | BLOCK bearish direction |
| Lagging RS + ETF up + SPY above 200SMA | HARD BLOCK |
| Lagging RS + SPY below 200SMA | bearish trades more acceptable |

---

### Q2 — Event density

**Verdict: Single-next-event logic is a "beginner-level safety check." Underpowered for credit spreads.**

> "A credit spread is not just exposed to whether the next event is close. It is exposed to the full path of price movement before expiry. Four macro events give the underlying four chances to gap, trend, or reprice."

**Recommended event severity weights:**

| Event | Weight |
|-------|--------|
| FOMC rate decision | 3 |
| CPI | 3 |
| NFP/jobs report | 2 |
| PCE inflation | 2 |
| FOMC minutes | 1–2 |
| Fed Chair speech | 1–2 |

**Escalation table (seller trades):**

| Events in DTE window | DTE 30–45 | DTE 21–29 | Under 21 |
|---------------------|-----------|-----------|---------|
| 0 | PASS | WARN | BLOCK |
| 1 | PASS/WARN | WARN | BLOCK |
| 2 | WARN | BLOCK | BLOCK |
| 3+ rate-sensitive ETF | BLOCK | BLOCK | BLOCK |
| 4+ any | BLOCK | BLOCK | BLOCK |

Rate-sensitive ETFs requiring stricter treatment: XLF, XLRE, XLU, XLE, IWM, QQQ.

---

### Q3 — Gate calibration

**Verdict: 0 GO is not automatically bad. But the system may be a risk-rejection engine, not a trade-selection engine.**

> "The problem may not be that gates are too strict. The problem may be that the direction generator is producing low-quality candidates, which then get blocked downstream."

Key insight: **true tradable universe is ~5 ETFs (Tier 1), not 15.** Tier 2 ETFs will almost always be blocked by liquidity.

**Expected win rate from CAUTION setups (if well-calibrated):**

| Setup type | Expected win rate |
|-----------|------------------|
| GO credit spreads | 65–75% |
| CAUTION credit spreads | 55–65% |
| CAUTION + event density | Below 55% — avoid |
| CAUTION + liquidity warning | Often not worth trading |

**Minimum acceptable GO rate:**

| Weekly GO count | Interpretation |
|-----------------|----------------|
| 0 GO for 1 week | Acceptable |
| 0 GO for 2–3 weeks | Watch closely |
| 0 GO for 4+ weeks | Calibration or universe problem |
| 1–3 GO/week | Healthy for selective system |

**Do not loosen liquidity gates to hit the target — that is fake calibration.**

Also recommended: track GO rate by ETF tier separately. Tier 1 (QQQ/IWM/XLF/XLK/XLY) GO rate is the meaningful metric.

---

### Q4 — Buy vs sell structure

**Verdict: Unknown IVR coerced to 0.0 is a design flaw. Missing data is not low volatility.**

> "The system may be making a false binary: high IVR → sell, low IVR → buy. The correct question is which structure has the best expected value given direction, vol, trend, events, liquidity, and data confidence."

Key findings:
- `IVR null → 0.0 coercion` distorts both buy and sell decisions — should be treated as "unknown confidence", not "low vol"
- `IVR < 30` threshold for buy_call is too restrictive — long calls are acceptable at IVR 30–50 if absolute trend is strong
- Bull call spread is the best structure in low-VIX bull trend (reduces theta/vega vs naked long call)
- Bear call spread in SPY-above-200SMA + VIX-17 environment = fighting the tape

**Recommended 4-step structure selection:**

| Step | Input | Decision |
|------|-------|----------|
| 1 — Market regime | SPY vs 200SMA, VIX level | Bullish/bearish/neutral bias |
| 2 — Sector trend | Quadrant + weekChange (absolute) | Direction allowed or WAIT |
| 3 — Vol valuation | IVR (if known), IV/HV | Debit vs credit structure |
| 4 — Liquidity | bid-ask spread, OI | Trade or no trade |

---

### Priority Fixes (ChatGPT ranking)

| Priority | Fix | Why |
|----------|-----|-----|
| 1 | Absolute trend gate for bear_call_spread | Prevents tape-fighting |
| 2 | Event density gate (events-in-window) | Prevents clustered macro exposure |
| 3 | Stop treating unknown IVR as 0.0 | Missing data ≠ low volatility |
| 4 | Separate Tier 1 tradable universe reporting | Avoid false expectations on 15 ETFs |
| 5 | Add bull_call_spread as preferred low/mid-IV bull structure | Reduce overdependence on credit spreads |
| 6 | Track 30–50 paper trades before claiming effectiveness | Current sample = 0 |
| 7 | Report GO/CAUTION rate by direction and ETF tier | Aggregate rate hides root causes |

> **Final verdict:** "OptionsIQ has a good risk-control foundation, but the biggest weaknesses are decision-context bugs — not math bugs. Relative weakness mistaken for bearishness. Single-event logic mistaken for event-risk control. Missing IVR mistaken for low IVR."

---

## External Audit — Perplexity (Day 49, 2026-05-08)

> **Context fed:** README.md + Phase7c_Research.md. All 4 prompts (D1–D4).

### D1 — Direction logic / tape-fighting

**Verdict: Yes — bear_call_spread recommended on sectors rising in absolute terms. Serious design gap (confirms ChatGPT).**

Key quote: *"RS is a ranking tool, not a directional tool. The Lagging quadrant tells you where to underweight, not where to short."*

**Recommended 3-tier absolute trend filter:**

| Scenario | RS Signal | weekChange | Allowed Action |
|----------|-----------|------------|----------------|
| Lagging + ETF down on week | rs_ratio < 98 | ≤ −0.5% | bear_call_spread — allowed |
| Lagging + ETF flat | rs_ratio < 98 | −0.5% to +0.5% | CAUTION only — no GO |
| Lagging + ETF up on week | rs_ratio < 98 | > +0.5% | BLOCK bearish direction |
| Lagging + ETF up + SPY above 200SMA | both | both rising | **HARD BLOCK** |
| Lagging + SPY below 200SMA | rs_ratio < 98 | any | bearish more acceptable |

**Minimum viable code change:** `weekChange <= 0` required in `quadrant_to_direction()` for `bear_call_spread`. (Perplexity adds optional ±0.5% dead zone; ChatGPT uses simple `<= 0`. Start with `<= 0`.)

---

### D2 — Event density

**Verdict: Single-next-event is a beginner-level safety check — underpowered for any DTE > 14 (confirms ChatGPT). Identical weighted severity model proposed.**

**Weighted event severity:**

| Event | Weight |
|-------|--------|
| FOMC rate decision | 3 |
| CPI | 3 |
| NFP / jobs report | 2 |
| PCE inflation | 2 |
| FOMC minutes | 1–2 |
| Fed Chair speech | 1–2 |

**Escalation table (seller trades):**

| Events in DTE window | Weighted score | DTE 30–45 | DTE 21–29 | Under 21 |
|---------------------|----------------|-----------|-----------|---------|
| 0 events | 0 | PASS | WARN | BLOCK |
| 1 minor | 1–2 | PASS | WARN | BLOCK |
| 1 major (FOMC/CPI) | 3 | WARN | WARN | BLOCK |
| 2+ events | 4–5 | WARN | BLOCK | BLOCK |
| 3+ or score ≥ 6 | 6+ | **BLOCK** | BLOCK | BLOCK |
| 4+ any events | any | **BLOCK** | BLOCK | BLOCK |

Rate-sensitive ETFs (XLF, XLRE, XLU, XLE, IWM, QQQ) escalate one tier earlier.

---

### D3 — Gate calibration

**Verdict: 0 GO is not automatically miscalibration — but the 15-ETF aggregate metric is misleading (confirms ChatGPT).**

Key insight: effective tradable universe = ~5 Tier 1 ETFs. Tier 2 ETFs are structurally blocked by liquidity in most conditions. The right metric is Tier 1 GO rate.

**Healthy target ranges (confirmed by both audits):**

| Weekly GO count (Tier 1 only) | Interpretation |
|-------------------------------|----------------|
| 0 GO for 1 week | Acceptable |
| 0 GO for 2–3 weeks | Watch |
| 0 GO for 4+ weeks | Calibration or universe problem |
| 1–3 GO/week | Healthy target |
| 4–5 GO/week consistently | Suspiciously loose |

**Expected win rates (calibrated system):**

| Setup type | Expected win rate |
|-----------|------------------|
| GO credit spreads | 65–75% |
| CAUTION credit spreads | 55–65% |
| CAUTION + clustered macro | Below 55% — avoid |
| CAUTION + liquidity warn | Often not worth slippage |

Do NOT loosen the 20% bid-ask block to hit a GO target — a 39% spread means ~$2,000 slippage per 100 contracts before the trade starts.

---

### D4 — Buy vs sell structure

**Verdict: IVR null → 0.0 is a design flaw (confirms ChatGPT). Missing data ≠ low volatility.**

Key insight: IVR null ETFs fall into a dead zone — fail seller threshold (IVR < 35%), fall through to buyer path, but buyer path blocked by tape-fighting logic → no direction recommended.

**Correct IVR null handling:**

| IVR state | Current | Correct |
|-----------|---------|---------|
| Known ≥ 35% | Seller gates run | ✅ Keep |
| Known < 30% | Buyer path eligible | ✅ Keep |
| Known 30–50% | Ambiguous | Prefer debit spread in bull trend |
| **Null / unknown** | **Coerced to 0.0 → fails seller** | **"IVR Unknown" — separate gate path, WARN** |

**Recommended 4-step structure selection (Perplexity — matches ChatGPT framework):**

| Step | Input | Decision |
|------|-------|----------|
| 1 — Market regime | SPY vs 200SMA, VIX | Bullish/bearish/neutral bias |
| 2 — Sector trend | Quadrant + weekChange (absolute) | Direction allowed or WAIT |
| 3 — Vol valuation | IVR (if known), IV/HV | Debit vs credit structure |
| 4 — Liquidity | bid-ask spread, OI | Trade or no trade |

**bull_call_spread** is the highest expected-value structure in low-VIX, SPY-above-200SMA, unknown/mid IVR — directionally aligned, theta-neutral, no Vol Risk Premium gate required.

---

### Priority Fixes (Perplexity ranking)

| Priority | Fix | File | Complexity |
|----------|-----|------|-----------|
| 1 | Absolute trend gate: `weekChange ≤ 0` for `bear_call_spread` | `sector_scan_service.py` | Low |
| 2 | Event density: events-in-window count + weighted score | `gate_engine.py` | Medium |
| 3 | IVR null handling: separate unknown path, never coerce to 0.0 | `analyze_service.py` + `gate_engine.py` | Medium |
| 4 | Tier 1 GO rate reporting separate from 15-ETF aggregate | `best_setups_service.py` + `DataProvenance.jsx` | Low |
| 5 | `bull_call_spread` for Leading/Improving + IVR 30–50 or null in bull regime | `sector_scan_service.py` + `analyze_service.py` | High |

---

## External Audit — Gemini (Day 49, 2026-05-08)

> **Context fed:** README.md + Phase7c_Research.md. All 4 prompts (D1–D4).

**D1:** Yes — tape-fighting confirmed. `rs_ratio < 98 AND rs_momentum < -0.5` is a relative ranking tool, not a directional tool. In SPY > 200SMA, sector +2% while SPY +5% still means the sector is appreciating. Fix: require `weekChange <= 0` for any `bear_call_spread`. If Lagging but rising with SPY above 200SMA → hard block.

**D2:** Single-next-event logic is underpowered for credit spreads in 30–45 DTE window. Credit spreads are exposed to full path until expiry, not just the nearest event. Fix: compute weighted event density score (FOMC=3, CPI=3, NFP=2, PCE=2) within DTE window. 2+ events in sub-30 DTE → automatic BLOCK. Rate-sensitive ETFs (XLF, XLRE, IWM) require stricter thresholds.

**D3:** 0 GO is not miscalibration, but evaluating against 15 ETFs is a flawed metric. True tradable universe = ~5 Tier 1 ETFs. Do NOT loosen the 20% bid-ask block — $2,000 slippage on 100 contracts before the trade starts. Track GO rate vs Tier 1 only. Healthy target: 1–3 GO/week. 0 GO for 4+ weeks on Tier 1 = calibration issue. Expected CAUTION win rate (well-calibrated): 55–65%.

**D4:** `IVR null → 0.0` is a severe design flaw — missing data is not low volatility. Fix: treat null IVR as "Unknown Confidence", issue WARN, do not route to buyer logic. `IVR < 30%` threshold for long calls is too restrictive — long options viable at 30–50% IVR if absolute trend is strong. `bull_call_spread` is the correct primary structure in low-VIX, SPY > 200SMA, mid-range or unknown IVR: directionally aligned, theta-neutral, no VRP gate required.

---

## External Audit — Synthesis (ChatGPT + Perplexity + Gemini)

> 3/3 LLMs agree on all 5 gaps. External audit complete.

### Agreement Matrix

| KI | Gap | ChatGPT | Perplexity | Gemini | Agreement |
|----|-----|---------|------------|--------|-----------|
| KI-098 | Absolute trend gate — weekChange ≤ 0 for bear_call_spread | ✅ P1 | ✅ P1 | ✅ P1 | **3/3 Full** |
| KI-097 | Event density — count events in DTE window | ✅ P2 | ✅ P2 | ✅ P2 | **3/3 Full** |
| KI-096 | IVR null ≠ 0.0 — treat as unknown confidence | ✅ P3 | ✅ P3 | ✅ P3 | **3/3 Full** |
| KI-100 | Tier 1 GO rate reporting separate from 15-ETF | ✅ P4 | ✅ P4 | ✅ P4 | **3/3 Full** |
| KI-099 | bull_call_spread for Leading/Improving mid-IVR | ✅ P5 | ✅ P5 | ✅ P5 | **3/3 Full** |

**All three audits share the same framing:**
- Gate math is correct. Liquidity gates are correct. Do NOT loosen them.
- The bugs are *decision-context bugs* — upstream of the gate engine, in how the system decides what to evaluate before gates run.
- Bear call spread in SPY-above-200SMA + VIX-17 is the lowest expected-value structure the system currently recommends.

**Useful nuance from Perplexity (not in others):**
- ±0.5% dead zone: flat-week ETF → CAUTION only, not GO. Optional refinement after the minimal `weekChange ≤ 0` fix.

### Implementation Order (confirmed by both audits)

| Order | KI | Complexity | Rationale |
|-------|----|-----------|-----------|
| 1st | KI-098 | Low (3-line change) | Highest P&L impact, confirmed safe, zero risk of breaking other paths |
| 2nd | KI-096 | Medium | Fixes null-IVR dead zone; unblocks correct direction recommendations |
| 3rd | KI-097 | Medium | Improves event risk control; existing calendar data, no new deps |
| 4th | KI-100 | Low (display only) | Better calibration visibility; no gate logic changes |
| 5th | KI-099 | High | Adds new direction path; needs full testing of all 4 directions post-change |

**Wait for Gemini before starting KI-097 or KI-099** — these are more complex and Gemini may add nuance. KI-098 is confirmed safe to implement now.

---

## Check 10.5 — EV Sanity

**Formula:** Expected move = underlying × IV × sqrt(DTE/365)

**Verified (Day 46, XLF bear_call_spread, DTE=22, underlying ~$55.70, IV ~20%):**
- 1-sigma move = 55.70 × 0.20 × sqrt(22/365) = $2.73
- Upper 1-sigma = $58.43
- Short call strike = $57.04 ← inside 1-sigma range
- McMillan Stress Check correctly fires WARN ✅

**Status: WORKING.** Stress gate correctly identifies short strikes inside expected move. Non-blocking warn — surfaces the risk correctly.

---

## Fixes Implemented

| Day | Fix | Status |
|-----|-----|--------|
| 46 | `ETF_DTE_SELLER_PASS_MIN` raised 21→30 | ✅ |
| 47 | `ETF_OPTIONS_LIQUID_TIER1` in constants (QQQ/IWM/XLF/XLK/XLY) | ✅ |
| 47 | Actionable liquidity block messages — Tier 2 ETF suggests QQQ/XLF alternative | ✅ |
| 47 | `_is_early_market_session()` helper — suggests rescan after 10 AM ET | ✅ |

---

## Deferred — Cyclical vs Defensive Weakening Logic

**Question:** Weakening cyclicals (XLI, XLY, XLB) → sell_call instead of WAIT?

**Status:** Deferred. Current scan shows XLI/XLY/XLB as Lagging (not Weakening). This question only activates when Weakening cyclicals are in ANALYZE status.

**Trigger:** When ≥2 of {XLI, XLY, XLB, XLF} show Weakening in the STA scan, revisit.

---

## Pending Code Changes

> External audit complete: ChatGPT + Perplexity = full agreement on all 5 items. Gemini pending (does not block KI-098).

| Priority | KI | Item | Gap | Change needed | Status |
|----------|----|------|-----|---------------|--------|
| 1 | KI-098 | Absolute trend gate | Lagging → bear_call_spread even if sector rising absolute | `weekChange ≤ 0` required in `quadrant_to_direction()` | **Ready — 3/3 confirmed** |
| 2 | KI-096 | IVR null handling | `None → 0.0` coercion — missing data treated as low vol | Treat as unknown confidence; separate null path in gate logic | **Ready — 3/3 confirmed** |
| 3 | KI-097 | Event density gate | Single-next-event misses 4 events in 22 DTE | Count events in DTE window, weighted score, escalate WARN→BLOCK | **Ready — 3/3 confirmed** |
| 4 | KI-100 | Tier 1 GO rate reporting | 15-ETF aggregate hides structural Tier 2 block | Track and display GO rate for Tier 1 (QQQ/IWM/XLF/XLK/XLY) separately | After KI-098/096 |
| 5 | KI-099 | bull_call_spread direction | Low/mid IVR bull setups have no debit spread option | Add bull_call_spread as direction for Leading/Improving + IVR 30–50 | After KI-097 |

---

## Roadmap

| Priority | Item | Status |
|----------|------|--------|
| Done | DTE seller floor: 21→30 | Day 46 ✅ |
| Done | ETF liquidity tier messaging | Day 47 ✅ |
| Done | Time-of-day spread advisory | Day 47 ✅ |
| Ongoing | Paper trade win rate (30 trades) | 0/30 logged |
| Ongoing | Adversarial LLM review | Monthly |
| Ongoing | Weekly gate pass rate log | Weekly |
| **Ready** | Absolute trend gate — KI-098 | 3/3 confirmed — implement now |
| **Ready** | IVR null handling — KI-096 | 3/3 confirmed — after KI-098 |
| **Ready** | Event density gate — KI-097 | 3/3 confirmed — after KI-096 |
| Future | Cyclical vs defensive Weakening logic | When Weakening cyclicals active |
| Future | Alternative strike search (higher delta for Tier 2 ETFs) | Research needed |
