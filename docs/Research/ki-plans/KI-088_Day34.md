# KI-088 Execution Plan — L3 Stale Banner Fix (Day 34)

> **Status:** Plan complete. Ready for Sonnet to execute.
> **Author:** Opus (planning) → Sonnet (execution)
> **Date:** 2026-04-30
> **Version target:** v0.25.1
> **Scope:** KI-088 only. KI-086 (app.py size) and KI-067 (QQQ ITM) are deferred to separate plans.

---

## 1. Problem Statement

When a user clicks **Run Analysis** on the L3 analysis panel, the result returns with `data_source: "ibkr_stale"` and the frontend displays the stale-chain banner — even when IB Gateway is connected and live during market hours.

The Best Setups scan path (Day 33 fix) does NOT have this issue because `_run_one` pre-fetches `currentPrice` from STA and injects it as `last_close`. The L3 path does not.

---

## 2. Root Cause (Traced End-to-End)

| Step | File:Line | What happens |
|------|-----------|--------------|
| 1 | Frontend POSTs to `/api/options/analyze` | Request body: `{ticker, direction, account_size, ...}` — **no `last_close`** |
| 2 | `app.py:108` | Calls `analyze_etf(payload, ticker, ...)` |
| 3 | `analyze_service.py:626` | `underlying_hint = payload.get("last_close")` → **`None`** |
| 4 | `analyze_service.py:637` | `data_svc.get_chain(ticker, ..., underlying_hint=None, ...)` |
| 5 | `data_service.py:302` | IBWorker submits `provider.get_options_chain(ticker, None, ...)` |
| 6 | `ibkr_provider.py` (inside `get_options_chain`) | Because `underlying_hint` is None, calls `get_underlying_price(ticker)` |
| 7 | `ibkr_provider.py:~340` | `reqMktData(snapshot=True)` + `sleep(1.2)` → bid/ask/last all `None` → raises `IBKRNotAvailableError` |
| 8 | `data_service.py:321` | Catches exception → records CB failure → falls through |
| 9 | `data_service.py:326-331` | Returns stale cache → `data_source = "ibkr_stale"` |
| 10 | Frontend | Banner shown |

**Why `reqMktData(snapshot=True)` returns None for liquid ETFs:** IBKR snapshot mode is unreliable for the 1.2s window the provider waits, particularly when the connection has been idle. This is a known IBKR quirk, not a bug in our code. We are not chasing it because **STA `/api/stock/{ticker}` is faster, more reliable, and already running** — verified returns `currentPrice: 52.02` for XLF in <100ms.

---

## 3. Architectural Decision

**STA is the canonical source for ETF underlying price in analysis paths.**

Rationale:
- STA is the user's own system, always running (per user — Day 34 session start)
- STA already serves `currentPrice` for all 16 ETFs from a real data feed
- STA has no rate limits and no IBKR connection-state dependencies
- Day 33 already established this pattern for VIX (stampede-safe with `threading.Lock`) and Best Setups underlying

This does NOT violate Golden Rule 1 ("Live Data Is the Default"). STA price is live (refreshed continuously). It is a different *transport*, not a stale fallback. IBKR remains the source of truth for the **option chain** itself (strikes, IVs, greeks, bid/ask) — only the underlying spot price is sourced from STA.

This does NOT violate Rule 6 ("STA Integration Is Optional, Never Required") because the helper falls back gracefully — if STA is unreachable, `underlying_hint` stays `None` and the existing IBKR path runs. The user has STA running by default in their workflow, so this is the happy path, not a hard requirement.

---

## 4. Implementation

### 4.1 Add helper to `analyze_service.py`

**Where:** Insert after line 48 (`_days_until_next_fomc`), before line 51 (`_etf_holdings_at_risk`).

**New function:**

```python
def _resolve_underlying_hint(ticker: str, payload: dict) -> float | None:
    """
    Resolve the underlying spot price hint for an analysis call.

    Order of precedence:
      1. payload['last_close'] — if explicitly provided by caller (e.g. _run_one)
      2. STA /api/stock/{ticker} currentPrice — STA is the user's canonical price source
      3. None — let downstream IBKR path fetch via get_underlying_price()

    Returning a hint here lets ibkr_provider.get_options_chain() bypass its internal
    reqMktData(snapshot=True) call, which is unreliable in the 1.2s window when
    the connection has been idle. See KI-088 (Day 34).
    """
    explicit = payload.get("last_close")
    if explicit is not None:
        try:
            val = float(explicit)
            if val > 0:
                return val
        except (TypeError, ValueError):
            pass

    try:
        resp = _requests.get(f"{STA_BASE_URL}/api/stock/{ticker}", timeout=3)
        price = resp.json().get("currentPrice")
        if price is not None:
            val = float(price)
            if val > 0:
                return val
    except Exception as exc:
        logger.debug("STA underlying price unavailable for %s: %s", ticker, exc)

    return None
```

### 4.2 Use helper in `analyze_etf()`

**File:** `backend/analyze_service.py`
**Replace lines 626–630** (the existing `underlying_hint = payload.get("last_close")` block):

**BEFORE:**
```python
    underlying_hint = payload.get("last_close")
    try:
        underlying_hint = float(underlying_hint) if underlying_hint is not None else None
    except Exception:
        underlying_hint = None
```

**AFTER:**
```python
    underlying_hint = _resolve_underlying_hint(ticker, payload)
```

Note: lines 631–635 (`target_price`) stay unchanged — they still fall back to `underlying_hint` correctly because the helper returns a valid float when STA succeeds.

### 4.3 Simplify `_run_one` in `app.py` (optional consistency cleanup)

**File:** `backend/app.py`
**Replace lines 431–447** (the inline STA fetch + payload construction):

**BEFORE:**
```python
        # Pre-fetch underlying price from STA to bypass IBKR reqMktData snapshot call.
        # Without this, all 8 parallel scans call get_underlying_price() simultaneously
        # via IBWorker, fail (bid/ask/last all None in 1.2s window), and trip the circuit breaker.
        last_close = None
        try:
            sta_stock = _requests.get(f"{STA_BASE_URL}/api/stock/{ticker}", timeout=3)
            last_close = sta_stock.json().get("currentPrice")
        except Exception:
            pass
        payload = {
            "ticker": ticker,
            "direction": direction,
            "account_size": account_size,
            "risk_pct": float(os.getenv("RISK_PCT", 0.01)),
            "planned_hold_days": 21,
            **({"last_close": last_close} if last_close else {}),
        }
```

**AFTER:**
```python
        # underlying price is now resolved inside analyze_etf via _resolve_underlying_hint.
        # We no longer need to pre-fetch here — kept payload structure flat.
        payload = {
            "ticker": ticker,
            "direction": direction,
            "account_size": account_size,
            "risk_pct": float(os.getenv("RISK_PCT", 0.01)),
            "planned_hold_days": 21,
        }
```

This is a **dedup**, not a behavior change — the same STA call now happens inside `_resolve_underlying_hint()`, which is invoked by `analyze_etf()`. Net effect on Best Setups scan: identical.

If `_requests` and `STA_BASE_URL` imports in `app.py` become unused after this change, leave them — they may be used elsewhere, and removing imports is out of scope for this fix.

### 4.4 No other files need to change

- `data_service.py` — no change. `get_underlying_price(hint=...)` already short-circuits when hint is provided.
- `ibkr_provider.py` — no change. When `underlying_hint` is non-None, `get_options_chain` uses it directly (already verified at line 387 of ibkr_provider.py).
- Frontend — no change.
- Tests — see §5.

---

## 5. Test Plan

### 5.1 Unit test (new)

**File:** `backend/tests/test_analyze_service.py` (or wherever helper-level tests live — verify with `ls backend/tests/`)

Add three test cases for `_resolve_underlying_hint`:

1. **Explicit `last_close` wins:**
   ```python
   assert _resolve_underlying_hint("XLF", {"last_close": 52.0}) == 52.0
   ```

2. **STA fallback when no explicit price** (mock `_requests.get` to return `{"currentPrice": 52.02}`):
   ```python
   # patch _requests.get with mock returning JSON {"currentPrice": 52.02}
   assert _resolve_underlying_hint("XLF", {}) == 52.02
   ```

3. **Returns None when STA unreachable** (mock `_requests.get` to raise):
   ```python
   # patch _requests.get to raise ConnectionError
   assert _resolve_underlying_hint("XLF", {}) is None
   ```

Target test count: 33 → 36.

### 5.2 Manual verification (required before declaring done)

1. Confirm IB Gateway connected (`curl localhost:5051/api/health`)
2. Confirm STA up (`curl localhost:5001/api/stock/XLF | grep currentPrice`)
3. Restart backend: `./stop.sh && ./start.sh`
4. Open frontend, navigate to Analyze tab, select XLF, click **Run Analysis**
5. **Pass criteria:**
   - Stale banner does NOT appear
   - `data_source` in response is `"ibkr_live"` or `"ibkr_cache"` (NOT `"ibkr_stale"`)
   - Underlying price displayed in panel matches STA's `currentPrice` (within $0.10)
6. Repeat for one Bullish ETF (XLK), one Bearish-eligible ETF (XLE)
7. Best Setups scan from "Setups" tab still returns 5–6 setups, scan time ~3–4 min (no regression)

### 5.3 STA-down regression check

1. Stop STA (`./stop.sh` in STA repo, or `kill` the port 5001 process)
2. Click **Run Analysis** on XLF
3. **Pass criteria:** request still returns (does not hang), banner may appear (acceptable — STA is the user's canonical source; if it's down, falling back to IBKR direct is OK)
4. Restart STA when done

---

## 6. Rollback Plan

If the fix breaks something:

1. Revert `analyze_service.py` lines 626–630 to the original 5-line block
2. Revert `app.py` lines 431–447 to the inline STA fetch
3. Delete `_resolve_underlying_hint` helper

Single commit, single revert. No DB migrations, no API contract changes.

---

## 7. Sonnet Execution Checklist

Sonnet should work this list top-to-bottom and stop at any failure to diagnose (per Golden Rule: "If fix fails, STOP — don't chain guesses").

- [ ] Read `backend/analyze_service.py` lines 1–50 and 605–650 to confirm structure
- [ ] Read `backend/app.py` lines 420–500 to confirm `_run_one` structure
- [ ] **Step 1:** Insert `_resolve_underlying_hint()` helper into `analyze_service.py` after `_days_until_next_fomc()` (per §4.1)
- [ ] **Step 2:** Replace the 5-line block at `analyze_service.py:626–630` with the single helper call (per §4.2)
- [ ] **Step 3:** Simplify `_run_one` in `app.py` per §4.3 (remove inline STA fetch + spread)
- [ ] **Step 4:** Add 3 unit tests per §5.1
- [ ] **Step 5:** Run full test suite: `cd backend && python -m pytest -q` — all 36 must pass
- [ ] **Step 6:** Restart backend and run manual verification §5.2
- [ ] **Step 7:** Run STA-down regression §5.3
- [ ] **Step 8 (session close):** Update CLAUDE_CONTEXT.md, KNOWN_ISSUES_DAY34.md (mark KI-088 RESOLVED), ROADMAP.md (tick KI-088), bump version v0.25.0 → v0.25.1, commit + push

---

## 8. Out of Scope (Document Separately)

- **KI-086** (app.py 536 lines, target 150) — `_seed_iv_for_ticker` + `_run_one` + `seed_iv_all` extraction to a service module. Bigger refactor, separate plan.
- **KI-067** (QQQ sell_put returns ITM strikes) — chain-too-narrow issue, separate strategy_ranker investigation.
- **Skew computation** — feature work, separate plan.
- **Root-causing IBKR `reqMktData(snapshot=True)` unreliability** — explicitly deferred. STA-as-canonical removes the dependency on this path for analysis. If we ever ship without STA, we'd need to revisit.

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| STA returns wrong price for an ETF | Low | Med (gate decisions on bad price) | Helper validates `> 0`; STA already used for VIX with no issues |
| STA latency > 3s causes route slowdown | Low | Low (3s timeout cap) | Timeout already set; user has STA on localhost (sub-100ms) |
| `_run_one` simplification regresses Best Setups | Low | Med | Behavior is identical (same STA call, just relocated); manual scan in §5.2 catches it |
| Helper masks a real IBKR issue we should fix | Med | Low | Acknowledged in §3 — STA-as-canonical is explicit user choice, not a band-aid |

**Overall risk: LOW.** Smallest possible change to fix the documented symptom. No frozen-file modifications. No DB or API changes.

---

## 10. Estimated Effort

- Sonnet implementation: 30–45 min (including tests)
- Manual verification: 10 min
- Session close docs: 15 min
- **Total: ~1 hour**
