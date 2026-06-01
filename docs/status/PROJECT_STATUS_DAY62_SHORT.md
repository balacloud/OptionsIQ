# Project Status — Day 62 (Jun 1, 2026)
> Version: v0.35.4

## What Happened

### Day 62 — Gate Recalibration + Dead Code Removal

**Theme:** The tool was over-gating. `/ibkr-scan` already validates IVR, IV/HV, trend, and direction — the backend was re-blocking on the same conditions, creating a broken experience where the tool vetoed trades the user had already decided to make.

### Gate Recalibration (gate_engine.py)

5 gates changed from hard-block to non-blocking warn:

| Gate | Was | Now | Reason |
|------|-----|-----|--------|
| `ivr` (buyer IVR rank) | BLOCK | WARN | `/ibkr-scan` already validated IV environment |
| `hv_iv` (HV/IV for buyers) | BLOCK | WARN | `/ibkr-scan` already checked IV_HV column |
| `market_regime` (SPY, buy_call) | BLOCK | WARN | `/ibkr-scan` already confirmed direction |
| `market_regime` (SPY, buy_put) | BLOCK | WARN | `/ibkr-scan` already confirmed direction |
| `max_loss` (position vs account) | BLOCK | WARN | Single lot only — advisory message |
| `hv_iv_vrp` (VRP, non-GLD) | BLOCK | WARN | `/ibkr-scan` IV_HV covers this; GLD block kept |

**Hard blocks that remain:**
- `trend_ema`: price below 200 EMA for sellers/call buyers (downtrend = structural risk)
- `hv_iv_vrp` for GLD only: IV/HV < 1.10 (too subtle for watchlist glance)
- FOMC: XLF/XLRE/TQQQ within 14 days

**Verified:** XLF buy_put test — 0 hard blocks, 4 advisory warnings. QQQ sell_put — 0 hard blocks.

### Dead Code Removed (App.jsx)

- `ETF Signal Scanner` component deleted — was calling `/api/sectors/scan` → 410 error on every click
- `useSectorData` hook import and all usage removed
- `ScannerRow` + `L2InlineDetail` inline components deleted (~100 lines)
- `signals` tab now shows `AnalysisPanel` full-width (no left panel)
- Empty state: "Select an ETF from Today's Trade"

### Scan Context Integration Confirmed Working

Live API test with Day 61 QQQ data:
- `IVR=36` correctly overrides DB value (84.52%) in IVR gate ✅
- `PC=0.94` flows into P/C sentiment gate ✅
- `IV_HV=1.214` flows into VRP gate ✅
- Trend gate passes silently (no PEMA data — correct for closed market) ✅

### Workflow Documented

Full 3-skill workflow clarified:
1. `/ibkr-scan` → SCAN CONTEXT → **paste into OptionsIQ** → get 3 strikes + exit plan
2. `/chartreview` → read + mental confirm (is strike above chart support?)
3. `/catalyst-check` → read + adjust (which of the 3 strikes to pick)

### Chart Context Feature Planned

Future: `/chartreview` outputs a CHART CONTEXT block (S1/S2/R1/R2) that pastes into the tool, which then shows "R1 strike $703 sits between S1=$710 and S2=$695 — above support ✅" per strategy. Not built yet.

### New Golden Rule Added

**Rule 23: Pre-Filter Tools Own Their Checks — Don't Double-Gate.**
If `/ibkr-scan` already validated a condition, the backend must not hard-block on it. Warn only.

## Test Count
**52 tests** — no change (gate logic changes are behavioral, not structural).

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear untested — DEFERRED (ETF-only) |
| KI-099 | LOW | buy_call direction for Leading/Improving ETFs — deferred |
| KI-110 | LOW | _rank_buy_call returns "itm_call"/"atm_call"/"otm_call" instead of "buy_call" |

## Next Session Priorities (Day 63)

### P0 — Monday live integration test (requires market hours)
Refresh IBKR watchlist → get live P/EMA200 + P/EMA50 → build full SCAN CONTEXT with all 7 fields → verify trend gate fires correctly.

### P1 — Chart Context feature
1. Update `/chartreview` skill to emit CHART CONTEXT block (S1/S2/R1/R2/TREND/RSI/ATR)
2. `chart_context_parser.py` (new, ~50 lines)
3. `analyze_service.py` — compute `strike_vs_support` label per strategy
4. `App.jsx` — second textarea for CHART CONTEXT paste
5. `TopThreeCards.jsx` — display label

### P2 — KI-110 fix (~8 lines)
`_rank_buy_call` → return `"buy_call"` not `"itm_call"`. Update pnl_calculator handlers.

### P3 — Frontend redesign
Full redesign discussion deferred. Key direction: one trade per screen, gates collapsed by default (warnings only), clean light aesthetic. Needs dedicated planning session.
