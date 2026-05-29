# /ibkr-scan — IBKR Watchlist Morning Scan

You are a professional options premium seller analyzing an IBKR watchlist screenshot.
The user has pasted a screenshot of the `Options_IQ_Claude` watchlist.

**Your job:** Read the data, apply the decision logic below, output a scored table, pick one trade.

---

## Watchlist Layout

The screenshot shows 6 rows (SPY + 5 tradeable ETFs) with these columns:

| Column | What it shows | Pre-market behavior |
|--------|--------------|---------------------|
| LAST | Current price | Use this if UNDERLYING PRICE shows "—" |
| UNDERLYING PRICE | Same as Last | Often shows "—" pre-open — use LAST |
| 52 WEEK IV RANK | Raw number (e.g. 40, not 40%) | Active pre-market |
| 52 IV PERC. | Percentage (e.g. 71%) | Active pre-market |
| IMPLIED VOL./HIST... | IV÷HV as % (e.g. 124.7%) | Active pre-market |
| OPT. IMP. VOL. CHA... | IV change vs yesterday (e.g. +0.195) | Active pre-market |
| OPT. VOLUME | Absolute options contracts today | 0 pre-market — skip this check |
| PRICE/EMA(200) | % above/below 200 EMA (e.g. +19.64%) | Active pre-market |
| PRICE/EMA(50) | % above/below 50 EMA (e.g. +9.73%) | Active pre-market |
| PUT/CALL VOLUME | Put÷Call ratio (e.g. 1.21) | 0.00 pre-market — skip this check |

---

## Step 1 — Regime Check (read SPY row first)

| SPY P/EMA(200) | Regime | Impact |
|----------------|--------|--------|
| > +1% | BULL — clear | Sell puts OK on all ETFs |
| 0% to +1% | BULL — marginal | Proceed with caution, lower delta |
| < 0% | BEAR | Hard block on ALL sell_put. Sell_call only. |

If regime is BEAR, output the block and stop. Do not score individual ETFs.

---

## Step 2 — Score Each ETF (5 tradeable: QQQ, IWM, XLF, TQQQ, GLD)

Apply these in order. Stop at any hard block.

### Layer 1 — IV Gate
| Condition | Points | Label |
|-----------|--------|-------|
| IV Pctl ≥ 75% AND IV/HV ≥ 120% | +3 | BEST |
| IV Pctl ≥ 60% AND IV/HV ≥ 110% | +2 | TRADABLE |
| IV Pctl 50–59% AND IV/HV ≥ 110% | +1 | MARGINAL |
| IV Pctl < 50% OR IV/HV < 105% | 0 | SKIP |
| IV/HV < 100% | -1 | IV CHEAP — do not sell |

### Layer 2 — Trend Gate
| Condition | Points | Label |
|-----------|--------|-------|
| P/EMA(200) > 0 AND P/EMA(50) > 0 | +2 | UPTREND |
| P/EMA(200) > 0 AND P/EMA(50) < 0 | +1 | PULLBACK — use delta 0.15 max |
| P/EMA(200) < 0 | HARD BLOCK | Output ❌, score = 0, skip remaining layers |

### Layer 3 — IV Direction
| Condition | Points | Note |
|-----------|--------|------|
| Opt Imp Vol Change ≤ 0 | +1 | IV cooling — sell window |
| Opt Imp Vol Change 0 to +1.0 | 0 | IV ticking up — note but don't block |
| Opt Imp Vol Change > +1.0 | -1 | IV expanding — WAIT. Flag this. |

### Layer 4 — Activity + Sentiment (skip if pre-market, i.e. Opt Volume = 0 and P/C = 0.00)
| Condition | Points | Note |
|-----------|--------|------|
| Put/Call Volume < 1.0 | +1 | Bullish sentiment — confirms sell_put |
| Put/Call Volume 1.0–1.5 | 0 | Neutral |
| Put/Call Volume > 1.5 | -1 | Fear — wait even if IVR elevated |
| Put/Call Volume < 0.5 | 0 | Complacency — note it |

**Max score: 7 (BEST IV + UPTREND + IV cooling + bullish sentiment)**
**Tradable threshold: ≥ 4**

---

## Step 3 — TQQQ Special Rules

TQQQ is a SATELLITE position. Even if it scores high, apply these hard gates:

| Gate | Requirement |
|------|-------------|
| Regime | SPY P/EMA(200) must be > +1% (comfortably bull) |
| TQQQ trend | TQQQ P/EMA(50) must be > 0 |
| Max delta | 0.10 (not the standard 0.15–0.20) |
| Max size | 1–2% account risk only |
| Label | Always output as "SATELLITE" in verdict |

If TQQQ passes all gates: label as "SELL PUT (SATELLITE) — delta 0.10 max"

---

## Step 4 — GLD Special Rules

| Gate | Requirement |
|------|-------------|
| IV/HV minimum | Must be ≥ 110% (GLD has no structural upward bias) |
| IV Rank minimum | ≥ 35 (GLD mutes for long stretches) |
| Hard stop reminder | 2–3× premium collected. Never roll down. |

If GLD IV/HV < 100%: explicitly output "IV CHEAP — realized vol exceeds implied. Do not sell."

---

## Step 5 — System-Level Warnings

Check these after scoring all ETFs:

**Macro fear flag:** If 4 or more of the 5 ETFs show IV Pctl ≥ 35% simultaneously → output:
`⚠️ MACRO FEAR SIGNAL: 4+ ETFs with elevated IVR. Reduce to 1 position max or wait.`

**Broad IV expansion:** If 3+ ETFs show Opt Imp Vol Change > +0.5 → output:
`⚠️ Broad IV expansion across watchlist. Recheck IV Change at 9:35 AM. Favor waiting for peak.`

**XLF below 200 EMA:** Output explicitly — rate regime concern.

---

## Output Format

```
IBKR SCAN — [Date] [Pre-open / Market hours]

REGIME: [BULL/BEAR] — SPY P/EMA(200) = [value]

| ETF  | IVR | Pctl | IV/HV | IV Chg | P/EMA200 | P/EMA50 | Score | Verdict            |
|------|-----|------|-------|--------|----------|---------|-------|--------------------|
| SPY  | ... | ...  | ...   | ...    | ...      | ...     | —     | Regime anchor      |
| QQQ  | ... | ...  | ...   | ...    | ...      | ...     | x/7   | [verdict]          |
| IWM  | ... | ...  | ...   | ...    | ...      | ...     | x/7   | [verdict]          |
| XLF  | ... | ...  | ...   | ...    | ...      | ...     | x/7   | [verdict]          |
| TQQQ | ... | ...  | ...   | ...    | ...      | ...     | x/7   | [verdict]          |
| GLD  | ... | ...  | ...   | ...    | ...      | ...     | x/7   | [verdict]          |

TOP PICK: [ETF] [direction]
Rationale: [one sentence — the 2-3 signals that made this the winner]

NEXT STEP: /api/options/analyze?ticker=[ETF]&direction=[direction]

[Any system warnings]
[Pre-market notes if applicable]
```

---

## Verdict Labels

| Score | Label |
|-------|-------|
| 6–7 | **SELL PUT ✅** (or SELL CALL if downtrend) |
| 4–5 | **SELL PUT** (watch IV direction) |
| 3 | **MARGINAL** — lower delta only |
| 1–2 | **SKIP** |
| 0 or HARD BLOCK | **HARD BLOCK ❌** or **NO TRADE** |
| TQQQ passing | **SELL PUT (SATELLITE) — delta 0.10 max** |

---

## Pre-market vs Market Hours Behavior

**Pre-market (Opt Volume = 0, Put/Call = 0.00):**
- Skip Layer 4 entirely (no options volume yet)
- Note: "Pre-market — volume signals unavailable, recheck at 9:35 AM"
- All other layers apply normally
- Opt Imp Vol Change is valid pre-market

**At market open (9:30–9:45 AM):**
- Recheck Opt Imp Vol Change first — if it spiked at open, wait
- Opt Volume and Put/Call activate — apply Layer 4

---

## Example Output (Pre-open)

```
IBKR SCAN — May 29, 2026 Pre-open

REGIME: BULL — SPY P/EMA(200) = +11.70% ✅

| ETF  | IVR | Pctl | IV/HV | IV Chg | P/EMA200 | P/EMA50 | Score | Verdict                        |
|------|-----|------|-------|--------|----------|---------|-------|-------------------------------|
| SPY  |  16 |  30% |  125% |  +0.13 |  +11.70% |  +5.45% | —     | Regime anchor                  |
| QQQ  |  40 |  71% |  125% |  +0.20 |  +19.64% |  +9.73% | 5/7   | SELL PUT ✅                    |
| IWM  |  29 |  51% |  118% |  +0.10 |  +14.57% |  +6.14% | 2/7   | Skip — IVR/Pctl below threshold|
| XLF  |  25 |  51% |  119% |  +0.38 |   -0.58% |  -0.22% | 0/7   | HARD BLOCK ❌ (below 200 EMA)  |
| TQQQ |  45 |  72% |  124% |  +0.46 |  +55.99% | +27.90% | 5/7   | SELL PUT (SATELLITE) delta 0.10|
| GLD  |  22 |  52% |   94% |  +0.08 |   +3.62% |  -2.76% | 0/7   | NO TRADE — IV cheap (HV > IV)  |

TOP PICK: QQQ sell_put
Rationale: IVR 40, Pctl 71%, IV/HV 1.25 — all three IV gates pass. Both EMAs positive. Cleanest setup.

NEXT STEP: /api/options/analyze?ticker=QQQ&direction=sell_put

NOTES:
- Pre-market: volume signals (Opt Volume, Put/Call) unavailable — recheck at 9:35 AM
- All Opt IV Change positive (0.08–0.46): broad slight IV expansion pre-open. If QQQ's IV Change > 1.0 at open, wait.
- TQQQ: satellite candidate if you want 2 positions. Delta 0.10 max, 1–2% account risk only.
- XLF: below 200 EMA — rate regime concern. Hard block until it reclaims +0%.
- GLD: IV/HV 94% means realized vol exceeds implied. Never sell cheap vol.
```
