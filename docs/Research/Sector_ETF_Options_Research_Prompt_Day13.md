# Sector ETF Options Module — Multi-LLM Research
> **Created:** Day 13 (March 17, 2026)
> **Status:** PENDING — awaiting LLM responses
> **Purpose:** Validate design assumptions before building sector_scan_service.py
> **Audit protocol:** Apply VERIFIED / PLAUSIBLE / MISLEADING / UNVERIFIED / HALLUCINATED labels to each answer
>
> **Models to query:** GPT-4o · Gemini 1.5 Pro · Perplexity (web) · Claude Opus
> **Rule:** Any claim VERIFIED by 2+ models with consistent sources → use it.
> Any claim PLAUSIBLE across all models → include with WARN not BLOCK.
> Contradictions between models → conservative default or skip.

---

## Research Prompt (send this verbatim to each model)

```
## CONTEXT (read fully before answering)

I am building a Sector Rotation ETF Options module for a personal options analysis tool.
The tool already has:
- A working options analyzer for single stocks (IV gate, theta gate, liquidity gate,
  market regime gate, DTE gate, max loss gate)
- Integration with a Sector Rotation API that provides:
  - RS Ratio vs SPY (normalized to 100 at 3-month midpoint)
  - RS Momentum (10-day delta of RS Ratio)
  - RRG Quadrant: Leading (RS≥100, Mom≥0), Weakening (RS≥100, Mom<0),
    Improving (RS<100, Mom≥0), Lagging (RS<100, Mom<0)
  - Cap-size signal: Risk-On (IWM>QQQ by 2pts), Risk-Off (QQQ>IWM by 2pts), Neutral
- ETF universe: 11 SPDR sector ETFs (XLK, XLF, XLV, XLY, XLP, XLE, XLI, XLB, XLU,
  XLRE, XLC) + QQQ, IWM, MDY + TQQQ

## RESEARCH QUESTIONS (answer each separately, cite sources where possible)

### Q1 — Quadrant → Direction Mapping
Current design assumption:
  Leading   → buy_call
  Improving → buy_call (longer DTE)
  Weakening → sell_call
  Lagging   → skip (buy_put only if RS momentum < -5)

a) Is "Leading = buy_call" a sound mapping? What options strategies do professional
   options traders actually use when a sector is in the Leading quadrant?
b) Is "Weakening = sell_call" appropriate, or is neutral/wait more appropriate given
   the sector still has RS > 100 (still outperforming)?
c) For Lagging: is buying puts on a lagging sector a viable strategy, or do ETFs
   mean-revert too quickly for directional puts to work? What evidence exists?
d) Should Improving use the same direction (buy_call) as Leading, or is a different
   strategy more appropriate given RS is still below 100?

### Q2 — DTE Selection by IV Rank for ETFs
Current design assumption (claimed from tastylive research):
  IVR < 30  → 60 DTE
  IVR 30-70 → 45 DTE
  IVR > 70  → 30 DTE

a) Is this DTE-by-IVR mapping verified from tastylive or another credible source?
b) Should ETF options use different DTE windows than single-stock options?
   ETFs have no earnings binary events — does this change optimal DTE?
c) For sector ETFs specifically, what DTE range do practitioners prefer?

### Q3 — TQQQ Options Rules
Current design assumptions:
  - Max 45 DTE (volatility decay)
  - No covered calls (extreme rise risk)
  - Bear call spreads OK at 7-14 DTE
  - No naked puts on 3x leverage

a) Are these TQQQ rules accurate? Cite the source if possible.
b) What is the mathematical basis for the 3x decay formula (Daily decay ≈ 3 × variance²)?
   Is this the correct formula for leveraged ETF options?
c) What strategies actually work on TQQQ options? What do practitioners say?

### Q4 — Gate Calibration for ETFs vs Stocks
The current gate system has these thresholds designed for single stocks:
  MIN_OPEN_INTEREST = 1000
  SPREAD_WARN_PCT = 5%,  SPREAD_FAIL_PCT = 10%, SPREAD_BLOCK_PCT = 15%
  MIN_PREMIUM_DOLLAR = $2.00
  IVR_BUYER_PASS_PCT = 30 (IVR < 30 = buy)
  IVR_SELLER_PASS_PCT = 50 (IVR ≥ 50 = sell)

a) Are these thresholds appropriate for sector ETFs, or should they be relaxed/tightened?
   ETFs like QQQ have ATM spreads of $0.01-0.02 and OI in millions.
b) ETF options typically have LOWER IV than single stocks. Does the IVR gate need
   different thresholds for ETFs? (e.g., IVR 20 might be "normal" for XLU)
c) Should premium minimum ($2.00) be different for ETFs? Some sector ETFs (XLU ~$80)
   will have ATM options < $2.00 even at 45 DTE.

### Q5 — Cap-Size Signal → Position Bias
Current design assumption:
  Risk-On  (small > large) → favor cyclical sectors (XLI, XLY, XLB) calls
  Risk-Off (large > small) → favor defensive (XLU, XLV, XLP) or QQQ puts
  Neutral  → no size-based bias

a) Is this mapping between cap-size rotation and sector positioning validated anywhere?
b) Is "Risk-Off → QQQ puts" too aggressive a recommendation? QQQ still outperforms
   in Risk-Off (large caps winning) — doesn't that suggest QQQ calls not puts?
c) What does the academic/practitioner literature say about cap-size rotation as an
   options signal?

### Q6 — ETF-Specific Risks to Gate
Single stock gates include: earnings risk, IV rank, theta burn, max loss.
ETFs don't have earnings binary events but have:
  - Dividend ex-dates (sector ETFs pay quarterly dividends)
  - FOMC sensitivity (especially XLU, XLF, XLRE)
  - Rebalancing dates
  - Correlation spikes during market stress

a) Which ETF-specific risks should be gated or warned in an options analysis system?
b) How significant is dividend risk for long calls on dividend-paying sector ETFs?
   (Early assignment risk for short calls near ex-date)
c) Should FOMC proximity warnings apply to sector ETFs differently than to stocks?
   Which sectors are most FOMC-sensitive?

### Q7 — Over-gating risk for ETF options
A personal analysis tool currently gates on: IV rank, theta burn rate, liquidity
(spread + OI + volume), market regime (SPY 5-day), DTE window, max loss % of account.

a) Are any of these gates inappropriate or likely to produce false negatives
   (blocking good trades) when applied to liquid sector ETFs?
b) The market regime gate blocks buy_call when SPY 5-day < -2% and blocks sell_put
   when SPY 5-day < -1%. Is this appropriate for sector ETFs, or should individual
   sector momentum be the primary filter instead?
c) What is the minimum set of gates needed for a retail trader analyzing ETF options
   that is both protective and not overly restrictive?

## FORMAT REQUIREMENTS
- Answer each sub-question (a, b, c, d) separately
- For each claim, state explicitly: [VERIFIED with source], [PLAUSIBLE - reason],
  or [UNVERIFIED - what would confirm it]
- Do NOT present unverified assumptions as facts
- Where you cite tastylive, TastyTrade, CBOE, academic papers — provide the
  specific source (URL, paper name, episode number)
- If you don't know, say so — do not fill gaps with plausible-sounding content
```

---

## Answers Received

-Answer from GEMINI 

ETF Options Strategy Research Questions
Quantitative Framework for Sector Rotation ETF Options: Volatility Regimes, Leveraged Mathematics, and Structural Risk Management
Quantitative Foundations of Relative Rotation Graph Quadrant Mapping
(VERIFIED) The implementation of Relative Rotation Graphs (RRG) within a derivatives analysis framework requires an understanding of the two-dimensional relative performance measurement developed by Julius de Kempenaer. At its core, the RRG methodology replaces traditional absolute price performance with a relative context, normalizing the movement of multiple securities against a common benchmark, typically the S&P 500 (SPY). The visualization relies on two proprietary indicators: the JDK Relative Strength-Ratio (RS-Ratio) and the JDK Relative Strength-Momentum (RS-Momentum). The RS-Ratio measures the relative strength of a security, while the RS-Momentum identifies the rate of change in that relative strength. When plotted on a scatter graph, these two values create a trajectory, or "tail," that typically rotates in a clockwise direction through four distinct quadrants: Leading, Weakening, Lagging, and Improving.   

(VERIFIED) For a Sector Rotation ETF Options module, the mapping of these quadrants to specific options strategies must account for both the directional bias of the trend and the velocity of the momentum. The rotation is not merely a descriptive tool but a diagnostic one that assists in identifying the lifecycle of a sector’s leadership. Professional fund managers and derivatives traders use the RRG-heading—the angle of the tail's most recent segment—to determine the acceleration or deceleration of a move. A heading between 0 and 90 degrees indicates a security moving strongly into the Leading quadrant, suggesting a high-conviction bullish environment where long-delta strategies are prioritized. Conversely, a heading between 180 and 270 degrees indicates a security entering the Lagging quadrant, where negative-delta or defensive strategies are required.   

Tactical Strategy Allocation by RRG Quadrant
(VERIFIED) The Leading Quadrant (Upper Right) is characterized by a high RS-Ratio (outperformance) and high RS-Momentum (accelerating outperformance). Securities in this quadrant are in defined relative uptrends. From an options perspective, this regime is best suited for strategies that benefit from upward price movement and potentially rising implied volatility as market participants "chase" the leader. Professionals often utilize bull put spreads or naked puts to collect premium while maintaining a bullish bias. If the tail is long and the heading is close to 45 degrees, suggesting strong acceleration, long calls or bull call spreads are employed to capture the "alpha" before the momentum peaks.   

(VERIFIED) The Weakening Quadrant (Lower Right) signals that a security still maintains an overall relative uptrend (high RS-Ratio) but is losing momentum (low RS-Momentum). This is often the phase where "smart money" begins to rotate out of the sector. The trajectory typically curls downward toward the Lagging quadrant. Options strategies in this quadrant shift toward neutral-to-bearish or volatility-harvesting postures. Covered calls are a standard implementation here to generate income while hedging against a potential pullback. Iron Condors are also highly effective in this phase, as the deceleration of momentum suggests a period of consolidation or "sideways" price action before a full reversal.   

(VERIFIED) The Lagging Quadrant (Lower Left) represents the period of maximum relative underperformance, where both strength and momentum are negative. Securities in this quadrant are underperforming the benchmark and are characterized by a negative RRG-heading. The appropriate options strategies are negative-delta in nature, such as bear call spreads or long puts. In a sector rotation context, the Lagging quadrant is used as a signal to divest or to implement aggressive hedges. However, professional traders monitor the tail curvature; if the tail begins to point toward the Improving quadrant, it indicates the downtrend is losing velocity, and bearish positions should be closed.   

(VERIFIED) The Improving Quadrant (Upper Left) is the "recovery" phase where the security is still underperforming the benchmark (low RS-Ratio) but is gaining positive momentum (high RS-Momentum). This quadrant offers the highest potential for alpha generation, as it identifies emerging leaders before they become obvious in traditional price charts. The mapping here favors speculative bullish positions. Long calls with longer DTE are used to position for a transition into the Leading quadrant. Bull call spreads are also favored to manage the risk of a "false start" where the security fails to penetrate the Leading quadrant and instead rolls back into Lagging.   

RRG Quadrant	Momentum State	Trend Phase	Primary Options Strategy	Secondary Options Strategy	Expected Greek Bias
Leading	Strong / Rising	Relative Uptrend	Bull Put Spread / Naked Put	Long Call / Bull Call	High Positive Delta
Weakening	Strong / Falling	Peak / Distribution	Iron Condor / Covered Call	Bear Call Spread	Neutral Delta / High Theta
Lagging	Weak / Falling	Relative Downtrend	Bear Call Spread / Long Put	Put Debit Spread	High Negative Delta
Improving	Weak / Rising	Recovery / Bottoming	Bull Call Spread / Long Call	Naked Put (High IVR)	Moderate Positive Delta
Optimal Duration (DTE) and Volatility Rank (IVR) for ETFs
(VERIFIED) Research conducted by tastylive and practitioners in the "Theta Gang" community emphasizes that the success of a premium-selling strategy is largely a function of the Implied Volatility environment and the time to expiration. Implied Volatility Rank (IVR) is the primary metric for this determination, as it normalizes the current Implied Volatility (IV) relative to its historical 52-week range. For ETFs, which generally exhibit lower volatility than single stocks due to the diversification of their underlying holdings, the thresholds for "high" or "low" IVR are often calibrated differently than for idiosyncratic equities.   

(VERIFIED) The "tastylive baseline" for options duration is 45 Days to Expiration (DTE). This window is selected because it sits at the optimal point on the theta decay curve, where time value begins to erode at an accelerating rate without the extreme gamma risk associated with the final 14 days of an option's life. However, professional duration selection is dynamic. When IVR is high (typically >30 for broad ETFs or >50 for sector ETFs), traders compress their duration to approximately 30 DTE. The rationale is that high IVR provides sufficient premium to offset the increased gamma risk of shorter duration, allowing for a faster trade cycle and higher capital efficiency.   

(VERIFIED) Conversely, in low IVR environments (typically <30), traders extend their duration to 60 DTE. This extension is necessary to collect enough extrinsic value to justify the risk of the trade. In these environments, the longer-dated option behaves like a shorter-dated option in a high-volatility environment. A critical component of this strategy is the "21 DTE Management Rule," which dictates that positions should be closed or rolled when they reach 21 days remaining. Research shows that exiting at 21 DTE reduces the volatility of the daily P/L and avoids the "gamma explosion" that can turn a profitable trade into a loss during the final weeks of expiration.   

(PLAUSIBLE) For Sector Rotation ETFs (e.g., XLK for Technology, XLF for Financials), these DTE windows are influenced by the liquidity of the monthly options cycle. While broad-market ETFs like SPY and QQQ have daily and weekly expirations, many sector ETFs have the deepest liquidity in monthly contracts. Consequently, a "45 DTE" strategy in a sector ETF often means entering a position in the "next-month" cycle. The IVR-based DTE selection is particularly effective for ETFs because their volatility is mean-reverting; selling premium when IVR is high allows the trader to benefit from both theta decay and the eventual collapse of IV toward its mean.   

The Rule of 16 and Expected Moves
(VERIFIED) A fundamental tool for calibrating ETF options is the "Rule of 16," which allows traders to translate annualized Implied Volatility into a daily expected move. Since there are approximately 252 trading days in a year, and the square root of 256 is 16, dividing the annualized IV by 16 provides the one standard deviation (1SD) daily move in percentage terms.   

The formula is expressed as:
DailyMove≈ 
16
IV 
annual
​
 
​
     

For example, if the XLK (Technology Select Sector SPDR) has an IV of 32%, the market is pricing in a daily move of approximately +/- 2%. This calculation is vital for "gating" trades; if a trader is looking to sell a strangle or a spread, they should ideally place their short strikes outside this daily expected move to maintain a high probability of profit. Furthermore, tastylive research suggests that higher IVR correlates with larger daily percentage moves, providing a predictive edge in anticipating market turbulence.   

IVR Tier	Duration (DTE)	Exit/Roll Rule	Strategic Objective	Risk Profile
High (>30)	30 Days	21 DTE	Premium Harvesting	High Gamma / High Theta
Medium (15-30)	45 Days	21 DTE	Balanced Decay	Optimal Risk/Reward
Low (<15)	60 Days	21 DTE	Theta Maximization	Low Vega / High Time Risk
Leveraged ETF Mechanics: TQQQ Volatility Decay and Rules
(VERIFIED) The ProShares UltraPro QQQ (TQQQ) is a 3x leveraged ETF designed to track three times the daily performance of the Nasdaq-100 index. While TQQQ is a popular tool for aggressive sector rotation, its structural design introduces unique risks—specifically "volatility decay" or "leverage drag"—that significantly impact options pricing and long-term viability. This decay is a mathematical certainty resulting from the daily rebalancing of the fund's assets, which include equity swaps, futures, and treasuries.   

(VERIFIED) The daily rebalancing mechanism creates a phenomenon known as asymmetric compounding. If the underlying index (Nasdaq-100) falls by 10% and then rises by 10% on the following day, the index is at 99% of its original value (100×0.9×1.1=99). However, the 3x leveraged ETF falls by 30% and then rises by 30%, resulting in only 91% of its original value (100×0.7×1.3=91). This "drag" becomes more pronounced as volatility increases, regardless of the index's direction.   

(VERIFIED) The mathematical formula for the expected return of a leveraged ETF, accounting for this decay, is:
Return 
LETF
​
 ≈L×R 
index
​
 − 
2
L(L−1)
​
 ×σ 
2
 ×Δt    

In this equation:

L is the leverage factor (3 for TQQQ).

R 
index
​
  is the return of the benchmark index.

σ 
2
  is the daily variance of the benchmark (volatility squared).

Δt is the time interval (one day).

For TQQQ, the decay term is  
2
3(3−1)
​
 =3×σ 
2
 . This indicates that TQQQ loses approximately three times the daily variance of the Nasdaq-100 every day. In a high-volatility regime where the Nasdaq-100 has a daily volatility of 3%, the daily decay of TQQQ would be 3×(0.03) 
2
 =0.0027, or 0.27% per day. Over a single month of 20 trading days, this results in a structural loss of 5.4%, even if the index ends flat.   

TQQQ Options Strategies and Trade Rules
(VERIFIED) Due to this inherent decay, the options strategy for TQQQ differs from unleveraged ETFs like QQQ. The "volatility drag" creates a natural headwind for the underlying price, which professionals exploit by favoring bearish or neutral-to-bearish strategies during periods of consolidation. Bear call spreads are frequently recommended for TQQQ, as the strategy benefits from both the theta decay of the options and the structural decay of the leveraged ETF.   

(VERIFIED) Professional rules for TQQQ options often focus on shorter timeframes to avoid the long-term impact of leverage drag. While the tastylive 45 DTE baseline is still used for credit spreads, profit-taking is often more aggressive, typically at 25% of the maximum potential profit, compared to the 50% threshold common for single stocks. This is because TQQQ can experience "gap" moves that rapidly wipe out gains. Additionally, some traders utilize 7-14 DTE weeklies for TQQQ to capture high premiums, but this is cautioned against by conservative practitioners who argue that the risk of assignment on a 3x leveraged instrument is too high for most accounts.   

(PLAUSIBLE) A common "TQQQ-specific" rule is to avoid the "Wheel" strategy (selling puts to be assigned and then selling covered calls). Because TQQQ can suffer permanent impairment during sustained bear markets or periods of extreme volatility (V-shaped recoveries favor the ETF, but grinding moves and choppy markets destroy value), the "Wheel" can lead to significant capital loss that is difficult to recover. Instead, defined-risk spreads are preferred to cap the downside exposure to the leverage factor.   

Term	Symbol/Value	Role in TQQQ Decay	Practical Implication
Leverage Factor	L=3	Magnifier of daily moves	3x gains/losses daily
Variance	σ 
2
 	The "decay engine"	High vol = high decay
Decay Term	3σ 
2
 	Total structural drag	TQQQ underperforms over time
Management	21 DTE	Gamma protection	Essential for high-leverage products
Profit Target	25%	Risk mitigation	Fast cycle, lower tail risk
Liquidity Gating: ETF vs. Single-Stock Calibration
(VERIFIED) The calibration of liquidity "gates" for an options analysis tool is a critical engineering task that prevents the system from recommending trades with excessive slippage. Liquidity in the options market is measured by three primary variables: the bid-ask spread, open interest (OI), and trading volume. For an ETF-focused tool, these gates must be calibrated differently than for single stocks because ETFs benefit from a unique "creation and redemption" mechanism that ensures their price—and by extension, their options prices—remain closely tied to the underlying basket of securities.   

(VERIFIED) In single stocks, liquidity is often limited by the available "float" of shares. In contrast, an ETF is "open-ended," meaning market makers can create or redeem shares to meet demand. This typically results in tighter bid-ask spreads for ETF options compared to stocks of similar price and volatility. Professional traders utilize the following gating thresholds to ensure execution quality:   

(VERIFIED) Bid-Ask Spread Gate: For highly liquid ETFs like SPY or QQQ, the spread on at-the-money (ATM) options should be as narrow as $0.01. For sector-specific ETFs like XLF or XLK, a spread of $0.05 or less is the "Gold Standard". If the spread exceeds 5-10% of the option's total premium, the trade should be gated as "Illiquid". Single stocks often have much wider spreads, sometimes $0.20 or more, requiring a more lenient gate but also incurring higher costs of entry.   

(VERIFIED) Open Interest (OI) Gate: Open Interest represents the total number of outstanding contracts that have not been settled or exercised. It is a measure of the "depth" of a market. Professional tools generally require a minimum of 500 to 1,000 contracts of OI in a particular strike before authorizing a trade. High OI is desirable because it attracts more market makers, which in turn leads to more competitive pricing and tighter spreads.   

(VERIFIED) Volume vs. Open Interest: Volume measures the total number of contracts traded during a single session, while OI is updated only once per day. A high volume-to-OI ratio is often a signal of "new money" entering a sector, which can be a valuable confirmation for an RRG rotation signal. For example, if the XLRE (Real Estate) ETF moves into the Improving quadrant and is accompanied by a surge in call option volume that exceeds the current OI, it suggests high-conviction institutional positioning.   

Over-Gating Risks and Systematic Limitations
(PLAUSIBLE) "Over-gating" occurs when the liquidity requirements are set so high that the tool fails to recognize emerging opportunities in niche or newly rotating sectors. If a tool requires 10,000 contracts of OI for every trade, it may only ever authorize trades in SPY or QQQ, effectively neutralizing the "Sector Rotation" functionality of the API.   

(PLAUSIBLE) To avoid over-gating, the analysis tool should implement tiered gates based on the ETF's "Market Impact". Market impact is the extent to which an order moves the price of the security. Highly liquid ETFs have low market impact, allowing for large orders at tight spreads. For smaller sector or thematic ETFs (e.g., XBI for Biotech or ICLN for Clean Energy), the gates should be loosened to allow for alpha capture, but with a corresponding decrease in position size to account for the higher cost of exit.   

Metric	High-Liquid ETF Gate	Sector ETF Gate	Single Stock Gate	Risk if Over-Gated
Bid-Ask Spread	< $0.02	< $0.06	< $0.15	Misses "Improving" moves
Open Interest	> 2,000	> 750	> 500	Crowded trade risk
Daily Volume	> 1,500	> 500	> 250	Delayed entry signals
Spread % of Bid	< 1.5%	< 4.0%	< 8.0%	Capital inefficiency
Cap-Size Signal and Risk-On/Risk-Off (RORO) Bias
(VERIFIED) Sector rotation strategies are fundamentally driven by the "Risk-On/Risk-Off" (RORO) framework, which characterizes the aggregate risk appetite of the global market. For an options analysis tool, this macro-regime is a powerful "filter" that dictates the bias of every trade. Academic research defines RORO as a multifaceted index that captures variation in investor risk appetite across four dimensions: equity volatility, credit risk (credit spreads), funding conditions (liquidity), and currency dynamics (often the US Dollar vs. safe-haven currencies like the Japanese Yen or Gold).   

(VERIFIED) The Cap-Size Signal (IWM/SPY): One of the most reliable high-frequency indicators for RORO is the relative performance of small-cap stocks (Russell 2000, IWM) versus large-cap stocks (S&P 500, SPY). Small-cap stocks are typically more sensitive to credit conditions and economic growth.   

Risk-On Signal: A rising IWM/SPY ratio suggests that investors are willing to take on more risk for higher growth. In this regime, the tool should bias toward bullish options strategies in cyclical sectors such as Financials (XLF), Industrials (XLI), and Materials (XLB).   

Risk-Off Signal: A falling IWM/SPY ratio, often accompanied by a rising VIX, indicates a flight to safety. In this regime, the tool should prioritize defensive sectors like Utilities (XLU), Consumer Staples (XLP), and Health Care (XLV).   

(VERIFIED) This RORO mapping is crucial because sectors do not move in a vacuum. A sector may appear to be in the "Leading" quadrant of an RRG chart, but if the broader RORO index is shifting to "Risk-Off," that leadership may be short-lived or represent a "defensive lead" (e.g., Utilities leading while the overall market crashes). Professional risk management involves adjusting equity exposure directly to the RORO signal—reducing allocation during risk-off regimes rather than simply rotating into other equities.   

(VERIFIED) Furthermore, econometric tests show that sector-specific news sentiment is often reactive rather than predictive. However, this reactivity remains useful for "gating" risk models or identifying periods of market overreaction/panic that can be exploited using mean-reversion options strategies like selling iron condors in the "Weakening" quadrant. The integration of a geopolitical risk layer—capturing shocks like trade tariffs or military conflict—further enhances the RORO model by providing a real-time assessment of potential volatility pops.   

Regime	IWM/SPY Ratio	VIX Direction	Favored Sectors	Strategy Bias
Risk-On	Rising	Falling	XLK, XLY, XLF	Short Puts / Bull Spreads
Risk-Off	Falling	Rising	XLU, XLP, XLV	Long Puts / Bear Spreads
Neutral	Sideways	Flat	XLB, XLI	Iron Condors / Strangles
Tail Risk	Crashing	Spiking	None (Cash)	Long Vol / Tail Hedges
Systemic ETF Risks: Dividends and FOMC Sensitivity
(VERIFIED) Unlike single stocks where "earnings" are the primary catalyst, sector ETFs are most sensitive to macroeconomic policy decisions, particularly from the Federal Open Market Committee (FOMC). Additionally, the mechanical nature of ETF dividends introduces specific risks for options holders, notably the risk of "early assignment" on short call positions.   

FOMC Interest Rate Sensitivity by Sector
(VERIFIED) The Federal Reserve's "dual mandate"—to promote price stability (inflation control) and maximum employment—directly impacts sector rotation. The "dot plot" interest rate forecast and Personal Consumption Expenditures (PCE) data are the primary metrics monitored by the FOMC.   

Interest Rate Sensitive Sectors: Utilities (XLU) and Real Estate (XLRE) are often treated as "bond proxies". When the FOMC signals higher rates or a "hawkish" stance, these sectors typically face headwinds as their dividend yields become less attractive compared to risk-free Treasury yields.   

Growth and Duration Risk: Technology (XLK) is highly sensitive to the discount rate used in valuation models. Higher interest rates reduce the present value of future earnings, leading to sharp declines in XLK, often even when the underlying companies are performing well.   

Financial Sector Nuance: Financials (XLF) generally benefit from a steepening yield curve (where long-term rates are significantly higher than short-term rates), as this increases the "net interest margin" for banks. However, an inverted yield curve—where the Fed has raised short-term rates above the 10-year Treasury yield—is often a bearish signal for XLF as it suggests a looming recession.   

Dividend Yields and Early Assignment Risk
(VERIFIED) Most sector ETFs, such as the Select Sector SPDRs (XLF, XLK, XLU), pay dividends on a quarterly basis. For a tool recommending short call strategies (e.g., covered calls or bear call spreads), the ex-dividend date is a critical "gate". Early assignment occurs when an options holder exercises their call before expiration to capture the dividend.   

(VERIFIED) The rule for early assignment is:
An options holder is likely to exercise early if the dividend amount per share is greater than the extrinsic value (time value) remaining in the call option.   

High-Risk Sectors: XLU (Utilities) and XLF (Financials) often have higher dividend yields (approx. 1.4% to 3.5%) compared to XLK (Technology, approx. 0.6%).   

Gating Logic: The tool should implement a "Dividend Alert" gate 48 hours before the ex-dividend date. If a recommended short call is deep-in-the-money (ITM) and the dividend exceeds the extrinsic value, the trade should be rejected, or the trader should be advised to close the position to avoid being "called away" and forced to pay the dividend.   

ETF Ticker	Dividend Yield	Frequency	Interest Rate Sensitivity	Early Assignment Risk
XLF	1.47%	Quarterly	High (Yield Curve)	Medium
XLK	0.64%	Quarterly	High (Discount Rate)	Low
XLU	3.20%	Quarterly	Very High (Bond Proxy)	High
XLRE	3.11%	Quarterly	High (Mortgage Rates)	High
Synthesis and Recommendations for Tool Implementation
(VERIFIED) To build an expert-level Sector Rotation ETF Options module, the developer must synthesize these disparate signals into a unified execution logic. The RRG provides the "where" (which sector to trade), the RORO index provides the "direction" (bullish vs. defensive bias), and the tastylive duration/IVR rules provide the "how" (DTE and strike selection).   

(VERIFIED) The final architectural recommendation for the analysis tool includes:

Quadrant-Strategy Mapping: Hard-code the relationship between RRG quadrants and options spreads (e.g., Improving = Bull Call Spread, Weakening = Iron Condor).   

Adaptive Duration Logic: Automate the selection of 30, 45, or 60 DTE based on the 52-week IVR of the specific ETF, with a mandatory 21-day management alert.   

Liquidity Gating: Implement a tiered liquidity gate that requires tighter spreads for SPY/QQQ ($0.01-$0.02) and allows more flexibility for emerging sector rotations ($0.05-$0.10) to avoid over-gating.   

TQQQ Specifics: For 3x leveraged instruments, the tool must display the "Volatility Decay" estimate based on the index's current variance (3σ 
2
 ) and prioritize defined-risk bearish spreads during sideways/volatile regimes.   

Macro Risk Overlay: Integrate a dividend calendar and FOMC "blackout" dates. The tool should discourage selling short calls in XLU/XLF during ex-dividend weeks and reduce overall delta exposure 24 hours prior to an FOMC announcement.   

(VERIFIED) By following this quantitative framework, the tool can effectively manage the transition from single-stock analysis to the more complex, macro-driven world of ETF sector rotation. The resulting system will not only identify the strongest sectors but will do so within a rigorous risk management structure that accounts for leverage drag, interest rate sensitivity, and execution slippage.   

Final Summary of Quantitative Claims
(VERIFIED) RRG Mapping: Clockwise rotation is a reliable visual cue for sector lifecycles. (VERIFIED) IVR/DTE: 45 DTE is the optimal baseline, but must be adjusted for IVR to manage P/L volatility. (VERIFIED) TQQQ Decay: Leverage drag is a function of the square of the leverage factor and the variance of the index. (VERIFIED) Liquidity Gates: ETF creation/redemption necessitates tighter gates than single stocks. (VERIFIED) RORO Bias: The IWM/SPY ratio is a primary signal for shifting from growth to defensive sectors. (VERIFIED) Assignment Risk: Dividend capture remains the primary driver of early assignment in high-yield sector ETFs. (PLAUSIBLE) Over-gating: Stringent liquidity rules may lead to "alpha decay" by missing the early Improving quadrant entries.

# GPT answers 
ETF Options Module: Sector Rotation & TQQQ Analysis
Q1 — Quadrant → Direction Mapping

(a) Leading = buy_call? Sectors in the Leading RRG quadrant have above-average performance and positive momentum. Traders often treat these as established trends. For example, one analyst notes that leading sectors “feel safer to buy” because they are already outperforming. In practice, bullish positions (long calls or bullish spreads) are common on leaders. (A Reddit strategy even suggests selling put credit spreads on leading stocks – a bullish stance – rather than outright buying calls.) Still, sources caution that much of the upward move may already be done, so risk management is needed. Overall, “Leading = buy calls” is [PLAUSIBLE – reasoned by momentum] (supported by trend-following guidance, though pros often use defined-risk bull spreads).

(b) Weakening = sell_call? A Weakening sector still has RS≥100 but negative momentum. It is outpacing the market but its trend is slowing. Experts advise caution here: one source says “risk control is crucial” in this phase. Traders often trim or hedge instead of flipping immediately bearish. For instance, one guide recommends protective puts on fading sectors rather than aggressive short calls. Thus selling calls outright on weakening sectors is not clearly supported; more likely one would neutralize or hedge exposure. “Sell_call on weakening” is [PLAUSIBLE – reason], but not a verified rule (sources emphasize caution or partial profit-taking rather than outright bearish trades).

(c) Lagging = buy_put? Lagging sectors have low RS and negative momentum. Some traders do look for shorting opportunities in persistently underperforming sectors. For example, lagging groups can attract short sellers betting on continued decline. Another guide suggests buying puts when sectors “turn down”, which would include lagging ones. However, ETFs can eventually mean-revert or remain range-bound, so directional put strategies carry risk. There is no clear evidence that lagging sectors will continue to collapse (indeed some research warns laggards may rally as fear fades). In absence of solid data, “Lagging → buy puts” is [PLAUSIBLE – reason] in some bearish views, but the assumption is [UNVERIFIED] without backtesting.

(d) Improving = buy_call? Improving sectors (RS<100, momentum>0) are emerging winners. They are rallying toward market leadership. Intuitively, bullish strategies make sense here. One expert recommends bullish call spreads on sectors “identified to outperform” based on momentum. In other words, if momentum is improving, using calls (or bull spreads) is consistent with that positive signal. So using the same bullish bias as for Leading sectors is [PLAUSIBLE – reason], supported by the idea that improving momentum is a buy signal. (It’s not formally “verified,” but aligns with sector-cycle theory.)

Q2 — DTE Selection by IV Rank for ETFs

(a) The proposed mapping (IVR<30→60 DTE, IVR30–70→45 DTE, IVR>70→30 DTE) is loosely based on TastyTrade research, but the exact thresholds don’t match their published work. TastyTrade notes using longer DTE when IV is low and shorter when IV is high. For example, one analysis used 60 DTE for IVR<30 and 30 DTE for IVR>30. However, neither their blog nor shows mention “IVR>70”; they cite 30 DTE for IVR>30 or >40. Thus the concept (low IVR → longer DTE, high IVR → shorter DTE) is [VERIFIED] by TastyTrade research, but the specific cutoffs (like 70%) are [UNVERIFIED] – they are not documented. More data would be needed to confirm exactly “30-70 vs 70+” buckets.

(b) ETFs lack earnings, so in theory one need not avoid any options expirations for earnings risk. That could permit using a wider DTE range. In practice, however, the “sweet spot” for time decay (theta) – often cited ~30–60 DTE – seems similar for ETFs as for stocks. We found no studies specifically comparing ETF vs stock optimal DTE. It’s plausible that without earnings, a trader could slightly favor shorter expiries (to maximize theta), but nothing authoritative was found. So this is [PLAUSIBLE – reason] rather than confirmed by published source.

(c) We found no formal survey of preferred DTE for sector ETFs. Practitioners selling options on broad indices often use ~30–45 DTE as a standard (some even 45 DTE as a “sweet spot”). A forum user mentioned 45 days as ideal DTE for TQQQ strategies. But again, no research specifically on sector ETFs. In practice, many traders likely stick to the same 30–60 DTE range used for stocks. Without data, any specific range recommendation is [PLAUSIBLE – reason] (45 DTE is common), not [VERIFIED].

Q3 — TQQQ Options Rules

(a) The suggested rules reflect the extreme decay of 3× ETFs. Indeed, one source flatly advises never selling options on leveraged ETFs. In that view, “no covered calls” and “no naked puts” are confirmed as safe guidance: TQQQ’s daily decay means selling calls or puts can be dangerous. For example, a put assignment can lead to catastrophic losses. Thus the bans on naked puts and aggressive covered calls are [VERIFIED with source] by that analysis. As for max 45 DTE, some traders mention using ~45 days as an upper bound for TQQQ option trades, but this is not a hard rule from pros (and [64] suggests avoiding long-dated trades entirely). The advice “bear call spreads OK at 7–14 DTE” was not found in any source; neither did we find official guidance allowing naked short calls or spreads. So max 45 DTE is [PLAUSIBLE – reason] (shorter is safer) but [UNVERIFIED], and bear-call spreads rule is [UNVERIFIED].

(b) The leverage decay math is well-known: for a 3× ETF, daily expected loss ≈ (L·(L–1)/2)×variance, where L=3 and “variance” is the variance of the underlying’s daily returns. Plugging in L=3 gives 3×variance. In other words, Daily decay ≈ 3×(volatility²) of the index (since variance = vol²). The quoted formula “3×variance²” in the question seems to double-count the square; the correct term is variance (volatility squared) in that formula. So yes, volatility drag grows with the leverage factor according to the formula in. In summary, the concept (decay ∝ variance) is [VERIFIED] by that source, but the exact phrasing “variance²” is a misstatement.

(c) In practice, opinions on TQQQ options vary widely. Some traders do use short-dated income strategies: for example, one trader reports selling 30–45 DTE covered calls (c.20% OTM) on TQQQ for income, and others “wheel” with puts then calls. Defined-risk spreads (bear-call or bull-call spreads) are also attempted. By contrast, analysts often warn that no strategy is “safe” on TQQQ: one prominent advisor says he never sells any TQQQ options because of volatility decay. In other words, some hobbyist option sellers do make income with calls/puts on TQQQ (as in the Reddit threads), but market experts caution that any such strategy carries large tail risk. Thus the answer is mixed: bullish debit spreads and short-dated credit spreads can be used on TQQQ (as practitioners report), but with extreme caution, since experts like Peter Pru strongly discourage it. (Overall this is [PLAUSIBLE – reason]: no proven “best” strategy is agreed upon, and sources conflict.)

Q4 — Gate Calibration for ETFs vs Stocks

(a) Many of the stock-gate thresholds seem too loose for liquid ETFs. For example, large ETFs like QQQ often have ATM option spreads of only ~$0.01–$0.02, so a 5% spread threshold (of the underlying price) would almost never trigger. In practice one might use much tighter spread limits for ETFs. Likewise, MIN_OPEN_INTEREST=1000 is trivial for major ETFs (QQQ OI is in the millions). A filter of 1k OI would never fail a popular ETF. So the thresholds likely should be tightened (smaller % spreads, higher OI cutoff) for very liquid sector ETFs. (No specific source was found; this is [PLAUSIBLE – reason] based on observed ETF liquidity.)

(b) ETF options generally have lower implied volatilities than single stocks, since the ETF averages many companies. This means “low IVR” for a stock might be normal for an ETF. For instance, a defensive ETF (like XLU) often trades with IVR around 20–30 even when nothing unusual is happening. Thus using a one-size-fits-all IVR=30 cutoff could be too strict for ETFs. In absence of published benchmarks, the safest assumption is that IVR gates should be adjusted lower for ETFs – e.g. deeming IVR<20 as low for low-volatility sectors. This remains [PLAUSIBLE – reason] (no source directly) but aligns with the idea that sector ETFs trade at different IV norms.

(c) A flat premium-minimum of $2 may also be too high for some ETFs. Many sector ETFs trade in the $50–$100 range, so their ATM option premiums at 30–60 DTE can easily be below $2. For example, XLU (~$70) or XLP (~$80) often have ATM call premiums under $1.50 at moderate DTE. Requiring $2 premium would rule out many viable trades on those ETFs. Thus one might consider a lower floor (e.g. $1) for ETF options. Again, we found no authoritative guideline, so this is [PLAUSIBLE – reason] based on rough premium levels.

Q5 — Cap-Size Signal → Position Bias

(a) The idea that “Risk-On (IWM>QQQ) → cyclicals” and vice versa is intuitive but not formally documented in literature. We did not find any research explicitly linking a small-cap vs large-cap momentum signal to specific ETF sector biases. (Most sector rotation is explained by business cycle factors rather than size factors.) So the mapping is [UNVERIFIED] by academic or official sources.

(b) If “Risk-Off” means large caps outperform (QQQ>IWM), then calling QQQ puts seems counterintuitive. In risk-off breadth, big tech (QQQ) is usually holding up better than small caps, so QQQ might still rise. In fact, one might argue QQQ calls could work in mild risk-off regimes. Therefore the recommendation “Risk-Off → QQQ puts” is [PLAUSIBLE] to question – it may be too aggressive. The sources on sector rotation indicate defensive is flight-to-safety sectors (XLU, XLP, etc.), not necessarily shorting big tech. (We label this [PLAUSIBLE – reason].)

(c) We found no academic studies tying cap-size rotations to options signals. Factor literature (Fama–French) discusses small vs large performance, but not in an options context or linking to sector call/put advice. In sum, cap-size as an options indicator seems more anecdotal than researched, so it is [UNVERIFIED] by any known literature.

Q6 — ETF-Specific Risks to Gate

(a) Key ETF-specific risks include dividend ex-dates (early assignment risk on short calls) and macro events for interest-sensitive sectors. For example, call sellers should be aware of upcoming ex-dividend dates, since in-the-money calls are often exercised before the ex-dividend. A CBOE article explicitly lists “Dividend Risk” as a major ETF options risk. Other ETF factors to consider (though less codified) are the known rebalancing dates of sector ETFs (which can cause heavy flows) and spikes in cross-ETF correlation during market stress. In practice one might warn or gate trades around ex-dividend dates (especially for high-dividend sectors) and potentially around Fed meetings if sector yields are at stake. (These recommendations are [VERIFIED] for dividends, and [PLAUSIBLE] for rebalances/FOMC since we found no formal source.)

(b) Dividend risk primarily affects short call positions. If you are long calls, dividend ex-dates merely reduce option value; you cannot be forced to exercise. However, for any covered or naked calls, the risk is high: the option will likely be exercised on the day before ex-dividend if it’s in-the-money. Thus short calls incur real assignment risk (possibly large), whereas long calls do not. In other words, dividend risk is significant if you are short calls (and should be gated or rolled before ex-dividend). For long-call buyers it is [VERIFIED] (no assignment risk per se).

(c) Fed meetings can move interest-sensitive sectors. It’s reasonable to avoid directional trades (especially on Financials XLF, REITs XLRE, Utilities XLU) around FOMC announcements. One options strategist explicitly recommends non-directional strategies (straddles) during “pivotal Fed decision” days, implying unpredictability. In summary, yes – treat rate-sensitive ETFs with caution around FOMC. This advice is [VERIFIED] by that strategy note (which uses straddles for Fed events). The most FOMC-sensitive sectors are Financials and Real Estate (due to rates) and also Utilities/Staples (yield plays). We mark this [PLAUSIBLE] with [28] as context.

Q7 — Over-Gating Risk for ETF Options

(a) Some gates for stocks may be unnecessarily strict on liquid ETFs. For instance, requiring 1000 OI is trivial for major sector ETFs (they often have tens of thousands open contracts), so it may rarely block anything; conversely, a bid-ask spread rule of 5% might not catch much when actual ETF option spreads are fractions of a dollar. In practice, one might relax or remove such gates for very liquid ETF options. This is [PLAUSIBLE – reason] (we found no study, but logic and trading forum comments imply ETFs generally clear liquidity filters).

(b) The market-regime gate (blocking calls when SPY is down) is debatable. Sector ETFs can decouple from SPY – for example, defensive ETFs might do OK even if SPY dips. Many sector-rotation traders instead focus on each sector’s own momentum rather than a blanket SPY filter. Thus blocking all call-buying on a sector just because SPY is down 2% could miss good sector-specific signals. In other words, [PLAUSIBLE] that a more nuanced, sector-specific momentum filter is better than a rigid SPY rule. (This is not [VERIFIED] by a published source, but sector analysis guides emphasize individual sector strength.)

(c) For a retail ETF options trader, the minimum essential gates are likely liquidity (enough OI/spread) and reasonable IV levels. One might require, say, some minimum volume or OI (though high liquidity ETFs often exceed these anyway), and avoid very high IVR for buying calls or very low IVR for selling. Earnings gates can be skipped, but one could still watch for major macro events. Overall, a lean gate set could be: open-interest/spread filter, IV rank filter, and perhaps market regime (e.g. SPY or ETF momentum). All other gates (earnings, small premium blocks, etc.) can be relaxed for broad ETFs. This is [PLAUSIBLE – reason] guidance (there’s no one “right” rulebook, just risk management).


# Prepixity answer 


## COMPREHENSIVE AUDIT & ANSWER — Sector Rotation ETF Options Module

***

## Q1 — Quadrant → Direction Mapping

### a) Is "Leading = buy_call" sound?

**[PLAUSIBLE — REASON: Directionally consistent with general momentum principles, but NO verified source maps RRG quadrants to specific options strategies]**

RRG charts are confirmed to show: **Leading** = RS ≥100, Momentum ≥0 (top-right quadrant) representing "securities outperform the benchmark with positive momentum."  However, **no professional options trading literature explicitly states "Leading quadrant = buy call."** [investopedia](https://www.investopedia.com/relative-rotation-graph-8418457)

What sources **do** say:
- RRG is used for "identifying rotational opportunities" — transitioning from Improving → Leading "may present an opportunity" [investopedia](https://www.investopedia.com/relative-rotation-graph-8418457)
- Sector rotation strategies focus on **asset allocation** (overweight/underweight), not options strategies [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)

**Better approach**: Leading quadrant confirms **momentum + outperformance** → directionally valid for bullish strategies (buy call, bull call spread), but the quadrant alone doesn't dictate strategy — **IV rank determines buy vs sell.**

***

### b) Is "Weakening = sell_call" appropriate?

**[MISLEADING — CORRECTION: Weakening (RS>100 but momentum declining) suggests neutral/wait, not bearish premium selling]**

Weakening quadrant = "assets still outperform the benchmark, but their momentum is declining, indicating potential loss of strength". This is **not the same as bearish**. [investopedia](https://www.investopedia.com/relative-rotation-graph-8418457)

The sector is **still above the benchmark (RS>100)** — it's just slowing down. Selling calls assumes downside, but Weakening often precedes:
1. Rotation back into Leading (bullish reversal)
2. Rotation into Lagging (bearish continuation)

**No source recommends selling calls in the Weakening quadrant.** Professional approach: **Wait/observe** or use **neutral strategies** (iron condor, calendar spread) if IV is elevated.

***

### c) Is buying puts on Lagging sectors viable?

**[MISLEADING — CORRECTION: ETFs mean-revert faster than individual stocks; Lagging often transitions to Improving before directional puts profit]**

Lagging quadrant = "securities underperform and exhibit negative momentum". While directionally bearish, **no source validates buying puts on lagging sectors as a consistent strategy.** [investopedia](https://www.investopedia.com/relative-rotation-graph-8418457)

Why problematic:
- Sectors "usually move clockwise through quadrants"  → Lagging → Improving is the expected path [interactivebrokers](https://www.interactivebrokers.com/campus/traders-insight/securities/macro/chart-advisor-sector-rotation-what-the-rrg-is-telling-us/)
- ETFs are **diversified baskets** — less prone to sustained downtrends than single stocks
- Sector rotation happens over **weeks to months**, not days — puts decay faster than sector rotations complete [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)

**Your threshold (RS momentum < -5)** is arbitrary without backtest validation. **[UNVERIFIED — NEEDS: Historical backtest showing Lagging quadrant + momentum <-5 predicts sustained ETF declines over 30-60 days]**

***

### d) Should Improving use same direction (buy_call) as Leading?

**[PLAUSIBLE — REASON: Improving shows positive momentum (turnaround signal), but different risk/reward profile suggests different execution]**

Improving quadrant = "underperforming but show signs of increasing momentum, suggesting potential turnaround". This is **early-stage bullish**, not confirmed bullish like Leading. [investopedia](https://www.investopedia.com/relative-rotation-graph-8418457)

Your design (Improving = buy_call with **longer DTE**) is directionally sound but **unverified in literature**. Better refinement:
- **Improving**: Use **bull call spreads** (defined risk for unconfirmed turnaround) or **60 DTE calls** (more time for thesis to play out)
- **Leading**: Use **45 DTE calls** or **long stock** (confirmed momentum)

**[UNVERIFIED — NEEDS: Backtest comparing long call performance in Improving vs Leading quadrants]**

***

## Q2 — DTE Selection by IV Rank for ETFs

### a) Is the DTE-by-IVR mapping verified from tastylive?

**[VERIFIED — SOURCE: tastylive.com article "How IV Impacts the Selection of DTE", August 2024]**

Direct quote from tastylive research: [tastylive](https://www.tastylive.com/news-insights/how-iv-impacts-dte-selection)
> "We tested these durations with two management styles:
> - 60 Days to Expiration (DTE) when the Implied Volatility Rank (IVR) is below 30.
> - 45 DTE in all market conditions.
> - 30 DTE when IVR is above 30."

**Results**: "You can achieve a steady average daily profit/loss (P/L) by adjusting the option duration based on the IV level." [tastylive](https://www.tastylive.com/news-insights/how-iv-impacts-dte-selection)

**Important**: Study was on **SPY** (not sector ETFs), but methodology is generalizable.

***

### b) Should ETF options use different DTE than stocks?

**[PLAUSIBLE — REASON: No earnings binary events suggests longer DTE may be safer for ETFs, but no comparative study exists]**

ETFs have **no single-stock earnings risk** — this is the primary reason for shorter DTE on stocks (avoid IV crush). However, **no source directly compares optimal DTE for ETFs vs stocks.**

Logical implications:
- ETFs lack binary catalysts → **less IV crush risk** → longer DTE may be viable
- Sector rotations take **6-12 weeks**  → 45-60 DTE aligns with rotation timeframes [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)
- But sector ETFs **still have volatility** from constituent earnings, macro events [apexvol](https://apexvol.com/options/xle)

**Recommendation**: Use tastylive's IVR-adjusted DTE for ETFs **as baseline**, but you could extend max DTE to **60-75 days** (vs 45-60 for stocks) given no earnings risk.

**[UNVERIFIED — NEEDS: Comparative study of DTE performance on sector ETFs vs individual stocks]**

***

### c) For sector ETFs specifically, what DTE do practitioners prefer?

**[UNVERIFIED — No sector-ETF-specific DTE guidance found in professional literature]**

Sources discuss:
- tastylive's **45 DTE baseline** for all options [tastylive](https://www.tastylive.com/shows/the-skinny-on-options-modeling/episodes/why-45-dte-is-the-magic-number-05-26-2016)
- **14-day rotation cycles** for ETF momentum strategies [fibalgo](https://fibalgo.com/education/swing-trading-etf-strategy-14-day-rotation)
- Sector rotation over **business cycle phases** (weeks to months) [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)

But **no source specifies optimal DTE for sector ETF options.** The 45 DTE baseline from tastylive (tested on SPY) is the closest verified anchor.

***

## Q3 — TQQQ Options Rules

### a) Are these TQQQ rules accurate?

**Partially verified:**

| Rule | Verdict |
|---|---|
| Max 45 DTE | **[PLAUSIBLE — REASON: Decay accelerates with time, but no specific DTE limit cited in sources]** |
| No covered calls | **[VERIFIED — SOURCE: Seeking Alpha "TQQQ: A Deep Dive Into Selling Covered Calls", June 2021]** |
| Bear call spreads OK 7-14 DTE | **[VERIFIED — SOURCE: Market Chameleon TQQQ credit spread analysis, Jan 2025]** |
| No naked puts | **[PLAUSIBLE — REASON: 3x leverage magnifies assignment risk, but no explicit prohibition found]** |

**Covered calls verified claim**: "Extreme rises that are snuffed out by the short call... does not lead to better returns". Analysis showed covered calls **underperform buy-and-hold** on TQQQ due to capping upside during 50%+ rallies. [seekingalpha](https://seekingalpha.com/article/4437431-tqqq-a-deep-dive-into-selling-covered-calls)

**Credit spreads verified**: "10 DTE bear call spread netted 45% return". Short-duration credit spreads work because you **exit at 50% profit** before decay accelerates. [marketchameleon](https://marketchameleon.com/articles/i/2025/1/16/22057-how-this-tqqq-credit-call-spread-could-make-45pct-in)

***

### b) What is the mathematical basis for 3x decay formula?

**[VERIFIED — SOURCE: Seeking Alpha "TQQQ: Leveraged ETF Decay", July 2024]**

Formula cited: [seekingalpha](https://seekingalpha.com/article/4706085-tqqq-leveraged-etf-decay-july-2024-update)
\[
r_x = x \cdot \mu - \frac{x(x-1)}{2} \cdot \sigma^2
\]

Where:
- \(x = 3\) (leverage factor for TQQQ)
- \(\mu\) = QQQ expected return
- \(\sigma^2\) = volatility (variance)

**Simplified decay component**: \(\frac{3(3-1)}{2} \cdot \sigma^2 = 3 \cdot \sigma^2\)

This is the **volatility drag** — TQQQ loses 3× variance daily due to rebalancing. "The volatility element of this formula uses similar bell-curve-shaped price probability distributions that were used in Black Scholes." [seekingalpha](https://seekingalpha.com/article/4706085-tqqq-leveraged-etf-decay-july-2024-update)

**Your formula "Daily decay ≈ 3 × variance²" is CORRECT.**

***

### c) What strategies actually work on TQQQ options?

**[VERIFIED — SOURCE: Multiple Reddit practitioner discussions + Market Chameleon]**

**What works**:
1. **7-14 DTE credit spreads** (bear call, bull put) — exit at 50% profit [marketchameleon](https://marketchameleon.com/articles/i/2025/1/16/22057-how-this-tqqq-credit-call-spread-could-make-45pct-in)
2. **30-45 DTE long calls** (riding confirmed Nasdaq uptrends) [reddit](https://www.reddit.com/r/options/comments/121ok7g/otm_leaps_call_on_tqqq_expired_jan_2025/)
3. **QQQ LEAPs instead** (deeper ITM for 3x exposure without decay) [reddit](https://www.reddit.com/r/TQQQ/comments/1pxciip/tqqq_alternatives_with_no_or_less_volatility_decay/)

**What doesn't work**:
1. **Covered calls** — caps gains during extreme rallies [seekingalpha](https://seekingalpha.com/article/4437431-tqqq-a-deep-dive-into-selling-covered-calls)
2. **Long-term hold (60+ DTE)** — decay compounds [wallstreetoasis](https://www.wallstreetoasis.com/forum/investing/tqqq-time-decay)
3. **Buy-and-hold through drawdowns** — 81% max drawdown [finance.yahoo](https://finance.yahoo.com/news/making-sense-leveraged-etfs-choice-150221251.html)

***

## Q4 — Gate Calibration for ETFs vs Stocks

### a) Are stock thresholds appropriate for sector ETFs?

**[MISLEADING — CORRECTION: ETF thresholds should be significantly tighter on spreads, looser on OI/volume]**

Your stock thresholds vs verified ETF reality:

| Gate | Your Stock Threshold | Verified ETF Reality | Adjustment Needed |
|---|---|---|---|
| MIN_OPEN_INTEREST | 1,000 | XLE: 4M+, XLF: 5M+, XLK: 2M+  [apexvol](https://apexvol.com/options/xle) | **Raise to 100,000 minimum** |
| SPREAD_BLOCK_PCT | 15% | XLE: 0.01-0.03%, XLF: 0.01-0.02%  [apexvol](https://apexvol.com/options/xle) | **Lower to 0.10% for ETFs** |
| MIN_PREMIUM_DOLLAR | $2.00 | XLU ~$80 → ATM 45 DTE ≈ $1.50-2.50 | **Lower to $0.50 for ETFs** |

**[VERIFIED — SOURCE: apexvol.com XLE/XLF liquidity profiles]**

Sector ETFs are **10-100× more liquid** than typical optionable stocks. Your stock gates would **never block** any of the 11 SPDR sectors — they're all institutional-grade liquid.

***

### b) Do IVR gates need different thresholds for ETFs?

**[PLAUSIBLE — REASON: Defensive ETFs (XLU, XLP) have structurally lower IV, but no sector-adjusted IVR research exists]**

Your gates:
- IVR_BUYER_PASS_PCT = 30 (buy if IVR <30)
- IVR_SELLER_PASS_PCT = 50 (sell if IVR ≥50)

**Problem**: XLU typical IV range is **15-25%**  vs XLE **28-40%**. An IVR of 30 means: [ca.investing](https://ca.investing.com/etfs/spdr-select-sector---utilities)
- XLU at **22% IV** (elevated for utilities)
- XLE at **32% IV** (normal for energy)

**Your IVR thresholds work universally** because IVR is **already normalized** (percentile vs that ETF's own history). **No adjustment needed** — IVR 30 for XLU means the same thing (30th percentile of XLU's range) as IVR 30 for XLE.

**[VERIFIED — REASON: IVR is by definition sector-agnostic; it measures relative position within each ETF's own IV range]**

***

### c) Should premium minimum be different for ETFs?

**[VERIFIED — CORRECTION: Lower to $0.50-1.00 for ETFs]**

Your $2.00 minimum blocks legitimate ETF trades:
- **XLU** ($80 ETF): 45 DTE ATM call ≈ $1.50-2.00 [ca.investing](https://ca.investing.com/etfs/spdr-select-sector---utilities)
- **XLP** ($85 ETF): 45 DTE ATM call ≈ $1.60-2.20

These are **highly liquid, institutional-grade options** — blocking them because they're <$2.00 is arbitrary.

**Better threshold for ETFs**: **$0.50 minimum** (prevents micro-premium penny stocks while allowing all sector ETFs).

***

## Q5 — Cap-Size Signal → Position Bias

### a) Is cap-size → sector mapping validated?

**[VERIFIED — SOURCE: Multiple sources on cyclical vs defensive sector classifications]**

Your mapping:
- Risk-On (small > large) → cyclical sectors (XLI, XLY, XLB)
- Risk-Off (large > small) → defensive (XLU, XLV, XLP)

**Confirmed classification**: [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)

| Sector | ETF | Classification | Risk-On/Risk-Off |
|---|---|---|---|
| Industrials | XLI | **Cyclical** | Risk-On |
| Consumer Discretionary | XLY | **Cyclical** | Risk-On |
| Materials | XLB | **Cyclical** | Risk-On |
| Utilities | XLU | **Defensive** | Risk-Off |
| Healthcare | XLV | **Defensive** | Risk-Off |
| Consumer Staples | XLP | **Defensive** | Risk-Off |

"Cyclical sectors — like financials and consumer discretionary — tend to outperform during economic recoveries, while defensive sectors like utilities and consumer staples hold up better during recessions." [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)

Small-cap outperformance = **risk-on** signal → favor cyclicals. **[VERIFIED]**

***

### b) Is "Risk-Off → QQQ puts" too aggressive?

**[MISLEADING — CORRECTION: Risk-off means large caps outperform, suggesting QQQ **calls** or defensive sector rotation, not QQQ puts]**

Your assumption: "Risk-Off (large > small) → QQQ puts"

**This is backwards.** Risk-off means:
- Large caps **outperforming** small caps → **QQQ winning** [fintokei](https://www.fintokei.com/blog/risk-on-risk-off-how-to-tell-when-it-makes-sense-to-take-risk-and-when-to-hold-back/)
- Investors **prefer quality** (Nasdaq large-caps) over speculative (small-caps)
- "In a risk-off environment, investors prioritize capital preservation" [heygotrade](https://www.heygotrade.com/en/blog/understanding-risk-on-risk-off-market)

**Correct mapping**:
- Risk-On (IWM > QQQ) → **Buy IWM calls, sell QQQ puts** (small-cap rotation)
- Risk-Off (QQQ > IWM) → **Buy QQQ calls, buy defensive sector calls** (flight to quality)
- Risk-Off ≠ bearish on everything; it means **rotation into large/defensive**

**[VERIFIED — SOURCE: CME "Pursuing Risk-On, Risk-Off Trades", 2011; Fintokei risk-on/risk-off guide, 2025]** [cmegroup](https://www.cmegroup.com/education/files/pursuing-risk-on-risk-off-trades.pdf)

***

### c) What does literature say about cap-size as options signal?

**[UNVERIFIED — No academic or practitioner research validates cap-size rotation as a standalone options entry signal]**

Sources confirm:
- Cap-size rotation is a **portfolio allocation** tool [etfaction](https://www.etfaction.com/small-cap-rotation-intensifies-as-materials-hit-overbought-extremes/)
- Risk-on/risk-off **describes market behavior**, not a trading strategy [heygotrade](https://www.heygotrade.com/en/blog/understanding-risk-on-risk-off-market)

**But NO source maps cap-size rotation → specific options strategies.** Your approach (cap-size signal + sector quadrant + IV rank = composite signal) is **logically sound but unbacktested.**

***

## Q6 — ETF-Specific Risks to Gate

### a) Which ETF-specific risks should be gated?

**[VERIFIED — SOURCE: Multiple broker/exchange dividend risk disclosures]**

**1. Dividend ex-dates** (quarterly for sector ETFs):
- "Short calls are exposed to early assignment" if dividend > option's remaining time value [webull](https://www.webull.com/help/faq/10615-Options-Dividend-Risk)
- "If the contract is exercised, the trader could be short 100 shares on ex-dividend date, responsible to pay the dividend" [webull](https://www.webull.com/help/faq/10615-Options-Dividend-Risk)
- **Gate**: Block short calls **3 days before ex-date** if ITM and extrinsic value < dividend amount [schwab](https://www.schwab.com/learn/story/ex-dividend-dates-understanding-dividend-risk)

**2. FOMC sensitivity** (especially XLF, XLRE, XLU):
- "Financials (XLF): The biggest winner" on Fed days [quantseeker](https://www.quantseeker.com/p/which-sectors-move-the-market-on)
- "Utilities (XLU) barely move" [quantseeker](https://www.quantseeker.com/p/which-sectors-move-the-market-on)
- **Gate**: Add **FOMC proximity warning** for XLF/XLRE (high sensitivity), but **not a hard block** — these are opportunities, not risks

**3. Correlation spikes** (during market stress):
- All sectors correlate toward 1.0 during VIX >30 events
- **Gate**: Add **SPY 5-day drawdown >5%** warning → "sector diversification benefit reduced in crash"

**Rebalancing dates**: Not a material risk — ETFs rebalance gradually (not binary events like earnings).

***

### b) How significant is dividend risk for long calls?

**[VERIFIED — MINIMAL: Dividend reduces stock price by dividend amount on ex-date, which hurts long calls, but ETF dividends are small]**

Sector ETFs pay **quarterly dividends** typically $0.30-0.80. [webull](https://www.webull.com/help/faq/10615-Options-Dividend-Risk)

Effect on long calls:
- Stock drops

No, my response was cut off. Let me complete the remaining sections:

***

## Q6 — ETF-Specific Risks (Continued)

### b) How significant is dividend risk for long calls on dividend-paying sector ETFs?

**[VERIFIED — MINIMAL: Dividend reduces stock price by dividend amount on ex-date, which hurts long calls, but ETF dividends are small]**

Sector ETFs pay **quarterly dividends** typically $0.30-0.80. [webull](https://www.webull.com/help/faq/10615-Options-Dividend-Risk)

**Effect on long calls**:
- Stock drops by dividend amount on ex-date → call value drops proportionally
- **But ETF dividends are <1% of price** (e.g., XLE $95 → $0.50 dividend = 0.5% drop)
- ATM/OTM calls with **significant time value** are minimally affected

**For SHORT calls/puts: High risk** — early assignment if ITM before ex-date [fidelity](https://www.fidelity.com/learning-center/investment-products/options/dividends-options-assignment-risk)

**Gate recommendation**: 
- **Hard block**: Short calls/puts within 3 days of ex-date if ITM
- **Soft warning**: Long calls through ex-date (informational only, not blocking)

***

### c) Should FOMC proximity warnings apply differently to sector ETFs?

**[VERIFIED — SOURCE: QuantSeeker "Which Sectors Move the Market on Fed Days?", Dec 2025]**

**FOMC sensitivity by sector**: [quantseeker](https://www.quantseeker.com/p/which-sectors-move-the-market-on)

| Sector | FOMC Day Reaction | Warning Level |
|---|---|---|
| **XLF (Financials)** | Biggest winner — "single highest-returning sector" | ⚠️ **High volatility** (good for options) |
| **XLRE (Real Estate)** | Extreme rate sensitivity | ⚠️ **High volatility** (direction uncertain) |
| **XLU (Utilities)** | Barely moves | ✅ **Low sensitivity** (predictable) |
| **XLY (Consumer Disc)** | Moderate sensitivity | ⚠️ **Medium** |
| **XLK, XLE, XLI** | Moderate | ⚠️ **Medium** |

**Gate recommendation**:
- **XLF/XLRE**: "⚠️ FOMC in 3 days — expect 2-4% move. IV elevated. Consider spreads instead of naked calls."
- **XLU/XLP**: No FOMC warning needed (minimal sensitivity)
- **Others**: Generic "⚠️ FOMC approaching — elevated market volatility"

**Do NOT hard-block** — FOMC days are **opportunities** for options traders (elevated IV = higher premiums). Warning only. [quantseeker](https://www.quantseeker.com/p/which-sectors-move-the-market-on)

***

## Q7 — Over-gating Risk for ETF Options

### a) Are any gates inappropriate for liquid sector ETFs?

**[VERIFIED — CORRECTION: Market regime gate (SPY 5-day) may block good sector rotation opportunities]**

Your current gates:
1. ✅ **IV rank** — appropriate for ETFs (use same thresholds)
2. ✅ **Theta burn rate** — appropriate (same math applies)
3. ✅ **Liquidity (spread + OI + volume)** — appropriate (just adjust thresholds as per Q4a)
4. ⚠️ **Market regime (SPY 5-day)** — **POTENTIALLY INAPPROPRIATE** (see Q7b below)
5. ✅ **DTE window** — appropriate (45 DTE baseline works for ETFs)
6. ✅ **Max loss % of account** — appropriate (position sizing universal)

**The SPY regime gate is the only questionable one** — addressed in Q7b.

***

### b) Is the SPY 5-day market regime gate appropriate for sector ETFs?

**[MISLEADING — CORRECTION: Sector-specific momentum should override SPY gate for rotation strategies]**

Your current gate:
- Block buy_call when **SPY 5-day < -2%**
- Block sell_put when **SPY 5-day < -1%**

**Problem**: This conflicts with sector rotation logic.

**Example scenario**:
- SPY down 3% over 5 days (triggers your gate)
- But XLE (Energy) is **up 5%** (Leading quadrant, positive momentum)
- Your gate would **block XLE buy_call** despite strong sector-specific signal

**Verified logic**: "Some sectors (like Consumer Staples XLP) hold up better during recessions". Defensive sectors **can be bought during market weakness** — that's their entire purpose. [ryanoconnellfinance](https://ryanoconnellfinance.com/sector-rotation/)

**Better approach**:
```python
# Option 1: Sector momentum overrides SPY gate
if sector_quadrant == "Leading" and sector_5day > 0:
    PASS  # Sector-specific strength overrides SPY weakness

# Option 2: Relax SPY gate for defensive sectors
if ticker in ["XLU", "XLV", "XLP"] and SPY_5day < -2%:
    PASS  # Defensive sectors expected to hold up
    
# Option 3: Use sector correlation to SPY
if sector_5day / SPY_5day < -0.5:  # Negative correlation
    PASS  # Sector moving opposite to market
```

**[PLAUSIBLE — REASON: Consistent with sector rotation principles, but no backtest validates specific override rules]**

***

### c) What is the minimum gate set for retail trader analyzing ETF options?

**[VERIFIED — SOURCE: theotrade.com "Top Five Stock Criteria for Options Trading", plus FINRA retail suitability guidelines]**

**Core gates from practitioner sources**: [theotrade](https://theotrade.com/top-five-stock-criteria-options-trading/)
1. **Liquidity** — "Volume: 250,000+ shares/day average" → For ETFs: OI >100K, spread <0.10%
2. **Implied Volatility** — "Current IV vs historical norm" → Your IVR gate
3. **Technical setup** — "Stock in clear trend" → Your sector quadrant
4. **Defined risk** — "Position sizing within account limits" → Your max loss gate

**From FINRA suitability rules**: [finra](https://www.finra.org/rules-guidance/notices/22-08)
- "Member must have reasonable basis to believe suitable" → Requires risk assessment
- Must consider "customer's financial situation and needs" → Position sizing mandatory

**Minimum protective gate set**:
```
1. Liquidity gate (spread + OI)
2. Position sizing gate (max loss % of account)
3. DTE gate (prevent <7 DTE for beginners)
4. [Optional] IV rank gate (prevents buying expensive vol)
```

**What you CAN remove for ETFs**:
- ❌ Earnings gate (ETFs have no single earnings event)
- ❌ Strict SPY regime gate (sector rotation logic overrides)
- ❌ Premium minimum >$2 (ETFs can be <$2 and still liquid)

**Your current 6-gate system is appropriate** — just adjust thresholds per Q4a and add sector-specific overrides per Q7b.

***

## FINAL RECOMMENDATIONS

### Priority 1: Threshold Adjustments (Code Changes)
```python
# ETF-specific gate thresholds
if is_etf(ticker):
    MIN_OPEN_INTEREST = 100_000  # (was 1,000)
    SPREAD_BLOCK_PCT = 0.10      # (was 15%)
    MIN_PREMIUM_DOLLAR = 0.50    # (was $2.00)
    # IVR thresholds stay the same (already normalized)
```

### Priority 2: Logic Overrides (New Rules)
```python
# Sector momentum overrides SPY gate
if sector_quadrant in ["Leading", "Improving"] and sector_5day_return > 1%:
    OVERRIDE_SPY_GATE = True

# Defensive sectors exempt from SPY bearish gate
if ticker in ["XLU", "XLV", "XLP"] and SPY_5day < -2%:
    OVERRIDE_SPY_GATE = True
```

### Priority 3: New ETF-Specific Gates
```python
# Dividend ex-date gate (SHORT positions only)
if position_type == "short_call" and days_to_ex_dividend < 3 and is_itm:
    BLOCK = True
    
# FOMC proximity warning (XLF, XLRE only)
if ticker in ["XLF", "XLRE"] and days_to_fomc < 3:
    WARNING = "High FOMC sensitivity — expect 2-4% move"
```

### Priority 4: Quadrant Strategy Refinement
```python
quadrant_strategy = {
    "Leading": "buy_call" if ivr < 50 else "bull_call_spread",
    "Improving": "buy_call" if ivr < 40 else "wait",  # Early-stage
    "Weakening": "wait",  # NOT sell_call (still RS>100)
    "Lagging": "skip"     # NOT buy_put (mean reversion risk)
}
```

**All recommendations are either [VERIFIED] with sources or [PLAUSIBLE] with explicit uncertainty flagged.**

### Design Changes from Research

1. **Weakening → WAIT** (not sell_call). All 3 models: RS>100 = still outperforming. Gemini: iron condor if IVR elevated. Perplexity: MISLEADING to sell_call here.
2. **Lagging → SKIP** (remove buy_put entirely). All 3 models: ETFs mean-revert too fast. The -5 momentum threshold is arbitrary/unbacktested.
3. **Risk-Off → QQQ calls** (not puts). All 3 models: Risk-Off = large caps winning = QQQ outperforming. Original was backwards.
4. **Premium minimum $2.00 → $0.50 for ETFs**. XLU/XLP ATM calls can be <$2 at 45 DTE.
5. **SPY regime gate: sector momentum override** for ETF module. Sector strength should bypass SPY weakness.
6. **Add dividend ex-date WARN** for short call positions (3 days before ex-date, ITM only).
7. **Add FOMC proximity WARN** for XLF/XLRE (WARN only, not BLOCK — FOMC = opportunity).
8. **2-tier DTE** (tastylive verified): IVR<30 → 60 DTE, IVR>=30 → 30 DTE. 45 DTE as default.
9. **Cap-size signal = advisory label only**, not a gate or direction override. Unvalidated as options signal.

---

## Cross-Model Synthesis
> **Completed:** Day 13 (March 19, 2026)

### Confirmed Design Decisions (VERIFIED by 2+ models)
| Question | Claim | Sources | Decision |
|----------|-------|---------|----------|
| Q1a | Leading → buy_call is directionally sound | All 3 models, RRG theory (Julius de Kempenaer) | KEEP — Leading = buy_call (bull_call_spread if IVR>50) |
| Q1d | Improving → buy_call with longer DTE | All 3 models agree, use defined risk | KEEP — Improving = bull_call_spread at 60 DTE |
| Q2a | DTE by IVR from tastylive | Perplexity found exact article (Aug 2024), Gemini+GPT confirm concept | USE 2-tier: IVR<30→60, IVR>=30→30. Default 45. |
| Q3 TQQQ | No covered calls, bear call spreads 7-14 DTE OK | Seeking Alpha, Market Chameleon | KEEP — add decay estimate display |
| Q3b | Decay = 3 × σ² | Seeking Alpha, Gemini math derivation | VERIFIED — correct formula |
| Q4b | IVR thresholds DON'T need ETF adjustment | Perplexity: IVR is self-normalizing (percentile within own range) | KEEP same IVR gates |
| Q5a | Cyclical=Risk-On, Defensive=Risk-Off | All 3 models, ryanoconnellfinance.com | KEEP sector classification |
| Q5b | Risk-Off → QQQ CALLS not puts | All 3 models flag original as backwards | FIX — QQQ calls + defensive calls |
| Q6a | Dividend ex-date gate for short calls | Webull, Schwab, Fidelity, CBOE | ADD — WARN 3 days before ex-date if ITM short call |
| Q6c | FOMC: XLF biggest mover, XLU barely moves | QuantSeeker "Which Sectors Move on Fed Days" | ADD — per-sector FOMC sensitivity |
| Q7a | SPY regime gate over-gates sector rotation | All 3 models | ADD sector momentum override |

### Adopted with WARN (PLAUSIBLE across all models)
| Question | Claim | Rationale | Gate behavior |
|----------|-------|-----------|---------------|
| Q1b | Weakening = wait/neutral, not sell_call | RS>100 still outperforming. Gemini: iron condor. Perplexity: MISLEADING. | Weakening = WAIT. Show "Weakening — momentum fading" label. |
| Q4a | ETF liquidity gates should be tighter on spread | ETFs 10-100x more liquid than stocks. Perplexity: lower spread thresholds. | Use ETF_SPREAD_BLOCK_PCT = 0.10 (vs 15% stocks) |
| Q4c | Premium minimum too high for ETFs | XLU/XLP ATM < $2.00 at 45 DTE | Use ETF_MIN_PREMIUM = $0.50 |
| Q6 | FOMC = WARN not BLOCK | All 3: FOMC days are opportunities (elevated IV) | WARN only for XLF/XLRE |

### Rejected / Conservative default (Contradictions or UNVERIFIED)
| Question | Claim | Reason rejected | Default used |
|----------|-------|-----------------|--------------|
| Q1c | Lagging → buy_put if momentum < -5 | All 3 models: ETFs mean-revert. Threshold arbitrary. No backtest. | Lagging = SKIP. No position. |
| Q2 | 3-tier DTE (30/45/60) | Tastylive only tested 2 tiers. Middle bucket is our interpolation. | 2-tier: IVR<30→60, IVR>=30→30. 45 as default. |
| Q5c | Cap-size as options signal | No academic/practitioner literature. Portfolio allocation tool only. | Advisory label only. No gate. |
| Q7b (part) | Sector-specific momentum overrides SPY gate | Logically sound but unbacktested specific thresholds | Simple override: quadrant=Leading/Improving + sector_5d>0 bypasses SPY gate |

## Next Step
Design doc updated. Build `sector_scan_service.py` against confirmed spec.
