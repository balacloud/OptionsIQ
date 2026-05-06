# OptionsIQ — Project Status Day 41 (Short)
> **v0.28.2** — May 6, 2026 | Tests: 36 | Next: Day 42

---

## What Shipped

### 1. DataFlowDiagram SVG updated — Tradier as primary (P0)
`frontend/src/components/DataProvenance.jsx` — 7 surgical changes to the SVG:
- IBKR box (blue) → **Tradier** (dark green, "PRIMARY LIVE") in the Live Analysis provider row
- DataService Cascade now shows cascade order: `BOD Cache · Tradier · Alpaca · yfinance`
- yfinance subtext: "OHLCV only" → "emergency"
- BOD batch action: "Pre-warm 16 ETF chains" → "Pre-warm chains (Tradier)"
- EOD batch action: "Seed IV history + OHLCV" → "Seed IV + OHLCV (IBKR)" — makes clear IBKR is EOD-only
- Legend: "Data Source" (blue) → "Primary Src" (green, matches Tradier box)
- Build verified: `npm run build` clean, zero warnings.

### 2. FOMC 2026 dates audit — verified correct (P1)
`constants.py` FOMC_DATES_2026 — all dates confirmed accurate:
- Jun 18 ✅, Jul 29 ✅, Sep 16 ✅, Nov 5 ✅, Dec 16 ✅
- Memory doc expectations (Jul 30, Sep 17, Nov 4, Dec 10) were rough estimates — constants.py already had corrections applied. No code changes needed.

### 3. Tradier startup health ping (P2)
`backend/app.py` — two changes:
1. After `TradierProvider` init, calls `get_underlying_price("QQQ")`. Stores result in `_tradier_ok: bool` and `_tradier_error: str|None`.
2. `/api/health` now returns `tradier_ok` and `tradier_error` fields.
Verified: `{"tradier_ok": true, "tradier_error": null}` on startup with valid key.
Log: `INFO:__main__:TradierProvider health check passed`
If TRADIER_KEY missing: `tradier_ok=false`, `tradier_error="TRADIER_KEY not configured"`.
If key wrong/network down: `tradier_ok=false`, `tradier_error="<exception message>"`.

---

## Tests
36 passing. No new tests (SVG + health ping are integration-level changes).

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

## Day 42 Priorities

| # | Priority | Task | Effort |
|---|----------|------|--------|
| P0 | NICE | Skew computation — put_iv_30delta - call_iv_30delta from Tradier chain | 45 min |
| P1 | MEDIUM | KI-064 investigation — IVR mismatch L2 vs L3 root cause | 30 min |
| P2 | LOW | KI-075 — GateExplainer GATE_KB audit (Category 9 sweep) | 30 min |
| P3 | LOW | KI-077 — DirectionGuide sell_put "capped" label fix | 15 min |
| P4 | LOW | KI-081 — CPI/NFP/PCE macro events calendar in constants.py | 30 min |
