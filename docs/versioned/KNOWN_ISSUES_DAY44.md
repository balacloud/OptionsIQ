# OptionsIQ — Known Issues Day 44
> **Last Updated:** Day 44 (May 6, 2026)
> **Previous:** KNOWN_ISSUES_DAY43.md

---

## Resolved This Session (Day 44)

### KI-076: TradeExplainer isBearish() not live-tested (LOW) ✅ RESOLVED Day 44
**Root cause:** isBearish() and isPut() logic in TradeExplainer.jsx had never been verified against live API responses for all 4 directions. Risk: profit/loss zones showing on wrong side.
**Verification method:** Called `POST /api/options/analyze` for all 4 directions on XLF (underlying @ $51.59, Tradier primary). Captured strategy_type from top_strategies[0], traced through isBearish() and isPut() arrays, verified zone labels and moneyness row.
**Result:** All 4 directions correct — no code changes needed.
- buy_call → itm_call: not bearish, not put → profit zone right ("Profit Zone →"), OTM|ATM|ITM ✓
- sell_call → bear_call_spread: bearish, not put → profit zone left ("← Profit Zone"), OTM|ATM|ITM ✓
- buy_put → itm_put: bearish, put → profit zone left ("← Profit Zone"), ITM|ATM|OTM ✓
- sell_put → bull_put_spread: not bearish, put → profit zone right ("Profit Zone →"), ITM|ATM|OTM ✓

### Tradier Category 7 live tests — all 4 directions (P1) ✅ CONFIRMED Day 44
**Context:** sell_put was the only direction end-to-end tested with Tradier primary (Day 40). buy_call, sell_call, buy_put were untested.
**Result:** All 4 confirmed working via XLF live API:
- All return `data_source: tradier`, `quality: live`
- Deltas correct: buy_call 0.67 (target ~0.68), buy_put -0.678 (target ~-0.68), sell_call 0.193 (ATM/OTM), sell_put -0.185 (ATM/OTM)
- P&L tables populated (scenarios + footer) for all 4 directions
- Gates routing correctly to buyer (Track A/B) vs seller tracks — different gate IDs confirmed
- CPI event (7 days away) detected and warned by events gate for all directions
- Credit-to-width warning fires correctly for sub-33% spread premium ratios

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21.

### KI-086 partial: app.py `_run_one` still inline (LOW)
`_run_one` closure still inline in app.py. app.py ~449 lines — Rule 4 (max 150) still violated.
Partial fix already done (Day 39): best_setups_service.py extracted. Remaining: move `_run_one` to best_setups_service.py or a new module.

---

## Resolved History (recent)
- KI-076: TradeExplainer isBearish() live test ✅ Day 44 (no bug — verified correct)
- KI-081: CPI/NFP/PCE macro events calendar ✅ Day 43
- KI-077: DirectionGuide sell_put label ✅ Day 43
- KI-075: GateExplainer GATE_KB drift ✅ Day 43
- KI-064: IVR mismatch L2 vs L3 ✅ Day 43
- KI-094: QualityBanner dead ibkr_cache key ✅ Day 42
- KI-095: BatchStatusPanel timestamp UTC offset ✅ Day 42
- KI-093: analyze_service iv_provider tradier mapping ✅ Day 40
- KI-092: "ibkr_cache" → "bod_cache" rename ✅ Day 40
- KI-091: Tradier direction-aware strike window ✅ Day 40
- KI-090: Tradier delta=0.0 coercion fix ✅ Day 40
- KI-086: app.py `_run_one` extraction ✅ Day 39 (partial — _run_one still inline)
- KI-067: QQQ sell_put ITM strike fix ✅ Day 39
- KI-088: L3 stale banner ✅ Day 34
