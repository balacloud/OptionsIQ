# OptionsIQ — Known Issues Day 54
> **Last Updated:** Day 54 (May 23, 2026)
> **Previous:** KNOWN_ISSUES_DAY53.md

---

## Resolved This Session (Day 54)

None — P2 implementation succeeded architecturally but scanner approach ruled out via live testing. No KI tickets closed.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design.

### KI-099: bull_call_spread missing as direction (LOW — DEFERRED)
For Leading/Improving ETFs + IVR 30–50%, a buyer direction (bull_call_spread) would be actionable. Currently only sell_put is suggested. High complexity (new direction track needed) — deferred to Day 55+.

---

## Architecture Finding (Day 54) — reqScannerSubscription Unsuitable for Targeted ETF Lookup

Tested live with IB Gateway connected. All 3 scanner codes returned 0/15 ETFs:

| Scan Code | Result |
|-----------|--------|
| HIGH_OPT_IMP_VOLAT_OVER_HIST | 0 ETFs (all 50 results were small-cap/bond funds) |
| HIGH_OPT_VOLUME_PUT_CALL_RATIO | 0 ETFs (IEFA appeared, our sector ETFs did not) |
| SCAN_ivRank52w_DESC | 0 ETFs (all individual stocks) |
| SCAN_impVolatOverHist_DESC | DISABLED by IBKR |

**Root cause:** IBKR scanner streams ~50 results maximum regardless of `numberOfRows`. Market-wide screens rank all ~12,000 US stocks; sector ETFs with moderate IV are middle-of-the-pack, not top-50.

**Decision:** `fetch_scanner_subscription_batch()` now delegates directly to `get_iv_hv_batch()` (reqHistoricalData). Put/call volume remains None (put/call sentiment gate handles gracefully as advisory pass). Future option: compute put/call from Tradier options chain.

---

## Resolved History (recent)
- KI-106: IBKR batch all-nan → reqHistoricalData ✅ Day 52
- KI-105: Tick 104 invalid for STK → 106+411+100+105 ✅ Day 51
- KI-104: snapshot=True invalid with genericTickList ✅ Day 51
- KI-103: is_connected() false-negative in scanner ✅ Day 51
- KI-102: XLI/XLB OHLCV corruption (Apr 25-26) ✅ Day 51
- KI-101: IV/HV null in watchlist ✅ Day 50
