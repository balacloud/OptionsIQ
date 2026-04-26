# OptionsIQ — Known Issues Day 28
> **Last Updated:** Day 28 (April 22, 2026)
> **Previous:** KNOWN_ISSUES_DAY27.md

---

## Resolved This Session (Day 28)

### KI-079: No ETF holdings earnings gate ✅ RESOLVED Day 28
Added `ETF_KEY_HOLDINGS` (16 ETFs → top moveable holdings) and `COMPANY_EARNINGS` (52 companies, Q2–Q4 2026 dates) to `constants.py`. New `_etf_holdings_at_risk()` helper in `analyze_service.py` computes holdings reporting before expiry. New `_etf_holdings_earnings_gate()` in `gate_engine.py` warns when any key holding reports inside the DTE window. Wired into all 4 ETF direction tracks. Verified live: XLK/May22 correctly shows AMD (6d), MSFT (7d), AAPL (9d) at risk.

### KI-080: Liquidity gate does not hard-fail on extreme bid-ask spread ✅ RESOLVED Day 28
Added `SPREAD_DATA_FAIL_PCT = 20.0` to `constants.py`. `_liquidity_gate()` now exposes raw `spread_pct` on the gate dict. `apply_etf_gate_adjustments()` only downgrades spread-fail to warn when `spread_pct <= 20%`; above 20% keeps `blocking=True` with reason "data unreliable at this width". Prevents bad delta data from driving wrong strike selection (the 27.52%-spread XLY trade that selected ATM instead of OTM).

### KI-FOMC-GATE: FOMC gate only checked imminence, not holding window ✅ RESOLVED Day 28
**Root cause:** `_etf_fomc_gate()` only warned when `5 <= fomc_days <= 10`. If FOMC was 20 days away but DTE was 30, FOMC was silently inside the holding window but the gate passed. Caught by ChatGPT stress test on XLK sell_put (FOMC April 29, DTE 30).
**Fix:** Gate now warns whenever `fomc_days < dte` (FOMC before expiry), regardless of absolute proximity. Clear threshold: warn if inside window, pass if outside. Reason string now shows both FOMC days and DTE for transparency.

---

## New Issues This Session (Day 28)

### KI-082: No credit-to-width ratio gate for defined-risk spreads (MEDIUM)
**Component:** `backend/gate_engine.py` — sell_put / sell_call gate tracks
**Description:** A bull_put_spread collecting $0.05 on a $1-wide spread (5% of width) was rated acceptable. Industry minimum is ~20% of width (e.g. $0.20 on $1 wide). At $0.05, commissions alone consume the credit and the risk/reward is indefensible. Caught by ChatGPT stress test on XLK 152/151 spread.
**Fix path:** Add `MIN_CREDIT_WIDTH_RATIO = 0.20` to `constants.py`. In `_run_etf_sell_put` and `_run_etf_sell_call`, after strategy selection, compute `credit / spread_width` and fail if below threshold. Requires strategy_ranker to pass `spread_width` and `credit_received` to gate_payload.
**Audit trigger:** Category 1 (Gate Logic), Category 5 (Behavioral Claims)

---

## Still Open (Carried Forward)

### KI-081: No CPI/NFP/PCE macro events calendar (LOW)
Only FOMC is tracked. CPI, NFP, PCE, and other major macro releases are not in the events gate. These can spike sector ETF IV significantly around release dates. Fix path: Add macro events calendar to constants.py (similar to FOMC_DATES).

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
ETF-only mode means stocks return 400. Deferred indefinitely.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put direction for QQQ returns ITM put strikes (~$637 vs $624 underlying). Chain struct_cache issue. Still open.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
~5pp gap between L2 percentile and L3 average. Data-specific, low impact.

### KI-044: API_CONTRACTS.md partially stale (MEDIUM)
ETF-only enforcement documented Day 27. OI supplement documented. Some ETF fields still not documented.

### KI-075: GateExplainer GATE_KB may drift from gate_engine.py logic (MEDIUM)
GATE_KB has hardcoded plain English pass/fail answers. If gate thresholds change, frontend answers go stale silently.

### KI-076: TradeExplainer isBearish() not live-tested against all 4 directions (MEDIUM)
`isBearish()` determines profit/loss zone colors. Not yet verified live for all 4 directions.

### KI-038: Alpaca OI/volume fields missing (LOW)
### KI-034: OHLCV temporal gap not validated (LOW)
### KI-013/KI-050: API URL hardcoded in JS files (LOW)
### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)
### KI-072: deepcopy() on every cache hit in data_service.py (LOW)
### KI-073: _struct_cache grows unbounded in ibkr_provider.py (LOW)
### KI-074: No IBWorker health check at startup (LOW)
### KI-077: DirectionGuide "Risk: Spread width (capped)" for sell_put may mislead (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 1 (KI-059 deferred) |
| Medium | 6 (KI-067, KI-064, KI-044, KI-075, KI-076, KI-082) |
| Low | 9 (KI-038, KI-034, KI-013/050, KI-049, KI-072, KI-073, KI-074, KI-077, KI-081) |
| **Total** | **16** |
| **Resolved Day 28** | **3** (KI-079, KI-080, KI-FOMC-GATE) |
| **Added Day 28** | **1** (KI-082 credit-to-width ratio) |
