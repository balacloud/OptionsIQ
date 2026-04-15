# OptionsIQ — Known Issues Day 23
> **Last Updated:** Day 23 (April 15, 2026)
> **Previous:** KNOWN_ISSUES_DAY22.md

---

## Resolved This Session (Day 23)

### KI-069: CAUTION verdict suppressing all ETF GO signals (HIGH → RESOLVED)
OI=0 platform limitation was always firing `liquidity` warn → verdict amber.
Fixed via ETF post-process in `app.py`: parses `computed_value` to check spread% and
premium; if OI is the only issue AND bid-ask spread < 10% (SPREAD_FAIL_PCT), demotes to
`status="pass"` with note "OI unavailable (IBKR platform limitation — confirmed Day 12)."
First confirmed GO signals: XLF bear_call_spread ($48/$152), XLV bear_call_spread ($41/$59).

### KI-068: strategy.type=None for ETF sell_call (MEDIUM → RESOLVED — was false alarm)
`strategy_type` field IS set correctly in `_rank_sell_call` (returns "bear_call_spread").
The real bug: when frontend passed `suggested_direction: "bear_call_spread"` from scanner to
backend, it bypassed direction normalization and fell through to wrong strategy builder.
Fixed: added `DIRECTION_TO_CHAIN_DIR.get(_raw_dir, _raw_dir)` normalization at
`_analyze_options_inner` entry in `app.py`.

### sell_put naked put always failing max_loss gate for ETFs (HIGH → RESOLVED)
`sell_put` direction built naked puts only → `max_loss = (strike - premium) × 100 ≈ $13k`
for XLI ($138) → always blocked.
Fixed: `_rank_sell_put_spread()` added to `strategy_ranker.py` for ETF sell_put mode.
Short put Δ0.30, long put Δ0.15 → max_loss = spread width × 100 ≈ $400–500.
ETF sell_put max_loss post-process added in `app.py`: re-evaluates gate using
`top_strat.max_loss_per_lot` (actual spread max loss) not naked put formula.

### ETF DTE seller gate always amber (MEDIUM → RESOLVED)
Seller DTE gate was calibrated for stocks (14-21 DTE pass). ETF sweet spot is 21-45 DTE.
Fixed: added ETF DTE seller post-process in `app.py` — promotes `dte_seller` warn→pass
when DTE is in [21, 45] (ETF_DTE_SELLER_PASS_MIN/MAX constants added to constants.py).

### PnLTable always starts collapsed (UX → RESOLVED)
`PnLTable.jsx` had `useState(false)` — table always hidden on first analysis.
Fixed: `useState(() => !!(table?.scenarios?.length))` — auto-opens when data available.

### MasterVerdict non-blocking fails invisible (UX → RESOLVED)
Gate inline detail only showed `blocking !== false` fails. `market_regime_seller`
has `blocking=false` — appeared as red dot with no explanation. Fixed: show ALL `fail`
gates inline (blocking and non-blocking).

---

## Still Open

### KI-071: ExecutionCard not wired into App.jsx (NEW — HIGH, Day 23)
`ExecutionCard.jsx` component created + `POST /api/orders/stage` endpoint built.
But ExecutionCard is NOT yet imported/rendered in `App.jsx` AnalysisPanel function.
CSS styles for `.execution-card`, `.execution-legs`, `.exec-leg-*`, `.exec-stage-btn` etc.
also NOT yet added to `index.css`.
**Fix needed:** Wire `<ExecutionCard>` after `<TopThreeCards>` in AnalysisPanel, add CSS.
**Note:** `ibkr_provider.py` already changed from `readonly=True` → `readonly=False`.
Stage order endpoint not yet live-tested.

### KI-070: stage_spread_order not yet live tested (NEW — MEDIUM, Day 23)
`IBKRProvider.stage_spread_order()` implemented but not yet tested against live IB Gateway.
ComboLeg import path (`ib_insync.objects.ComboLeg`) and `LimitOrder` import need
verification at market open. `transmit=False` safety must be confirmed in TWS.
**Fix needed:** Live test at market open — stage XLF 53/55 Bear Call, verify order
appears in TWS blotter with transmit=False, does NOT submit to market.

### KI-059: buy_put + sell_call on individual stocks not live tested (HIGH)
Lower priority — ETF-only mode means stocks return 400. Deferred.

### KI-067: QQQ chain fractional strikes (MEDIUM)
sell_put direction for QQQ returns ITM put strikes (~$637 vs $624 underlying).
Chain struct_cache issue. Lower priority.

### KI-064: IVR mismatch between L2 and L3 (MEDIUM)
~5pp gap between L2 percentile and L3 average. Data-specific, low impact.

### KI-044: API_CONTRACTS.md stale (MEDIUM)
ETF-only enforcement, Signal Board, `_etf_payload` fields, `POST /api/orders/stage` not documented.

### KI-001/KI-023: app.py still ~750+ lines (MEDIUM)

### KI-038: Alpaca OI/volume fields missing (LOW)

### KI-034: OHLCV temporal gap not validated (LOW)

### KI-008: fomc_days_away defaults to 999 (LOW)

### KI-013/KI-050: API URL hardcoded in JS files (LOW)

### KI-049: account_size hardcoded in PaperTradeBanner.jsx (LOW)

---

## Summary

| Severity | Remaining |
|----------|-----------|
| Critical | 0 |
| High | 2 (KI-071 ExecutionCard wiring, KI-059 deferred) |
| Medium | 5 (KI-070, KI-067, KI-064, KI-044, KI-001) |
| Low | 5 |
| **Total** | **12** |
| **Resolved Day 23** | **6** (KI-069 verdict, KI-068 direction, sell_put spread, DTE seller, PnL auto-open, verdict all-fails) |
