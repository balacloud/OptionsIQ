# OptionsIQ — Project Status Day 38
> **Version:** v0.27.1
> **Date:** May 5, 2026
> **Tests:** 36

---

## What Shipped (Day 38)

### DataFlowDiagram in Data Provenance tab
- **What:** SVG architecture diagram embedded directly in the Data Provenance tab — always visible without running health check.
- **Two sections:** Live Analysis Flow (Analyze ETF trigger → IBKR/Alpaca/yfinance/STA → DataService → MD.app supplement → iv_store.db → gate_engine → MasterVerdict) + Batch/Nightly Flow (APScheduler → BOD/EOD → chain_cache.db/iv_store.db → run_startup_catchup).
- **File:** `frontend/src/components/DataProvenance.jsx` — `DataFlowDiagram()` function + `<DataFlowDiagram />` wired after error block.
- **Verification:** Component renders on tab open, no health check required.

### DATA_PROVIDERS_SYNTHESIS.md corrections
- MD.app tier corrected: "Starter $12/mo — ACTIVE" → "FREE tier (100 credits/day, ~33 used)"
- Total monthly cost corrected: "$12/mo" → "$0"
- Tradier section updated: added confirmed support quote ("The subscription level does not impact your API level")
- Added explicit upgrade trigger condition for MD.app Starter.

### MEMORY.md corrections
- MD.app free tier confirmed + Tradier pending integration note added.

---

## Open Issues

| ID | Severity | Description |
|----|---------|-------------|
| KI-086 | MEDIUM | app.py 497 lines — `_run_one` still inline (Rule 4 violation) |
| KI-067 | MEDIUM | QQQ sell_put returns ITM strikes (chain too narrow) |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift from gate_engine.py |
| KI-059 | HIGH (deferred) | Single-stock bear untested (ETF-only mode, stocks return 400) |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested all 4 directions |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | sell_put "capped" label may mislead |

---

## Next Session Priorities (Day 39)

| Priority | Item | Effort |
|----------|------|--------|
| P0 | Tradier integration — account open → live test → `tradier_provider.py` | 2 hrs |
| P1 | KI-086: Move `_run_one` to `best_setups_service.py` (app.py 497→~420) | 45 min |
| P2 | KI-067: QQQ sell_put ITM strike fix | 30 min |
| P3 | Live verify startup catch-up in backend.log | 15 min |
| P4 | FOMC dates audit (2026 calendar complete?) | 15 min |
