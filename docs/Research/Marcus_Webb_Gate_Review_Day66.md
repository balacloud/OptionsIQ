# Marcus Webb — OptionsIQ Gate Review
> **Date:** Day 66 (Jun 5, 2026)
> **Reviewer:** Marcus Webb (persona defined in `docs/stable/QUANT_PERSONA.md`)
> **Source material:** `docs/stable/GATE_REFERENCE.md`
> **Verdict format:** KEEP AS-IS / DOWNGRADE TO WARN / REMOVE / MISSING

---

## Opening statement

I've been doing this for 30 years. I've seen systems with 3 gates and systems with 50. The 50-gate systems don't make more money — they make fewer trades and give the developer the feeling of rigor without the substance of it. So before I go gate by gate, here's my top-line read:

This system knows what it's doing on the structural rules. The 200 EMA gate, the GLD VRP gate, the FOMC block for rate-sensitive tickers — those are real. Someone who has been hurt by the market wrote those.

Where it needs work: there are 9 hard blocks on sell_put. That's too many. Three or four of them are preferences dressed up as laws. I'll point them out. Fix them and you'll have a system that finds trades instead of filing reasons not to take them.

---

## Buyer Tracks (buy_call / buy_put)

### `ivr` — IV Rank (Buyer)
**Verdict: KEEP AS-IS**

Warn only for buyers is correct. High IVR means you're paying more for the option — that's a real concern (IV crush after entry), but it doesn't make the trade impossible. It changes the entry size and target DTE. The morning scan already flagged it. Don't double-gate it here.

---

### `hv_iv` — HV/IV Ratio (Buyer)
**Verdict: KEEP AS-IS**

Same logic. If IV is running above HV for buyers, that's an IV crush risk signal. Worth showing. Not worth blocking on. The scan handles it.

---

### `theta_burn` — Theta Burn (Buyer)
**Verdict: KEEP AS-IS — but verify the hold period assumption**

If theta is eating more than 12% of the option value over the planned hold, you're in a time race you're going to lose. That's a structural entry problem. Hard block is defensible.

My one question: what is "planned hold period" hardcoded as? If it's a fixed 21 days for a 60-DTE option, the math is fine. If it's hardcoded to something that doesn't match the actual strategy DTE, your theta calculations are wrong. Verify the assumption. If it's correct, this gate earns its keep.

---

### `dte` — DTE Selection (Buyer)
**Verdict: KEEP AS-IS**

Below 14 DTE for a buyer is not a trade. Gamma is chaotic, bid-asks are wide, and you need an immediate directional move to profit before time decay kills you. Hard block at 14 is right.

The IVR-based DTE recommendation — 60 DTE when IVR is low, 30 DTE when IVR is high — is also sound. In high-IV environments you need less time because the premium is richer relative to the move you need. This is evidence-based. Leave it alone.

---

### `events` — FOMC (Buyer)
**Verdict: KEEP AS-IS**

Buyers have defined risk. The worst FOMC can do is cause IV crush after the event resolves, which hurts the option value. But you can't lose more than you paid. Warn is correct. Never block buyers on events.

---

### `holdings_earnings` — Key Holdings Earnings (Buyer)
**Verdict: KEEP AS-IS**

ETF diversification genuinely reduces single-stock event risk. When JPMorgan reports, XLF moves — but XLF is 40 names, not one. A gap that would crater a single-stock call barely moves the ETF call. Warn is appropriate. Don't over-gate this.

---

### `liquidity` — Bid-Ask Spread (Buyer/Seller)
**Verdict: KEEP AS-IS — consider tightening to 15% eventually**

At 20% spread, you're getting filled at the offer going in and the bid coming out. On a $2.00 spread option that's $0.40 of immediate slippage before the market does anything. That is not a trading cost — that's a donation.

20% is the right floor. I'd personally use 10% but I understand the ETF market can be wider on OTM contracts early in the session. 20% as an absolute block is defensible. Once you have paper trade history, consider tightening to 15%.

---

### `market_regime` — SPY Regime (Buyer)
**Verdict: KEEP AS-IS**

Warn only for buyers is correct. Regime is context, not a law, and the scan already surfaces it. A directional buyer who wants to buy calls in a weakening market is making a contrarian bet — that's their right. Tell them the context, don't stop them.

---

### `trend_ema` — EMA Gate (Buyer)
**Verdict: KEEP AS-IS**

Don't buy calls when price is below the 200 EMA. Don't buy puts when price is above the 200 EMA. This is survival, not analysis. I've been saying this since 1997. Hard block is correct.

One design note: the gate is pass-through when no /ibkr-scan context is pasted. That means a user who skips the morning scan bypasses the most important gate in the system. Not a code bug — a workflow discipline issue. Make sure the UI makes that consequence visible.

---

### `position_size` (Buyer)
**Verdict: KEEP AS-IS for now — revisit at 30 paper trades**

1% risk budget is conservative. For a system with zero paper trade history, that's the right call. You don't know your edge yet. When you have 30 trades and a real win rate, you'll have the data to justify a larger allocation. 2-3% per position is where most professional traders land. For now, warn at 0 lots is fine.

---

## Seller Tracks (sell_put / sell_call)

### `ivr_seller` — IV Rank (Seller)
**Verdict: DOWNGRADE TO WARN**

This is my biggest objection to the current system.

IVR below 25% blocks the trade. But your own morning scan (/ibkr-scan) already checked IVR before the user opened OptionsIQ. If the scan passed and the user came here, you're now overruling the scan's decision. That's double-gatekeeping. It tells the user "the scan said OK, but actually no." That's a broken experience.

More importantly: IVR is a preference, not a law. You can absolutely sell a put when IVR is 22% if IV/HV is above 1.05. The volatility risk premium still exists. The gate that earns the right to be a hard block is `hv_iv_vrp` — that's checking whether the edge is actually present. IVR alone is just checking historical context, which the scan already handled.

**Action: downgrade `ivr_seller` to WARN only. Let `hv_iv_vrp` be the VRP law-enforcer.**

---

### `hv_iv_vrp` — Vol Risk Premium (Sinclair)
**Verdict: KEEP AS-IS — this is the best gate in the system**

Euan Sinclair spent 20 years proving this empirically. IV trades above realized vol on average — that's the edge. When IV drops below HV, the edge is gone or inverted. You're not collecting a premium anymore; you're selling cheap.

GLD hard block at IV/HV < 1.10 is correct. Gold options have unusual correlation with equity vol, commodity trends, and currency moves. The 1.10 floor accounts for that complexity. For non-GLD, warn at 1.0 is also right — you might still trade it, but you need a good reason.

This gate alone justifies the entire system. Don't touch it.

---

### `vix_regime` — VIX Regime (Seller)
**Verdict: KEEP AS-IS**

February 5, 2018. VIX went from 17 to 37 in a single session. XIV, the short-vol ETF, went to zero. Every trader who was short premium without a VIX gate got a portfolio reminder that day.

At VIX > 40, vol-of-vol is so high that your delta hedge is perpetually behind. You're playing catch-up. Hard block is right. The warn at VIX < 15 is also right — thin premium is a slow leak that erodes edge without the obvious pain of a spike.

The thresholds (15 / 30 / 40) align with Tastylive's 21-year study. Don't touch them.

---

### `strike_otm` — Strike OTM Check (Seller)
**Verdict: KEEP AS-IS — as a safety net**

If this gate fires, something is broken in the chain fetch upstream. A properly calibrated strategy ranker with delta 0.15-0.28 targeting should never surface an ITM sell strike under normal conditions. This gate is a canary, not a real filter. Keep it as a hard block — it should fire only when the data pipeline has a problem.

---

### `dte_seller` — DTE Window (Seller)
**Verdict: PARTIALLY DOWNGRADE — keep < 21 and > 60 as BLOCK, relax 21-29 to WARN**

The research is right: 30-45 DTE is the sweet spot. Tastylive has the data. I have 30 years that agrees. But here's the problem:

You're hard-blocking 21-29 DTE. A 28-DTE setup with perfect IV/HV, perfect trend, perfect strike — blocked because DTE is 2 days short of 30. That is a preference, not a law. 21-29 DTE is suboptimal; it's not catastrophic. Gamma is rising but not yet dangerous. Theta is still accelerating.

Hard block makes sense at the extremes:
- **< 21 DTE**: Gamma acceleration is real. You're in the danger zone. Block.
- **> 60 DTE**: Theta is too slow, capital tied up too long. Block.
- **21-29 DTE**: Suboptimal. Warn with "DTE below optimal entry window — gamma risk rising." Let the trader decide.

**Action: relax 21-29 DTE block to WARN. Keep < 21 and > 60 as hard blocks.**

---

### `events` — FOMC Calendar (Seller)
**Verdict: KEEP AS-IS — do not touch this gate**

I'll defend this in any room.

XLF is 40% financials. Rate decisions reprice bank earnings, loan books, and net interest margin in real time. XLRE is 100% real estate — the most rate-sensitive sector in the market. TQQQ is 3x leveraged technology. Within 14 days of a Fed meeting, options on these instruments develop wide bid-asks, reduced liquidity, and binary event risk.

I've been on the wrong side of FOMC in 2004 (the 50bp surprise), in 2013 (taper tantrum), and in 2022 (75bp shock). Every time, the short-premium position lost money — not because the trade was wrong directionally, but because the exit was ugly. Hard block for these tickers within 14 days is not caution — it's experience.

---

### `event_density` — Multi-Event Density
**Verdict: KEEP AS-IS — but measure its fire rate**

Stacking events is a real concern. CPI + NFP + FOMC in a 30-day window changes the risk profile of a short-premium position materially. Warn only is correct — it's advisory context, not a structural block.

My only warning: if this gate warns on > 60% of normal 45-DTE setups (because there's almost always something in a 45-day window), it becomes noise. Track what percentage of setups it fires on. If it's consistently high, reduce sensitivity or narrow the scoring window.

---

### `holdings_earnings` — Key Holdings Earnings (Seller)
**Verdict: KEEP AS-IS**

Same logic as buyer tracks. ETFs dilute single-stock event risk. The 52-company calendar is good coverage. Warn is appropriate. Don't block — the ETF structure means you're not taking earnings binary risk the way single-stock options do.

---

### `market_regime_seller` — SPY Regime (Seller)
**Verdict: DOWNGRADE sell_put to WARN — align with sell_call treatment**

You already downgraded this to WARN for sell_call in Day 62. You didn't do it for sell_put. That asymmetry doesn't hold up.

Here's the logic problem: sell_put and sell_call are both short-premium strategies. The argument for blocking sell_put on SPY regime is "SPY strongly down = structural risk for put sellers." But you already have `trend_ema` as a hard block for exactly that condition — price below 200 EMA for sell_put is already a structural block.

So what is `market_regime_seller` adding on top of `trend_ema`? If both are in the same gate track, `trend_ema` catches the structural case, and `market_regime_seller` is catching a softer "SPY 5-day return negative" case. That's a preference, not a law. And the scan already told the user what the regime is.

**Action: downgrade sell_put `market_regime_seller` to WARN only. `trend_ema` owns the structural case.**

---

### `stress_check` — McMillan Historical Stress
**Verdict: KEEP AS-IS**

McMillan's rolling max drawdown work is legitimate context. If the ETF has historically made 21-day moves of 18% and your short strike is only 5% OTM, that's information worth surfacing. Warn only is exactly right — historical data tells you what's possible, not what's likely. You'll still take the trade but with adjusted expectations.

---

### `put_call_sentiment` — Put/Call Volume Ratio
**Verdict: KEEP AS-IS — but be careful with directional interpretation**

P/C ratio above 1.3 is worth noting. My only caution: at extreme readings (P/C > 2.0), put buying sometimes signals a market near a sentiment extreme — everyone's hedged, the pain trade is up. It can be a contrary indicator at the tail. For moderate elevated readings (1.3-1.8), it's a genuine warning. Warn only is correct. Don't try to make this a block.

---

### `skew_flow` — IV Skew / Institutional Flow
**Verdict: KEEP AS-IS — good addition, right thresholds**

Finally. This is the gate I was looking for.

When 30-delta put IV is 10 points above 30-delta call IV, someone with serious capital is paying up for downside protection. That doesn't mean you don't take the trade — sometimes institutions hedge badly, and their hedging creates rich premium you can harvest. But it means you size down and pick a wider strike cushion.

7 points elevated: yellow light. 10+ points: orange light. Both as WARN only is the right architecture — it's information that changes position sizing, not a hard no.

The sell_call case (skew ≤ 2 pts = call momentum) is equally valid. When calls are nearly as expensive as puts, someone is chasing upside aggressively. Selling calls into that flow is fighting momentum. Worth knowing. Warn is right.

---

### `max_loss` — Max Loss (sell_put)
**Verdict: KEEP AS-IS**

For a naked put, theoretical max loss is the full strike value. Any gate trying to compare that against account size is going to either block everything or warn on everything. Warn only is the right call — it's surfacing information about position sizing, not making a structural judgment.

---

### `risk_defined` — Risk Defined (sell_call)
**Verdict: KEEP AS-IS**

Flagging naked calls is right. Uncapped upside risk is real. Some traders are comfortable with it, some aren't. Warn without blocking respects both.

---

### `trend_ema` — EMA Gate (Seller)
**Verdict: KEEP AS-IS — the asymmetry between sell_put and sell_call is justified**

Hard block for sell_put when pema200 < 0: correct. Selling puts below the 200 EMA is one of the most reliable ways to lose money in options. You're selling insurance against a decline into a market that is already declining. The premium looks rich because the risk is real.

WARN only for sell_call when pema200 > 0: also correct. Selling calls in an uptrend is higher risk, but it's not structurally wrong — especially if IV/HV is strong and the ticker has sector-specific weakness. Asymmetric treatment is justified here.

---

### `tqqq_satellite` — TQQQ Rules
**Verdict: KEEP AS-IS**

TQQQ max delta 0.10 is right. A 2% market move is a 6% TQQQ move. At delta 0.20 you're taking on genuine near-money risk for a 3x product. 0.10 as the cap gives real cushion.

VIX ≥ 18 warn for TQQQ is also right — at elevated vol, 3x leverage turns normal daily moves into position-killers. Warn without blocking respects the trader's judgment while making sure they're aware.

---

## Missing Gates

### MISSING 1: Strike vs 1-SD Expected Move
**Verdict: ADD as WARN**

You display expected move per strategy in TopThreeCards. Good. But is there a gate that fires when the short strike is *inside* the expected 1-SD move?

If the market is pricing a 1-SD move of ±3% and your short put strike is only 2% OTM, your probability of profit is below 50%. You are not selling a safe OTM put — you are making a directional bet with a liability attached. That deserves an explicit warning: *"Short strike is inside 1-SD expected move — probability of assignment elevated."*

This is one of the most common mistakes I see from traders building their first systematic approach. They look at delta 0.20 and think "80% win rate." But if the expected move puts the strike in-play, the delta is a trailing indicator — the chain hasn't repriced yet.

**Suggested threshold:** if strike is within the 1-SD expected move range → WARN "Strike inside expected move — POP < 50%."

---

### MISSING 2: Exit plan as a formal gate — or at least as a commitment field
**Verdict: ADD as informational display, not a gate**

You show exit_plan per strategy. That's good. But the most common way traders lose money on short-premium strategies is not entry — it's holding past the optimal exit. Holding a short put that's at 50% profit waiting for 80% profit, running into an event week, and giving it all back.

This can't be enforced through software. But at the time of logging a paper trade, the exit rules should be captured as committed fields: "Target: 50% profit. Hard stop: 200% of premium received. Time stop: 21 DTE." If those aren't committed at entry, the paper trade record is incomplete.

---

## Overall Verdict

**The structural bones are correct.** The 200 EMA gate, GLD VRP gate, FOMC block for rate-sensitive tickers, VIX crisis block — these are real, evidence-based, and correctly implemented as hard blocks. Whoever designed these has been hurt by the market at some point and learned the right lesson.

**The calibration needs one more round.** You have 9 hard blocks on sell_put. After the changes I'd recommend, you'd be at 6:

| Gate | Recommendation |
|------|---------------|
| `ivr_seller` | DOWNGRADE to WARN — double-gatekeeping with scan |
| `market_regime_seller` (sell_put) | DOWNGRADE to WARN — `trend_ema` owns structural case |
| `dte_seller` (21-29 DTE) | DOWNGRADE to WARN — suboptimal, not catastrophic |

That gets sell_put from 9 hard blocks to 6. Those 6 are: trend_ema (200 EMA), FOMC for rate-sensitive, GLD VRP, liquidity (>20% spread), VIX > 40, and strike_otm (safety net). Every one of those is a law.

**Is it a machine for finding trades or avoiding them?**

Right now: 60% avoidance, 40% finding. After the recommended changes: 40% avoidance, 60% finding. That's where it should be.

The best options systems I've seen have 4-5 hard blocks and 8-10 advisories. You're close. Clean up the three preference-disguised-as-law blocks, add the expected move gate, and this is a system I'd use.

---

## Action Items (priority order)

| # | Action | Gate | Impact |
|---|--------|------|--------|
| 1 | Downgrade to WARN | `ivr_seller` | Removes double-gatekeeping vs scan |
| 2 | Downgrade sell_put to WARN | `market_regime_seller` | Aligns with sell_call treatment; trend_ema owns structural case |
| 3 | Relax 21-29 DTE to WARN | `dte_seller` | Recovers valid setups in 21-29 DTE window |
| 4 | Add new gate | `expected_move_check` | Surfaces when strike is inside 1-SD move |
| 5 | Paper trade capture | Exit rules at entry | Commits exit plan fields at trade log time |

---

*Review completed by Marcus Webb persona. Findings saved per docs/stable/QUANT_PERSONA.md instructions.*
*Implement changes via normal session protocol — verify against gate_engine.py before coding.*
