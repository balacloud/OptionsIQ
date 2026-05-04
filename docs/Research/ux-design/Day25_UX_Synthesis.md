# UX Research Synthesis — Day 25 (April 17, 2026)

## Source Research
- **GPT-4o**: Options Education UX + Number Line Spec + Gate Table
- **Gemini**: Behavioral Interface Architecture + 5 Pillars + Assignment Risk
- **Perplexity**: Full HTML/CSS mockups (5 tabbed panels, interactive, dark theme)
- Raw responses: `docs/Research/Multi_LLM_UX_Design_OptionsIQ_Recommendations.md`
- HTML mockups: `docs/Research/exported-assets_Preplixity/options-edu-panel.html` + `_1.html`

---

## Consensus (All 3 LLMs Agree — High Confidence)

| Decision | Detail |
|----------|--------|
| **Percentage-based number line** | `pct = (val - chartMin) / (chartMax - chartMin) * 100` with dynamic padding |
| **Proportional risk/reward bar** | flex widths: profit% / loss% (e.g., 21% green / 79% red) |
| **Zone coloring** | green = profit, amber = caution/breakeven, red = loss |
| **Plain English gate Q&A** | question + pass answer + fail answer + "why it matters for your money" |
| **Marker colors** | current price = blue (#3B82F6), short strike = red (#FF4444), breakeven = amber (#F59E0B) dashed, long strike = blue |
| **PUT/CALL zones flip** | ITM/OTM zones reverse for puts vs calls — auto-detect from direction |
| **5 core concepts** | Direction, Risk/Reward, Breakeven, Expiration/DTE, Leg mechanics/Gates |
| **Dark theme validated** | #0D1117 background reduces emotional reactivity (Gemini behavioral research) |

---

## Adopted Unique Insights

### From GPT-4o
- **Single-column stack layout** for inline analysis (not tabs) — everything visible, scrollable
- **Label collision handling**: if two strike markers are within 36px, stagger labels vertically
- **"Today vs Expiry" note**: "This shows your trade at expiry. Before expiry, actual P&L will vary."
- **Chart padding formula**: `padding = Math.max((max - min) * 0.35, 0.75)` — prevents marker crowding

### From Gemini
- **"Margin of Safety" framing** — label the gap between current price and short strike
- **"Credit is not profit yet"** — show collected premium as collateralized until expiration
- **Theta Acceleration** — time decay isn't linear, accelerates in final 21-45 days (defer visual to Learn tab)
- **Assignment Risk Meter** — track extrinsic value of short leg (defer — needs real-time data)
- **Dark theme as behavioral tool** — muted semantic colors reduce fight-or-flight response

### From Perplexity
- **Ready-to-use CSS tokens** — almost exact match to OptionsIQ colors (`--bg:#0D1117`, `--green:#00C896`, `--red:#FF4444`)
- **Accordion gate pattern** — compact header + expandable Q&A + meter bar per gate
- **SVG payoff diagram** — two-color polyline (green flat -> red slope -> red flat) with BE/price markers
- **DTE bar with optimal window** — horizontal bar showing current DTE position vs optimal seller window (21-45d)
- **Event cards with severity** — earnings=HIGH/red, FOMC=MEDIUM/amber, CPI=LOW/green
- **Readiness score bar** — "5/7 gates passed" with proportional green fill

---

## Skipped (Too Complex or Inconsistent)

| Recommendation | Source | Reason to Skip |
|---|---|---|
| JetBrains Mono + Inter fonts | Perplexity | OptionsIQ uses IBM Plex Sans/Mono — keep consistent |
| Tabbed layout for inline analysis | Perplexity | Tabs hide info; single-column scroll better for inline (GPT-4o agrees) |
| "Donut Chart" for credit/risk | Gemini | Over-engineered; proportional bar already communicates this |
| Mobile vertical "Price Ladder" | Gemini | Desktop-only for now |
| Theta acceleration curve | Gemini | Complex SVG; defer to Learn tab |
| Assignment Risk Meter | Gemini | Requires real-time extrinsic value tracking |

---

## Architecture Decision

**Confirmed blended approach:**
- **Inline analysis panel**: Single-column stack (GPT-4o style) — Direction -> TradeExplainer -> Gates -> Strategies. Everything visible, no tabs.
- **Learn tab**: Tabbed lessons (Perplexity style) — Strikes / Directions / Spreads / Gates. Interactive tutorials with mock data, always available.

---

## Implementation Plan

### Part 1: Analysis Panel (6 items)

#### 1. `DirectionGuide.jsx` (NEW — replaces DirectionSelector)
- 2x2 grid: Bullish (Buy Call, Sell Put) | Bearish (Sell Call, Buy Put)
- Each card shows: direction name, plain English market view, risk description
- Props: `{ direction, setDirection, locked }` — same as DirectionSelector

#### 2. `TradeExplainer.jsx` (NEW — core visual component)
**Section A: Strike Zone Number Line**
- Percentage-based positioning with dynamic padding
- Markers: current price (blue), short strike (red), long strike (blue), breakeven (amber dashed)
- Zones: profit (green), caution (amber), loss (red) — positioned by strategy type
- ITM/ATM/OTM labels below number line
- "Margin of Safety" label showing distance from current price to short strike
- Note: "This shows your trade at expiry. Before expiry, actual P&L will vary."

**Section B: Risk/Reward Bar**
- Proportional flex widths: max_gain_per_lot / max_loss_per_lot
- Plain English: "You can make at most $21" / "You can lose at most $79"
- Credit framing for sellers: "You collected $X credit — this is not profit until expiry"

**Plain English templates by strategy_type:**
- `bear_call_spread`: "You profit if {ticker} stays below ${breakeven} for {dte} days"
- `bull_put_spread`: "You profit if {ticker} stays above ${breakeven} for {dte} days"
- `itm_call`: "You profit if {ticker} rises above ${breakeven} within {dte} days"
- `itm_put`: "You profit if {ticker} drops below ${breakeven} within {dte} days"
- `sell_call`: "You profit if {ticker} stays below ${strike} for {dte} days — UNLIMITED RISK"
- `sell_put`: "You profit if {ticker} stays above ${strike} for {dte} days"

**Data mapping from `top_strategies[0]`:**
- `strategy_type` -> template selection
- `short_strike`, `long_strike` -> marker positions
- `underlying_price` (from root response) -> current price marker
- `breakeven` -> breakeven marker
- `max_gain_per_lot`, `max_loss_per_lot` -> risk/reward bar widths
- `dte` -> "for the next N days"
- `right` -> "C" = Calls, "P" = Puts

Props: `{ strategy, underlyingPrice, ticker, direction }`

#### 3. `GateExplainer.jsx` (NEW — replaces GatesGrid)
- **Default**: Compact header with dots + "Safety Checks 6/7 passed" + readiness score bar
- **Expanded**: Click to show categorized Q&A (Market Conditions -> Option Pricing -> Risk Management)
- Each gate shows: plain English question, pass/fail answer with live data, "why it matters"
- Auto-opens if any gate fails

**Gate-to-question mapping:**

| Gate ID | Category | Question |
|---------|----------|----------|
| `ivr` | pricing | "Is IV cheap enough to buy?" |
| `ivr_seller` | pricing | "Is premium expensive enough to sell?" |
| `hv_iv` | pricing | "Are options fairly priced vs recent movement?" |
| `strike_otm` | pricing | "Is the strike safely OTM?" |
| `theta_burn` | pricing | "Will time decay eat my profit?" |
| `dte` / `dte_seller` | pricing | "Is the expiry well-timed?" |
| `events` | market | "Any earnings or FOMC surprises?" |
| `liquidity` | risk | "Can I exit this trade easily?" |
| `market_regime` / `market_regime_seller` | market | "Is the broad market supportive?" |
| `risk_defined` | risk | "Is my loss capped?" |
| `position_size` | risk | "Can I afford this without too much risk?" |
| `max_loss` | risk | "Is total risk within my account limits?" |

Props: `{ gates, direction }`

#### 4. MasterVerdict Enhancement
Add plain English subtitle after headline:
- GO: "This trade meets all safety checks. Review the details below before placing."
- CAUTION: "Some conditions are concerning. Read the warnings below — you may want to wait."
- BLOCK: "Critical safety check failed. Do NOT place this trade until conditions improve."
~5 lines change in MasterVerdict.jsx

#### 5. TopThreeCards Enhancement
Add "In Plain English" line at top of rank 1 card:
- "SELL the $54 call + BUY the $55 call for $0.21/share credit. You keep the credit if XLF stays below $54 by May 15."
~15 lines change in TopThreeCards.jsx

#### 6. Wire into App.jsx
- Import DirectionGuide, TradeExplainer, GateExplainer
- Replace DirectionSelector with DirectionGuide
- Replace GatesGrid with GateExplainer
- Add TradeExplainer between MasterVerdict and GateExplainer
- Pass `underlyingPrice={data?.underlying_price}` and `ticker={selectedETF.etf}` to TradeExplainer
- Add Learn tab toggle at top level

### Part 2: Learn Tab (1 component)

#### 7. `LearnTab.jsx` (NEW)
- Tab navigation at top of App: [Signal Board] [Learn]
- 4 sub-tabs: Strikes | Directions | Spreads | Gates
- **Strikes**: Interactive price slider, ITM/ATM/OTM zone visualization, call vs put flip
- **Directions**: 4 market views with P&L line sketches, buyer vs seller key insight
- **Spreads**: Bear call spread example with SVG payoff diagram, "what happens" scenarios
- **Gates**: 3 categories (Market/Pricing/Risk) with educational explanations

### Part 3: CSS (~350 lines in index.css)
Styles for all new components matching existing dark theme tokens.

---

## Layout Order in AnalysisPanel (after implementation)

```
1. QualityBanner (if not live data)
2. Price Row (underlying + IVR badge)
3. DirectionGuide (NEW — replaces DirectionSelector)
4. [Run Analysis] button
5. MasterVerdict (ENHANCED — plain English subtitle)
6. TradeExplainer (NEW — number line + risk/reward)
7. GateExplainer (NEW — compact dots + expandable Q&A)
8. TopThreeCards (ENHANCED — plain English line)
9. ExecutionCard (existing)
10. PnLTable (existing)
11. Advisories (existing)
12. PaperTradeBanner (existing)
```

---

## Files to Create / Modify

### New Files
| File | Purpose | Lines Est. |
|------|---------|-----------|
| `frontend/src/components/DirectionGuide.jsx` | Educational direction selector | ~90 |
| `frontend/src/components/TradeExplainer.jsx` | Number line + risk/reward + plain English | ~200 |
| `frontend/src/components/GateExplainer.jsx` | Compact dots + expandable Q&A | ~180 |
| `frontend/src/components/LearnTab.jsx` | 4 interactive lessons | ~350 |

### Modified Files
| File | Change |
|------|--------|
| `frontend/src/App.jsx` | Swap components, add Learn tab toggle, wire TradeExplainer |
| `frontend/src/components/MasterVerdict.jsx` | Add plain English subtitle |
| `frontend/src/components/TopThreeCards.jsx` | Add "In Plain English" summary |
| `frontend/src/index.css` | ~350 lines new CSS |

### Untouched
- No backend changes
- No gate logic changes
- No strategy ranking changes

---

## Verification Plan

1. Start frontend dev server (`cd frontend && npm start`)
2. **Learn tab**: Click Learn -> verify 4 lessons render, slider works on Strikes
3. **Signal Board**: Click any ETF "Analyze ->" -> select sell_call -> Run Analysis
4. Verify each component with real data:
   - DirectionGuide: 4 cards with descriptions, active highlight
   - TradeExplainer: Number line with markers + risk/reward bar
   - GateExplainer: Compact dots default, expand shows Q&A
   - TopThreeCards: "In Plain English" line
5. Test all 4 directions
6. Test edge cases: no strategies, BLOCK verdict, CAUTION verdict
7. Visual check: dark theme, spacing
