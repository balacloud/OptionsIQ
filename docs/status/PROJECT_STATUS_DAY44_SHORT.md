# Project Status — Day 44 (May 6, 2026)
> **Version:** v0.30.0
> **Tests:** 36 (unchanged)

---

## What Shipped

### KI-076: TradeExplainer isBearish() — all 4 directions live-verified
**Status:** No bug found. Logic was already correct.
**Method:** Called live API (`POST /api/options/analyze`) for all 4 directions on XLF (underlying $51.59). Captured `strategy_type` from `top_strategies[0]`, traced through `isBearish()` and `isPut()` in TradeExplainer.jsx.

| Direction | strategy_type | isBearish | isPut | Profit Zone | Moneyness |
|-----------|--------------|-----------|-------|-------------|-----------|
| buy_call | itm_call | ✗ | ✗ | RIGHT (Profit →) | OTM\|ATM\|ITM |
| sell_call | bear_call_spread | ✓ | ✗ | LEFT (← Profit) | OTM\|ATM\|ITM |
| buy_put | itm_put | ✓ | ✓ | LEFT (← Profit) | ITM\|ATM\|OTM |
| sell_put | bull_put_spread | ✗ | ✓ | RIGHT (Profit →) | ITM\|ATM\|OTM |

**Verification:** Zone label text, profit zone positioning, and moneyness order all semantically correct. ✅

### Category 7: Tradier live tests — buy_call, sell_call, buy_put confirmed
**Context:** Only sell_put had been end-to-end tested with Tradier primary (Day 40).
**Results on XLF:**
- All 4 return `data_source: tradier`, `quality: live` ✓
- Deltas on target: buy_call 0.67 (≈0.68), buy_put -0.678 (≈-0.68) ✓
- Seller OTM selection working: sell_call delta 0.193, sell_put delta -0.185 ✓
- P&L table populated for all 4 (scenarios + footer with breakevens, max losses, theta burns) ✓
- Gate routing correct: buyers get ivr/hv_iv/theta_burn tracks; sellers get ivr_seller/hv_iv_vrp/vix_regime tracks ✓
- CPI event (7 days) correctly detected and warns across all 4 ✓
- Credit-to-width warning fires correctly (sell_call 27% < 33%, sell_put 18% < 33%) ✓

**Note:** Gate parsing bug in test scripts (checked `g.get('passed')` instead of `g.get('status')`) — gates were always appearing to fail. Not a product bug; test script issue only.

### Data requirements audit (earlier in session)
- BOD batch: zero IBKR dependency confirmed — `run_bod_batch()` → Tradier cascade only ✓
- EOD batch: hard IBKR dependency confirmed — `seed_iv_for_ticker()` → `reqHistoricalData OPTION_IMPLIED_VOLATILITY` (no alternative source; HV≠IV)
- IBKR only required ~4:05 PM ET window for EOD IV seeding

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (DEFERRED) | Single-stock bear tracks untested — ETF-only mode (400) |
| KI-086 | LOW (partial) | app.py `_run_one` closure still inline, ~449 lines, Rule 4 violation |

---

## Next Session Priorities (Day 45)

| Priority | Issue | Effort |
|----------|-------|--------|
| P0 | KI-086 partial: app.py `_run_one` extraction to best_setups_service.py | 45 min |
| P1 | Phase 7c: Weakening → sell_call for cyclical sectors (research first) | 60 min |
| P2 | MASTER_AUDIT_FRAMEWORK weekly sweep (skip until Day 49+ — last audit Day 42) | 90 min |
| P3 | (backlog) | — |
