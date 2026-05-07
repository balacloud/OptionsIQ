# Phase 7c — Trading Effectiveness: Actionable Improvements (Day 47)
> **Date:** Day 47 (May 7, 2026)
> **Builds on:** Phase7c_Trading_Effectiveness_Day46.md
> **Framework:** MASTER_AUDIT_FRAMEWORK v1.4, Category 10

---

## Summary of Day 46 Findings (Carried Forward)

| Check | Status | Finding |
|-------|--------|---------|
| 10.1 Gate Pass Rate | 2/11 CAUTION | Dominant blocker = Liquidity Proxy (bid-ask >20%), NOT vol miscalibration |
| 10.2 Always One Direction | MET | XLF + QQQ CAUTION — system correctly surfaces liquid ETFs |
| 10.3 DTE Calibration | FIXED (Day 46) | ETF_DTE_SELLER_PASS_MIN raised 21→30 |
| 10.4 Unbiased Evaluation | PENDING | Paper trade log + adversarial LLM review not yet started |
| 10.5 EV Sanity | WORKING | McMillan Stress Check correctly fires on XLF |

---

## Phase 7c Root Cause Analysis — Why 9/11 Are Blocked

### The Liquidity Tier Problem

The 15 ETFs in the universe fall into two distinct options liquidity classes:

**Tier 1 — Tight OTM spreads (typically <5% at 0.30 delta):**
- QQQ: ~3M options contracts/day (top-5 globally)
- IWM: ~600k contracts/day  
- XLF: ~500k contracts/day (financials = high volatility interest)
- XLK: ~400k contracts/day (tech sector)
- XLY: ~200k contracts/day (consumer discretionary)

**Tier 2 — Wide OTM spreads (commonly 10-40% at 0.30 delta):**
- XLV, XLI, XLC, XLB, XLP, MDY — sector ETFs with lower options volume
- OTM calls on these ETFs have wide spreads because market makers need a larger edge to provide liquidity

### Why the Gate Is Correct (Not Miscalibrated)

The 20% hard-block threshold (`SPREAD_DATA_FAIL_PCT`) is appropriate:
- A 39% bid-ask spread on XLV means paying ~$0.20 edge per contract on a $1.00 option
- At 100 contracts, that's $2,000 in slippage before the trade starts
- This genuinely destroys expected value — blocking is correct

### The Actual Problem

The issue isn't gate calibration. It's **strike selection in a liquidity-stratified universe**:
- Strategy ranker targets 0.30-delta short call for bear_call_spread
- For Tier 2 ETFs, the 0.30-delta OTM call has wide spreads structurally (low volume, market maker risk)
- The system correctly blocks these but doesn't explain the structural reason to the user

---

## Changes Implemented (Day 47)

### 1. ETF Options Liquidity Tier (constants.py)

```python
ETF_OPTIONS_LIQUID_TIER1 = frozenset({"QQQ", "IWM", "XLF", "XLK", "XLY"})
```

Used in gate messages to distinguish Tier 1 (tight spreads) from Tier 2 (wider spreads).

### 2. Actionable Liquidity Block Messages (analyze_service.py)

**Before (generic):**
> "Bid-ask spread 39.2% — data unreliable at this width; do not trade until spread narrows"

**After (actionable):**
> "Bid-ask spread 39.2% — too wide for efficient execution. XLV options have moderate liquidity; QQQ/XLF/IWM offer tighter OTM spreads for the same directional exposure"

And if scanning during early market session (9:30-10:00 AM ET):
> "[...] Early session: OTM spreads typically narrow after 10:00 AM ET — rescan later"

### 3. Time-of-Day Context (_is_early_market_session helper)

```python
def _is_early_market_session() -> bool:
    # True if 9:30-10:00 AM ET on a weekday
```

OTM option bid-ask spreads are empirically 2-3x wider in the first 30 minutes of market open. Adding this context to blocked setups gives the user a concrete action: rescan later.

---

## Trading Effectiveness Impact Assessment

| Scenario | Before Day 47 | After Day 47 |
|----------|--------------|--------------|
| XLV blocked by 39% spread | "data unreliable" — no guidance | "XLV Tier 2 — use QQQ/XLF for same direction" |
| XLI blocked at 9:45 AM | "data unreliable" | "Rescan after 10:00 AM" |
| QQQ/XLF blocked | same generic message | same message (correct: if even Tier1 is blocked, it's genuine) |

**Bottom line:** The system now guides traders toward liquid alternatives rather than just saying "blocked." This directly increases the probability of finding a tradeable setup when the preferred ETF is illiquid.

---

## Remaining Phase 7c Work

### Check 10.4 — Unbiased Evaluation (PENDING — USER ACTION REQUIRED)

**Method (a): Paper trade log**
- Infrastructure: PaperTradeDashboard.jsx is live
- Action: Log the next XLF or QQQ bear_call_spread setup when it shows CAUTION
- Target: 30 trades before checking win rate
- Current: 0 trades logged

**Method (b): Adversarial LLM review (run monthly)**
Paste this prompt into ChatGPT or Claude with Opus:
```
Act as an adversarial options risk manager. I am considering selling an XLF bear_call_spread 
with strike $57/$58, expiry 22 DTE, credit $0.22, IVR=51, IV/HV=1.53. VIX=17.4, SPY above 200SMA. 
List every reason NOT to take this trade, ranked by severity. Be harsh.
```

**Method (c): Weekly gate pass rate log**

| Date | Candidates | GO | CAUTION | BLOCKED | Dominant Blocker |
|------|-----------|----|---------|---------|--------------------|
| 2026-05-07 | 11 | 0 | 2 | 9 | Liquidity Proxy (bid-ask >20%) |

---

## Phase 7c Deferred — Cyclical vs Defensive Weakening Logic

**Original question:** Weakening cyclicals (XLI, XLY, XLB) → sell_call instead of WAIT?

**Status:** Deferred. Today's universe shows XLI/XLY/XLB as **Lagging** (not Weakening) → bear_call_spread. The cyclical-vs-defensive question only activates when Weakening cyclicals are in ANALYZE status. No Weakening cyclicals today (XLE/XLRE = Weakening but both in WATCH/SKIP).

**Trigger:** When at least 2 of {XLI, XLY, XLB, XLF} show Weakening in the STA scan, revisit this research.

---

## Long-Term Trading Effectiveness Roadmap (Phase 7c+)

| Priority | Item | Status |
|----------|------|--------|
| Done | DTE seller floor: 21→30 | Day 46 ✅ |
| Done | ETF liquidity tier messaging | Day 47 ✅ |
| Done | Time-of-day spread advisory | Day 47 ✅ |
| Pending | Paper trade win rate (30 trades) | Ongoing |
| Pending | Adversarial LLM review | Monthly |
| Pending | Weekly gate pass rate trending | Weekly |
| Future | Cyclical vs defensive Weakening logic | When Weakening cyclicals active |
| Future | Alternative strike search (higher delta for Tier2 ETFs) | Research needed |
