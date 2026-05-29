# Known Issues — Day 57 (May 29, 2026)

## Open — HIGH

None currently.

## Open — MEDIUM

### KI-107: TQQQ delta guard not enforced in gate_engine
The ibkr-scan skill enforces delta 0.10 max for TQQQ at the read/decision layer, but `gate_engine.py` has no gate that blocks TQQQ strategies with delta > 0.10. `TQQQ_MAX_DELTA=0.10` constant exists in constants.py but is not read by gate_engine. A user who bypasses /ibkr-scan and calls /api/options/analyze directly for TQQQ could receive a delta 0.25 strategy without a hard warning.
**Fix:** Add TQQQ delta check in `_etf_liquidity_gate` or a new `_tqqq_special_gate`. ~10 lines.

### KI-108: GLD IV-cheap gate not enforced in gate_engine
GLD has a rule: if IV/HV < 1.0, "IV CHEAP — do not sell". The ibkr-scan skill enforces this at the read layer, but gate_engine has no GLD-specific IV/HV gate. A GLD sell_put analysis with IV/HV < 1.0 would pass the IV gate with a WARN rather than a hard block.
**Fix:** Check ticker == "GLD" AND hv_iv_ratio < 1.0 in `_etf_hv_iv_seller_gate`. 3 lines.

## Open — LOW

### KI-059: Single-stock bear untested
Stocks return 400 (not in ETF universe). Deferred — ETF-only going forward.

### KI-099: buy_call direction for Leading/Improving ETFs
bull_call_spread direction not implemented. Low priority — system now single-leg only.

## Resolved This Session (Day 57)

### FOMC over-blocking (resolved Day 57)
FOMC gate was blocking QQQ 70-95% of the time (FOMC meets 8×/year, every ~42 days; 30-45 DTE nearly always has FOMC in window). Fixed: 3-tier sensitivity. XLF/XLRE/TQQQ hard block within 14 days; QQQ/IWM/GLD warn-only within 7 days, never block. Event density score threshold raised 7→12.

### Spread strategies returning for ETFs (resolved Day 57)
strategy_ranker was returning bull_put_spread and bear_call_spread for ETF sell directions instead of single-leg puts/calls. Fixed: complete rewrite of strategy_ranker.py to single-leg only.

### Tradier chain ATM-centered for sell directions (resolved Day 57)
Tradier was fetching 12 puts sorted by proximity to underlying (ATM-centered), giving delta 0.38-0.53 range — unusable for delta 0.15-0.28 sell targets. Fixed: sort by |abs(delta) - 0.22| for sell directions.
