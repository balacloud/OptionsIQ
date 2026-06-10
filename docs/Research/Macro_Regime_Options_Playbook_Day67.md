# Macro Regime Options Playbook
> **Day 67 (Jun 6, 2026)**
> **Status:** Standalone research — not yet wired into OptionsIQ
> **Purpose:** Cyclical macro patterns with mechanical fundamental links, ranked by reliability and options tradability

---

## What Makes a Pattern Worth Trading

The best macro patterns share three properties:
1. **Mechanical link** — a clear fundamental cause → effect (not just historical correlation)
2. **Observable trigger** — a real-time signal you can watch (yield spread, VIX level, CPI print)
3. **Options-friendly** — defined duration, clear direction, IV environment suits the structure

---

## Tier 1 — Mechanically Reliable

### 1. Yield Curve Steepening → Banks
**The link:** Banks borrow short (deposits, fed funds) and lend long (mortgages, commercial loans). Net interest margin (NIM) directly tracks the spread between short and long rates. Steeper curve = wider NIM = more earnings.

**Watch:** 10-year yield minus 2-year yield (10Y–2Y spread)
**Trigger:** Spread turns positive after inversion, or steepens > 50bps from trough
**Direction:** Bullish on XLF / RY / TD / JPM
**Options structure:** Bull Call Spread — 45 DTE, buy ATM call + sell OTM call
**Historical instances:** 1994–95, 2004–06, 2010–11, 2022–23 (post-inversion steepening)
**Caution:** Works in the steepening phase. Inverted curve (2Y > 10Y) is bearish for banks — do not sell puts during inversion.

---

### 2. Fed Pivot to Cutting → Tech/Growth (QQQ)
**The link:** Tech stocks are long-duration assets — their value is the discounted present value of future earnings. Lower discount rate (fed funds) increases that present value mechanically. Growth stocks with earnings 5–10 years out benefit most.

**Watch:** Fed dot plot, FOMC statement language
**Trigger:** Language shifts from "higher for longer" to "data dependent" to first cut
**Direction:** Bullish on QQQ, TQQQ (carefully), XLK
**Options structure:** Bull Call Spread — 60–90 DTE (give the move time to develop)
**Historical instances:** 1998, 2001 (delayed 18mo), 2008 (delayed), 2019, 2020, 2024
**Caution:** 2001 and 2008 had cuts but market kept falling — recession was the issue. Requires SPY above 200 EMA (regime anchor) to avoid catching a falling knife.

---

### 3. VIX Spike → Mean Reversion (Premium Selling)
**The link:** VIX represents 30-day implied volatility of S&P 500 options. When panic is acute, IV overestimates actual realized volatility — sellers of that panic premium collect edge. VIX above 40 has NEVER sustained more than 90 days in 30 years of data.

**Watch:** VIX index
**Trigger:** VIX > 35 (elevated), > 40 (crisis — maximum edge for sellers)
**Direction:** Neutral to bullish — sell puts on QQQ/SPY
**Options structure:** Sell OTM puts (OptionsIQ core workflow), 30–45 DTE
**Historical instances:** 1998 (LTCM), 2002 (dot-com), 2008–09, 2011 (EU crisis), 2020 (COVID), 2022 (rate shock)
**Caution:** This is the OptionsIQ core pattern. VIX gate (hard block > 40) handles the one failure mode — extreme panic can persist 3–6 weeks before IV crush begins.

---

### 4. Rising CPI + Falling Real Rates → Gold (GLD)
**The link:** Gold pays no yield. It competes with real (inflation-adjusted) bond yields. When real rates go negative (inflation > nominal yield), gold becomes the better store of value. Mechanically: Real rate = 10Y nominal yield − CPI. When this formula goes below zero, capital flows to gold.

**Watch:** Monthly CPI print + 10-year Treasury yield
**Trigger:** CPI exceeds 10Y yield (real rate negative), sustained 2+ months
**Direction:** Bullish on GLD
**Options structure:** Bull Call Spread — 45 DTE. Note: GLD IV/HV gate must pass (IV > HV × 1.10)
**Historical instances:** 2008–09, 2011–12, 2019–20, 2022–24
**Caution:** GLD skew inverts during rallies (calls get bid above puts — demand for upside exposure). Standard skew gate reads wrong for GLD — see GATE_REFERENCE.md.

---

## Tier 2 — Reliable, Longer/Messier Cycles

### 5. Oil Above Breakeven → Energy (XLE)
**The link:** Energy company free cash flow is directly (oil price − production cost). Breakeven for most US producers: $45–55/barrel. WTI sustained above $75 = strong margins + buybacks + dividends.

**Watch:** WTI crude price
**Trigger:** WTI breaks and holds above $75, OR OPEC announces production cut
**Options structure:** Bull Call Spread on XLE — 45–60 DTE
**Historical instances:** 2004–08, 2010–14, 2021–22

---

### 6. China Stimulus → Copper/Materials (XLB)
**The link:** China consumes 50–55% of global copper demand. Fiscal stimulus = infrastructure build = copper purchases. Copper prices respond within days of announcement.

**Watch:** PBOC rate decisions, China State Council fiscal announcements
**Trigger:** PBOC rate cut OR major infrastructure spending headline
**Options structure:** Bull Call Spread on XLB or FCX — 45 DTE
**Caution:** China headlines can be walk-backs. Wait for second confirmation before entry.

---

### 7. Mortgage Rate Drop → Homebuilders (XHB)
**The link:** 30-year fixed mortgage rate directly gates housing affordability. 50bps rate drop typically adds ~$50–80k to buyer purchasing power. New home orders surge within 60–90 days.

**Watch:** 30-year fixed mortgage rate (Freddie Mac weekly survey)
**Trigger:** Rate falls below 6.5% AND sustained (not one-week anomaly)
**Options structure:** Bull Call Spread on XHB — 60–90 DTE (longer lead time needed)
**Historical instances:** 2009, 2012, 2019–20, 2023

---

## Tier 3 — Seasonal / Statistical Only

| Pattern | Historical Hit Rate | Window | Structure |
|---------|-------------------|--------|-----------|
| September weakness | ~65% of years S&P negative | Short window Aug → Sep | Sell calls in late August |
| Santa Claus rally | ~75% | Dec 24 – Jan 2 | Bull Call Spread QQQ, very short DTE |
| January small-cap | ~60% | First 2 weeks January | Bull Call Spread IWM |
| "Sell in May" | ~55% (weakest) | May–October | Mild bias, not a standalone signal |

Tier 3 lacks a fundamental mechanism — patterns are partially arbitraged away and fail more in structural shifts. Use only as secondary confirmation, never primary signal.

---

## Decision Matrix: Which Structure for Which Pattern

| Trigger Type | Options Structure | Why |
|-------------|-----------------|-----|
| Known calendar event (FOMC, CPI, earnings) | Calendar Spread | Sell near-term theta, hold long-term directional |
| Directional macro regime (curve, pivot, oil) | Bull Call Spread | Cap cost, reduce theta drag vs naked long call |
| VIX spike / IV elevated | Sell puts (short premium) | Collect overpriced fear premium |
| Mean-reversion / range-bound | Sell straddle or iron condor | Theta harvest, no directional requirement |

---

## Regime Stacking (Most Powerful Setups)

The strongest setups occur when **2+ Tier 1 signals align simultaneously**:

- **Fed cut + VIX declining + QQQ above 200 EMA** → sell puts on QQQ (OptionsIQ sweet spot)
- **Yield curve steepening + CPI falling + XLF above 200 EMA** → Bull Call Spread XLF
- **Real rates negative + GLD above 200 EMA + IV/HV > 1.10** → Bull Call Spread GLD
- **VIX > 35 + SPY above 200 EMA (or at it)** → sell puts — maximum edge scenario

Avoid: any Tier 1 bullish signal when SPY is below its 200 EMA. Regime anchor overrides sector signal.

---

## Connection to OptionsIQ

| Pattern | Currently in OptionsIQ? | Gap |
|---------|------------------------|-----|
| VIX spike → sell puts | ✅ VIX regime gate | Core workflow |
| Yield curve → XLF | ⚠️ Partial (FOMC gate, hv_iv_vrp gate) | No yield curve signal wired |
| Fed pivot → QQQ | ⚠️ Partial (trend EMA gate) | No Fed language signal |
| Real rates → GLD | ✅ GLD IV/HV hard block | No real rate computation |
| Seasonal patterns | ❌ None | Low priority |

**Future idea:** A "macro regime dashboard" that reads: 10Y–2Y spread, VIX level, real rate (10Y minus CPI), oil price vs $75 breakeven — and flags which Tier 1 setups are currently active. Surfaces as a banner in the Signal Board.

---

## References
- Yield curve and bank NIM: Federal Reserve Bank of St. Louis FRED data
- VIX mean reversion: Cboe 30-year VIX history, tastylive 21-year study
- Real rates and gold: Erb & Harvey (2013) "The Golden Dilemma" — Journal of Portfolio Management
- Fed pivot and growth stocks: Fama & French factor research + Damodaran discount rate mechanics
- Canada-specific context: see `Canadian_TSX_Options_Day67.md`
