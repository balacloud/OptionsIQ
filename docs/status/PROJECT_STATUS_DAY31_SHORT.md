# OptionsIQ — Project Status Day 31
> **Date:** April 29, 2026
> **Version:** v0.23.0
> **Previous:** PROJECT_STATUS_DAY30_SHORT.md

---

## What Shipped Today

### KI-084/087 RESOLVED — XLRE/SCHB OHLCV seeded
`_seed_iv_for_ticker()` in `app.py` enhanced to also call `get_ohlcv_daily()` (IBKR primary, yfinance fallback, 90 days). XLRE and SCHB seeded. HV-20 and McMillan stress check now have valid data for these tickers.

### KI-085 RESOLVED — VIX badge in RegimeBar
`_fetch_vix()` called in `/api/sectors/scan` to keep VIX cache warm. `get_vix_status()` result wired into `sectorData.vix`. `RegimeBar.jsx` shows a color-coded "VIX: XX.X" badge: green (15-30), orange (>30), red (>40), grey (<15 or unavailable).

### LearnTab — Perplexity-style 5-panel redesign
Complete rewrite of `LearnTab.jsx` from 4-lesson generic format to a Perplexity-inspired 5-panel trade education panel:
- **Panel 1 — Risk/Reward**: proportional colored bar + leg rows (sell/buy, credit/debit, width)
- **Panel 2 — Strike Zones**: full SVG number line with staggered markers (current price + long strike above axis; short strike below; breakeven as dashed line further below — no label overlap)
- **Panel 3 — Breakeven**: formula card + SVG payoff diagram
- **Panel 4 — Timing/DTE**: DTE track bar with optimal zone highlight + event list
- **Panel 5 — Safety Gates**: score bar + expandable gate Q&A rows (GATE_KB inline)

Context-aware: when ETF is selected and analyzed, uses `data.underlying_price`, `data.top_strategies[0].strike/premium/spread_width/expiry_display`. Falls back to XLF bear call spread defaults ($52.16, short $54, long $55, credit $0.21).

### Paper Trade Workflow Rebuild
- `PaperTradeBanner.jsx`: strategy picker, trade details preview, confirmation button
- `PaperTradeDashboard.jsx`: per-trade mark/close/delete actions
- `PATCH /api/options/paper-trade/<id>`: update mark-to-market price
- `DELETE /api/options/paper-trade/<id>`: remove a trade
- `dashRefreshTick` counter pattern: useEffect dependency triggers reload without double-fire
- Auto-tab-switch to Dashboard after logging a trade

### Best Setups as Home Screen
- Default tab changed from `'sectors'` to `'setups'`
- `BestSetups.jsx` auto-scans on mount (useEffect with empty deps)
- SetupCards are clickable: `onSelect` → `handleSelectFromSetups(ticker, direction)` → runs analysis → switches to Signal Board tab

---

## Current Test Count
33 tests (pytest, 5 files) — unchanged from Day 30.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-086 | MEDIUM | app.py ~470 lines — Rule 4 max 150. Move `_seed_iv_for_ticker` + `_run_one` to service modules |
| KI-067 | MEDIUM | QQQ sell_put returns ITM strikes — chain too narrow for current price |
| KI-064 | MEDIUM | IVR mismatch L2 vs L3 (~5pp gap) |
| KI-075 | MEDIUM | GateExplainer GATE_KB may drift from LearnTab GATE_KB (two copies) |
| KI-076 | LOW | TradeExplainer isBearish() not live-tested (sell_call + buy_put zone colors unverified) |
| KI-059 | HIGH (deferred) | Single-stock bear untested — ETF-only mode returns 400 |
| KI-081 | LOW | No CPI/NFP/PCE macro events calendar |
| KI-077 | LOW | DirectionGuide sell_put "capped" label may mislead |

---

## Next Session Priorities (Day 32)

1. **P1 (MEDIUM):** KI-086 — app.py size cleanup. Move `_seed_iv_for_ticker` + `_run_one` closure to service modules.
2. **P2 (LOW):** Skew computation — `put_iv_30delta - call_iv_30delta` from existing chain data. No new source.
3. **P3 (MEDIUM):** KI-067 — QQQ sell_put ITM strike fix.
