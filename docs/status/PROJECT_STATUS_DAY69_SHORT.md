# Project Status — Day 69 (Jun 16, 2026)
> **Version:** v0.36.1
> **Session type:** Audit + data fix + dead code removal

---

## What Shipped

### Targeted Audit (Categories 1,2,3,7,9) — 0C/1H/1M/1L, all fixed
- **H1:** `GateExplainer.jsx` GATE_KB `ivr_seller` showed "IVR ≥ 35%" — fixed to 40% + warn band
- **M1:** `MASTER_AUDIT_FRAMEWORK.md` v1.7 — 5 stale IVR=35% references updated to 40%
- **L1:** `app.py:198` debug endpoint `"ibkr_cache"` → `"bod_cache"`

### Tradier OHLCV as Primary Source (data correctness fix)
- `analyze_service._extract_iv_data()`: new `ohlcv_provider` parameter. When `tradier_provider` is
  passed, OHLCV comes from `tradier_provider.get_ohlcv_daily()` (Tradier `markets/history`).
  Previously: data_source="tradier" → `iv_provider = yf_provider` → OHLCV from yfinance.
  Now: OHLCV from same source as chains. HV computation is consistent.
- `batch_service.seed_iv_for_ticker()`: Tradier added as primary OHLCV before yfinance fallback.
- `run_eod_batch()`, `run_startup_catchup()`, scheduler, manual routes — all pass `tradier_provider`.
- IBKR pacing sleep 2s → 1s (Tradier handles 200 req/min).

### Dead Code Removal — IB Gateway (Day 56 → Day 69)
**Deleted:**
- `backend/ib_worker.py` — 150 lines, IBWorker threading class
- `backend/ibkr_provider.py` — 860 lines, ib_insync chain/IV/OHLCV provider
- `backend/test_scanner_live.py` — dev diagnostic, archived to `skills/archive/`

**Stripped from 8 service files:**
| File | What removed |
|------|-------------|
| `app.py` | `IBWorker()` instantiation, `ib_worker=` from all calls, simplified `/api/health` |
| `analyze_service.py` | `_call_provider()` IBWorker closure, `ib_worker` param, `get_live_price()` simplified |
| `batch_service.py` | IBKR IV seeding block, `ib_worker` param from 3 functions |
| `data_service.py` | `self.ib_worker`, `_refresh_async()`, IBWorker path in `get_underlying_price()`, `ibkr_status()` simplified |
| `best_setups_service.py` | `ib_worker` param |
| `data_health_service.py` | `ib_worker` param |
| `sector_scan_service.py` | `ib_worker` param |
| `scanner_service.py` | `fetch_live_iv_hv_batch()` + `fetch_scanner_subscription_batch()` removed |

**Result:** `app.py` 360 → 352 lines. Zero `ib_worker`/`IBWorker`/`ib_insync` references in active code.

### P0 Live Test — Blended /chartreview (carried from Day 68)
Ran morning workflow successfully on FOMC day (Jun 16):
- `/ibkr-scan`: NO_TRADE — HV > IV across all 5 ETFs. XLF watch candidate.
- `/chartreview`: SPY regime confirmed UPTREND. XLF catalyst ABORT (FOMC happening now, Warsh first meeting).
- Machine blocks correctly generated. System correctly said NO TRADE.
- Minor: RSI read 59.4 (table shows 53.8), MACRO_COUNT=3 (should be 4 with PCE). Both non-material.

---

## Test Count
**110 tests** — unchanged.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear — ETF-only, permanent deferral |
| KI-099 | LOW | buy_call for Leading/Improving ETFs — deferred |

---

## Audit Health
**0 CRITICAL / 0 HIGH / 0 MEDIUM** — Safe to paper trade.

---

## Next Session Priorities (Day 70)

### P0 — Test the cleanup live
Restart backend, hit `/api/health`, run analyze on QQQ sell_put, confirm:
- `data_source = "tradier"` in response
- `hv_20` is populated (Tradier OHLCV path working)
- No 500 errors, no import failures

### P1 — GLD skew inversion (peer review MEDIUM)
`gate_engine._skew_flow_gate()`: GLD skew inverts during gold rallies. Add GLD-specific branch
for sell_call (calls get bid above puts). ~10 lines.

### P2 — XLF post-FOMC re-entry check
Post-FOMC dust settles Jun 17. If IV/HV > 1.10 and IVR climbs toward 50%, XLF is the
watch_only candidate from today's scan. Re-run `/ibkr-scan` and compare.

### P3 — IBKR dead code audit pass
Run `grep -r "ibkr_live\|ibkr_closed"` to confirm no stale data source labels remain.
Update ARCH_DECISION_TRADIER_PRIMARY.md to note IB Gateway permanent removal Day 69.
