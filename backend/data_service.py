"""
OptionsIQ — Data Service

Provider selection: IBKR (via IBWorker) → Persistent cache → Alpaca → yfinance → Mock
Persistent SQLite chain cache survives Flask restarts (TTL per constants.py).
Circuit breaker: 2 consecutive IBKR failures → 45s cooldown.

Provider quality labels returned:
  "ibkr_live"   — fresh from IB Gateway (market open, live bid/ask/greeks)
  "ibkr_closed" — IBKR connected but market closed; BS-computed greeks, no bid/ask/OI
  "ibkr_cache"  — within TTL window (background refresh triggered)
  "ibkr_stale"  — beyond TTL but IBKR unavailable (background refresh triggered)
  "alpaca"      — Alpaca REST fallback (15-min delayed, real greeks + OI)
  "yfinance"    — yfinance fallback
  "mock"        — dev/CI only
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from copy import deepcopy
from pathlib import Path

from constants import (
    CHAIN_CACHE_TTL_SEC,
    DEFAULT_MIN_DTE,
    IB_CB_COOLDOWN_SEC,
    IB_CB_FAILURE_THRESHOLD,
    IB_WORKER_TIMEOUT_FULL,
    IB_WORKER_TIMEOUT_SMART,
)

logger = logging.getLogger(__name__)


class DataService:
    """
    Central data access layer. All Flask routes should use this class —
    never call IBWorker or providers directly.
    """

    def __init__(
        self,
        ib_worker=None,
        yf_provider=None,
        mock_provider=None,
        alpaca_provider=None,
        db_path: str | None = None,
    ) -> None:
        self.ib_worker = ib_worker
        self.yf_provider = yf_provider
        self.mock_provider = mock_provider
        self.alpaca_provider = alpaca_provider

        base = Path(__file__).resolve().parent
        self._db_path = Path(db_path) if db_path else base / "data" / "chain_cache.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        # Circuit breaker state
        self._cb_failures = 0
        self._cb_open_until = 0.0
        self._cb_lock = threading.Lock()

        # Background refresh dedup
        self._refresh_lock = threading.Lock()
        self._refreshing: set[str] = set()

    # ─── DB init ─────────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chain_cache (
                  cache_key TEXT PRIMARY KEY,
                  chain_json TEXT NOT NULL,
                  saved_at   REAL NOT NULL,
                  expires_at REAL NOT NULL
                )
                """
            )

    # ─── Circuit breaker ─────────────────────────────────────────────────────

    def _cb_allowed(self) -> bool:
        with self._cb_lock:
            return time.time() >= self._cb_open_until

    def _cb_record(self, success: bool) -> None:
        with self._cb_lock:
            if success:
                self._cb_failures = 0
                self._cb_open_until = 0.0
                return
            self._cb_failures += 1
            if self._cb_failures >= IB_CB_FAILURE_THRESHOLD:
                self._cb_open_until = time.time() + IB_CB_COOLDOWN_SEC
                logger.warning(
                    "IB circuit OPEN for %ss after %s failures",
                    IB_CB_COOLDOWN_SEC,
                    self._cb_failures,
                )

    def cb_status(self) -> dict:
        with self._cb_lock:
            open_until = self._cb_open_until
            failures = self._cb_failures
        open_now = time.time() < open_until
        return {
            "open": open_now,
            "failures": failures,
            "open_until": open_until if open_now else None,
            "seconds_remaining": max(0.0, round(open_until - time.time(), 1)) if open_now else 0.0,
        }

    # ─── Persistent chain cache ───────────────────────────────────────────────

    @staticmethod
    def _cache_key(ticker: str, profile: str, direction: str | None) -> str:
        p = (profile or "smart").strip().lower()
        d = (direction or "all").strip().lower()
        return f"{ticker.upper()}::{p}::{d}"

    def _cache_set(
        self,
        ticker: str,
        chain: dict,
        profile: str = "smart",
        direction: str | None = None,
    ) -> None:
        key = self._cache_key(ticker, profile, direction)
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO chain_cache (cache_key, chain_json, saved_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                  chain_json = excluded.chain_json,
                  saved_at   = excluded.saved_at,
                  expires_at = excluded.expires_at
                """,
                (key, json.dumps(chain), now, now + CHAIN_CACHE_TTL_SEC),
            )

    def _cache_get(
        self,
        ticker: str,
        profile: str = "smart",
        direction: str | None = None,
        allow_stale: bool = False,
    ) -> dict | None:
        key = self._cache_key(ticker, profile, direction)
        now = time.time()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT chain_json, expires_at FROM chain_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        if (not allow_stale) and now > float(row["expires_at"]):
            return None
        try:
            return json.loads(row["chain_json"])
        except Exception as exc:
            logger.warning("Cache JSON decode error for key %s: %s", key, exc)
            return None

    def evict_expired_cache(self) -> int:
        """Delete expired cache entries. Returns number deleted."""
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM chain_cache WHERE expires_at < ?", (time.time(),)
            )
            return cur.rowcount

    # ─── Timeout helper ───────────────────────────────────────────────────────

    @staticmethod
    def _timeout(profile: str) -> float:
        return float(
            IB_WORKER_TIMEOUT_FULL
            if (profile or "smart").lower() == "full"
            else IB_WORKER_TIMEOUT_SMART
        )

    # ─── Background refresh ───────────────────────────────────────────────────

    def _refresh_async(
        self,
        ticker: str,
        profile: str,
        direction: str | None,
        underlying_hint: float | None,
        target_price: float | None,
        min_dte: int,
    ) -> None:
        key = self._cache_key(ticker, profile, direction)
        with self._refresh_lock:
            if key in self._refreshing:
                return
            self._refreshing.add(key)

        def _run() -> None:
            try:
                if self.ib_worker is None or self.ib_worker.provider is None:
                    return
                if not self._cb_allowed():
                    return
                chain = self.ib_worker.submit(
                    self.ib_worker.provider.get_options_chain,
                    ticker,
                    underlying_hint,
                    direction,
                    target_price,
                    profile,
                    min_dte,
                    timeout=self._timeout(profile),
                )
                self._cache_set(ticker, chain, profile, direction)
                self._cb_record(success=True)
                logger.debug("Background chain refresh done for %s", key)
            except Exception as exc:
                logger.debug("Background chain refresh skipped for %s: %s", key, exc)
            finally:
                with self._refresh_lock:
                    self._refreshing.discard(key)

        threading.Thread(target=_run, daemon=True).start()

    def get_cache_stats(self, tickers: list[str]) -> dict:
        """Return chain cache age/freshness per ticker for data provenance."""
        from datetime import datetime as _dt
        now = time.time()
        result = {}
        with self._conn() as conn:
            for ticker in tickers:
                rows = conn.execute(
                    "SELECT cache_key, saved_at, expires_at FROM chain_cache WHERE cache_key LIKE ?",
                    (f"{ticker.upper()}::%",),
                ).fetchall()
                if not rows:
                    result[ticker] = {
                        "status": "missing", "saved_at": None,
                        "age_minutes": None, "expires_in_minutes": None, "entries": 0,
                    }
                else:
                    latest = max(rows, key=lambda r: r["saved_at"])
                    age_sec = now - latest["saved_at"]
                    expires_in = latest["expires_at"] - now
                    result[ticker] = {
                        "status": "fresh" if expires_in > 0 else "stale",
                        "saved_at": _dt.utcfromtimestamp(latest["saved_at"]).isoformat(timespec="seconds"),
                        "age_minutes": round(age_sec / 60, 1),
                        "expires_in_minutes": round(max(0.0, expires_in) / 60, 1),
                        "entries": len(rows),
                    }
        return result

    # ─── Public API ───────────────────────────────────────────────────────────

    def get_chain(
        self,
        ticker: str,
        profile: str = "smart",
        direction: str | None = None,
        underlying_hint: float | None = None,
        target_price: float | None = None,
        min_dte: int | None = None,
    ) -> tuple[dict, str]:
        """
        Returns (chain_dict, data_source).
        data_source: "ibkr_live" | "ibkr_closed" | "ibkr_cache" | "ibkr_stale" | "yfinance" | "mock"
        """
        ticker = ticker.upper()
        min_dte_val = int(min_dte if min_dte is not None else DEFAULT_MIN_DTE)

        # 1. Fresh cache — serve immediately + trigger background refresh
        cached = self._cache_get(ticker, profile, direction)
        if cached is not None:
            self._refresh_async(
                ticker, profile, direction, underlying_hint, target_price, min_dte_val
            )
            return deepcopy(cached), "ibkr_cache"

        # 2. IBKR live via IBWorker
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
                        # BS-computed greeks — don't store in live-quote cache
                        return chain, "ibkr_closed"
                    self._cache_set(ticker, chain, profile, direction)
                    return chain, "ibkr_live"
                except TimeoutError:
                    logger.warning("IBKR chain timeout for %s", ticker)
                    self._cb_record(success=False)
                except Exception as exc:
                    logger.warning("IBKR chain error for %s: %s", ticker, exc)
                    self._cb_record(success=False)

        # 3. Stale cache (IBKR was down)
        stale = self._cache_get(ticker, profile, direction, allow_stale=True)
        if stale is not None:
            self._refresh_async(
                ticker, profile, direction, underlying_hint, target_price, min_dte_val
            )
            return deepcopy(stale), "ibkr_stale"

        # 4. Alpaca (15-min delayed REST, real greeks + OI — better than yfinance)
        if self.alpaca_provider is not None:
            try:
                chain = self.alpaca_provider.get_options_chain(
                    ticker,
                    underlying_hint,
                    direction,
                    target_price,
                    profile,
                    min_dte_val,
                )
                return chain, "alpaca"
            except Exception as exc:
                logger.warning("Alpaca chain error for %s: %s", ticker, exc)

        # 5. yfinance
        if self.yf_provider is not None:
            try:
                chain = self.yf_provider.get_options_chain(
                    ticker,
                    underlying_hint,
                    direction,
                    target_price,
                    profile,
                    min_dte_val,
                )
                return chain, "yfinance"
            except Exception as exc:
                logger.warning("yfinance chain error for %s: %s", ticker, exc)

        # 6. Mock (last resort — never for live paper trades)
        if self.mock_provider is not None:
            chain = self.mock_provider.get_options_chain(ticker)
            return chain, "mock"

        raise RuntimeError(f"No chain data available for {ticker}")

    def get_underlying_price(self, ticker: str, hint: float | None = None) -> float:
        """Returns underlying price from best available source."""
        ticker = ticker.upper()
        if hint and float(hint) > 0:
            return float(hint)

        # IBKR
        if (
            self.ib_worker is not None
            and self.ib_worker.provider is not None
            and self._cb_allowed()
        ):
            try:
                return self.ib_worker.submit(
                    self.ib_worker.provider.get_underlying_price,
                    ticker,
                    timeout=10.0,
                )
            except Exception as exc:
                logger.warning("IBKR price error for %s: %s", ticker, exc)

        # yfinance
        if self.yf_provider is not None:
            try:
                return self.yf_provider.get_underlying_price(ticker)
            except Exception as exc:
                logger.warning("yfinance price error for %s: %s", ticker, exc)

        # Mock
        if self.mock_provider is not None:
            return self.mock_provider.get_underlying_price(ticker)

        raise RuntimeError(f"Cannot get underlying price for {ticker}")

    def quality_label(self, data_source: str, chain: dict) -> str:
        """Maps (data_source, chain) → human-readable quality label for frontend."""
        if data_source == "mock":
            return "mock"
        if data_source in ("ibkr_stale",):
            return "stale"
        if data_source == "alpaca":
            return "delayed"
        if data_source == "yfinance":
            return "yfinance"
        if data_source == "ibkr_cache":
            return "cached"
        if data_source == "ibkr_closed":
            return "closed"
        # ibkr_live — check completeness
        contracts = chain.get("contracts") or []
        if not contracts:
            return "partial"
        total = len(contracts)
        ok_quote = sum(1 for c in contracts if c.get("bid") and c.get("ask"))
        ok_greeks = sum(1 for c in contracts if c.get("delta") is not None)
        if ok_quote / total >= 0.7 and ok_greeks / total >= 0.7:
            return "live"
        if ok_greeks / total >= 0.4:
            return "degraded"
        return "partial"

    def ibkr_status(self) -> dict:
        """Returns IBKR connection status for /api/health."""
        if self.ib_worker is None:
            return {"connected": False, "error": "IBWorker not initialised"}
        error = self.ib_worker.init_error
        connected = self.ib_worker.is_connected()
        return {
            "connected": connected,
            "error": error,
            "circuit_breaker": self.cb_status(),
        }
