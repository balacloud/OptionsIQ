# OptionsIQ — Project Status Day 40 (Short)
> **v0.28.1** — May 5, 2026 | Tests: 36 | Next: Day 41

---

## What Shipped

### 1. KI-090 resolved — Tradier delta coercion fix
`tradier_provider.py` lines 195-198: replaced `_f(g.get("delta")) or None` with `float(g[key]) if g.get(key) is not None else None` for delta, gamma, theta, vega.
Root cause: `0.0 or None` evaluates to `None` in Python — deep-OTM contracts (valid delta=0.0) were being treated as missing.
Downstream bug: strategy_ranker `_closest_delta()` treated None as abs(0.0)=0, making every deep-OTM contract appear to match delta=0.30 target.
Verified: QQQ chain — `delta=None: 0/24`, sample values: -0.45, -0.38, -0.31, -0.26...

### 2. KI-091 resolved — Tradier direction-aware strike window
`tradier_provider.get_options_chain()`: added direction-aware OTM filter in the per-expiry contract loop.
`sell_put`: `if strike > underlying: continue` (exclude ITM puts)
`sell_call`: `if strike < underlying: continue` (exclude ITM calls)
Root cause: symmetric ±10% window had no direction awareness — KI-067 fix in ibkr_provider did not apply to Tradier path.
Verified: QQQ sell_put smoke test — 0 ITM puts, short_strike=680.0 < underlying=683.98.

### 3. KI-092 resolved — "ibkr_cache" → "bod_cache" rename
`data_service.py`: renamed `"ibkr_cache"` → `"bod_cache"` in docstring, `_cache_get()` return value, and `quality_label()` check.
`data_health_service.py`: `chain_src = "ibkr_cache"` → `"bod_cache"`.
Root cause: BOD batch now fills cache via Tradier (not IBKR), but label still said "ibkr_cache" — DataProvenance UI was lying.

### 4. KI-093 resolved — iv_provider selection for data_source="tradier"
`analyze_service.py` line 680: updated iv_provider selection.
Before: `"tradier"` fell through to `mock_provider`.
After: `data_source in {"yfinance", "tradier", "alpaca"} → yf_provider`. Also updated `"ibkr_cache"` → `"bod_cache"` in the IBKR set.

### 5. P1 End-to-end smoke test — PASSED
- IB Gateway OFF (`ibkr_connected: false`)
- Best Setups scan: 5/5 setups with `data_source=tradier`, 0 errors
- QQQ sell_put: 24 OTM puts, 0 ITM, all deltas non-null (real values from Tradier greeks)
- QQQ chain direct: `underlying=683.98`, all strikes OTM, data_source=tradier

---

## Tests
36 passing. No new tests added (Tradier bug fixes are chain-level — integration tested manually).

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (deferred) | Single-stock bear untested |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB drift risk |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |

---

## Day 41 Priorities

| # | Priority | Task | Effort |
|---|----------|------|--------|
| P0 | NICE | Update DataFlowDiagram SVG in DataProvenance.jsx — IBKR demoted to EOD-only, Tradier as primary | 20 min |
| P1 | NICE | FOMC 2026 dates audit in constants.py (verify Jun 18, Jul 30, Sep 17, Nov 4, Dec 10) | 15 min |
| P2 | NICE | Tradier startup health ping — verify TRADIER_KEY on startup, log result | 15 min |
| P3 | NICE | Skew computation from Tradier chain (put_iv_30delta - call_iv_30delta) | 45 min |
| P4 | MEDIUM | KI-064 investigation — IVR mismatch L2 vs L3 root cause | 30 min |
