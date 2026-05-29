# Project Status — Day 59 (May 29, 2026)
> **Version:** v0.35.2
> **Tests:** 37 (all pass)

---

## What Shipped

### KI-107: TQQQ Delta Guard (MEDIUM — resolved)
**Root cause:** strategy_ranker used identical delta targets (0.20/0.15/0.28) for all ETFs including TQQQ. gate_engine had no TQQQ-specific delta gate despite TQQQ_MAX_DELTA=0.10 existing in constants.py.
**Fix:** `strategy_ranker._rank_sell_put_etf` now branches on `is_tqqq` → uses delta 0.10/0.08/0.06. New `gate_engine._tqqq_satellite_gate()` wired into `_run_etf_sell_put` (Gate 9) and `_run_etf_sell_call` (Gate 12) — informational gate with VIX check + TQQQ constraint reminder.
**Verification:** 37 tests pass. TQQQ sell_put requests will now receive delta 0.10/0.08/0.06 strategies and see the satellite gate in the gate list.

### KI-108: GLD IV/HV Gate (MEDIUM — resolved)
**Root cause:** `_etf_hv_iv_seller_gate` used uniform IV/HV ≥ 1.05 threshold for all ETFs. GLD requires ≥ 1.10 (confirmed in Day 57 ETF universe research) but gate didn't enforce it — only ibkr-scan skill enforced it.
**Fix:** Added `is_gld = ticker == "GLD"` branch in `_etf_hv_iv_seller_gate`. GLD: hard block if IV/HV < 1.10. Others: unchanged (pass ≥ 1.05, warn 1.0–1.05, fail < 1.0).
**Verification:** 37 tests pass. GLD sell directions with thin IV/HV now receive a gate BLOCK from backend.

### KI-109: sell_call FOMC Tier Consistency (MEDIUM — resolved)
**Root cause:** `_run_etf_sell_call` Gate 6 had a 22-line manual events check using simple <5d/<10d thresholds — did NOT use `_etf_fomc_gate`. XLF/TQQQ sell_call got only a WARN near FOMC (not hard block), unlike sell_put which correctly used the 3-tier gate (BLOCK for Tier-1 tickers ≤14d).
**Fix:** Replaced Gate 6 in `_run_etf_sell_call` with single call: `self._etf_fomc_gate(p, dte, "sell_call")`. 22 lines → 1 line.
**Verification:** 37 tests pass. XLF/TQQQ sell_call now hard-blocked within 14 FOMC days. QQQ/IWM/GLD sell_call warns only (same tier logic as sell_put).

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear untested — deferred, ETF-only going forward |
| KI-099 | LOW | buy_call direction for Leading/Improving ETFs — deferred, single-leg only |
| KI-110 | LOW | _rank_buy_call returns stale type names (itm_call/atm_call/otm_call vs buy_call) |

---

## Next Session Priorities (Day 60)

| # | Priority | Description | Effort |
|---|----------|-------------|--------|
| P1 | KI-110 (LOW) | Fix buy_call/_rank_buy_call stale strategy_type names — rename itm_call/atm_call/otm_call to buy_call; update pnl_calculator + TopThreeCards defensive handlers | ~8 lines |
| P2 | End-to-end workflow test | ibkr-scan → analyze → verify TopThreeCards display (expected_move, strike_vs_em_label, exit_plan) → log paper trade | ~30 min |
| P3 | /chartreview skill | `.claude/commands/chartreview.md` — TradingView screenshot → chart GO/WAIT + key S/R levels | ~1 day |
| P4 | /catalyst-check skill | `.claude/commands/catalyst-check.md` — ticker + DTE → FOMC/macro events + holdings earnings + web search synthesis | ~1 day |
| P5 | Audit trigger | MASTER_AUDIT_FRAMEWORK v1.5 — last run Day 58, next scheduled Day 65 | Weekly |
