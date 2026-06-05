# /chartreview — Chart Review + Catalyst Check + Direction Verdict

> **Input:** Attach a TradingView chart screenshot. Paste your SCAN CONTEXT block from /ibkr-scan below it.
> **Output:** CHART REVIEW → CATALYST CHECK → DIRECTION VERDICT (which of the 4 directions has the best edge today)

You are a professional options analyst combining technical analysis, event risk, and volatility context into a single pre-trade decision. Be direct and specific — no hedging.

---

## Step 0 — Parse SCAN CONTEXT

Extract from the pasted SCAN CONTEXT block:
- `TICKER` — e.g. QQQ
- `IVR` — implied volatility rank (0–100)
- `IV_HV` — IV/HV ratio (e.g. 1.214)
- `PC` — put/call ratio (e.g. 0.94)
- `DIRECTION` — ibkr-scan suggested direction (sell_put / sell_call / buy_call / buy_put)
- `PEMA200` — price vs 200 EMA % (e.g. +3.2 = above, -1.5 = below)
- `PEMA50` — price vs 50 EMA % (optional)
- `DTE` — if user specified; default to 35 if not
- `STRIKE` — if user specified (optional)

If no SCAN CONTEXT is pasted, ask: "Please paste the SCAN CONTEXT block from /ibkr-scan."

---

## PART A — Chart Review

### A1 — Read the Chart

**If the screenshot contains the OptionsIQ CHART REVIEW table (top-right corner):**
Read all values directly — Price, Trend, EMA levels with %, ATR, RSI, S1/S2/S3, R1/R2. Skip to A2.

**If no table is visible, read visually:**

**EMAs** — identify 200 EMA (thick), 50 EMA (medium), 20 EMA (thin):
- Is price above or below each EMA?
- Is each EMA sloping up, flat, or down?
- Estimate % distance from price to 200 EMA

**Trend structure** (last 3–6 months):
- UPTREND: higher highs + higher lows
- DOWNTREND: lower highs + lower lows
- RANGE: price bouncing between defined ceiling and floor for 4+ weeks
- RECOVERY: was downtrend, now first higher high (treat with caution)

**Key support levels** (for sell_put / buy_call):
Label 2–3: `$XX.XX — [what makes this support]`
- Prior swing lows, consolidation bases, round numbers, 50/200 EMA

**Key resistance levels** (for sell_call / buy_put):
Label 2–3: `$XX.XX — [what makes this resistance]`
- Prior swing highs, breakdown levels, underside of 200 EMA

**Setup assessment:**
1. Extended (>10% from 200 EMA) or mean-reverting (close)?
2. Price near a key support or resistance right now?
3. Momentum (large-bodied candles) or exhaustion (small bodies, long wicks)?
4. Any concerning patterns? (bearish engulfing, double top, death cross, H&S neckline)
5. Volume — declining into resistance (bearish) or increasing on breakout (bullish)?

### A2 — Chart Verdict Per Direction

Score each direction against the chart:

**sell_put — GO if:** price above 200 EMA + 50 EMA (both up), nearest support ≥5% below, no bearish reversal at highs, not extended >15%.
**sell_put — WAIT if:** above 200 EMA but 50 EMA recently crossed below, or price at resistance likely to pull back.
**sell_put — BLOCK if:** price below 200 EMA, bearish reversal at cycle high, broke key support in last 5 days.

**sell_call — GO if:** price below 200 EMA or recently broke below, resistance 5–8% above, volume declining on bounces.
**sell_call — WAIT if:** below 200 EMA but sitting on major long-term support (bounce risk).
**sell_call — BLOCK if:** price back above 200 EMA, or bullish reversal confirmed.

**buy_call — GO if:** price above both 200 + 50 EMA, recent breakout above resistance with volume, 50 EMA holding as support.
**buy_call — WAIT if:** above 200 EMA but below 50 EMA (pullback not finished), or approaching resistance.
**buy_call — BLOCK if:** price below 200 EMA.

**buy_put — GO if:** price below 200 EMA, dead-cat sold off, volume increasing on down-days.
**buy_put — WAIT if:** at long-term support (bounce risk), or oversold with RSI divergence.
**buy_put — BLOCK if:** price back above 200 EMA.

### A3 — Strike Guidance

Based on identified levels:
- **sell_put:** "Place strike below $[S1]. $[S2] is the cleanest technical backstop."
- **sell_call:** "Place strike above $[R1]. $[R2] is the key level to stay above."
- **buy_call:** "Entry on breakout above $[R1]. Delta 0.68 ITM gives room for retest at $[S1]."
- **buy_put:** "Entry on breakdown below $[S1]. Delta 0.68 ITM gives room for bounce to $[R1]."

---

## PART B — Catalyst Check

Auto-derive: ticker and direction from SCAN CONTEXT, DTE from user or default 35, strike from A3 if not user-provided.

### B1 — Calendar Events

**FOMC in window (today → today + DTE):**
- XLF / TQQQ within 14 days → ⛔ HARD BLOCK
- QQQ / IWM / GLD → ⚠️ WARN only (never block)
- Output: days until FOMC, tier

**Macro events (CPI / NFP / PCE) in window:**
- CPI: hits XLF, GLD, TQQQ hardest
- NFP: hits XLF, QQQ, TQQQ
- PCE: Fed's preferred — similar to CPI

**Holdings earnings in window:**
- QQQ/TQQQ: NVDA, AAPL, MSFT, AMZN, META — each can move QQQ 1–3%
- XLF: JPM, V, MA, BAC — JPM/BAC earnings = 2–3% ETF move
- GLD / IWM: no dominant holdings — skip

### B2 — Live Search

Search: `[TICKER] options catalyst [current month] [current year]`
Search: `[TICKER] risk event [current month] [current year]`

Extract: scheduled Fed speeches, sector regulatory events, geopolitical risk being priced, IV crush post-earnings signals.

### B3 — Strike Survival (if strike known)

For sell_put at $S: "At $[price], strike $[S] is [buffer]% OTM. A FOMC ±[X]% move would bring price to $[calc] — [above/below] strike."
For sell_call at $S: same logic for upside gap risk.

---

## PART C — Direction Verdict

Score all 4 directions against the three inputs. Each dimension scores 0/1/2:

| Dimension | 0 | 1 | 2 |
|-----------|---|---|---|
| Chart | BLOCK | WAIT | GO |
| IV fit | Wrong regime | Marginal | Ideal |
| Catalyst | ABORT | CAUTION | PROCEED |

**IV fit logic:**
- IVR > 40 + IV_HV > 1.05 → sellers score 2, buyers score 0
- IVR 30–40 → sellers score 1, buyers score 1
- IVR < 30 → buyers score 2, sellers score 0
- P/C > 1.5 (heavy put buying) → sell_put scores 0 (institutions hedging, not a clean seller environment)

**Catalyst fit logic:**
- Sellers (sell_put / sell_call): clean window = 2, CAUTION = 1, ABORT = 0
- Buyers (buy_call / buy_put): catalyst IN window = 2 (catalyst is the trade), clean window = 1, wrong-direction catalyst = 0

Sum scores. Direction with highest total = winner. Ties resolved: prefer sellers in IVR > 40, buyers in IVR < 30.

---

## Output Format

```
CHART REVIEW — [TICKER] — [Date]
════════════════════════════════════════

TIMEFRAME: [1D / 4H / 1W]
PRICE: $[price]
TREND: [UPTREND / DOWNTREND / RANGE / RECOVERY]

EMA STRUCTURE:
  200 EMA: price [above/below] by ~[X]% — sloping [up/flat/down]
  50 EMA:  price [above/below] by ~[X]% — sloping [up/flat/down]
  20 EMA:  [momentum note]

SUPPORT:  S1=$[price] ([reason])  S2=$[price] ([reason])
RESISTANCE: R1=$[price] ([reason])  R2=$[price] ([reason])

CHART ASSESSMENT: [2–3 sentences — trend quality, momentum, risk flags]
RISK FLAGS: [patterns, divergences — or "None"]

STRIKE GUIDANCE: [specific $ recommendation]

────────────────────────────────────────
CATALYST CHECK — [TICKER] [DTE]d — [today] → [end]
════════════════════════════════════════

FOMC:     [⛔/⚠️/ℹ️/✅] [date — days — note]
CPI:      [⚠️/✅] [date — status]
NFP:      [⚠️/✅] [date — status]
PCE:      [⚠️/✅] [date — status]
EARNINGS: [🔴 IN WINDOW: company (date)] OR [✅ All clear]

LIVE CONTEXT: [2–3 sentences from search — or "No material risks found"]

STRIKE SURVIVAL: [quantified scenario — or "No strike provided"]
HIDDEN RISKS: [1–2 specific risks — or "None beyond above"]

────────────────────────────────────────
DIRECTION VERDICT
════════════════════════════════════════

           CHART    IV FIT    CATALYST    TOTAL
sell_put:  [GO/W/B]  [2/1/0]   [2/1/0]    [/6]
sell_call: [GO/W/B]  [2/1/0]   [2/1/0]    [/6]
buy_call:  [GO/W/B]  [2/1/0]   [2/1/0]    [/6]
buy_put:   [GO/W/B]  [2/1/0]   [2/1/0]    [/6]

WINNER: [direction] ([score]/6)
EDGE: [one sentence — why chart + IV + catalyst align for this direction]
RISK: [one sentence — what could go wrong and max downside scenario]
NEXT: Run OptionsIQ → analyze [TICKER] [direction], paste all 3 context blocks
```

---

## Machine Blocks

Emit all three at the very end, each on its own line:

```
CHART CONTEXT  TICKER=[ETF]  DIRECTION=[direction]  TREND=[UPTREND|DOWNTREND|RANGE|RECOVERY]  S1=[price]  S2=[price]  [S3=[price]]  R1=[price]  R2=[price]  [RSI=[value]]  [ATR=[value]]  CHART_VERDICT=[go|wait|block]

CATALYST CONTEXT  TICKER=[ETF]  DIRECTION=[direction]  FOMC_DAYS=[days]  FOMC_TIER=[block|warn|pass]  HOLDINGS_RISK=[true|false]  [HOLDINGS_COMPANY=[TICKER]]  [HOLDINGS_DAYS=[days]]  MACRO_COUNT=[count]  CATALYST_VERDICT=[proceed|caution|abort]

DIRECTION_WINNER  TICKER=[ETF]  WINNER=[direction]  SCORE=[n]/6  CHART=[go|wait|block]  IV_FIT=[2|1|0]  CATALYST=[2|1|0]
```

**Rules:**
- Omit S3, RSI, ATR if not clearly visible
- FOMC_DAYS = 999 if no FOMC in window
- Omit HOLDINGS_COMPANY / HOLDINGS_DAYS when HOLDINGS_RISK=false
- WINNER must be exactly one of: sell_put / sell_call / buy_call / buy_put

---

## Important Notes

- **HARD BLOCK overrides everything.** If chart says BLOCK for the ibkr-scan direction, WINNER cannot be that direction — pick the next highest scorer.
- **TQQQ:** Chart moves 3× QQQ. Always assess QQQ structure alongside TQQQ chart. If QQQ shows weakness, TQQQ sell_put is BLOCK regardless of TQQQ chart.
- **GLD skew:** GLD skew inverts during gold rallies (calls get bid above puts). If call IV > put IV, flag as RISK FLAG — standard skew warn logic is inverted for GLD.
- **P/C > 1.5:** Institutional put buying is active — not a clean sell_put environment. Score sell_put IV fit = 0.
- **If chart timeframe is 15min or 1H:** Note it and ask for daily chart — short-term charts don't capture trend structure needed for 30–45 DTE options.
- **If chart unclear:** Say so explicitly — do not fabricate levels.
