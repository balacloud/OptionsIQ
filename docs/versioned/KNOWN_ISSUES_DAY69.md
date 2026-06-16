# Known Issues — Day 69 (Jun 16, 2026)

## Open — HIGH
None.

## Open — MEDIUM
None.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (ETF-only). Permanent deferral.

### KI-099: buy_call for Leading/Improving ETFs
Single-leg only, deferred.

## Resolved This Session (Day 69)

### Audit H1: GateExplainer.jsx ivr_seller showed IVR ≥ 35% — contradicts 40% gate ✅
`GateExplainer.jsx` GATE_KB `ivr_seller` passAnswer updated to 40% + warn band explanation.

### Audit M1: MASTER_AUDIT_FRAMEWORK.md 5 stale IVR=35% references ✅
All 5 updated to 40%. Framework updated to v1.7.

### Audit L1: `app.py` debug endpoint `"ibkr_cache"` stale label ✅
Replaced with `"bod_cache"`.

### Data Bug 1: OHLCV sourced from yfinance even though Tradier has it ✅
`_extract_iv_data()` now accepts `ohlcv_provider=tradier_provider`. When Tradier is available,
`get_ohlcv_daily()` (Tradier `markets/history`) is called instead of yfinance. HV computation
now uses same source as chains.

### Data Bug 2: EOD batch OHLCV path missing Tradier ✅
`seed_iv_for_ticker()` now: Tradier → yfinance fallback. IBKR path removed.

### Dead code removed: ib_worker.py + ibkr_provider.py deleted ✅
IB Gateway dead since Day 56. 1000+ lines of dead code removed across 8 service files.
`scanner_service.py` IBWorker functions stripped (kept `get_scanner_data()` for cache reads).

### Syntax error in data_service.py from dead code removal ✅
Stray `)` left on line 181 after removing `_timeout()` method. Caused `SyntaxError` on
startup — caught immediately by live import test. Fixed and pushed as separate commit 1a537c1.
This confirms: always run import test after structural refactors, not just unit tests.

## Audit Health
**0 CRITICAL / 0 HIGH / 0 MEDIUM** — Safe to paper trade.
