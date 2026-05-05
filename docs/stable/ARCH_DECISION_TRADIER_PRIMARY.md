# Arch Decision: Tradier as Primary Live Chain Source

**Date:** 2026-05-05 (Day 39)
**Version:** v0.28.0
**Status:** ACTIVE

---

## Decision

Remove IBKR live chain fetch from `DataService.get_chain()`. Tradier becomes the
primary real-time chain source during market hours. IBKR is only called by batch
jobs (`run_bod_batch`, `run_eod_batch`) in `batch_service.py`.

---

## Why

IB Gateway was required to run **all day** during market hours for live analysis.
This caused repeated pain:
- Gateway crashes mid-session → analysis breaks, circuit breaker trips
- Gateway auth issues (20-30s reconnect) → timeout cascades
- IBWorker is single-threaded → every ETF queues behind the previous one
- Best Setups scan took 3-4 min because IBKR pacing rules forced sequential waits

Tradier (brokerage account) provides real-time option chains via a simple REST call
with no protocol overhead, no single-threaded queue, and no pacing limits at our scale.

**IB Gateway is now only needed once per trading day: 4:05 PM ET for EOD IV seeding.**
BOD chain pre-warm (9:31 AM) also runs through Tradier now; user may still start
Gateway at BOD time but it is no longer required.

---

## New Cascade (DataService.get_chain)

```
1. BOD cache (IBKR-or-Tradier pre-warmed at 9:31 AM)   → "ibkr_cache"
2. Tradier REST (real-time, live greeks + OI)            → "tradier"
3. Stale BOD cache (IBKR was down at BOD time)          → "ibkr_stale"
4. Alpaca (15-min delayed REST)                         → "alpaca"
5. yfinance (free, BS-computed greeks)                  → "yfinance"
6. Mock (dev/CI only)                                   → "mock"
```

IBKR live (`"ibkr_live"`, `"ibkr_closed"`) is no longer emitted by DataService.
It was steps 2a/2b in the old cascade.

---

## Old Cascade (preserved for revert)

```
1. Fresh cache          → "ibkr_cache"   (+ background IBKR refresh)
2. IBKR live            → "ibkr_live" or "ibkr_closed"
3. Stale cache          → "ibkr_stale"   (+ background IBKR refresh)
4. Tradier              → "tradier"
5. Alpaca               → "alpaca"
6. yfinance             → "yfinance"
7. Mock                 → "mock"
```

---

## What IBKR Is Still Used For

| Job | Code path | IBKR needed? |
|-----|-----------|--------------|
| EOD IV seeding | `batch_service.run_eod_batch()` → `ib_worker.submit(provider.get_historical_iv)` | **YES** — IBKR is the only source for `OPTION_IMPLIED_VOLATILITY` bars |
| BOD chain pre-warm | `batch_service.run_bod_batch()` → `data_svc.get_chain()` | No — DataService now goes to Tradier |
| Live analysis (Best Setups, L3) | `data_svc.get_chain()` | **No** — Tradier |
| IVR percentile (iv_store) | Reads SQLite seeded by EOD batch | No |
| HV-20 | Reads SQLite seeded by EOD batch | No |
| Underlying price | STA → `_resolve_underlying_hint()` | No |
| VIX | STA → `_fetch_vix()` | No |

---

## Files Changed

| File | Change |
|------|--------|
| `backend/data_service.py` | Removed IBKR live step + background refresh from `get_chain()` |
| `backend/data_service.py.pre_tradier_primary` | **Backup of original** — copy over data_service.py to revert |

---

## How to Revert

If Tradier is unavailable (API outage, key expired) and you need IBKR back as
the live chain source:

**Step 1** — Restore the backup:
```bash
cp backend/data_service.py.pre_tradier_primary backend/data_service.py
```

**Step 2** — That's it. The backup is the fully working pre-Tradier-primary version.

Alternatively, restore just the `get_chain()` method to the old cascade by adding
back the IBKR live block between steps 1 and 3:

```python
# 2. IBKR live via IBWorker  ← RE-INSERT THIS BLOCK
if self.ib_worker is not None and self._cb_allowed():
    provider = self.ib_worker.provider
    if provider is not None:
        try:
            chain = self.ib_worker.submit(
                provider.get_options_chain,
                ticker,
                underlying_hint,
                direction,
                target_price,
                profile,
                min_dte_val,
                timeout=self._timeout(profile),
            )
            self._cb_record(success=True)
            if chain.get("market_closed"):
                return chain, "ibkr_closed"
            self._cache_set(ticker, chain, profile, direction)
            return chain, "ibkr_live"
        except TimeoutError:
            logger.warning("IBKR chain timeout for %s", ticker)
            self._cb_record(success=False)
        except Exception as exc:
            logger.warning("IBKR chain error for %s: %s", ticker, exc)
            self._cb_record(success=False)
```

And add back `_refresh_async` calls in step 1 (cache hit) and step 3 (stale cache):
```python
# In step 1 (after cache hit):
self._refresh_async(ticker, profile, direction, underlying_hint, target_price, min_dte_val)

# In step 3 (after stale cache hit):
self._refresh_async(ticker, profile, direction, underlying_hint, target_price, min_dte_val)
```

---

## Trade-offs Accepted

| Trade-off | Impact |
|-----------|--------|
| IBKR chain data no longer used for live analysis | Tradier greeks are equivalent quality for our gate engine |
| BOD cache may be Tradier-sourced instead of IBKR-sourced | Acceptable — both have accurate bid/ask/greeks |
| `"ibkr_live"` data_source label will not appear in live analysis | DataProvenance badge will show `"tradier"` during live hours |
| IBKR circuit breaker unused in live path | CB code stays in place (used by `get_underlying_price`), no side effects |
