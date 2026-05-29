# IBKR Watchlist Setup — OptionsIQ v0.35.0
> **Watchlist name:** Options_IQ_Claude
> **Last verified:** Day 56 (May 28, 2026)
> **Status:** LOCKED — 9 columns confirmed live from screenshot

---

## Tickers (6 rows)

| # | Ticker | Role | Trade? |
|---|--------|------|--------|
| 1 | SPY | Regime anchor | No — context only |
| 2 | QQQ | Tech/growth primary | Yes |
| 3 | IWM | Small cap divergence | Yes |
| 4 | XLF | Financials, rate-sensitive | Yes |
| 5 | TQQQ | Satellite, high premium | Yes (strict rules) |
| 6 | GLD | Non-equity diversifier | Yes |

SPY is kept as a regime-only row. If Price/EMA(200) for SPY is negative → bear regime → no sell_put on any ticker.

---

## Column Configuration

**How to add:** IBKR Watchlist → edit icon (pencil, top right) → Manage Columns

### Exact column names as they appear in IBKR UI
> LOCKED — 3/3 LLMs (GPT-4o + Gemini + Claude). Day 57.

| # | IBKR Display Name | Manage Columns Category | Role in Decision |
|---|-------------------|------------------------|-----------------|
| 1 | UNDERLYING PRICE | Options | Price anchor — base reference for all decisions |
| 2 | 52 WEEK IV RANK | Options | Historical vol elevation (≥ 35 acceptable, ≥ 50 strong) |
| 3 | 52 IV PERC. | Options | Primary IV signal — spike-resistant (≥ 60% tradable, ≥ 75% strong) |
| 4 | IMPLIED VOL./HIST. VOL % | Options | Core VRP signal (≥ 110% tradable, ≥ 120% strong) |
| 5 | OPT. IMP. VOL. CHANGE | Options | IV direction — ≤ 0 = sell window, > +1.0 = wait |
| 6 | OPT. VOLUME CHANGE % | Options | Unusual activity flag (> 200% = hidden catalyst) |
| 7 | OPT VOLUME | Options | Absolute chain liquidity (critical for GLD/TQQQ) |
| 8 | PUT/CALL VOLUME | Options | Sentiment context only — > 1.5 = wait, < 0.5 = complacency |
| 9 | PRICE/EMA(200) | Technical Indicator | Hard regime gate — below = no sell_put |
| 10 | PRICE/EMA(50) | Technical Indicator | Pullback detector — below = reduce delta to 0.15 |

**Removed from prior version:** `OPT. IMPLIED VOLATILITY %` — redundant with IV Rank + IV Pctl + IV/HV
**Added:** `UNDERLYING PRICE` (missing anchor), `OPT VOLUME` (absolute liquidity)
**Default columns to keep:** LAST
**Columns to remove:** CHANGE %, VOLUME (stock volume), BID, ASK

---

## How to Read Each Column

### PRICE/EMA(200)
- Shows as `+11.78%` (above) or `-0.51%` (below)
- **> 0:** Bull regime. Sell puts OK.
- **< 0:** Bear regime. Hard block on sell_put. Consider sell_call only.
- **TQQQ special:** Must be > +1% (comfortably above, not just barely)

### PRICE/EMA(50)
- Shows as `+10.04%` (above) or `-3.51%` (below)
- **> 0 AND EMA(200) > 0:** Healthy uptrend. Full size, standard delta.
- **< 0 AND EMA(200) > 0:** Pullback in uptrend. Reduce delta (0.15 not 0.20). Proceed with caution.
- **< 0 AND EMA(200) < 0:** Confirmed downtrend. Hard block.
- **TQQQ special:** If < 0, skip TQQQ entirely regardless of other signals.

### 52 WEEK IV RANK
- Shows as raw number (e.g., `38`, not `38%`)
- **≥ 35:** IV historically elevated. Sell premium candidate.
- **25–34:** Marginal. OK if IV/HV ≥ 110% and other signals strong.
- **< 25:** IV too cheap. Wait.

### 52 IV PERC.
- Shows as percentage (e.g., `68%`)
- **≥ 75%:** Strong signal. Best premium-selling conditions.
- **60–74%:** Tradable. Primary threshold for sell premium.
- **50–59%:** Marginal. Only proceed if IV/HV ≥ 1.20 and all other signals align.
- **< 50%:** Skip. IV not genuinely elevated on a frequency basis.
- **Use both:** If IV Rank ≥ 35 AND IV Pctl ≥ 60% → tradable. If they diverge, trust Pctl.
- **Key case:** IV Rank 28%, Pctl 62% → a prior spike deflated Rank. Pctl says elevated → lean toward sell.

### IMPLIED VOL./HIST. VOL %
- Shows as percentage (e.g., `123.7%` = IV is 1.237× HV)
- **≥ 110% (1.10×):** VRP present. Working sell signal.
- **105–110%:** Marginal. Transaction costs eat the edge. Reduce size.
- **< 105%:** Do not sell. Premium is not elevated relative to realized vol.
- **< 100%:** IV is actually CHEAP relative to realized vol. Buy premium environment, not sell.

### OPT. IMPLIED VOLATILITY %
- Shows as percentage (e.g., `20.1%` for QQQ, `60.2%` for TQQQ)
- Use for sizing context only (not a pass/fail gate)
- Higher IV% = higher margin requirement, higher premium collected
- TQQQ at 60%+ is normal for a 3× leveraged ETF

### OPT. IMP. VOL. CHANGE
- Shows as decimal (e.g., `-0.580`, `+0.246`)
- **≤ 0 (flat or falling):** IV compressing. Sell window. Premium at or near peak.
- **0 to +1.0:** Minor uptick. Proceed but note it.
- **> +1.0:** IV actively rising. Wait. Someone is positioning or a catalyst is developing. Selling into rising IV gets worse fills and starts underwater.
- This is the non-obvious edge column. Retail traders ignore it. Don't.

### OPT. VOLUME CHANGE %
- Shows as percentage (e.g., `96.519%`, `110.950%`)
- Baseline is 80–100% (normal daily variation)
- **> 200%:** Unusual options activity spike. Hidden catalyst risk. Investigate before trading.
- **Normal range:** Ignore.

### PUT/CALL VOLUME
- Shows as ratio (e.g., `1.20`, `0.72`)
- **< 0.5:** Complacency. Market buying calls heavily. Pullback risk.
- **0.5–1.5:** Neutral. Don't factor in.
- **> 1.5:** Fear. Market buying puts heavily. IV elevated but risky for naked sellers. Wait for vol to peak.
- **Note:** IWM and equity ETFs run structurally higher P/C than GLD/TQQQ. Context matters.

---

## Decision Matrix (Summary)
> Thresholds locked via multi-LLM research (GPT-4o + Gemini + Claude). Day 57.

### Best Setup — Desk Quality (all required)
- IV Pctl ≥ 75% AND IV/HV ≥ 120% AND both EMAs positive AND Opt Imp Vol Change ≤ 0

### Sell_Put — Tradable (all 3 required)
1. IV Pctl ≥ 60% AND IV Rank ≥ 35
2. IV/HV ≥ 110%
3. Opt Imp Vol Change ≤ 0

### Sell_Put — WAIT (any 1 pauses the trade)
- Opt Imp Vol Change > +1.0 (IV actively rising — wait for peak)
- Opt Volume Change% > 200% (unusual activity — hidden catalyst)
- Put/Call Volume > 1.5 (market fearful — wait for vol to peak)
- Price/EMA(50) < 0 (reduce delta to 0.15 max, not full block)

### Hard Block (any 1 kills sell_put)
- Price/EMA(200) < 0
- IV Pctl < 50% AND IV/HV < 105%
- TQQQ: Price/EMA(50) < 0

---

## TQQQ Special Rules (Satellite)

| Rule | Value |
|------|-------|
| Max delta | 0.10 (not 0.15-0.20 standard) |
| Regime requirement | SPY Price/EMA(200) > +1% (comfortably bull) |
| Trend requirement | TQQQ Price/EMA(50) > 0 |
| Max size | 1-2% account risk (25% of normal lot) |
| DTE | 21-35 DTE (shorter than standard) |
| Exit | 25% profit OR 14 DTE, whichever first |

---

## GLD Special Rules

| Rule | Value |
|------|-------|
| IV/HV minimum | 110% (GLD has no structural upward bias — don't sell cheap vol) |
| IV Rank minimum | 35 (GLD mutes for long stretches — wait for genuine elevation) |
| Hard stop | 2-3× premium collected. Never roll down indefinitely. |
| Avoid | Immediately before major FOMC, CPI, USD events |

---

## Sample Reading (May 28, 2026)

| ETF | IVR | Pctl | IV/HV | IV Chg | P/EMA200 | P/EMA50 | Verdict |
|-----|-----|------|-------|--------|----------|---------|---------|
| SPY | 15 | 27% | 123% | -0.63 | +11.78% | +5.64% | Regime: BULL ✅ |
| QQQ | 38 | 68% | 124% | -0.58 | +19.74% | +10.04% | **SELL PUT ✅** |
| IWM | 28 | 47% | 119% | -0.78 | +15.03% | +6.69% | Wait — IVR < 35 |
| XLF | 23 | 41% | 115% | -0.55 | -0.51% | -0.16% | **HARD BLOCK** (below 200 EMA) |
| TQQQ | 44 | 71% | 124% | -1.71 | +56.36% | +28.95% | Satellite candidate (delta 0.10) |
| GLD | 22 | 52% | 94% | +0.25 | +2.97% | -3.51% | No trade — IV/HV < 1.0 |
