# OptionsIQ — Project Status Day 36
> **Date:** May 4, 2026
> **Version:** v0.26.1
> **Tests:** 36 (unchanged)

---

## What Shipped Day 36

### 1. MarketData.app Greeks Surfaced Through Pipeline
**Root cause addressed:** `get_oi_volume()` was discarding IV, delta, gamma, theta, vega fields from
the MD.app API response — only OI/volume were passed back.
**Fix (`marketdata_provider.py`, 90→114 lines):** Parse IV, delta, gamma, theta, vega using a `_first()`
helper that safely extracts the first list element. Log IV + delta alongside OI/volume.

### 2. IV Patching from MD.app When Chain IV is Null
**Root cause addressed:** When Alpaca is the fallback chain provider, it returns greeks but no IV
(model limitation). IVR gate operates on `ivr_data.current_iv` — when that's null, IVR percentile
can't be computed and the gate fires with no data.
**Fix (`analyze_service.py`, 811→835 lines):** After `get_oi_volume()`, if `_md_oi_volume["iv"]`
is present AND `ivr_data["current_iv"]` is absent, patch the ivr_data dict:
- `current_iv` = MD.app IV × 100 (decimal → pct)
- `ivr_pct` = recomputed via `iv_store.compute_ivr_pct()`
- `hv_iv_ratio` = recomputed from patched IV
- `iv_source` = `"marketdata"` (distinguishes from IBKR/Alpaca sources)

### 3. `md_supplement` Field in Analyze Response
**What:** Added `md_supplement` dict to the top-level analyze response containing all greeks
fetched from MD.app (iv, delta, gamma, theta, vega, open_interest, volume, credits_remaining).
**Why:** Enables frontend debugging and future display of MD.app-sourced data alongside chain data.

---

## Open Issues Table

| ID | Severity | Description |
|----|----------|-------------|
| KI-086 | MEDIUM | app.py 492 lines (Rule 4 max 150) — _run_one still inline |
| KI-067 | MEDIUM | QQQ sell_put picks ITM strikes (chain too narrow for ~$658) |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift from gate_engine |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested all 4 directions |
| KI-059 | HIGH-DEFERRED | Single-stock bear untested (ETF-only pivot makes this low priority) |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |

---

## Next Session Priorities

| Priority | Item | Effort |
|----------|------|--------|
| P0 | Verify EOD auto-batch fired at 4:05 PM — check Data Provenance batch log | 5 min |
| P1 | Live market test — run Best Setups, verify batch-warmed chain cache hits | 20 min |
| P2 | Verify MD.app IV patching fires in practice — check backend.log for `iv_source: marketdata` | 10 min |
| P3 | KI-086 — move _run_one to best_setups_service.py (app.py 492→~420) | 45 min |
| P4 | KI-067 — QQQ sell_put ITM strike fix | 30 min |
