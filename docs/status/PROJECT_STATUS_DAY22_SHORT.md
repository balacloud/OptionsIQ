# Project Status — Day 22 (April 14, 2026)
> **Version:** v0.15.1
> **Session Type:** Live market smoke test + ETF signal fixes + UI gate visibility

## What Happened

### Live Market Smoke Test (IB Gateway connected)
- Backend confirmed running on port 5051, frontend on 3050
- IB Gateway connected (live account U11574928)
- Sector scan live: 15 ETFs returned, SPY regime correct
- IVR tiered directions confirmed: XLI/XLK/QQQ/MDY → sell_put (IVR>50%), IWM → buy_call (IVR<30%)
- XLF/XLV sell_call (bear_call_spread) → CAUTION with 3 strategies + P&L table ✅

### 5 Bug Fixes (app.py + sector_scan_service.py)
1. **market_regime_seller blocking ETF sell_call** — Lagging sector bear plays in bull market
   were BLOCKED. Fixed via ETF post-process: `blocking=False` with regime override reason.
2. **Liquidity non-blocking fail showing red** — ETF post-process condition was blocking-only.
   Fixed: condition checks `status=="fail"` regardless of blocking flag.
3. **spy_above_200sma None→False** — `bool(dict.get("key", True))` with existing `None` value
   returns `False`, not the default `True`. Fixed: explicit `if _spy_above_raw is not None` guard.
4. **MasterVerdict gate details invisible** — user saw colored dots with no labels.
   Fixed: blocking fails + warns now rendered inline with name/value/reason in verdict card.
5. **IVR not wired into scan_sectors()** — `quadrant_to_direction()` was IVR-aware but called
   without `ivr=`. Fixed: `scan_sectors(iv_store=iv_store)`, `_get_ivr()` helper per ETF.

### GatesGrid auto-open
`GatesGrid.jsx` now defaults open when any fail or warn present.

## Current Signal State (live, market open)
| ETF | Quadrant | Direction | Verdict |
|-----|----------|-----------|---------|
| XLF | Lagging | sell_call/bear_call_spread | CAUTION (non-blocking only) |
| XLV | Lagging | sell_call/bear_call_spread | CAUTION (non-blocking only) |
| XLY | Lagging | sell_call/bear_call_spread | CAUTION |
| XLI/XLK | Leading | sell_put | BLOCKED (max_loss — naked put too large) |
| IWM | Leading | buy_call | BLOCKED (IVR=100% — IV crush) |
| All others | Weakening | None (WAIT) | — |

**Key insight:** System correctly blocks buy_call at IVR=100% and sell_put naked max_loss.
Best current plays are XLF/XLV/XLY bear_call_spread (CAUTION). GO never reached because:
(a) liquidity OI=0 always warns (platform limitation), (b) verdict requires zero warns for GO.

## New Known Issues
- **KI-068:** strategy.type=None for ETF sell_call (display bug)
- **KI-069:** CAUTION verdict suppresses GO for all-non-blocking sets (OI=0 platform limit inflating warn count)

## Open Strategic Question
User asked: "at any point in time, at least one ETF should be eligible for a positive options call —
is the system too strict?" Diagnosis: system logic is correct but two structural issues prevent GO:
1. OI=0 platform limitation always creates a warn → verdict always CAUTION at best
2. sell_put needs bull_put_spread (defined risk) the way sell_call has bear_call_spread

## Next Session Priorities
1. **P0:** Fix KI-069 — audit verdict logic: ETF OI=0 warn should be `info` not `warn` for verdict
2. **P0:** Fix KI-068 — strategy.type=None in ETF sell_call path
3. **P1:** Implement bull_put_spread for sell_put (parallel to bear_call_spread for sell_call)
4. **P2:** After fixes: re-run XLF/XLV/IWM — confirm at least one GO signal
5. **P3:** KI-044 API_CONTRACTS.md sync
