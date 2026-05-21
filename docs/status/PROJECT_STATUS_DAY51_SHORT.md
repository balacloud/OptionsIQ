# OptionsIQ — Project Status Day 51
> **Date:** May 21, 2026 | **Version:** v0.33.1 | **Tests:** 44

## What Shipped

### P0: Scanner Integration Live Test — Completed with Findings

**Goal:** Verify IV/HV column populates from live IBKR batch (tick 106) in Best Setups watchlist.

**Result:** Scan confirmed working. IV/HV populates correctly for all 7 ETFs — via **Tradier chain** (primary path), not IBKR batch. IBKR batch fires but returns `{}` due to market data subscription requirement (see architecture limitation below).

---

### Bug Fix 1 — XLI/XLB OHLCV Corruption (KI-102 RESOLVED)

**Root cause:** 4 rows in `ohlcv_daily` (XLI and XLB, Apr 25-26) had identical wrong closes (100.62 / 100.25). XLI's real price is ~$171, XLB is ~$51. The corruption caused 20-day HV to compute as 193.88% (XLI) and 234.72% (XLB) — making IV/HV show 0.11 and 0.08 in the watchlist.

**Fix:** `DELETE FROM ohlcv_daily WHERE ticker IN ('XLI','XLB') AND date IN ('2026-04-25','2026-04-26')` — 4 rows deleted.

**Verification:** Re-ran scan → XLI HV=19.74%, IV/HV=1.06; XLB HV=20.43%, IV/HV=1.08. All plausible.

---

### Bug Fix 2 — `fetch_live_iv_hv_batch` False-Negative Skip (KI-103 RESOLVED)

**Root cause:** `ib_worker.is_connected()` returned False before any IBKR call (lazy connection), causing early return `{}`. The batch never executed even when IB Gateway was running.

**Fix:** Replaced `is_connected()` guard with a 0.5s TCP port check:
```python
with socket.create_connection((host, 4001), timeout=0.5):
    pass
```
Fast offline detection (avoids the 12s client-ID scan when truly offline), batch proceeds when gateway reachable.

**File:** `backend/scanner_service.py`

---

### Bug Fix 3 — `reqMktData snapshot=True` Invalid with `genericTickList` (KI-104 RESOLVED)

**Root cause:** IBKR Error 321: "Snapshot market data subscription is not applicable to generic ticks." `snapshot=True` cannot be combined with a non-empty `genericTickList`.

**Fix:** Changed to `snapshot=False` (streaming mode). Error 321 eliminated.

**File:** `backend/ibkr_provider.py`

---

### Bug Fix 4 — Tick 104 Invalid for STK Contracts (KI-105 RESOLVED)

**Root cause:** Generic tick 104 (histVol) is not in the legal tick list for STK (Stock/ETF) contracts. Also removed ticks 29/30 (callVolume/putVolume) which are also invalid for STK.

**Fix:** Changed `genericTickList` from `"104,106,29,30"` to `"106,411,100,105"` (impVol, rtHistVol, optVol, avgOptVol — all valid for STK).

**File:** `backend/ibkr_provider.py`

---

### Architecture Finding — IBKR Market Data Subscription Required

`reqMktData` with streaming mode (`snapshot=False`) and valid generic ticks returns all `nan` for ETFs not owned in portfolio. Root cause: IBKR requires a paid US Equity market data subscription ($4.50–6/month per exchange) for arbitrary ticker streaming. Portfolio positions receive live data automatically. ETFs held as analysis targets (XLK, XLE, etc.) require explicit subscription.

**Impact:** IBKR batch returns `{}`. Best Setups scan unaffected — Tradier provides chain IV for all ETFs. All 7 ETFs show correct IV/HV values.

**Resolution path:** Subscribe to market data in IBKR account settings. Code is ready — batch will populate immediately once subscribed.

---

## Test Count
44 (unchanged — no new gate logic, data plumbing and bug fixes only)

## Open Issues
| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH | Single-stock bear untested — deferred by design (ETF-only mode) |
| KI-099 | LOW | bull_call_spread direction for Leading/Improving + IVR 30–50% |

## Next Session Priorities
1. **P0 — Paper trade logging** — still 0/30. Log next XLF or QQQ CAUTION setup to Paper Trade Dashboard. Cannot calibrate gates without 30-trade sample. ~5 min user action.
2. **P1 — MASTER_AUDIT_FRAMEWORK sweep** — overdue since Day 42 (9 sessions). All 10 categories. Focus Category 10 (Trading Effectiveness) and gate calibration.
3. **P2 — Put/call ratio gate** — ticks 29/30 are NOT available via reqMktData for ETFs. Remove P3 from priorities (invalid approach). If put/call ratio is desired, source from Tradier API instead.
4. **P3 — KI-099** — bull_call_spread for Leading/Improving ETFs. Plan before touching.
5. **P4 — IBKR market data subscription** — subscribe to US Equity data in IBKR account settings to enable live IV/HV batch. ~15 min setup, cost ~$6/month.
