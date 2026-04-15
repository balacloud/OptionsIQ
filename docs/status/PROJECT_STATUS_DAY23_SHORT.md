# OptionsIQ — Day 23 Status
> **Date:** April 15, 2026
> **Version:** v0.16.0
> **Session type:** Fix session + new feature

---

## What Happened

### P0: First GO Signals Achieved
Three structural issues were blocking every ETF from ever showing GO (green):
1. OI=0 platform limitation always fired liquidity warn → CAUTION
2. sell_put built naked puts → max_loss gate always blocked (~$13k)
3. bear_call_spread direction from scanner didn't route to sell_call chain

All three fixed. First confirmed GO signals:
- **XLF bear_call_spread → GO ✓** ($48 max profit / $152 max loss, May 2026)
- **XLV bear_call_spread → GO ✓** ($41 max profit / $59 max loss)

### P1: bull_put_spread for sell_put
Added `_rank_sell_put_spread()` to `strategy_ranker.py` (mirrors `_rank_sell_call`).
ETF sell_put now builds defined-risk spreads (Δ0.30 short / Δ0.15 protection).
Max loss ~$400-500 vs naked put ~$13k+ — gate now passes.

### P2: UI Fixes
- P&L table auto-opens when data available (was always collapsed)
- MasterVerdict inline detail now shows ALL fail gates (blocking + non-blocking)

### P3: ExecutionCard (in progress — NOT wired into UI yet)
New `ExecutionCard.jsx` built: shows legs (SELL 53C + BUY 55C), net credit, max profit/loss.
"Stage in TWS" button → `POST /api/orders/stage` → ib_insync `placeOrder(transmit=False)`.
Order appears in TWS order blotter for user to review and click Transmit.
`ibkr_provider.py` changed `readonly=True → False`.
**Blocked:** Not yet wired into App.jsx, CSS not added, not live-tested.

---

## Files Changed Day 23

| File | Change |
|------|--------|
| `backend/app.py` | Direction normalization, ETF sell_put max_loss post-process, ETF DTE seller post-process, OI=0 liquidity pass logic, `POST /api/orders/stage` endpoint |
| `backend/strategy_ranker.py` | `_rank_sell_put_spread()` added, ETF routing in `rank()` |
| `backend/ibkr_provider.py` | `readonly=False`, `stage_spread_order()` method added |
| `backend/constants.py` | `ETF_DTE_SELLER_PASS_MIN=21`, `ETF_DTE_SELLER_PASS_MAX=45` |
| `frontend/src/components/PnLTable.jsx` | `useState(false)` → auto-open |
| `frontend/src/components/MasterVerdict.jsx` | All fail gates shown inline |
| `frontend/src/components/ExecutionCard.jsx` | **NEW** — not yet wired into App.jsx |

---

## Next Session Priorities (Day 24)

1. **P0:** Wire ExecutionCard into App.jsx AnalysisPanel + add CSS to index.css (KI-071)
2. **P0:** Live test `stage_spread_order()` at market open — verify XLF order in TWS blotter with transmit=False (KI-070)
3. **P1:** QQQ sell_put chain returns ITM puts — fix struct_cache or widen strike window (KI-067)
4. **P2:** API_CONTRACTS.md sync — add `POST /api/orders/stage` + ETF-only fields (KI-044)
5. **P3:** Smoke test: XLI bull_put_spread → should GO after spread fixes
