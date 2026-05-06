# Project Status — Day 43 (May 6, 2026)
> **Version:** v0.30.0
> **Tests:** 36 (unchanged)

---

## What Shipped

### KI-064: IVR mismatch L2 vs L3 — ATM contract IV fix
**File:** `backend/analyze_service.py` → `_extract_iv_data()`
**Root cause:** L3 was averaging all direction-filtered contracts. Sell_put fetches only puts, whose OTM skew inflated the average 5-8pp above ATM IV. IBKR's historical baseline is ATM-weighted.
**Fix:** Selects ATM contract (nearest strike to underlying) for `current_iv`. Fallback to average if ATM IV is null.
**Verified:** Same-direction gap XLF sell_call ~2pp (timing noise). ✅

### KI-075: GateExplainer GATE_KB drift — 3 sub-fixes
**Files:** `frontend/src/components/GateExplainer.jsx`, `backend/gate_engine.py`, `backend/constants.py`
1. Added `hv_iv_vrp` GATE_KB entry (was showing raw gate ID)
2. Added `vix_regime` GATE_KB entry (was showing raw gate ID)
3. Fixed `_run_etf_sell_put` DTE gate: now imports and uses `ETF_DTE_SELLER_PASS_MIN=21` / `ETF_DTE_SELLER_PASS_MAX=45` instead of single-stock VCP constants (14–21 was wrong for ETF sellers)
**Verified:** gate_engine.py + GateExplainer.jsx both clean. ✅

### KI-077: DirectionGuide sell_put "capped" label
**File:** `frontend/src/components/DirectionGuide.jsx`
Updated risk text from misleading "capped with spread" to honest: "Large (up to full strike value if naked). Bull put spread caps this — check strategy type."

### KI-081: Macro events calendar gate (CPI/NFP/PCE)
**Files:** `backend/constants.py`, `backend/analyze_service.py`, `backend/gate_engine.py`, `frontend/src/components/GateExplainer.jsx`
- `MACRO_DATES` dict added to constants.py (CPI, NFP, PCE 2026-2027 approximate dates)
- `_days_until_next_macro()` helper → `(days, event_name)` tuple
- `_fomc_days`, `_macro_days`, `_macro_name` computed once before gate_payload (also fixed pre-existing bug: fomc_days_away was always 999 in gate_payload due to explicit override of swing_data value)
- `_etf_fomc_gate()` extended: picks nearest event (FOMC or macro), shows combined computed_value
- `_run_sell_call` gate 4 updated inline to check macro events
- GateExplainer `events` GATE_KB updated to mention CPI/NFP/PCE
**Verified:** XLF sell_put live → `events: warn · "CPI in 7d falls inside holding window (23 DTE)"` ✅

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (DEFERRED) | Single-stock bear tracks untested — ETF-only mode (400) |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested (all 4 directions) |

---

## Next Session Priorities (Day 44)

| Priority | Issue | Effort |
|----------|-------|--------|
| P0 | KI-076: Live test all 4 directions for TradeExplainer zone colors | 30 min |
| P1 | Category 7: Tradier live tests buy_call, sell_call, buy_put (only sell_put tested Day 40) | 45 min |
| P2 | app.py size (KI-086 partial): `_run_one` closure still inline, app.py still >400 lines | 45 min |
| P3 | Phase 7c: Weakening → sell_call for cyclical sectors (research first) | 60 min |
| P4 | MASTER_AUDIT_FRAMEWORK weekly sweep (if Day 43 is 7+ days since last full audit) | 90 min |
