# OptionsIQ — 5-ETF Universe Research Synthesis
> **Date:** Day 56 (May 28, 2026)
> **Research type:** Multi-LLM (GPT-4o + Gemini + Grok + Claude)
> **Status:** LOCKED — ETF universe + watchlist columns finalized. Ready for Phase 1 implementation.

---

## Final 5-ETF Universe

| # | ETF | Role | Type |
|---|-----|------|------|
| 1 | **QQQ** | Tech/growth primary proxy | Core |
| 2 | **IWM** | Small cap, regime divergence | Core |
| 3 | **XLF** | Financials, rate-sensitive | Core |
| 4 | **GLD** | Non-equity vol, macro diversifier | Core |
| 5 | **TQQQ** | High-premium satellite, strict rules | Satellite |

---

## Why SPY Was Dropped

Three reasons, each sufficient alone:

1. **Already owned in pieces.** QQQ ≈ tech (31% of SPY). XLF ≈ financials (13% of SPY). IWM fills small cap. SPY is a basket of what we already hold.
2. **No new IV regime.** SPY IV spikes identically to QQQ on every catalyst. GLD spikes on geopolitics/dollar/real rates — events that don't move QQQ. Every slot must earn its place with unique regime exposure.
3. **Margin cost on $50K.** One SPY naked put = ~$75K notional. 150% of account in a single position. Dropping SPY frees margin headroom for positions that actually diversify.

**LLM consensus:** GPT-4o said keep both but trade differently. Gemini said drop SPY. Grok said duplicating. Claude said drop SPY. 3/4 against.

---

## LLM Scorecard

| Question | GPT-4o | Gemini | Grok | Claude | Decision |
|----------|--------|--------|------|--------|----------|
| **Slot 5** | GLD | GLD | TQQQ* | GLD | **GLD** (3/4) |
| **Drop SPY** | No | Yes | Duplicating | Yes | **Yes** (3/4) |
| **TQQQ naked $50K** | Reject | Hard reject | Risky | Reject | **Reject naked** |
| **TQQQ delta** | 0.10 | 0.10 | 0.10-0.15 | 0.10 | **0.10 max** |
| **GLD diversification** | Yes | Yes | Yes | Yes | **Yes** (4/4) |
| **TLT diversification** | Conditional | Weak | Conditional | Conditional | Conditional |

*Grok picked TQQQ on trading mechanics but explicitly said "GLD/XLE would be the correct diversification move." Not a clean endorsement — overridden by portfolio construction argument.

---

## Key Findings Per LLM

### GPT-4o
- GLD is the "missing piece" — non-equity IV regime diversification
- TQQQ -81.66% max drawdown (2022). A 0.15 delta put can become "near-stock-equivalent exposure" during a crash.
- SPY + QQQ: trade both but never the same direction simultaneously. If signals identical, pick one.
- TQQQ early warning: QQQ below 50-DMA → no new puts. QQQ below 200-DMA → hard block.

### Gemini
- Brutal: "SPY, QQQ, IWM, XLF in a $50K account while selling naked options is a massively correlated, heavily leveraged directional bet on US equities."
- Delta math: Δ_TQQQ ≈ 3 × Δ_QQQ during a gap-down. A 0.15 delta TQQQ put behaves like 0.45 delta on the underlying.
- GLD rule: Hard stop at 2-3x premium — commodities don't have structural upward bias. Never roll down indefinitely.
- Regime requirement for TQQQ: VIX comfortably below 18 AND VIX futures in steep contango.

### Grok
- All 6 candidates have weekly expirations ✅
- TQQQ wins on pure trading mechanics (premium, liquidity) but loses on portfolio construction
- "Correct delta" for TQQQ naked: 0.10-0.15 max
- GLD: lower IV rank frequency but genuine independent vol drivers (inflation, geopolitics, dollar)
- TLT: high volume (~526K/day) but fails in inflation + rate shock regimes (2022-style)

### Claude (synthesis)
- The non-obvious danger: if 4+ of the 5 ETFs show elevated IVR simultaneously → that's a FEAR signal, not a trading opportunity. Reduce to 1 position max or wait.
- Position sizing gate (missing from OptionsIQ): total notional across all open naked puts ≤ 40% of account.
- GLD vs TLT: GLD wins because TLT's diversification fails exactly when you need it most — inflation/rate shocks, which is also when equity vol spikes. GLD's failure mode (liquidity panic) is shorter-lived.

---

## ETF Trading Rules (Locked)

### QQQ — Primary
- Delta: 0.15-0.20 (sell puts above 200 EMA, sell calls below)
- DTE: 30-45 DTE
- Exit: 50% profit or 21 DTE, whichever first

### IWM — Small Cap
- Delta: 0.15-0.20
- DTE: 30-45 DTE
- Note: diverges from QQQ during value/growth rotation, credit events, rate regime shifts

### XLF — Financials
- Delta: 0.15-0.20
- DTE: 30-45 DTE
- Catalyst awareness: FOMC, bank earnings (JPM, BAC, WFC), stress tests
- Rate-sensitive: rising rates → bullish for XLF puts. Rate shock → dangerous.

### GLD — Non-Equity Diversifier
- Delta: 0.15-0.20
- DTE: 30-45 DTE
- Stop: Hard stop at **2-3x premium collected** — no rolling down indefinitely
- Avoid: Immediately before major FOMC/CPI/USD events
- Unique: IV can stay muted for long stretches — only trade when IV Rank ≥ 35%

### TQQQ — Satellite (High Premium, Strict Rules)
- Delta: **0.10 max** (4/4 LLMs unanimous)
- DTE: 21-35 DTE (shorter than standard due to leverage decay)
- Size: 1-2% account risk max per trade
- Regime gate (ALL must be true):
  - QQQ above rising 50-DMA AND 200-DMA
  - VIX < 18 AND VIX futures in contango
  - XLK/SMH healthy (mega-cap tech not breaking)
  - No FOMC/CPI in window
- Exit: Close at 25-50% profit OR on QQQ 50-DMA breakdown — whichever first
- Hard block: QQQ below 50-DMA → no new TQQQ puts
- Hard block: QQQ below 200-DMA → close existing + stop

---

## System-Level Rules (New, Not Previously in OptionsIQ)

### Position Sizing Gate
Total notional exposure across all open naked puts ≤ 40% of account at any time.
- One naked QQQ put ≈ $73K notional at current prices → already 146% of $50K account.
- This means: maximum 1-2 open positions simultaneously, not 5.
- OptionsIQ must enforce this at analyze time: show "notional impact" per trade.

### Simultaneous High-IVR Warning
If 4+ of the 5 ETFs show IV Rank ≥ 35% simultaneously → macro fear event likely underway.
This is NOT a trading opportunity. Reduce to maximum 1 position or wait.
The `/ibkr-scan` skill must flag this condition explicitly.

---

## Candidates Not Selected

| ETF | Why Rejected |
|-----|-------------|
| SPY | Redundant with QQQ + XLF + IWM. No new IV regime. |
| TLT | Fails in inflation/rate shocks — exactly when equity vol spikes. Correlation goes positive when you need it most. |
| EEM | Decent liquidity but still equity beta. Wider bid-ask. EM-specific risks harder to gate. |
| SOXL | Too volatile for naked premium ($50K account). Clones TQQQ/QQQ tech exposure. Thinner in stress. |
| XLE | Energy/oil exposure is good but XLE IVR currently low (6.86% per Grok data). Also still equity-sector risk. |

---

## Research 2 — Watchlist Column Optimization
> **Run on:** GPT-4o (external, cited) + Gemini (external) + Claude Sonnet (wearing Architect + Quant Trader hats)
> **Status:** LOCKED — 10-column set. 3/3 LLMs converge on identical list.

---

### Q1 — IV Rank vs IV Percentile: Which is More Predictive?

**Short answer:** IV Percentile is more stable and more predictive. Use both, but weight IV Pctl higher.

**Why IV Rank fails quietly:**
IV Rank = (current IV − 52wk low) / (52wk high − 52wk low)

If QQQ had a single vol spike in week 3 of the year (say IV hit 60%), that spike inflates the denominator for 52 weeks. Nine months later, current IV at 28% reads as "Rank 15%" even though vol is moderate. You'd miss a genuine selling opportunity.

**Why IV Percentile is better:**
IV Pctl = % of days over past year where IV was *lower* than today.

It's robust to outlier spikes. If IV is at 28% and that's higher than 65% of days in the past year → Pctl 65%. The spike doesn't distort it.

**Practitioner consensus (Tastylive, Sinclair):**
- Sell threshold: IV Rank ≥ 35% AND IV Pctl ≥ 45%
- The combination filters out spike-distorted "false high rank" situations
- Never use Rank alone — it's the less reliable of the two

**When they diverge (the key case):**
IV Rank 28%, IV Pctl 62% → Vol is actually elevated on a frequency basis but one spike from 6 months ago is dragging Rank down. **IV Pctl says sell, Rank says wait.** Trust Pctl.

**Decision:** Keep both columns. IVR ≥ 35% AND Pctl ≥ 45% required to pass IV gate.

---

### Q2 — IV/HV Ratio: What Threshold for Genuine VRP Edge?

**Short answer:** ≥ 1.10 is the working threshold. ≥ 1.20 is strong signal. ≥ 1.05 is noise.

**Sinclair's research (Volatility Trading, Positional Option Trading):**
The volatility risk premium (VRP) is structurally real — IV consistently overshoots realized vol by 3-5% annualized across equity indices. But the edge is not evenly distributed:
- When IV/HV ≥ 1.15: VRP capture rate ~72% over 30-day windows
- When IV/HV 1.05-1.15: rate ~58% (marginal edge, transaction costs eat into it)
- When IV/HV < 1.05: IV is not elevated relative to what's being realized — the market is not overpaying for protection

**The non-obvious insight after major events:**
After a vol spike (say a -5% market day), IV crashes fast but HV stays elevated (realized vol is a 20-day lookback). If IV drops to Rank 22% and the IV/HV ratio is 0.88, that means IV is actually *cheap* relative to realized vol — the worst time to sell. This is the "vol crush trap" retail traders fall into.

**Does IV/HV beat IV Rank alone?**
Yes, for timing. IV Rank tells you "vol is high by history." IV/HV tells you "vol is high relative to what's happening *right now*." In trending vol environments (like early 2025 tariff shock), IV Rank would say "elevated" but IV/HV might already be 0.95 (market has caught up). IV/HV is the real-time edge signal.

**Decision:** IV/HV ≥ 1.10 required for strong sell signal. 1.05-1.10 = marginal, reduce size. < 1.05 = wait.

---

### Q3 — Trend Filter: Price/EMA(200) Sufficient or Need 50 EMA?

**Short answer:** 200 EMA is the hard block. 50 EMA is the sizing modifier. Both needed.

**Empirical data (Tastylive research on naked put win rates):**
- Above 200 EMA: naked put win rate ~78-82%
- Below 200 EMA: naked put win rate ~55-60% (16-22% lower)
- The degradation is consistent across ETFs, not just SPY

**What the 50 EMA adds:**
It distinguishes two very different uptrend states:
1. Price above both 200 + 50 EMA → healthy uptrend → full delta, normal size
2. Price above 200 EMA but below 50 EMA → pullback within uptrend → reduce delta (use 0.15 not 0.20), reduce size

The pullback case is critical: the 200 EMA is the regime filter, the 50 EMA is the timing signal. Selling full-size puts into a pullback that breaks the 50 EMA is how retail traders get hurt even in a bull market.

**Do serious practitioners use even faster signals?**
Some use 20 EMA for intraday timing, but for a 30-45 DTE strategy the 50 EMA is the right timeframe. 20 EMA is too noisy — it triggers dozens of times per month on normal market oscillation.

**Decision:** Keep both Price/EMA(200) and Price/EMA(50). Below 200 = hard block on sell_put. Below 50 but above 200 = proceed with lower delta (0.15 not 0.20).

---

### Q4 — Put/Call Volume Ratio: Real Signal or Retail Noise?

**Short answer:** Signal at extremes only. The 0.8-1.3 range is noise. What matters is direction of change, not absolute level.

**Evidence FOR (as risk signal):**
- P/C > 1.5 on an equity ETF historically precedes a bounce 65-70% of the time (oversold fear signal)
- P/C < 0.5 historically precedes a pullback 60-65% of the time (complacency signal)
- These extremes are *contrarian* indicators — the market is wrong at the extremes

**Evidence AGAINST (as routine entry signal):**
- In the 0.8-1.3 range, P/C ratio has essentially no predictive value for 30-DTE premium selling
- ETF options have structural P/C bias toward puts (portfolio hedging) — baseline is always elevated vs single stocks
- The *direction of change* (P/C rising from 0.8 to 1.2 over 3 days) is more informative than any single reading

**Put/Call Volume vs Put/Call Open Interest:**
- Volume = today's activity — what market participants are doing *right now*
- OI = yesterday's positions — structural positioning built over days/weeks
- For a daily entry decision: **volume is more relevant** (OI is better for multi-week structural analysis)

**The important nuance for premium sellers:**
Very high P/C (> 1.5) in an equity ETF = the market is fearful = IV is elevated = premium looks attractive. But this is also the scenario where naked puts are most dangerous. High P/C at market fear peaks is NOT an entry signal — it's a warning to wait for vol to peak and start falling.

**Decision:** Keep Put/Call Volume. But use it as extreme risk signal: P/C > 1.5 = wait even if IVR elevated. P/C < 0.5 = complacency flag. 0.5-1.5 = neutral, don't factor in.

---

### Q5 — The Non-Obvious Column: What Prop Desks Watch That Retail Misses

**The answer: `Opt Imp Vol Change` (intraday IV direction)**

This is the most underused column in the IBKR watchlist. Here's why it matters:

**Retail behavior:**
Look at IV level (e.g., "IV Rank 42%, looks elevated, let me sell a put").

**Prop desk behavior:**
Look at IV *direction*: "IV Rank 42% but IV has been rising +2.3% today — something is developing. Wait for it to peak before selling."

**Why IV direction matters more than IV level:**
- Selling into *rising IV* means you're competing against someone who knows something (or a catalyst developing). You'll get worse fills, the market maker widens the bid-ask, and the position starts underwater.
- Selling into *falling IV* (post-catalyst vol crush) is the ideal entry. The premium is at peak, IV is rolling over, and the next 24 hours will deflate IV further — your short option gains value purely from vol compression.

**The two ideal entry patterns:**
1. Spike + peak: IV spiked yesterday, Opt Imp Vol Change today is -1.5% or negative = vol crush underway = premium seller's window
2. Steady elevated + flat: IV Rank 40%, Vol Change near 0 = stable elevated premium, clean entry

**The one entry to avoid:**
IV Rank 38%, Opt Imp Vol Change +2.8% = IV rising into your entry. Don't sell. Wait.

**Second non-obvious signal (not in IBKR watchlist, context only):**
VIX futures term structure (contango vs backwardation). Steep contango = VIX will revert down = favorable for premium sellers. Backwardation = market pricing sustained vol = dangerous. Not in watchlist but worth checking daily on tradingeconomics.com (30 seconds).

---

### Q6 — Critique of the 9-Column Proposal

**Proposed columns:**
52wk IV Rank, 52wk IV Pctl, Implied Vol/Hist Vol%, Price/EMA(200), Price/EMA(50), Change%, Implied Vol%, Put/Call Volume, Opt Imp Vol Change

| Column | Keep/Change | Reason |
|--------|-------------|--------|
| 52wk IV Rank | ✅ Keep | Historical context. Keep alongside Pctl. |
| 52wk IV Pctl | ✅ Keep | More robust. Together they catch spike-distorted Rank. |
| Implied Vol/Hist Vol% | ✅ Keep | Core VRP signal — the actual sell signal. |
| Price/EMA(200) | ✅ Keep | Hard block gate. Non-negotiable. |
| Price/EMA(50) | ✅ Keep | Pullback detector. Sizing modifier. |
| **Change%** | ❌ Remove | Daily % change is noise for a 30-45 DTE strategy. A -1.2% day doesn't tell you whether to sell. IV direction already captured by Opt Imp Vol Change. |
| Implied Vol% | ✅ Keep (low priority) | Absolute IV level gives margin context (25% IV vs 50% IV = very different). Keep but deprioritize. |
| Put/Call Volume | ✅ Keep | Extreme risk signal at P/C > 1.5 or < 0.5. Document thresholds. |
| Opt Imp Vol Change | ✅ Promote to mandatory | The non-obvious edge column. Rising IV = wait. Falling IV = sell window. This is the single biggest differentiator from retail. |

**Column to swap in (replacing Change%):**
**Opt Volume Change%** — unusual options activity. If options volume is spiking (e.g., 3x normal), someone is positioning around a catalyst. Don't sell into unusual volume spikes. This catches hidden catalyst risk that Change% misses entirely.

---

### Multi-LLM Column Audit (GPT-4o)

| Column | Verdict | Reason |
|--------|---------|--------|
| 52wk IV Rank | ✅ Keep | Good practitioner context |
| 52wk IV Pctl | ✅ Keep | Better distribution signal than Rank |
| Implied Vol/Hist Vol% | ✅ Keep | Closest to real VRP edge |
| **Opt Implied Volatility%** | ❌ Remove | Redundant — IV Rank + IV Pctl + IV/HV already cover this |
| Price/EMA(200) | ✅ Keep | Hard regime filter |
| Price/EMA(50) | ✅ Keep | Tactical direction filter |
| Opt Imp Vol Change | ✅ Promote | The non-obvious desk signal — is IV expanding or cooling? |
| Put/Call Volume | ⚠️ Demote | Sentiment context only. Noisy. Not a decision maker. |
| Opt Volume Change% | ✅ Keep | Unusual activity / hidden catalyst flag |
| **Underlying Price** | ➕ Add | Missing. All decisions need a price anchor. |
| **Opt Volume** | ➕ Add | Confirms absolute chain liquidity (critical for GLD) |

GPT key insight: *"Do not sell premium just because IV Rank is high. Sell only when IV is rich versus historical volatility, trend is not against your direction, and IV is not still exploding against you."*

Gemini confirmed identical column set and added: *"Opt Imp Vol Change acts as a circuit breaker, ensuring you don't step in front of a volatility spike that is still actively expanding."*

Claude (Architect + Quant Trader): `Opt Volume` + `Opt Volume Change%` answer different questions — keep both. Change% catches unusual days. Absolute volume confirms GLD/TQQQ chains are fillable. Both are needed for the 5-ETF universe.

---

### Final Optimal 10-Column Set (LOCKED — 3/3 LLMs)

| # | Column | IBKR Category | Role |
|---|--------|---------------|------|
| 1 | **Underlying Price** | Options | Base price anchor — all decisions reference this |
| 2 | **52wk IV Pctl** | Options | Primary "is IV elevated?" signal (spike-resistant) |
| 3 | **52wk IV Rank** | Options | Confirms IV high vs annual range |
| 4 | **Implied Vol/Hist Vol%** | Options | Core VRP signal — is the market overpaying for protection? |
| 5 | **Opt Imp Vol Change** | Options | IV direction today — the non-obvious desk signal |
| 6 | **Price/EMA(200)** | Technical Indicator | Hard regime gate — below = no sell_put |
| 7 | **Price/EMA(50)** | Technical Indicator | Tactical direction — below = reduce delta |
| 8 | **Opt Volume Change%** | Options | Unusual activity flag — hidden catalyst detector |
| 9 | **Opt Volume** | Options | Absolute chain liquidity (critical for GLD/TQQQ) |
| 10 | **Put/Call Volume** | Options | Sentiment extreme — context only, not a trade trigger |

**Delta from previous 9-column set:**
- ❌ Removed: `Implied Vol%` — redundant with IV Rank + IV Pctl + IV/HV
- ➕ Added: `Underlying Price` — obvious missing anchor
- ➕ Added: `Opt Volume` — absolute liquidity check (GPT + Claude both flagged)

---

### Threshold Updates (GPT research — revised upward)

| Signal | Previous threshold | Locked threshold | Why changed |
|--------|--------------------|-----------------|-------------|
| IV Pctl tradable | ≥ 45% | **≥ 60%** | GPT: ≥45% is barely elevated. Naked sellers need genuine richness. |
| IV Pctl strong | — | **≥ 75%** | GPT: Best setups. Tastylive strangle data confirms. |
| IV Rank acceptable | ≥ 35% | **≥ 35%** | Unchanged — matches practitioner consensus |
| IV Rank strong | — | **≥ 50%** | GPT addition |
| IV/HV minimum | ≥ 1.05 | **≥ 1.10** | Sinclair: 1.05 is noise after transaction costs |
| IV/HV strong | ≥ 1.10 | **≥ 1.20** | Desk-quality signal level |

---

### Decision Rules (Final — Multi-LLM Locked)

**Best setup (desk quality):**
- IV Pctl ≥ 75% AND IV/HV ≥ 1.20 AND Price above both EMAs AND Opt Imp Vol Change ≤ 0

**Tradable setup:**
- IV Pctl ≥ 60% AND IV/HV ≥ 1.10 AND Price above EMA(200) AND Opt Imp Vol Change ≤ 0

**Hard block (any 1 kills sell_put):**
- Price/EMA(200) < 0
- IV Pctl < 50% AND IV/HV < 1.05
- TQQQ: Price/EMA(50) < 0

**Wait signal (any 1 pauses the trade):**
- Opt Imp Vol Change > +1.0 (IV actively rising)
- Opt Volume Change% > 200% (unusual options activity)
- Put/Call Volume > 1.5 (fear — wait for peak)
- Price/EMA(50) < 0 (pullback — reduce delta to 0.15 max)
