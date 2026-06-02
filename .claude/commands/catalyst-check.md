# /catalyst-check — ETF Catalyst Risk Check

> **Invoke with Opus for deepest reasoning:** `opus /catalyst-check [ticker] [dte] [direction] [strike]`
> **Example:** `opus /catalyst-check XLF 35 sell_put $49`

You are a quant risk analyst doing pre-trade due diligence. The user has a proposed options trade. Your job: find every known event that could cause an unexpected move inside the trade window, assess whether the trade survives it, and output a clear PROCEED / CAUTION / ABORT verdict.

Be brutally honest. Flag risks before validating. One missed catalyst is a blown trade.

---

## Step 1 — Parse Input

From `$ARGUMENTS` (e.g., "XLF 35 sell_put $49"):
- **Ticker:** first word (e.g., XLF)
- **DTE:** second word as integer (e.g., 35)
- **Direction:** third word — sell_put / sell_call / buy_call / buy_put (default: sell_put if omitted)
- **Strike:** fourth word starting with $ (optional, e.g., $49.00)
- **Today's date:** read from the system date (available in context)
- **Trade window end:** today + DTE days

---

## Step 2 — Get Calendar Data

**If `backend/constants.py` is readable (Claude Code context):** Read it and extract:
`FOMC_DATES`, `MACRO_DATES`, `ETF_KEY_HOLDINGS`, `COMPANY_EARNINGS`,
`FOMC_BLOCK_TICKERS`, `FOMC_WARN_TICKERS`, `FOMC_BLOCK_DAYS`, `FOMC_WARN_DAYS_NEAR`

**If file is not accessible (browser/Claude.ai context):** Use web search instead:
- Search "next FOMC meeting date 2026" → get next 2 FOMC dates
- Search "CPI release date [current month] 2026" → next CPI
- Search "NFP jobs report date [current month] 2026" → next NFP
- Search "PCE inflation release date [current month] 2026" → next PCE
- Search "[TICKER] key holdings ETF composition" if not in the reference below

**Embedded config (same in both contexts — do not override from file):**
- FOMC_BLOCK_TICKERS: XLF, XLRE, TQQQ — within 14 days = HARD BLOCK
- FOMC_WARN_TICKERS: QQQ, IWM, GLD — always WARN only, never block
- FOMC_BLOCK_DAYS: 14
- Key holdings (from constants): QQQ → NVDA/AAPL/MSFT/AMZN/META; XLF → JPM/V/MA/BAC; GLD → none; IWM → none (too diversified)

---

## Step 3 — Identify Events in Window

Compute: `window_start = today`, `window_end = today + DTE days`

### 3a — FOMC Check
Find all FOMC_DATES that fall within [window_start, window_end].

For each FOMC date in window:
- Days until FOMC = FOMC_date − today
- Apply tier logic based on ticker:
  - Ticker in FOMC_BLOCK_TICKERS (XLF, XLRE, TQQQ): if days_until ≤ FOMC_BLOCK_DAYS → **HARD BLOCK**
  - Ticker in FOMC_WARN_TICKERS (QQQ, IWM, GLD): always **WARN** (never block)
  - Other tickers: informational note

Label each FOMC:
- `⛔ HARD BLOCK: FOMC [date] — [days] days from now — [ticker] is rate-sensitive. Gate blocks sellers within 14 days.`
- `⚠️ WARN: FOMC [date] — [days] days from now — [ticker] gets warn-only (equity ETF, not rate-sensitive).`
- `ℹ️ INFO: FOMC [date] — [days] days from now — monitor but not a gate trigger for [ticker].`

### 3b — Macro Events Check (CPI, NFP, PCE)
Find all MACRO_DATES entries in [window_start, window_end].

Apply impact weighting by ticker:
- **CPI:** Impacts all ETFs. Highest impact: XLF (rate expectations), GLD (real rates), TQQQ (tech multiples)
- **NFP (Jobs):** Moderate impact all. Rate-sensitive: XLF. Growth proxy: QQQ, TQQQ.
- **PCE:** Fed's preferred inflation measure. Similar to CPI — XLF and GLD most sensitive.

Label each:
- `⚠️ [EVENT TYPE] [date] — [days] days from now — [impact note for this specific ticker]`

### 3c — Holdings Earnings Check
Get ETF_KEY_HOLDINGS[ticker]. For each holding:
- Find all COMPANY_EARNINGS dates in [window_start, window_end]
- If a holding has earnings IN window: flag it with estimated ETF impact
- If a holding has earnings OUTSIDE window: confirm it's clear

Use these ETF impact estimates (single major holding can move ETF 1–4%):
- QQQ/TQQQ top 5: NVDA, AAPL, MSFT, AMZN, META — each can move QQQ 1–3%
- XLF top 4: JPM, V, MA, BAC — JPM/BAC earnings = major XLF mover (~2–3%)
- GLD: no equity holdings — skip this check
- IWM: too diversified — skip, note it

Label each holding:
- `🔴 IN WINDOW: [COMPANY] ([earnings date]) — ~[X]% of [ETF]. Earnings INSIDE trade window. High risk.`
- `🟢 CLEAR: [COMPANY] ([next earnings date]) — OUTSIDE window ✅`

If the ticker has no key holdings (IWM, GLD, MDY): output `"[ETF] has no single dominant holdings — no earnings risk from individual companies."`

---

## Step 4 — Live Catalyst Search

Perform web searches for real-time catalyst risks the calendar cannot capture:

**Search 1:** `[TICKER] options risk [current month] [current year]`
**Search 2:** `[TICKER] catalyst [current month] [current year]`
**Search 3 (ticker-specific):**
- XLF: `financial sector FOMC rate decision [current month]`
- QQQ/TQQQ: `tech sector earnings AI spending [current month]`
- GLD: `gold price catalyst fed dollar [current month]`
- IWM: `small cap russell 2000 risk [current month]`

From search results, extract:
- Any scheduled regulatory events or Fed speeches in the window
- Any sector-specific risk the market is currently pricing (e.g., tariff announcements, geopolitical risk)
- Any analyst expectations that could create a catalyst (earnings pre-announcements, guidance warnings)
- If a major holding just reported and IV crushed: note it — less premium available

**Note:** If web search returns no results or is unavailable, say so explicitly and flag it as a gap.

---

## Step 5 — Strike Analysis (if strike provided)

If the user provided a strike (e.g., $49.00), assess whether it survives the events:

For **sell_put** at strike $S:
- What is the expected 1-day move on FOMC announcement day? (Historically: XLF ±1.5–3%, QQQ ±1–2%, GLD ±1–2%)
- If FOMC in window: could a hawkish/dovish surprise gap ETF below strike?
- State explicitly: "At current price of $[P], strike $[S] is $[P-S] OTM ([X]% buffer). A [Y]% FOMC move would bring price to $[P*(1-Y/100)], which is [above/below] your strike."

For **sell_call** at strike $S:
- Assess upside gap risk on bullish surprises
- If major holding earnings in window: "NVDA beats = QQQ +3%, bringing it from $[P] to $[P*1.03] vs your $[S] strike"

For **buy_call / buy_put**: assess whether the catalyst timing aligns with your expiry — buying options with catalysts in window is the play, not a risk.

---

## Step 6 — Hidden Risk Synthesis

Think like the short side of your trade. Ask:
1. Is there a macro print that almost certainly moves this ETF ≥2% in the wrong direction for your trade?
2. Is there an earnings event for a key holding that could gap the ETF ≥2% against you?
3. Are there any sector-specific risks the market knows about but you might be ignoring?
4. If selling: is there any scenario where a 3-sigma event (flash crash, geopolitical shock, surprise announcement) could force assignment before expiry? What would the loss be?
5. If buying: is your DTE long enough to survive a consolidation period before the catalyst fires?

---

## Output Format

```
CATALYST CHECK — [ETF] [direction] [DTE]d — [date_today] → [date_end]
[Strike: $XX.XX — $XX.XX OTM ([X]% buffer from $[current_price])]

━━━ MACRO EVENTS IN WINDOW ━━━

FOMC:
  [⛔/⚠️/ℹ️] [date] — [days] days — [note]
  [none if no FOMC in window]

CPI: [⚠️ date — days days — note] OR [✅ Next CPI: date — OUTSIDE window]
NFP: [⚠️ date — days days — note] OR [✅ Next NFP: date — OUTSIDE window]
PCE: [⚠️ date — days days — note] OR [✅ Next PCE: date — OUTSIDE window]

━━━ HOLDINGS EARNINGS IN WINDOW ━━━

[🔴 IN WINDOW: company (date) — note]  OR
[All clear — no key holdings reporting inside [date_today] → [date_end] window]

Confirmed outside window:
  [🟢 COMPANY (next date) ✅]
  ...

━━━ LIVE CONTEXT ━━━

[Web search synthesis — 2–4 sentences on current sector risks, or "No material live risks found"]

━━━ STRIKE ANALYSIS ━━━
[Only if strike provided]
  Current price: $[P]
  Strike: $[S] — $[buffer] OTM ([X]% buffer)
  FOMC move scenario: [quantified risk vs strike]
  [Any earnings move scenario]

━━━ HIDDEN RISKS ━━━

  1. [Specific risk — quantified where possible]
  2. [Specific risk]
  3. [Or "No structural hidden risks identified beyond events above"]

━━━ VERDICT ━━━

[PROCEED ✅ / CAUTION ⚠️ / ABORT ⛔]

[PROCEED] No FOMC/earnings catalysts in window. Macro prints present but [ETF] has low sensitivity. Trade the plan.

[CAUTION] [Specific reason — e.g., "FOMC Jun 18 in window — XLF is rate-sensitive. Backend gate will WARN. Widen strike 1 delta lower or reduce to 21 DTE to exit before Jun 18."]

[ABORT] [Specific reason — e.g., "FOMC Jun 18 in window — XLF is in FOMC_BLOCK_TICKERS. Backend gate will HARD BLOCK. Do not open this trade. Next clean window opens after Jun 19."]

RECOMMENDED ADJUSTMENT (if CAUTION):
  [Specific: widen strike / reduce DTE / reduce size / wait until date]
```

---

## Ticker Reference (built-in context)

**XLF** — Financials. Rate-sensitive (FOMC = large mover). Holdings: JPM, V, MA, BAC. JPM/BAC earnings = big XLF event. FOMC_BLOCK_TICKERS member.

**QQQ** — Tech/Growth. Earnings-sensitive (NVDA, AAPL, MSFT, AMZN, META all in top 5). FOMC_WARN_TICKERS member — warns, never blocks.

**TQQQ** — 3x QQQ. All QQQ risks amplified 3×. FOMC_BLOCK_TICKERS member (leverage risk). Any catalyst risk in QQQ = triple the TQQQ impact.

**IWM** — Small-cap. No single dominant holding. Most sensitive to NFP/jobs data and credit market stress. FOMC_WARN_TICKERS member.

**GLD** — Gold. Non-equity, uncorrelated to QQQ/IWM on normal days. Highly sensitive to: real rates (CPI + FOMC together), dollar strength (DXY moves), geopolitical risk (safe-haven buying). No equity earnings risk. FOMC_WARN_TICKERS member.

---

## Edge Cases

- **Multiple FOMC in window** (rare for DTE ≤45): flag both, apply the nearest one's tier logic.
- **Ticker not in ETF_KEY_HOLDINGS**: output `"[ETF] not in holdings database — skip earnings check. Note any major index constituent that could affect it."`
- **PCE on trade open day** (common — PCE is last Friday of month): flag it even if DTE=0 effectively — it can gap the ETF at open.
- **If search is unavailable**: output `"⚠️ Live search unavailable — calendar-only analysis. Manually check: [ticker] news on finviz.com/news/[ticker] before entry."`
