# OptionsIQ — Concurrency & Connection Architecture
> **Status:** Research plan — to be implemented in Phase 4+
> **Last Updated:** Day 3 (March 6, 2026)

---

## Current Architecture (Day 3 state)

```
Flask (multi-threaded) → IBWorker.submit() → queue.Queue → single "ib-worker" thread
                                                              ↓
                                                       IBKRProvider.get_options_chain()
                                                       (ib_insync IB() instance lives here)
```

**What works:**
- Single IB() instance in one thread — Rule 2 satisfied
- Request/result queue — thread-safe Flask → IBKR communication
- 24s timeout on submit() — Flask caller times out and falls through to yfinance
- In-memory structure cache (4h) — reqSecDefOptParams result reused intraday
- SQLite chain cache (2min TTL) — survives restarts

---

## Known Problems (5 root causes)

### Problem 1: Queue Poisoning
**Symptom:** After a timeout, subsequent requests hang for 2+ minutes.

**Cause:** When `submit(fn, timeout=24s)` raises TimeoutError on the Flask side, the
worker thread is still executing `fn`. The worker has no concept of "the caller gave up".
The next submit() call queues behind the still-running call. If the call takes 2 minutes
total, every subsequent request in that window also waits 2 minutes.

**Example trace:**
```
t=0s   Flask submits chain fetch → Worker starts reqTickers for 12 contracts
t=24s  Flask times out → falls through to yfinance → returns yfinance response ✓
t=24s  Another Flask request submits chain fetch → queued behind still-running t=0 call
t=90s  Worker finishes t=0 call (IBKR was slow) → starts t=24s call
t=114s Second request completes (90s wait!)
```

**Fix: Request expiry.**
Add a `submitted_at` + `expires_at` to each `_Request`. Worker checks on dequeue:
if `time.time() > req.expires_at`, put `("err", TimeoutError(...))` in result_q and skip.
The Flask caller raised TimeoutError at t=24s and already returned, but we still need
to drain the result_q — so the worker just discards expired requests silently.

```python
class _Request:
    __slots__ = ("fn", "args", "kwargs", "result_q", "expires_at")

    def __init__(self, fn, args, kwargs, timeout):
        ...
        self.expires_at = time.time() + timeout

# In _run() loop:
req = self._req_queue.get()
if time.time() > req.expires_at:
    req.result_q.put(("err", TimeoutError("Request expired in queue")))
    continue  # discard — don't execute
```

**Impact:** A queue-poisoned state self-heals within one call duration (~30s) instead of
cascading all pending requests to that same slow duration.

---

### Problem 2: No Request Deduplication
**Symptom:** 3 users click Analyze simultaneously → 3 AMD chain fetches queue.

**Cause:** IBWorker.submit() blindly queues every request.

**Fix: In-flight tracking with shared futures.**

At the DataService level, track in-flight (ticker, profile, direction) tuples:
```python
# DataService
self._inflight: dict[str, "Future"] = {}
self._inflight_lock = threading.Lock()

def get_chain(self, ticker, profile, direction, ...):
    key = self._cache_key(ticker, profile, direction)
    with self._inflight_lock:
        if key in self._inflight:
            # Already fetching — wait for existing result
            fut = self._inflight[key]
    if fut:
        return fut.result(timeout=30)  # wait for existing call
    # Otherwise, start a new fetch and register it
```

**Impact:** N simultaneous requests for the same ticker = 1 IBKR call, N waiters.

---

### Problem 3: No ib_insync Internal Timeout
**Symptom:** `reqTickers` can block for 30+ seconds (IBKR pacing, bad data).

**Cause:** ib_insync's `reqTickers` uses `waitOnUpdate()` internally. Default timeout
for `waitOnUpdate` is `IB.RequestTimeout` which defaults to 0 (unlimited).

**Fix: Set `ib.RequestTimeout` per call.**

```python
# In IBKRProvider.get_options_chain():
old_timeout = self.ib.RequestTimeout
self.ib.RequestTimeout = timeout_sec  # e.g. 20s for reqTickers
try:
    tickers = self.ib.reqTickers(*chunk)
finally:
    self.ib.RequestTimeout = old_timeout
```

This makes ib_insync internally abort if IBKR doesn't respond within timeout_sec.
Combined with request expiry (Problem 1), this creates a two-level timeout:
- Level 1: IBWorker request expires → worker discards (fast)
- Level 2: ib_insync RequestTimeout → ib_insync raises TimeoutError internally (safe)

---

### Problem 4: No Connection Heartbeat
**Symptom:** `is_connected()` returns True but connection is silently dead.

**Cause:** `ib.isConnected()` is a local flag set by ib_insync. It goes False on disconnect
events. But some network failures (TCP timeout, NAT keepalive expiry) don't generate
disconnect events — the connection appears alive but requests hang.

**Fix: Background keepalive in the IBWorker.**

```python
def _run(self):
    ...
    self._heartbeat_at = time.time()

    while True:
        try:
            req = self._req_queue.get(timeout=30.0)  # 30s idle timeout
        except queue.Empty:
            # Idle — send keepalive
            try:
                self._provider.ib.reqCurrentTime()
                self._heartbeat_at = time.time()
            except Exception:
                self._heartbeat_at = 0.0  # mark stale
            continue
        ...

def is_connected(self) -> bool:
    # Both ib_insync flag AND recent heartbeat
    flag = self._provider.is_connected() if self._provider else False
    heartbeat_ok = (time.time() - self._heartbeat_at) < 90.0  # 90s tolerance
    return flag and heartbeat_ok
```

**Impact:** Detects silent connection drops within 30-90s.

---

### Problem 5: Dual Circuit Breakers
**Symptom:** Circuit breaker in `app.py` and circuit breaker in `DataService` — independent state.

**Cause:** app.py's legacy circuit breaker was not removed when DataService was added.
Both track failures independently, creating inconsistent state.

**Fix:** Remove `_ib_chain_failures`, `_ib_chain_open_until`, `_ib_chain_lock`,
`_ib_chain_allowed()`, `_ib_chain_record()` from app.py. All CB logic is in DataService only.
The `_get_chain_with_timeout()` and `_fetch_chain_with_retry()` functions in app.py are
now dead code (DataService replaced them).

---

## Implementation Priority

| Priority | Problem | Effort | Impact |
|----------|---------|--------|--------|
| P1 | Request expiry (Problem 1) | Low — add `expires_at` to `_Request` | Fixes cascade hang immediately |
| P1 | Set `ib.RequestTimeout` (Problem 3) | Low — 2 lines in get_options_chain | Limits ib_insync blocking |
| P2 | Remove dual CB (Problem 5) | Medium — refactor app.py | Eliminates inconsistency |
| P3 | Background heartbeat (Problem 4) | Medium — add to IBWorker._run | Detects stale connections |
| P4 | Request deduplication (Problem 2) | High — needs Future coordination | Performance under load |

---

## Additional Improvements (Post-Phase 4)

### Batch IV + OHLCV Fetches
Currently `_extract_iv_data()` submits 2 separate IBWorker calls (get_historical_iv + get_ohlcv_daily).
These execute serially. Could batch into a single IBWorker call:
```python
def _fetch_iv_bundle(self, ticker, days_iv, days_ohlcv):
    return {
        "history": self.get_historical_iv(ticker, days_iv),
        "ohlcv": self.get_ohlcv_daily(ticker, days_ohlcv),
    }
# One submit() call instead of two
```
**Impact:** 1 queue roundtrip instead of 2.

### Persistent Structure Cache (SQLite)
Current structure cache is in-memory (lost on restart). After restart, first request
always does a fresh `reqSecDefOptParams`.
Could persist to SQLite with 4h TTL — structure rarely changes intraday.

### Market Hours Detection
Pre-market / post-market: IBKR returns options with no bid/ask (market closed).
Could detect market hours (9:30am-4pm ET Mon-Fri) and skip live pricing:
- Market open: reqTickers for live quotes + greeks
- Market closed: return chain structure only + Black-Scholes greeks (no IBKR pricing call)
**Impact:** Pre-market fetches complete in ~2s instead of ~8s with empty quote data.

---

## Files to Change (Implementation)

| File | Change |
|------|--------|
| `ib_worker.py` | Add `expires_at` to `_Request`; add heartbeat loop; set `RequestTimeout` |
| `ibkr_provider.py` | Set `ib.RequestTimeout` around `reqTickers`; add `_fetch_iv_bundle()` |
| `data_service.py` | Add in-flight dedup dict; call `_fetch_iv_bundle` in one submit |
| `app.py` | Remove legacy circuit breaker; remove `_get_chain_with_timeout`/`_fetch_chain_with_retry` |

---

*This is a research plan — not all items need to be done before paper trading.*
*P1 items (request expiry + RequestTimeout) should be done before the first live session.*
