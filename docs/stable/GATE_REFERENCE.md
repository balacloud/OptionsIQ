# OptionsIQ — Gate Reference
> **Last Updated:** Day 66 (Jun 5, 2026)
> **Purpose:** Complete gate inventory — all 4 directions, all thresholds, block vs warn classification.
> **Source of truth:** `backend/gate_engine.py` + `backend/constants.py`

---

## Related docs
- [GOLDEN_RULES.md](GOLDEN_RULES.md) — Rule 23 (pre-filter tools own their checks), Rule 22 (Quant + Architect personas)
- [QUANT_PERSONA.md](QUANT_PERSONA.md) — Marcus Webb persona for adversarial gate review
- [API_CONTRACTS.md](API_CONTRACTS.md) — gate fields in analyze response (`gates`, `verdict`, `blocking_gate`)
- [MASTER_AUDIT_FRAMEWORK.md](MASTER_AUDIT_FRAMEWORK.md) — Category 3: Gate Logic Audit
- [ROADMAP.md](ROADMAP.md) — Phase 11: gate calibration history
- [`backend/constants.py`](../../backend/constants.py) — all numeric thresholds
- [`backend/gate_engine.py`](../../backend/gate_engine.py) — gate implementations

---

## Hard block philosophy (Rule 23)

A gate should be a **hard block** only if:
1. The condition represents an **immutable, age-old risk law** — not a preference
2. **No pre-filter tool** (e.g. `/ibkr-scan`) already checked it before the user reached this screen

Gates that duplicate a pre-filter check must be advisory WARN only. Hard blocks are reserved for structural risks that the system uniquely enforces.

**Current hard blocks that meet this bar:**
- `trend_ema` — price below 200 EMA for sellers: structural downtrend = structural risk
- `events` (FOMC for XLF/XLRE/TQQQ) — rate/leverage instruments inside FOMC window
- `hv_iv_vrp` for GLD — GLD IV/HV < 1.10 is too subtle for a watchlist scan; backend must own it
- `liquidity` — spread > 20%: data is garbage at that spread, strikes are unreliable

---

## Quick reference — all 4 directions

| Gate | buy_call | buy_put | sell_put | sell_call |
|------|----------|---------|----------|-----------|
| `ivr` / `ivr_seller` | WARN | WARN | WARN *(Day 66)* | WARN *(Day 66)* |
| `hv_iv` / `hv_iv_vrp` | WARN | WARN | **BLOCK** (GLD only) / WARN | **BLOCK** (GLD only) / WARN |
| `vix_regime` | — | — | **BLOCK** (VIX > 40) | **BLOCK** (VIX > 40) |
| `theta_burn` | **BLOCK** (burn > 12%) | **BLOCK** (burn > 12%) | — | — |
| `dte` / `dte_seller` | **BLOCK** (< 14 DTE) | **BLOCK** (< 14 DTE) | **BLOCK** (< 7 or > 60) / WARN (14–29) | **BLOCK** (< 7 or > 60) / WARN (14–29) |
| `events` (FOMC) | WARN | WARN | **BLOCK** (XLF/XLRE/TQQQ ≤14d) | **BLOCK** (XLF/XLRE/TQQQ ≤14d) |
| `event_density` | — | — | WARN | WARN |
| `holdings_earnings` | WARN | WARN | WARN | WARN |
| `liquidity` | **BLOCK** (spread > 20%) | **BLOCK** (spread > 20%) | **BLOCK** (spread > 20%) | **BLOCK** (spread > 20%) |
| `market_regime` (bull) | WARN | — | — | — |
| `market_regime` (bear) | — | WARN | — | — |
| `market_regime_seller` | — | — | WARN *(Day 66)* | WARN *(Day 66)* |
| `stress_check` | — | — | WARN | WARN |
| `put_call_sentiment` | — | — | WARN | WARN |
| `skew_flow` | — | — | WARN | WARN |
| `max_loss` | — | — | WARN | — |
| `risk_defined` | — | — | — | WARN |
| `trend_ema` | **HARD BLOCK** (pema200 < 0) | **HARD BLOCK** (pema200 > 0) | **HARD BLOCK** (pema200 < 0) | WARN (pema200 > 0) |
| `tqqq_satellite` | — | — | WARN (TQQQ only) | WARN (TQQQ only) |
| `position_size` | WARN | WARN | — | — |
| **Total gates** | **10** | **10** | **16** | **16** |
| **Hard blocks** | **3** | **3** | **6** *(was 9, Day 66)* | **5** *(was 7, Day 66)* |
| **WARN only** | **7** | **7** | **10** | **11** |

---

## Gate detail — buyer tracks (buy_call / buy_put)

Both buyer tracks share the same 10-gate structure. They differ only in `trend_ema` direction and `market_regime` polarity.

### `ivr` — IV Rank (Buyer)
- **What it checks:** Is implied volatility cheap enough that buying options has edge?
- **Thresholds:** IVR < 30% → pass; 30–50% → warn; > 50% → warn (IV crush risk)
- **Blocking:** WARN only — `/ibkr-scan` owns environment check (Rule 23)
- **Constant:** `IVR_BUYER_PASS_PCT=30`, `IVR_BUYER_WARN_PCT=50`

### `hv_iv` — HV/IV Ratio (Buyer)
- **What it checks:** Are options fairly priced relative to how much the ETF actually moves?
- **Thresholds:** IV/HV < 1.05 → pass; 1.05–1.10 → warn; > 1.10 → warn
- **Blocking:** WARN only
- **Constant:** `HV_IV_PASS_RATIO`, `HV_IV_WARN_RATIO`

### `theta_burn` — Theta Burn
- **What it checks:** Will theta decay eat too much of the option value over the planned hold?
- **Thresholds:** ≤ 8% over hold period → pass; 8–12% → warn; > 12% → **BLOCK**
- **Blocking:** YES — excessive theta on a long option is a structural entry problem
- **Constant:** `THETA_BURN_PASS_PCT=8`, `THETA_BURN_WARN_PCT=12`

### `dte` — DTE Selection (Buyer)
- **What it checks:** IVR-based DTE recommendation. Low IVR → target 60 DTE. High IVR → target 30 DTE.
- **Thresholds:** Within ±10 DTE of target → pass; outside → warn or fail
- **Blocking:** YES if DTE < 14 (absolute minimum — gamma chaos)
- **Constant:** `DEFAULT_MIN_DTE=14`, `ETF_DTE_LOW_IVR=60`, `ETF_DTE_HIGH_IVR=30`

### `events` — FOMC / Macro Calendar (Buyer)
- **What it checks:** Is there a FOMC meeting or major macro event inside the holding window?
- **Blocking:** WARN only for buyers — defined risk means a vol spike can't cause more than premium paid
- **Note:** Never blocks buyers even for XLF/XLRE/TQQQ — only sellers are blocked

### `holdings_earnings` — Key Holdings Earnings
- **What it checks:** Does any major holding of the ETF report earnings before expiry?
- **Blocking:** WARN only. ETF diversification reduces single-stock gap risk.
- **Source:** `ETF_KEY_HOLDINGS` (16 ETFs) + `COMPANY_EARNINGS` (52 companies, Q2–Q4 2026)

### `liquidity` — Bid-Ask Spread
- **What it checks:** Is the bid-ask spread tight enough for fair execution?
- **Thresholds:** ≤ 20% → WARN (normal ETF range); > 20% → **BLOCK** (data unreliable)
- **Blocking:** YES above 20% — at that spread, mid-price is meaningless for strike selection
- **Constant:** `SPREAD_DATA_FAIL_PCT=20.0`

### `market_regime` — SPY Regime (Buyer)
- **What it checks:** Is the broad market aligned with the direction?
  - buy_call: SPY above 200 SMA + 5d return positive → pass
  - buy_put: SPY below 200 SMA + 5d return negative → pass
- **Blocking:** WARN only — `/ibkr-scan` already surfaces regime

### `trend_ema` — Trend Gate (Buyer)
- **What it checks:** Is EMA trend aligned with direction? (from `/ibkr-scan` P/EMA values)
  - buy_call: pema200 < 0 → **HARD BLOCK** "don't buy calls in a downtrend"
  - buy_put: pema200 > 0 → **HARD BLOCK** "don't buy puts in an uptrend"
- **Blocking:** YES — unconditional. Only activates when `/ibkr-scan` context is pasted.
- **Note:** If no scan context pasted → pass-through (gate shows pass with "no scan data")

### `position_size` — Position Sizing
- **What it checks:** Can you afford at least 1 lot within the 1% risk budget?
- **Blocking:** WARN only

---

## Gate detail — seller tracks (sell_put / sell_call)

Seller tracks share most gates. Key differences noted per gate.

### `ivr_seller` — IV Rank (Seller)
- **What it checks:** Is premium elevated enough to make selling worthwhile?
- **Thresholds:** IVR ≥ 35% → pass; 25–35% → warn; < 25% → **BLOCK**
- **Blocking:** YES — selling into thin IV is negative-expectancy (Sinclair / tastylive research)
- **Constant:** `IVR_SELLER_PASS_PCT=35`, `IVR_SELLER_MIN_PCT=25`
- **Rule 23 note:** `/ibkr-scan` also checks IVR. Consider whether this should be WARN only.

### `hv_iv_vrp` — Volatility Risk Premium (Sinclair)
- **What it checks:** Is IV > HV (i.e., are you actually collecting a premium edge)?
- **Thresholds (non-GLD):** IV/HV ≥ 1.05 → pass; 1.0–1.05 → warn; < 1.0 → warn
- **Thresholds (GLD):** IV/HV ≥ 1.10 → pass; < 1.10 → **HARD BLOCK**
- **Blocking:** YES for GLD only. Gold options have unique correlation dynamics — GLD IV/HV < 1.10 means insufficient premium for the underlying correlation risk.
- **Constant:** `HV_IV_SELL_PASS_RATIO=1.05`

### `vix_regime` — VIX Regime (Seller)
- **What it checks:** Is market fear at a level where short-premium has positive expectancy?
- **Thresholds:** < 15 → warn (too thin); 15–30 → pass; 30–40 → warn (reduce size); > 40 → **BLOCK**
- **Blocking:** YES at VIX > 40 — crisis regime, negative expectancy for short premium (tastylive 21-year study)
- **Constant:** `VIX_LOW_VOL=15`, `VIX_STRESS=30`, `VIX_CRISIS=40`

### `strike_otm` — Strike OTM Check
- **What it checks:** Is the recommended strike actually OTM?
  - sell_put: strike must be ≥ 3% below underlying → pass
  - sell_call: strike must be ≥ 2% above underlying → pass
- **Blocking:** YES if ITM — entering an ITM sell position has immediate intrinsic loss
- **Constant:** `SELL_PUT_OTM_PASS_PCT=3.0`, `SELL_CALL_OTM_PASS_PCT=2.0`

### `dte_seller` — DTE Window (Seller)
- **What it checks:** Is DTE in the ETF seller sweet spot?
- **Thresholds:** 30–45 DTE → pass; 21–29 DTE → warn (entering gamma zone); < 21 or > 60 → BLOCK
- **Blocking:** YES outside window. Research: 30-45 DTE captures 46% of high-Sharpe profit before gamma amplifies (tastylive 200k+ trades).
- **Constant:** `ETF_DTE_SELLER_PASS_MIN=30`, `ETF_DTE_SELLER_PASS_MAX=45`

### `events` — FOMC / Macro Calendar (Seller)
- **What it checks:** Is a rate-moving event inside the holding window?
- **Blocking (3-tier):**
  - XLF/XLRE/TQQQ sellers within 14d → **HARD BLOCK** (rate/leverage sensitive)
  - QQQ/IWM/GLD within 7d → WARN (vol risk but not structural)
  - FOMC inside DTE window (any ticker) → WARN
  - FOMC outside DTE window → pass
- **Constant:** `FOMC_BLOCK_TICKERS={XLF, XLRE, TQQQ}`, `FOMC_BLOCK_DAYS=14`

### `event_density` — Multi-Event Density (KI-097)
- **What it checks:** Are there multiple macro events (FOMC + CPI + NFP + PCE) stacked inside the DTE window?
- **Blocking:** WARN only — one event is a gate; stacking is escalating advisory
- **Weighted:** Rate-sensitive ETFs escalate one tier earlier

### `holdings_earnings` — Key Holdings Earnings
- Same as buyer tracks. WARN only. See buyer section above.

### `liquidity` — Bid-Ask Spread
- Same as buyer tracks. BLOCK above 20%. See buyer section above.

### `market_regime_seller` — SPY Regime (Seller)
- **What it checks:** Is the broad market safe for premium selling?
  - sell_put: SPY above 200 SMA + 5d return not strongly negative → pass
  - sell_call: same check but polarity inverted (wants flat/weak market)
- **Blocking:**
  - sell_put: YES if SPY strongly down — downtrend = structural risk for put sellers
  - sell_call: **WARN only** — sector RS/momentum weakness overrides SPY trend for relative shorts (overridden in `apply_etf_gate_adjustments` Day 62)

### `stress_check` — McMillan Historical Stress (Day 30)
- **What it checks:** Is the short strike inside the ETF's worst historical 21-day swing?
  - sell_put: strike vs worst 21-day drawdown
  - sell_call: strike vs worst 21-day rally
- **Blocking:** WARN only — historical data is informational, not a structural rule
- **Source:** `iv_store.compute_max_21d_move()` from `ohlcv_daily` table

### `put_call_sentiment` — Put/Call Volume Ratio (Day 54)
- **What it checks:** Is options volume sentiment aligned with the trade direction?
- **Thresholds:** P/C > 1.3 → warn (heavy put buying); P/C < 0.6 → warn (aggressive call buying)
- **Blocking:** WARN only — sentiment is advisory, not a structural gate
- **Constant:** `PUT_CALL_RATIO_BEAR_WARN=1.3`, `PUT_CALL_RATIO_BULL_WARN=0.6`

### `skew_flow` — IV Skew / Institutional Flow (Day 66) ⭐ new
- **What it checks:** Is 30-delta put/call IV skew signalling unusual institutional hedging flow?
  - sell_put: put_iv_30d − call_iv_30d ≥ 7 pts → warn (institutions hedging); ≥ 10 pts → strong warn
  - sell_call: skew ≤ 2 pts → warn (call momentum / squeeze risk)
- **Blocking:** WARN only — Rule 23: `/ibkr-scan` owns flow checks
- **Source:** `tradier_provider.compute_skew()` → 30-delta put vs call IV
- **Constant:** `SKEW_PUT_WARN_PTS=7.0`, `SKEW_PUT_STRONG_PTS=10.0`, `SKEW_CALL_WARN_PTS=2.0`

### `max_loss` — Max Loss vs Account (sell_put)
- **What it checks:** Does the max loss fit within account risk limits?
- **Thresholds:** ≤ 10% of account → pass; 10–20% → warn; > 20% → warn (not block for naked put)
- **Special case:** For bull_put_spread, recalculated on spread width — can block if spread max loss > 20%
- **Blocking:** Generally WARN only. Block only for oversized spreads.
- **Constant:** `MAX_LOSS_WARN_PCT=0.10`, `MAX_LOSS_FAIL_PCT=0.20`

### `risk_defined` — Risk Defined (sell_call)
- **What it checks:** Is the sell_call a spread (defined max loss) or naked call (uncapped risk)?
- **Blocking:** WARN only — naked calls are permitted but flagged

### `trend_ema` — Trend Gate (Seller)
- **What it checks:** EMA trend alignment from `/ibkr-scan` P/EMA values
  - sell_put: pema200 < 0 → **HARD BLOCK** "don't sell puts into a downtrend"
  - sell_call: pema200 > 0 → **WARN only** (uptrend = higher risk but not structural block)
- **Blocking:** HARD BLOCK for sell_put only. sell_call never blocks on trend.
- **Note:** Inactive (pass-through) if no `/ibkr-scan` context pasted.

### `tqqq_satellite` — TQQQ Rules (KI-107, sell tracks only)
- **What it checks:** TQQQ-specific constraints (3x leverage rules)
  - Strategies filtered to delta ≤ 0.10
  - VIX ≥ 18 → warn (3x leverage amplifies vol-crash risk)
- **Blocking:** WARN only — user verified QQQ regime via `/ibkr-scan`
- **Constant:** `TQQQ_MAX_DELTA=0.10`

---

## Gate count summary

| | buy_call | buy_put | sell_put | sell_call |
|-|----------|---------|----------|-----------|
| Total gates | 10 | 10 | 16 | 16 |
| Hard blocks | 3 | 3 | 9 | 7 |
| WARN only | 7 | 7 | 7 | 9 |

Buyer tracks are lean by design — defined risk means fewer structural constraints.
Seller tracks are heavier — undefined loss requires more pre-trade guardrails.

---

## Gates that could be relaxed (Rule 23 review candidates)

| Gate | Direction | Current | Argument for WARN |
|------|-----------|---------|-------------------|
| `ivr_seller` | sell_put/sell_call | BLOCK | `/ibkr-scan` already gates IVR environment |
| `market_regime_seller` | sell_put | BLOCK | Already WARN for sell_call — asymmetric treatment |
| `dte_seller` | sell_put/sell_call | BLOCK (< 30 DTE) | 21-29 DTE is suboptimal, not catastrophic |

These have not been changed because: (a) no paper trade data yet to validate relaxation, (b) the blocking only fires on genuinely marginal setups.

---

## Version history

| Day | Change |
|-----|--------|
| Day 66 | `skew_flow` gate added (sell_put + sell_call, WARN only). This document created. Marcus Webb gate review: `ivr_seller` + `market_regime_seller` (both sell tracks) downgraded to WARN. sell_put hard blocks: 9→6. DTE threshold corrected (21-29 DTE was already WARN — GATE_REFERENCE had wrong values). |
| Day 62 | 5 gates changed hard-block → warn: `ivr_buyer`, `hv_iv_buyer`, `market_regime` (all dirs), `max_loss`, VRP non-GLD. Rule 23 added. |
| Day 60 | `trend_ema` gate added to all 4 tracks. HARD BLOCK for sell_put/buy_call/buy_put. |
| Day 59 | GLD `hv_iv_vrp` upgraded to hard block (< 1.10). TQQQ `tqqq_satellite` added. |
| Day 57 | Architecture pivot — single-leg only. `event_density` gate added. FOMC 3-tier logic. |
| Day 54 | `put_call_sentiment` gate added (non-blocking). |
| Day 49 | `event_density` weighted scoring. IVR null → `ivr_confidence="unknown"` warn not fail. |
| Day 29 | `stress_check`, `put_call_sentiment`, `vix_regime`, VRP seller gate added. |
| Day 28 | `holdings_earnings` gate added (ETF key holdings + company earnings calendar). |
