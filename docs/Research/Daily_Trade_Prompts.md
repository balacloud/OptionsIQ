# OptionsIQ — Daily Trade Research Prompts
> Use these prompts with your AI subscriptions before taking any trade.
> Total daily time: ~10 minutes.
> Fill in [DATE], [TICKER], [SECTOR], and paste OptionsIQ output where indicated.

---

## Daily Workflow

| Time | Tool | Prompt | Minutes |
|------|------|--------|---------|
| 8:30 AM | Perplexity | #1 — Macro Regime Check | 2 |
| 8:35 AM | Perplexity | #2 — Sector Catalyst Check | 3 |
| 8:40 AM | Run OptionsIQ | Get verdict + strategy | 2 |
| 8:42 AM | ChatGPT | #4 — Trade Thesis Stress Test (paste from OptionsIQ) | 3 |
| **Done** | — | Go / No-Go decision | — |
| Sunday PM | Gemini | #6 — Weekly Sector Briefing | 5 |

---

## PERPLEXITY PRO PROMPTS
*(Best for: live news, current catalysts, real-time data — run FIRST)*

---

### Prompt 1 — Daily Macro Regime Check
*Run once every morning before market open. Tells you whether today is a buying or selling premium environment.*

```
Today is [DATE]. I trade options on sector ETFs (16 ETFs: XLK, XLY, XLP,
XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, SCHB, QQQ, TQQQ).

Give me a morning regime check in this exact format:

**MACRO BACKDROP (today)**
- VIX level and what it means (calm/elevated/fear)
- Is SPY above or below its 200-day SMA?
- Any overnight news that changes the market tone?

**EVENTS IN NEXT 21 DAYS (date + what it is)**
- Next FOMC meeting or Fed speaker
- Next CPI / NFP / major economic release
- Any Treasury auction or debt ceiling risk

**VERDICT: Is this a good week to BUY options premium or SELL premium?**
(one sentence, yes/no with brief reason)
```

---

### Prompt 2 — Sector Catalyst Check
*Run for your top 1-2 ETF candidates after reviewing the sector scan. Replace [TICKER], [SECTOR NAME], and [DIRECTION].*

```
Today is [DATE]. I'm considering a [buy_call / buy_put / sell_put] trade
on [TICKER] ([SECTOR NAME] sector ETF).

Give me a focused catalyst check in this format:

**WHAT'S MOVING THIS SECTOR THIS WEEK**
- Top 1-3 news items or data releases affecting this sector right now

**EARNINGS RISK**
- Are any major companies inside [TICKER] reporting earnings in the next
  21 days? List them with dates.
  (Key names for XLK: AAPL, MSFT, NVDA, GOOGL. For XLY: AMZN, TSLA.
   For XLF: JPM, GS, BAC. For XLE: XOM, CVX. For XLV: JNJ, UNH, LLY.
   For XLC: META, GOOGL, NFLX. For XLI: CAT, HON, UPS. For QQQ: NVDA, AAPL, MSFT.)

**ANALYST SENTIMENT**
- Any recent upgrades, downgrades, or price target changes on [TICKER] itself
  or its top 5 holdings this week?

**IV CONTEXT**
- Is there a specific reason IV would be elevated or suppressed in [TICKER]
  right now? (upcoming catalyst, recent vol crush, sector event?)

**ONE-LINE VERDICT**
- Is the sector narrative aligned or against a [bullish/bearish] options trade?
```

---

### Prompt 3 — Unusual Options Activity
*Run when OptionsIQ shows green verdict — confirm smart money agrees.*

```
Today is [DATE]. Search for any unusual options activity, large block trades,
or notable flow in [TICKER] in the last 2-3 trading days.

Format:
- Any large call or put sweeps? (size, strike, expiry)
- Any notable change in put/call ratio for [TICKER]?
- Any dark pool or institutional prints worth noting?
- Does the flow lean bullish or bearish?

If no unusual activity found, just say "No notable flow — normal trading."
```

---

## CHATGPT PLUS (GPT-4o) PROMPTS
*(Best for: reasoning, stress-testing, bear cases — run AFTER OptionsIQ gives you a green verdict)*

---

### Prompt 4 — Trade Thesis Stress Test
*OptionsIQ generates this prompt for you automatically — use the "Copy for ChatGPT" button in the app.*
*Paste directly into ChatGPT without editing.*

> **Note:** The "Copy for ChatGPT" button in OptionsIQ pre-fills this entire prompt with your actual
> analysis data (ticker, verdict, gate scores, strategy details, P&L scenarios).
> You just click Copy → paste into ChatGPT → hit send.

---

### Prompt 5 — IV Environment Check
*Run when you're unsure whether to buy or sell premium. Fill in VIX, IVR from OptionsIQ output.*

```
Today is [DATE]. VIX is at [X]. I trade options on sector ETFs.

My system shows:
- [TICKER] IVR: [X]% (cheap = below 30, expensive = above 60)
- HV20: [X]%
- Suggested direction from sector scan: [buy_call / sell_put]

Help me think through the IV environment:

1. At VIX [X], should I prefer buying premium (directional calls/puts)
   or selling premium (covered calls, put spreads)?

2. [TICKER] IVR is [X]%. Is this cheap enough to buy, or better to sell?

3. If I buy a call with 49 DTE and the trade goes sideways for 2 weeks,
   how much IV crush or theta burn would I typically expect?

4. What's the one thing about IV I should watch before entering this trade?

Answer in plain English, under 200 words.
```

---

## GEMINI PRO PROMPTS
*(Best for: structured synthesis, weekly planning — run once per week on Sunday evening)*

---

### Prompt 6 — Weekly Sector Rotation Briefing
*Run Sunday evening or Monday pre-market. Gives you the weekly plan for all 16 ETFs.*

```
Today is [DATE]. I trade options on these 16 sector ETFs:

XLK (Tech), XLY (Cons. Discretionary), XLP (Cons. Staples),
XLV (Health Care), XLF (Financials), XLI (Industrials), XLE (Energy),
XLU (Utilities), XLB (Materials), XLRE (Real Estate), XLC (Comm. Services),
MDY (Mid-Cap), IWM (Small-Cap), SCHB (Broad Market), QQQ (Nasdaq 100),
TQQQ (3x Nasdaq — leveraged, use caution)

Give me a structured weekly briefing:

**MARKET REGIME THIS WEEK**
- Risk-on or risk-off? Why?
- What sectors are likely to lead? What sectors to avoid?

**TOP 3 BULLISH SETUPS** (sectors with tailwinds this week)
| ETF | Reason | Trade Bias |
|-----|--------|-----------|

**TOP 2 BEARISH / DEFENSIVE SETUPS** (if market regime is risk-off)
| ETF | Reason | Trade Bias |
|-----|--------|-----------|

**AVOID THIS WEEK** (earnings risk, binary events, or overextension)
| ETF | Reason |
|-----|--------|

**KEY EVENTS CALENDAR** (next 5 trading days)
| Date | Event | ETFs affected |
|------|-------|--------------|

**ONE TRADE IDEA** (your highest conviction setup for the week)
- ETF, direction, and 1-sentence reason
```

---

### Prompt 7 — Earnings Blast Radius Check
*Run when OptionsIQ flags earnings risk or when IVR is unusually elevated.*

```
Today is [DATE]. I need an earnings calendar for the next 21 days for the
top holdings inside these ETFs: [TICKER1], [TICKER2].

For each ETF, list:
- Top 10 holdings by weight (approximate %)
- Which of those report earnings in the next 21 days
- Expected date
- Whether the earnings could cause a large gap in the ETF (>3% move)

Format as a table. If no major earnings risk, say:
"Clean — no major holdings reporting in the next 21 days."

Also flag: is [TICKER] itself sensitive to any sector-wide earnings
(e.g., bank earnings affecting XLF even before direct holdings report)?
```

---

## ETF Sector Reference Card
*Quick lookup when filling in [SECTOR NAME] and key holdings for Prompts 2 & 7*

| ETF | Sector | Key Holdings to Watch |
|-----|--------|-----------------------|
| XLK | Technology | AAPL, MSFT, NVDA, AVGO, AMD |
| XLY | Consumer Discretionary | AMZN, TSLA, HD, MCD |
| XLP | Consumer Staples | PG, KO, PEP, COST, WMT |
| XLV | Health Care | JNJ, UNH, LLY, ABBV, MRK |
| XLF | Financials | JPM, BAC, WFC, GS, BRK.B |
| XLI | Industrials | CAT, HON, UPS, LMT, RTX |
| XLE | Energy | XOM, CVX, COP, EOG, SLB |
| XLU | Utilities | NEE, DUK, SO, AEP |
| XLB | Materials | LIN, APD, ECL, NEM |
| XLRE | Real Estate | AMT, PLD, EQIX, SPG |
| XLC | Communication Services | META, GOOGL, NFLX, DIS, CMCSA |
| MDY | Mid-Cap S&P 400 | Broad mid-cap — no single dominant |
| IWM | Small-Cap Russell 2000 | Broad small-cap — rate sensitive |
| SCHB | Broad Market | Mirrors total US market |
| QQQ | Nasdaq 100 | NVDA, AAPL, MSFT, GOOGL, AMZN |
| TQQQ | 3x Nasdaq | Same as QQQ — volatility amplified 3x |
