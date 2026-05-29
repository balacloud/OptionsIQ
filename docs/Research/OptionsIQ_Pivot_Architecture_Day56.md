# OptionsIQ Strategic Pivot — Design Document
> **Version target:** v0.35.0
> **Status:** LOCKED — ETF universe + watchlist columns finalized. Ready for Phase 1 implementation.
> **Session:** Day 56 — Major direction change
> **Last refined:** 5-ETF universe locked via Multi-LLM research (GPT-4o + Gemini + Grok + Claude). SPY dropped. GLD confirmed slot 5. TQQQ satellite.

---

## Architecture (Locked — Confirmed in Session)

### Data Sources

| Source | What It Does | How Accessed |
|--------|-------------|--------------|
| **IBKR Watchlist** (web UI) | Morning regime check — 5 ETFs × 9 columns: IV Rank, IV Pctl, IV/HV, Price/EMA(200/50), P/C Volume | Screenshot → `/ibkr-scan` skill |
| **TradingView** | Chart confirmation for the 1 ETF that passed scan — trend strength, support levels | Screenshot → `/chartreview` skill |
| **Tradier REST API** | Live options chain for that ETF — strikes, deltas, premiums, bid/ask | Called by `/api/options/analyze` |
| **OptionsIQ backend** | Strike selection, expected move, exit plan, paper trade log | Flask app, Tradier-powered |

### What Died

| Component | Why Dead |
|-----------|----------|
| **IB Gateway API** (IBWorker, reqHistoricalData) | IBKR watchlist gives IV Rank/Pctl/IV-HV computed for free via its own UI. We were rebuilding what IBKR already computes. |
| **BOD batch** (9:31 AM chain warm) | Tradier is <500ms REST. Nothing to pre-warm. |
| **EOD IV batch** (reqHistoricalData seeding) | IBKR watchlist `52wk IV Rank` + `52wk IV Pctl` are authoritative and real-time. iv_history.db was a workaround. |
| **scanner_service.py** | Replaced by `/ibkr-scan` skill |
| **sector_scan_service.py** | Replaced by IBKR watchlist (5 ETF universe, not 15) |
| **best_setups_service.py** | Replaced by `/ibkr-scan` skill |

### Three Claude Skills

| Skill | Input | Output | Answers |
|-------|-------|--------|---------|
| `/ibkr-scan` | IBKR watchlist screenshot (5 ETFs × 9 cols) | Scored table + top pick + direction | "Is the vol environment right?" |
| `/chartreview` | TradingView screenshot + scan context | Chart GO / WAIT + key S/R levels | "Is the trend supporting this trade?" |
| `/catalyst-check` | Ticker + DTE (e.g. "XLF 35") | Events in window + hidden risks | "What don't I know that could blow this up?" |

### `/catalyst-check` Skill Design

The question it answers: **"Why might this ETF move unexpectedly in the next N days?"**

**Step 1 — Macro events in DTE window**
Read `constants.py` FOMC_DATES + MACRO_DATES (CPI/NFP/PCE). Flag any event falling inside the trade window. Weight by impact: FOMC > CPI > NFP > PCE for rate-sensitive ETFs (XLF). All are equal weight for equity ETFs (SPY/QQQ/IWM).

**Step 2 — Holdings earnings in window**
Read `constants.py` COMPANY_EARNINGS + ETF_KEY_HOLDINGS. Flag any major holding with earnings inside the window. Include % weight in the ETF. Example: "JPM (11.2% of XLF) reports Jul 15 — OUTSIDE your 35-day window ✅"

**Step 3 — Live catalyst search**
Web search: `[TICKER] options catalyst [current month]` + `[TICKER] risk next 30 days`
Surface: any sector-specific news the market is pricing in (regulatory risk, earnings surprises, macro thesis shifts).

**Step 4 — Hidden risk synthesis**
The non-obvious questions a quant trader asks:
- Is there a FOMC inside the DTE window? Rate-sensitive ETFs (XLF) need wider strikes.
- Is options vol expanding or contracting today? (Opt Imp Vol Change from watchlist — rising IV before entry = dangerous for sellers, wait for it to peak)
- Is this ETF above or below its earnings pin? (Major sector earnings just passed = IV crush already happened, less premium available)
- What would make this trade fail? (Explicit worst-case framing)

**Output Example:**
```
XLF CATALYST CHECK — 35 DTE window (May 26 → June 30)

MACRO IN WINDOW:
  ⚠️ Jun 11-12: FOMC Rate Decision — XLF is rate-sensitive. Major catalyst.
  ⚠️ Jun 6: NFP Jobs Report — broad market + financials mover.

HOLDINGS EARNINGS:
  JPM (11.2%): Jul 15 → OUTSIDE window ✅
  BAC (8.1%): Jul 15 → OUTSIDE window ✅

LIVE CONTEXT: [web search result]

HIDDEN RISKS:
  - FOMC inside window. Hawkish surprise = XLF -3-5% possible.
  - Your put at $49 needs XLF to stay above $49 through FOMC.
  - Suggested: widen strike 1 delta lower OR reduce DTE to 20 days (before FOMC).

VERDICT: ⚠️ Proceed with caution. FOMC risk is real for XLF.
         Recommended adjustment: use delta 0.15 instead of 0.20.
```

### ETF Universe (LOCKED — Day 56 Multi-LLM Research)

| # | ETF | Role | Status |
|---|-----|------|--------|
| 1 | QQQ | Tech/growth primary proxy — deepest liquid chain | ✅ Locked |
| 2 | IWM | Small cap — genuine regime divergence from QQQ | ✅ Locked |
| 3 | XLF | Financials — rate-sensitive, FOMC catalyst machine | ✅ Locked |
| 4 | GLD | Non-equity vol — gold macro drivers, true diversification | ✅ Locked (Research 1) |
| 5 | TQQQ | Satellite — high premium, leveraged, strict rules | ✅ Locked (Research 1) |

**SPY dropped** — redundant with QQQ + XLF + IWM. Adds no new IV regime. $75K notional per put on $50K account consumes margin without diversification benefit.

**TQQQ satellite rules (non-negotiable):**
- Delta: **0.10 max** (4/4 LLMs unanimous)
- Regime: QQQ above 200 EMA + VIX < 18 + QQQ 50-DMA rising
- Size: 1-2% account risk max per trade
- Exit: Close at 1.5-2x credit OR on QQQ breakdown below 50-DMA — no exceptions, no rolling down
- Block: QQQ below 50-DMA → no new TQQQ puts. QQQ below 200-DMA → hard block.

**GLD rules:**
- Delta: 0.15-0.20 (standard)
- DTE: 30-45 DTE
- Stop: Hard stop at 2-3x premium collected — commodities have no structural upward bias, do NOT roll down indefinitely
- Avoid: Immediately before FOMC, CPI, major USD events

---

## The Reframe (What Changed This Session)

We came in thinking we had data gaps. We don't. The IBKR watchlist already computes:
- IV Rank (13wk, 26wk, 52wk) → real-time, no batch needed
- Implied Vol / Historical Vol ratio → IV/HV directly
- Put/Call Volume ratio → sentiment signal
- Price/EMA(20/50/200) → trend position numerically (% above or below each EMA)

Every planned feature we were going to code — STA SMA batch (GAP-001), compute_put_call_ratio() (GAP-003), chart trend gate — is already in IBKR sitting unused.

The real architecture is: **use IBKR watchlist as the data dashboard, use Claude as the reading engine, use OptionsIQ backend only for what it's uniquely good at (Tradier chain analysis + paper trade log).**

---

## Three Strategic Changes (Locked)

1. **5-ETF universe only** — SPY, QQQ, IWM, XLF, TQQQ (already configured in IBKR watchlist)
2. **Single-legged options only** — sell_put, sell_call, buy_call, buy_put (no spreads)
3. **Human-in-the-loop with IBKR watchlist screenshot** — replaces programmatic scan entirely

---

## The Decision Workflow (30-Year Quant Design)

```
MORNING ROUTINE (10 minutes total)

STEP 1: Open IBKR watchlist (pre-configured, 5 ETFs × 12 columns) — 30 seconds
STEP 2: Screenshot → paste to /ibkr-scan skill — 30 seconds
STEP 3: Claude reads screenshot, scores all 5 ETFs, says: 
         "Trade XLF sell_put. IVR=47%, IV/HV=1.15, above 200 EMA, P/C=0.85 (bullish)" — 60 seconds
STEP 4: If GO on 1 ETF → open TradingView for that ETF only (confirm S/R levels) — 3 min
STEP 5: Run /api/options/analyze → get 3 strike options + expected move + exit plan — 60 seconds
STEP 6: Pick strike, log paper trade — 2 minutes

TOTAL: ~8 minutes. Zero manual data collection. Zero scanning 15 ETFs.
```

---

## IBKR Watchlist Configuration (What to Add)

User configures these columns in IBKR "Manage Columns" (already shown in screenshots):

### Mandatory Columns (Layer 1+2 — Regime + IV Gate)
| Column | Category | What It Tells Us |
|--------|----------|-----------------|
| Last | Prices | Current price |
| Change % | Prices | Today's momentum direction |
| 52wk IV Rank | Options | Is premium elevated? (≥35% = sell, <25% = buy or wait) |
| Implied Vol % | Options | Current ATM IV absolute level |
| Hist Vol Close % | Options | 20-day realized vol (HV) |
| Implied Vol/Hist Vol % | Options | VRP ratio — is IV > HV? (≥105% = sell premium) |

### Mandatory Columns (Layer 3 — Trend Gate, replaces GAP-001)
| Column | Category | What It Tells Us |
|--------|----------|-----------------|
| Price/EMA(20) | Technical Indicator | % above/below 20 EMA (short-term trend) |
| Price/EMA(50) | Technical Indicator | % above/below 50 EMA (intermediate trend) |
| Price/EMA(200) | Technical Indicator | % above/below 200 EMA (long-term regime) |

### Mandatory Columns (Layer 4 — Sentiment, replaces GAP-003)
| Column | Category | What It Tells Us |
|--------|----------|-----------------|
| Put/Call Volume | Options | <0.8 = bullish, >1.3 = bearish |
| Option Open Interest | Options | Chain liquidity health |

### Total: 12 columns. One watchlist screenshot = complete decision input.

---

## Data Gap Resolution (Updated)

| Gap | Previous Plan | New Plan |
|-----|--------------|----------|
| GAP-001: Chart trend (SMA/EMA) | Build fetch_etf_sma_batch() ~50 lines | IBKR Price/EMA(20/50/200) columns — **zero code** |
| GAP-002: Skew gate | Wire compute_skew() in gate_engine | Visible in IV Rank + IV/HV columns — **advisory, human reads it** |
| GAP-003: Put/Call ratio | Build compute_put_call_ratio() ~30 lines | IBKR Put/Call Volume column — **zero code** |
| IV Rank (IVR) | IBKR EOD batch → iv_history.db computation | IBKR 52wk IV Rank column real-time — **BOD batch may be redundant** |
| HV (20-day) | IBKR EOD OHLCV batch | IBKR Hist Vol Close % column — **real-time** |
| IV/HV ratio | Computed in analyze_service.py | IBKR Implied Vol/Hist Vol % — **direct** |

**Quant trader observation:** The EOD IBKR batch job (the part we hate — IB Gateway API pain) may become redundant. The watchlist gives IV Rank + HV + IV/HV in real-time during market hours. The BOD cache matters for after-hours analysis, but if we're doing this as a morning routine, we look at live IBKR data directly.

**Decision pending:** Do we keep the BOD batch? Arguments:
- Keep: useful for persistence, historical IVR percentile is more accurate over 52wk than IBKR's intraday computation
- Remove: simplifies architecture dramatically, IBKR's own 52wk IV Rank is correct and authoritative
- **Lean: keep for paper trade records / audit trail, but don't rely on it for daily decision**

---

## New Slash Command: `/ibkr-scan`

**Replaces:** Best Setups tab scan, sector_scan_service.py, scanner_service.py  
**Input:** Screenshot of IBKR watchlist (5 ETFs × 12 columns)  
**Output:** Scored ETF decision table + top pick + direction recommendation

### Decision Logic (Claude reads screenshot and applies these rules)

**Layer 1 — Macro Regime (SPY/QQQ anchor)**
- Price/EMA(200) for SPY: positive → bull regime → sell puts OK
- Price/EMA(200) for SPY: negative → bear regime → NO sell puts (sell calls only or wait)
- VIX level: if TQQQ Change% extreme (>5% intraday) → VIX likely elevated → reduce size warning

**Layer 2 — IV Gate (per ETF)**
- 52wk IV Rank ≥ 35% + IV/HV ≥ 105% → SELL PREMIUM candidate
- 52wk IV Rank < 25% → BUY PREMIUM candidate (or wait)
- 25-35% IVR → neutral, marginal

**Layer 3 — Trend Gate (per ETF, most important gate)**
- Price/EMA(200) > 0 AND Price/EMA(50) > 0 → UPTREND → sell_put OK
- Price/EMA(200) < 0 AND Price/EMA(50) < 0 → DOWNTREND → NO sell_put, sell_call if IVR elevated
- Price/EMA(200) > 0 but Price/EMA(50) < 0 → PULLBACK within uptrend → proceed with caution, use lower delta
- Price/EMA(200) < 0 but price above 50 EMA → counter-trend bounce → WAIT, don't force trade

**TQQQ Special Rules:**
- Only sell puts when: SPY Price/EMA(200) > +1% (comfortably above, not just barely)
- Only sell puts when: TQQQ Price/EMA(50) > 0 (intermediate uptrend)
- Max delta: 0.15 regardless of IVR
- If TQQQ Change% > +5% today → likely IV elevated from vol crush → check before trading

**Layer 4 — Sentiment Check (per ETF)**
- Put/Call Volume < 0.8 → market buying calls = bullish → confirms sell_put
- Put/Call Volume > 1.3 → market buying puts = bearish → warns against sell_put, favors sell_call
- Put/Call 0.8-1.3 → neutral, don't factor in

**Scoring (0-6 per ETF):**
```
+2: IVR ≥ 35% AND IV/HV ≥ 105%
+2: Price/EMA(200) and Price/EMA(50) aligned with direction
+1: Put/Call Volume confirms direction
+1: OI > threshold (chain is liquid)
-1: IVR < 25% (premium too cheap)
-2: Trend opposes direction (BLOCK — do not override)
```

### Output Format
```
IBKR WATCHLIST SCAN — May 26, 2026 10:15 AM

SPY  | IVR: 28% | IV/HV: 1.08 | Trend: +2.3% above 200EMA | P/C: 0.75 | Score: 3/6 | Direction: sell_put (IVR marginal)
QQQ  | IVR: 31% | IV/HV: 1.12 | Trend: +1.8% above 200EMA | P/C: 0.82 | Score: 4/6 | Direction: sell_put
IWM  | IVR: 42% | IV/HV: 1.19 | Trend: -0.5% below 50EMA  | P/C: 1.10 | Score: 3/6 | Direction: PULLBACK — lower delta only
XLF  | IVR: 47% | IV/HV: 1.21 | Trend: +3.1% above 200EMA | P/C: 0.85 | Score: 6/6 | Direction: sell_put ✅
TQQQ | IVR: 61% | IV/HV: 1.34 | Trend: +4.2% above 200EMA | P/C: 0.71 | Score: 5/6 | Direction: sell_put (delta ≤0.15)

TOP PICK: XLF sell_put — IVR elevated, VRP present, trend aligned, bullish sentiment
NEXT STEP: Run /api/options/analyze?ticker=XLF&direction=sell_put
```

---

## What OptionsIQ Backend Does After /ibkr-scan

After `/ibkr-scan` identifies the ETF + direction:

```
POST /api/options/analyze { ticker: "XLF", direction: "sell_put" }
```

Backend (Tradier chain) returns:
```
STRIKE SELECTION — XLF sell_put (May 26, 2026)
Underlying: $51.90 | IV: 28% | DTE: 32 days (June 27)

Expected Move (±1σ): ±$3.20 by June 27

Rank 1: Strike $47 | Delta 0.15 | Premium $0.48 | PoP 85%
         Strike is $4.90 OTM (1.53× expected move) ✅ Outside 1σ
         Exit plan: Close at $0.24 (50% profit) or June 6 (21 DTE), whichever first

Rank 2: Strike $48 | Delta 0.20 | Premium $0.62 | PoP 80%
         Strike is $3.90 OTM (1.22× expected move) ⚠️ Near 1σ boundary
         Exit plan: Close at $0.31 or June 6

Rank 3: Strike $49 | Delta 0.28 | Premium $0.89 | PoP 72%
         Strike is $2.90 OTM (0.91× expected move) ⚠️ INSIDE expected move
         Higher premium but statistically unfavorable — quant would avoid
```

**New fields to add to analyze response (not currently there):**
1. `expected_move`: IV × √(DTE/365) × underlying_price (±1σ)
2. `strike_vs_expected_move`: how many σ OTM is the strike
3. `exit_plan`: `{ profit_target_pct: 50, profit_target_credit: 0.24, dte_exit: 21, exit_date: "June 6" }`

---

## Architecture: What Changes vs What Stays

### Stays (no change needed)
- `backend/app.py` + `/api/options/analyze` endpoint
- `tradier_provider.py` — live chain, strike/delta/premium data
- `gate_engine.py` — individual gates still run (some simplify)
- `pnl_calculator.py` — single-leg P&L (simpler now)
- `paper_trade` SQLite table + endpoints

### Simplifies (reduce complexity)
- `strategy_ranker.py` — remove all spread builders, keep single-leg only
- `gate_engine.py` — remove credit-to-width check
- `constants.py` — ETF_UNIVERSE 15→5, TQQQ_MAX_DELTA=0.15, remove spread constants

### Effectively Replaced (can deprecate)
- `scanner_service.py` — replaced by `/ibkr-scan` skill
- `sector_scan_service.py` — replaced by IBKR watchlist (15 ETF scan → 5 ETF watchlist)
- `best_setups_service.py` — replaced by `/ibkr-scan` skill
- `fetch_etf_sma_batch()` — never needed now (IBKR Price/EMA columns)
- BOD batch for IVR — IBKR watchlist gives 52wk IV Rank in real-time

### New (add)
- `.claude/commands/ibkr-scan.md` — the core daily skill
- `expected_move` field in analyze response (~5 lines)
- `exit_plan` field in analyze response (~5 lines)
- `strike_vs_expected_move` ratio in analyze response (~3 lines)

---

## TQQQ Special Rules (enforced by gate + displayed in output)

| Rule | Value | Why |
|------|-------|-----|
| Max delta | 0.15 | 3x leverage means 3x the move. Delta 0.15 gives PoP ~85%. |
| Min SPY regime | SPY Price/EMA(200) > +1% | Must be comfortably in bull regime, not at 200 EMA |
| Max position size | 25% of normal lot | TQQQ can move 15%+ in a day. Size accordingly. |
| DTE range | 21-35 DTE | 45 DTE is too much theta exposure on a leveraged ETF |
| Exit rule | 25% profit OR 14 DTE | Tighter exit than standard (leveraged decay) |
| BLOCK condition | Price/EMA(50) < 0 | If intermediate trend down, skip TQQQ entirely |

---

## Single-Legged Options — Strategy Rankings

### sell_put (primary strategy, ~70% of trades)
- R1: Delta 0.20 | PoP ~80% | "Standard" — best premium/risk balance
- R2: Delta 0.15 | PoP ~85% | "Conservative" — lower premium, higher PoP
- R3: Delta 0.28 | PoP ~72% | "Aggressive" — warned if strike inside expected move

### sell_call (secondary, used in downtrend)
- R1: Delta 0.20 OTM above underlying
- R2: Delta 0.15 OTM
- R3: Delta 0.25 (capped, warn if near expected move upside)

### buy_call (directional, strong trend)
- R1: Delta 0.68 ITM (high PoP directional play)
- R2: Delta 0.50 ATM (balanced)
- R3: Delta 0.30 OTM (lottery, explicitly labeled)

### buy_put (directional, confirmed downtrend)
- R1: Delta -0.68 ITM
- R2: Delta -0.50 ATM
- R3: Delta -0.30 OTM

---

## LLM Research Tasks (Run Before Any Implementation)

---

### Research 1 — 5th ETF Slot (Multi-LLM)

**Question:** Which ETF earns slot 5 alongside SPY, QQQ, IWM, XLF?  
**Candidates:** TQQQ, GLD, TLT, EEM, SOXL, XLE, ARKK  
**Run on:** GPT-4o, Gemini, Grok, Claude Opus (4 independent answers)  
**Filler until complete:** TQQQ

#### Prompt (same prompt, all 4 LLMs)
```
I sell options premium (naked puts and naked calls) on ETFs for a personal ~$50K account.
I have locked in 4 ETFs: SPY, QQQ, IWM, XLF.
I need exactly 1 more ETF for slot 5. Candidates: TQQQ, GLD, TLT, EEM, SOXL, XLE.

Evaluate each candidate on these criteria:
1. Average daily options volume (contracts/day) — is the chain deep enough for retail fills?
2. Bid-ask spread on near-ATM options — as % of mid price. Under 2% = good.
3. How many weeks per year does 52wk IV Rank reach ≥35%? (seller threshold)
4. Does it offer meaningful IV REGIME DIVERSIFICATION from SPY/QQQ/IWM/XLF?
   (i.e., does its IV spike at different times than equity fear events?)
5. Weekly expirations available? (required for 30-45 DTE seller strategy)

Then answer these directly:
A. SPY and QQQ are highly correlated. Do I genuinely need both, or am I duplicating?
   When do they diverge meaningfully enough to justify holding both?

B. Is TQQQ appropriate for a $50K account selling naked puts?
   - What was the worst drawdown scenario for TQQQ in recent years?
     Give me the most recent significant bear market you know of.
     If I had a 0.15 delta put open during that event, what was the realistic loss?
     What early warning signals would have told me to close before the worst of it?
   - What regime conditions MUST be true before selling TQQQ puts?
   - Correct delta for TQQQ: 0.10, 0.15, or 0.20?

C. Does GLD or TLT give genuine diversification for a premium seller?
   Does gold/bond vol behave independently from equity vol? When does it fail?

Give me your single top recommendation for slot 5 with the key rule for trading it.
Be brutally honest — tell me what's wrong before validating.
```

**Synthesis target:** 3/4 LLMs agree → slot 5 locked. Disagreement → pick the most conservative answer.

---

### Research 2 — IBKR Watchlist Columns (Single LLM, Deep Answer)

**Question:** What columns in the IBKR watchlist give genuine options-selling edge?  
**Run on:** Claude Opus (deepest reasoning) OR Perplexity (cited sources)  
**Goal:** Validate or replace my current 9-column set. Find the non-obvious ones.

#### Prompt
```
I am a premium seller (naked puts, naked calls) on 5 liquid ETFs (QQQ, IWM, XLF, GLD, TQQQ).
My morning decision: which ETF to trade today and in which direction.
I have 60 seconds to look at a watchlist.

Here is the COMPLETE list of columns available in IBKR "Manage Columns":

OPTIONS category:
- 13wk IV High — max intraday IV over last 13 weeks
- 13wk IV Low — min intraday IV over last 13 weeks
- 13wk IV Pctl — % of days IV closed below current IV (13wk window)
- 13wk IV Rank — rank of current IV between 13wk high and low
- 26wk IV High — max intraday IV over last 26 weeks
- 26wk IV Low — min intraday IV over last 26 weeks
- 26wk IV Pctl — % of days IV closed below current IV (26wk window)
- 26wk IV Rank — rank of current IV between 26wk high and low
- 52wk IV High — max intraday IV over last 52 weeks
- 52wk IV Low — min intraday IV over last 52 weeks
- 52wk IV Pctl — % of days IV closed below current IV (52wk window)
- 52wk IV Rank — rank of current IV between 52wk high and low
- Closing Impl Vol % — IV based on closing price
- Hist Vol Close % — historical volatility based on previous close
- Implied Vol % — current intraday implied volatility
- Implied Vol/Hist Vol % — IV divided by HV, as percentage (VRP ratio)
- In The Money — in-the-money value for an option contract
- Opt Imp Vol Change — absolute change in IV vs yesterday's value
- Opt Implied Volatility % — option implied volatility
- Opt Volume — total option volume today
- Opt Volume Change % — today's option volume as % of average option volume
- Option Open Interest — option open interest
- Put/Call Interest — put OI divided by call OI
- Put/Call Volume — put volume divided by call volume
- Time Value (%) — option premium in excess of intrinsic value
- Underlying Price — current price of the underlying

TECHNICAL INDICATOR category:
- EMA(20) — exponential moving average, N=20 (absolute price)
- EMA(50) — exponential moving average, N=50 (absolute price)
- EMA(100) — exponential moving average, N=100 (absolute price)
- EMA(200) — exponential moving average, N=200 (absolute price)
- Price/EMA(20) — (price/EMA(20) - 1) × 100, shown as %
- Price/EMA(50) — (price/EMA(50) - 1) × 100, shown as %
- Price/EMA(100) — (price/EMA(100) - 1) × 100, shown as %
- Price/EMA(200) — (price/EMA(200) - 1) × 100, shown as %

Question 1 — IV Rank vs IV Percentile:
Which is more PREDICTIVE of whether premium selling will be profitable over the next 30 days?
Should I use 13wk, 26wk, or 52wk window?
Academic research and practitioner consensus? At what threshold for each?

Question 2 — IV/HV ratio (VRP):
What threshold ratio signals genuine edge vs selling cheap vol?
≥1.05? ≥1.10? ≥1.20? What does Sinclair's research say?
Does this column alone beat IV Rank as a timing signal?

Question 3 — Trend filter:
For premium sellers, is Price/EMA(200) sufficient as a "no sell puts" filter?
Or do serious practitioners use a faster signal (50 EMA pullback detection)?
What does the data say about selling puts below the 200 EMA — actual win rate impact?

Question 4 — Put/Call ratio:
Does Put/Call VOLUME ratio have genuine predictive value for ETF options?
Or is it noise that retail traders overweight? Cite evidence either way.
Is Put/Call INTEREST ratio better or worse than volume ratio for this purpose?

Question 5 — The non-obvious one:
From the full column list above, what would a professional options desk use that most retail traders ignore?
What separates a $50K amateur from a prop desk when evaluating whether to sell premium today?

Question 6 — My proposed 9 columns:
  52wk IV Rank, 52wk IV Pctl, Implied Vol/Hist Vol%, Opt Implied Volatility%,
  Price/EMA(200), Price/EMA(50), Opt Imp Vol Change, Put/Call Volume, Opt Volume Change%

Are any of these redundant or misleading? What would you remove and what would you add?
Pick only from the columns listed above — maximum 10, minimum noise.
Be brutally honest — cite evidence, not opinion.
```

**Output to save:** `docs/Research/ETF_Universe_5_Day56.md` (combined synthesis of both research tasks)

---

## Open Questions (Not Yet Decided)

1. **Slot 5: TQQQ vs GLD vs TLT?** 
   - Claude recommendation: TQQQ (most premium per capital, already in system)
   - Decision: await GPT/Gemini/Grok responses
   
2. **Do we keep BOD/EOD IBKR batch?**
   - Pro keep: historical audit trail, paper trade records, after-hours IVR
   - Pro remove: IBKR watchlist gives same data in real-time during market hours
   - Lean: keep EOD batch for historical IV seeding (IVR percentile accuracy), remove BOD batch

3. **Do we deprecate sector_scan_service.py and best_setups_service.py?**
   - These are replaced by `/ibkr-scan` skill
   - Lean: deprecate (delete) after new workflow is validated over 2 weeks

4. **Frontend: does Best Setups tab survive?**
   - Current: programmatic scan result displayed in UI
   - New: scan is a Claude skill (screenshot-based), not a UI tab
   - Lean: replace Best Setups tab with "Today's Trade" — shows the output from /ibkr-scan manually pasted + analysis result

---

## Implementation Sequence (After Research Synthesis)

**Phase 0 (Today): Research**
- User runs Prompts A/B/C externally
- Synthesize into `docs/Research/ETF_Universe_5_Day56.md`
- Lock the 5-ETF list

**Phase 1 (~1 day): `/ibkr-scan` command**
- Create `.claude/commands/ibkr-scan.md`
- User configures IBKR watchlist with 12 columns
- Test with real watchlist screenshot

**Phase 2 (~1 day): Analyze response enrichment**
- Add `expected_move` to analyze_service.py
- Add `exit_plan` to analyze response
- Add `strike_vs_expected_move` ratio
- Update TopThreeCards.jsx to display

**Phase 3 (~1 day): Single-leg simplification**
- `strategy_ranker.py`: remove spread builders
- `gate_engine.py`: remove credit-to-width check
- `constants.py`: ETF_UNIVERSE 15→5, add TQQQ_MAX_DELTA

**Phase 4 (~1 day): Deprecation**
- Deprecate scanner_service.py, sector_scan_service.py, best_setups_service.py
- Remove or archive Best Setups tab
- Run all tests (44 → some removed, target ~25 focused tests)

---

## Files Modified (Final Inventory)

| File | Change | Priority |
|------|--------|----------|
| `.claude/commands/ibkr-scan.md` | NEW — core daily skill | P1 |
| `backend/analyze_service.py` | Add expected_move + exit_plan + strike_vs_em | P2 |
| `backend/strategy_ranker.py` | Remove spread builders, single-leg only | P3 |
| `backend/gate_engine.py` | Remove credit-to-width check | P3 |
| `backend/constants.py` | ETF_UNIVERSE 15→5, TQQQ_MAX_DELTA=0.15 | P3 |
| `frontend/.../TopThreeCards.jsx` | Display expected move + exit plan | P2 |
| `frontend/.../BestSetups.jsx` | Replace or archive | P4 |
| `backend/scanner_service.py` | Deprecate | P4 |
| `backend/sector_scan_service.py` | Deprecate | P4 |
| `backend/best_setups_service.py` | Deprecate | P4 |
| `docs/Research/ETF_Universe_5_Day56.md` | NEW — LLM research synthesis | P0 |
