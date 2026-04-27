# OptionsIQ — Multi-LLM Improvement Synthesis
**Date:** 2026-04-22 | **Version baseline:** v0.19.0 (Day 29) | **Sources:** Grok, GPT-4o, Perplexity, Gemini

---

## What I Asked

Four models were given different angles on the same tool:
- **Grok** — 30-year trader audit of current system gaps
- **GPT-4o** — TastyLive-backed trade management rules (profit targets, stop rules, 21 DTE)
- **Perplexity** — Empirical thresholds from tastylive backtests + academic volatility literature
- **Gemini** — Architecture upgrade: composite gate scoring, EM gate, portfolio correlation

---

## Cross-Model Consensus (High Confidence — All 4 Agree)

These points came from multiple models independently. They are the highest-confidence improvement signals.

### 1. OI Threshold — Already Correct (No Action Needed)
- **Grok audit said:** "OI >100 is too loose" — would require raising
- **Actual current value:** `MIN_OPEN_INTEREST = 1000` in constants.py
- **Verdict:** Our OI floor is already correct and well above Grok's concern. This is a non-issue for OptionsIQ. The audit was based on an assumed value, not the actual code.
- **Takeaway:** Confirms the liquidity gate is functioning as designed.

### 2. Trade Management Rules Are Missing From the System
- **GPT-4o:** Full TastyLive-backed ruleset: 50% profit target, 2× credit stop, 21 DTE = close/roll
- **Grok:** "No explicit trade management rules baked in — this is a critical gap"
- **Action:** These rules belong in the Paper Trade Dashboard and the "Record Paper Trade" flow as UI checkboxes. They do NOT need to be in gate_engine.py (you can't automate exit logic without live P&L feeds). But displaying them prominently at trade entry is the right UX intervention.
- **File:** `PaperTradeBanner.jsx`, `PaperTradeDashboard.jsx`

### 3. Backtesting Is the #1 Missing Foundation
- **Grok:** "Backtesting missing or weak — this is the #1 killer of retail systems"
- **Perplexity:** Every cited empirical threshold (50% profit, IVR>30, 20-delta strikes) comes from tastylive's backtests — we have no equivalent for our specific ETF set
- **Gemini (implied):** Composite scoring is meaningless without validation that the scores predict outcomes
- **Assessment:** This is a long-term build (weeks, not days). Not blocking current work. But it shapes how aggressive we should be with any threshold change — don't change constants based on theory alone.

### 4. Credit-to-Width Ratio Is a Gate, Not a Display Field
- **Perplexity:** "Credit received ≥ 1/3 of spread width is the minimum quality filter. A 10-delta short strike typically fails this test — the 90% win rate is misleading on a P&L expectancy basis."
- **Gemini (implied):** Expectancy math shows the 20–25 delta range dominates even at lower win rates
- **Current state:** KI-082 tracks this as open. It should be a hard gate, not just a display.
- **Action:** Add `credit_to_width_ratio` check in `gate_engine.py`. Threshold: `< 0.33` = BLOCKED.

---

## Model-Specific Insights (Single Source, Still High Value)

### From Grok — Threshold Calibration

**Theta gate:**
> "5%/week is HALLUCINATED — should be 0.5%/day"

Check current `constants.py` theta threshold. If it uses weekly, fix to daily. This changes how the theta gate passes.

**IV Percentile missing:**
> "High IVR can mislead — you need IV Rank AND IV Percentile (252-day lookback)"

IV Rank = current IV relative to its range. IV Percentile = what % of days in last 252 had IV below current. They diverge when IV has been compressed for a long time (IV Rank could be 80 while IV Percentile is 40 because one spike sets the high). Adding IV Percentile requires storing daily IV snapshots — we have `iv_history.db` with 7,492 rows which should be sufficient.

**Regime breadth missing:**
> "SPY vs 200 SMA is decent but lacks breadth — % sectors above 50/200 SMA matters"

Current regime = SPY price vs 200 SMA + 5-day return. A bull market with sector rotation showing 60% of sectors below 200 SMA is a different risk environment than 90% above. The sector scan endpoint already fetches quadrant data — aggregate it.

### From GPT-4o — TastyLive Rules (Exact Thresholds)

These are research-backed, not opinion:

| Rule | Value | Why |
|------|-------|-----|
| Profit target | 50% of max credit | Best balance of realized gain vs holding risk |
| Fast profit rule | 25–35% in first 3–5 days → close early | High return-on-time ratio |
| 21 DTE | Force decision: close winners, roll losers for net credit only | Gamma risk rises |
| Stop loss | 2× credit received (not 1×) | 1× causes whipsaws on ETF dips that recover |
| Short strike breach | Not auto-stop — triggers review only | ETFs recover; breach + loss at 1.5–2× = stop |

**UI discipline checkboxes to add to PaperTradeBanner:**
- ✅ Profit rule followed? (closed at 50% or fast 25–35% gain)
- ✅ Risk rule followed? (closed at 2× loss / reviewed breach)
- ✅ 21-DTE action logged? (closed / rolled for net credit / held with reason)

### From Perplexity — IVR Threshold Recalibration

**Current OptionsIQ IVR minimum:** Check constants.py — likely set to 30 or 40.

**Empirical finding:**
- IVR > 30 = defensible minimum for normal regimes
- IVR > 40 = optimal but severely restricts frequency
- IVR > 50 = NOT meaningfully better than 40 — the incremental credit is offset by the fact that high-IVR clusters around directional trending moves (binary sector events)
- **Post-spike regime (VIX just spiked from <20 to >25):** Drop IVR bar to ≥10–15 — absolute IV is already elevated

**Verdict:** If `IVR_MIN_SELL` is currently 50, lower to 35. If it's already 30–35, keep it.

**VIX regime buckets to hard-code:**

| VIX | Bucket | Action |
|-----|--------|--------|
| < 15 | Low Vol | CAUTION — thin premiums, poor R/R |
| 15–20 | Moderate | OK — moderate credit |
| 20–30 | Sweet Spot | GO — best risk-adjusted P&L |
| > 30 | High / Stress | REDUCE SIZE — large adverse swings offset rich premium |
| > 40 | Crisis | BLOCK — negative expectancy empirically |

**Sector correlation risk:** XLK + QQQ + TQQQ all sell off together at VIX > 25. XLU and XLV have IV that diverges from VIX more than XLK/XLF — VIX alone is insufficient filter for those ETFs. Rely on their own IVR.

### From Gemini — Composite Score Architecture

**Key insight:** Binary pass/fail gates create cliff effects. A trade rejected at IVR 29.9 instead of 30.0 is economically identical to one at IVR 30.1. The current verdict system partially addresses this (CAUTION vs BLOCK) but the underlying gate logic is still binary.

**Formula:**
```
Composite Score = (Product of all Hard Constraints) × Weighted Average of Soft Signals
```

Hard constraints (binary — 0 if fail, kills the score):
- DTE in valid window
- Bid-ask spread < threshold
- OI above minimum

Soft signals (scaled 0–100, weighted):
- IVR (weight 0.6): linear ramp from 0 at IVR=20 to 100 at IVR=50+
- Trend/regime (weight 0.4): sector quadrant score

**Expected Move Gate:**
```
EM = price × IV × √(DTE / 365)
Bull put: short strike must be ≤ price − EM
Bear call: short strike must be ≥ price + EM
```

This is a 1-sigma gate. If the short strike is within the expected move, you're pricing the trade at worse-than-theoretical probability of profit. This is a meaningful quality check that we don't currently have.

**Portfolio correlation gate:**
```python
SECTOR_BUCKETS = {
    'TECH': ['XLK', 'QQQ', 'TQQQ'],
    'FINANCE': ['XLF'],
    'ENERGY': ['XLE'],
    ...
}
if current_portfolio['TECH_DELTA'] + new_trade['DELTA'] > MAX_TECH_DELTA:
    FAIL: "Sector Concentration"
```

Correlation threshold: if 30-day Pearson r > 0.85 between new trade ETF and existing position, trigger reduce/block.

---

## My Assessment Through the Rule 22 Two-Persona Lens

### Systems Architect Says:

**Don't break what works.** The gate engine is solid. Binary gates are debuggable. Composite scoring adds complexity — it needs a display layer so users understand WHY a score is 67 vs 82. Without transparency, it's a black box. Add composite scoring as a **display metric alongside** the existing gate grid, not as a replacement.

**Threshold changes must be atomic.** Each constant change in `constants.py` should be a single-commit, single-reason change with a comment referencing the source (e.g., `# Perplexity synthesis 2026-04-22: empirical optimum vs >50 which restricts frequency`). Never batch threshold changes.

**The `iv_history.db` is the only backtesting data we have.** Before any threshold change, query how many trades would have passed vs failed at the old vs new threshold. This takes 10 minutes and is the minimum responsible validation.

**The 604-line `analyze_service.py` is not an emergency.** Grok flagged it as monolithic. It is. But it's a working monolith with 27 tests passing. Refactoring it risks regressions. Defer.

### Quant Trader Says:

**Expectancy > win rate.** Perplexity's math is correct and important: 75% win rate at 33% credit-to-width beats 90% win rate at 15% credit-to-width. The current delta targets (~0.30 short strike) are close to right, but we're not computing expectancy. The paper trade dashboard should show **expected value per trade** once we have enough data.

**The 21 DTE rule is the most actionable thing from this entire research round.** It's a concrete, time-based trigger that requires no new data. Add it as a "DTE Alert" in the paper trade list — if a recorded trade is within 21 days of expiry, flag it with the 3-option menu: Close / Roll for net credit / Hold (with reason required).

**Portfolio correlation is real and dangerous.** Having XLK + QQQ + TQQQ positions simultaneously is 3 leveraged bets on the same tech index. We trade ETFs precisely to avoid single-stock risk, but sector clustering re-creates it. The sector bucket gate from Gemini is the right call — implement it before scaling up position count.

**VIX buckets > anything else for regime context.** Knowing we're in a VIX 20–30 "sweet spot" regime vs VIX < 15 "thin premium" regime is more actionable than the SPY 200 SMA flag alone. Add the VIX bucket to the regime bar display and gate logic.

---

## Prioritized Implementation Plan

Organized by: **Impact × Effort × Risk**. Lower risk always wins a tiebreak.

### Priority 0: Fix the IVR Seller Threshold (30 minutes)
**`IVR_SELLER_PASS_PCT = 50` is too restrictive — change to 35.**
- `constants.py`: `IVR_SELLER_PASS_PCT = 35` (was 50)
- Keep `IVR_SELLER_MIN_PCT = 30` as the soft floor (already correct)
- **Why P0:** Perplexity's tastylive data is explicit: IVR > 50 sacrifices 60–70% of trade frequency for negligible marginal benefit over IVR > 40. The marginal credit collected above IVR 40 is offset by the fact that high-IVR clusters around directional events that make short-premium entries riskier. IVR > 35 is the defensible empirical threshold.
- **Note:** `MIN_OPEN_INTEREST = 1000` is already correct (Grok flagged 100 as wrong — our value is already at 1000). No OI change needed.

### Priority 1: Credit-to-Width Gate (2 hours)
**KI-082: Add hard gate for credit ≥ 1/3 of spread width**
- `gate_engine.py`: `if credit / spread_width < 0.33: BLOCKED`
- Display the ratio in the strategy card so user sees the number
- **Why P1:** Perplexity cites this as the single most important spread quality filter. Expectancy math confirms it. We have the data (credit and width are already in the strategy ranker output).

### Priority 2: VIX Regime Buckets in Gate + Display (3 hours)
**Add VIX level to regime context and gate logic**
- `constants.py`: Add `VIX_BUCKETS = {15: "low_vol", 20: "moderate", 30: "sweet_spot", 40: "stress", 999: "crisis"}`
- `sector_scan_service.py` or `analyze_service.py`: fetch VIX (already have yfinance) → classify bucket
- `gate_engine.py`: In `etf_mode=True` tracks — apply VIX bucket modifier
  - VIX < 15: CAUTION on all sell positions (thin premium)
  - VIX > 40: BLOCK on all new positions
  - VIX > 30: Reduce size signal (display warning)
- `RegimeBar.jsx` or equivalent: Show VIX bucket alongside SPY regime
- **Why P2:** Perplexity's 21-year tastylive study is definitive. VIX > 40 = negative expectancy. This is a safety gate we're currently missing.

### Priority 3: Trade Management UI Rules (2 hours)
**Add TastyLive discipline rules to paper trade flow**
- `PaperTradeBanner.jsx`: Add constants display — "Target: 50% profit | Stop: 2× credit | Review at: 21 DTE"
- `PaperTradeDashboard.jsx`: In trade list, flag trades within 21 DTE with an action prompt
- `iv_store.py`: Add `target_exit_pct`, `stop_loss_mult`, `days_to_expiry` to stored trade data
- **Why P3:** GPT's rules are research-backed and require zero model changes. Pure UX. Prevents the #1 retail mistake: not managing winners.

### Priority 4: Expected Move Gate (4 hours)
**Add EM check to strategy ranker output**
- `bs_calculator.py` or `strategy_ranker.py`: `em = price × iv × sqrt(dte/365)`
- For bull put: check `short_strike <= price - em`
- For bear call: check `short_strike >= price + em`
- Display EM in strategy card as context (even if we don't hard-gate on it initially)
- **Why P4:** This is a legitimate statistical quality check (1-sigma alignment). Start as display, promote to gate once we validate it doesn't reject too many otherwise-valid trades.

### Priority 5: IV Percentile Addition (4 hours)
**Add IV Percentile alongside IV Rank**
- `iv_store.py`: Add `get_iv_percentile(symbol, current_iv, lookback=252)` — count days where stored IV < current_iv, divide by total days
- `analyze_service.py`: Call it alongside `get_iv_rank()`
- `GatesGrid.jsx`: Display both with explanation tooltip
- Note: Requires 252 days of stored IV data per ticker. Check coverage before displaying (show N/A if < 100 days).

### Priority 6: Sector Concentration Gate (6 hours)
**Block same-bucket positions exceeding delta cap**
- `constants.py`: Add `SECTOR_BUCKETS` dict and `MAX_BUCKET_DELTA_PCT = 0.10` (10% of account in one sector bucket)
- `iv_store.py` or new `portfolio_state.py`: Track open paper trades by bucket
- `analyze_service.py`: Before returning result, check current exposure
- **Why deferred to P6:** Requires tracking open paper trades as "active positions" with delta — we don't currently do that. Paper trade schema stores entry delta, but not current delta. This is a meaningful addition but higher complexity.

### Do NOT Do (Based On This Research)

1. **Do not raise IVR minimum above 40.** Perplexity's research is explicit: IVR > 50 sacrifices 60–70% of trade frequency for negligible marginal benefit. If the current threshold is 30–35, keep it or nudge to 35 max.

2. **Do not refactor `analyze_service.py` right now.** Grok flagged it as monolithic (604 lines). True. But it has 27 tests and works. The risk of regression in a refactor outweighs the maintainability benefit at current scale.

3. **Do not implement composite gate scoring as a replacement for current gates.** Add it as a display metric alongside the existing gate grid. The binary gates are understandable and auditable. A composite score without transparency is a black box. Show both.

4. **Do not add backtesting before we have 30+ paper trades.** Grok's backtesting advice is correct in the long run. But backtesting with < 30 trades produces statistically meaningless results. Get the paper trade discipline in place first (P3 above), accumulate 30+ trades, then build the backtester.

5. **Do not change multiple thresholds at once.** Each constant change must be a single-commit, single-reason change. Batching makes debugging impossible if a change causes unexpected behavior.

---

## Quick Reference: Threshold Corrections From This Research

| Parameter | Current (actual) | Corrected | Source |
|-----------|---------------------|-----------|--------|
| `MIN_OPEN_INTEREST` | 1000 | ✅ Already correct | (Grok said 100 was wrong — ours is 1000) |
| `IVR_SELLER_PASS_PCT` | 50 | 35 | Perplexity (tastylive empirical) |
| `IVR_SELLER_MIN_PCT` | 30 | ✅ Already correct | Keep as soft floor |
| Credit-to-width min | Not gated | 0.33 (33%) | Perplexity + tastylive |
| VIX gate | None | < 15 = CAUTION, > 40 = BLOCK | Perplexity |
| Profit target | Not in system | 50% of max credit | GPT / TastyLive |
| Stop loss | Not in system | 2× credit received | GPT / TastyLive |
| 21 DTE rule | Not in system | Force decision: close/roll/hold+reason | GPT / TastyLive |

---

## Implementation Sequence (Recommended Order)

```
Week 1 (now):
  Day 1 — P0: Fix OI_MIN (30 min) → commit
  Day 1 — P1: Credit-to-width gate (2 hr) → commit
  Day 2 — P3: Trade management UI rules (2 hr) → commit + test in browser
  
Week 2:
  Day 3–4 — P2: VIX regime buckets (3 hr) → commit
  Day 4–5 — P4: Expected Move gate as display (4 hr) → commit
  
Week 3–4:
  P5: IV Percentile (4 hr, gated on data coverage check)
  P6: Sector concentration (6 hr, higher complexity)
```

---

## Closing Observations

All 4 models independently validated the same core truth: **the gate engine architecture is sound, but the thresholds and display are undercooked.** The system can filter trades but currently can't guide trade management, correct for sector correlation risk, or show whether the premium collected is a statistically meaningful edge.

The fastest path to real-money confidence is:
1. Fix the one wrong threshold (OI_MIN)
2. Add the one missing gate (credit-to-width)
3. Show the TastyLive rules in the paper trade UI
4. Record 30+ paper trades with discipline
5. Then build the analytics layer on top of real data

This is not a system rebuild. It is targeted threshold correction + UX discipline enforcement. The bones are already excellent.
