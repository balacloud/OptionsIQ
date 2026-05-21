"""
scanner_service.py — Reads IBKR scanner data written by the /etf-scan Claude command.

The /etf-scan command parses an IBKR Market Screener screenshot and writes
backend/data/scanner_cache.json with live IV rank, IV/HV ratio, and option
volume data for all 15 ETFs. This module reads that cache and provides it to
best_setups_service.py to fill data gaps (KI-101: IV/HV null when chain IV missing).
"""
from __future__ import annotations

import json
import logging
import os
import socket
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "scanner_cache.json")


def get_scanner_data(ticker: str) -> dict:
    """Return scanner fields for ticker, or {} if cache is missing, expired, or lacks data.

    Fields returned (all may be None):
      ivr_52w         — 52-week IV rank (integer, e.g. 62)
      iv_hv_pct       — IV / Historical Vol % (float, e.g. 118.3)
      opt_volume      — today's options volume (integer)
      avg_opt_volume  — average daily options volume (integer)
      put_call_volume — put/call volume ratio (float)
      last_price      — underlying last price (float)
      change_pct      — today's price change % (float, signed)
    """
    try:
        with open(_CACHE_PATH) as f:
            cache = json.load(f)

        generated_at_str = cache.get("generated_at", "")
        generated_at = datetime.fromisoformat(generated_at_str)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)

        ttl_hours = cache.get("ttl_hours", 4)
        age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
        if age_hours > ttl_hours:
            logger.debug("scanner_cache expired (%.1fh old, TTL=%sh)", age_hours, ttl_hours)
            return {}

        return cache.get("etfs", {}).get(ticker, {})

    except FileNotFoundError:
        return {}
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("scanner_cache read error: %s", exc)
        return {}


def fetch_live_iv_hv_batch(tickers: list[str], ib_worker) -> dict[str, dict]:
    """
    Fetch IV + HV for ETFs via IBKR reqHistoricalData (Historical Data Farm).

    Uses OPTION_IMPLIED_VOLATILITY + HISTORICAL_VOLATILITY bar data — request-response,
    no streaming subscription required. Returns last daily bar close.
    Returns dict[ticker → {iv, hv, iv_hv_pct, iv_hv_ratio, opt_volume}].
    Returns {} gracefully when IB Gateway is offline or unavailable.
    """
    if ib_worker is None or ib_worker.provider is None:
        return {}
    if not tickers:
        return {}
    # Quick port check — avoid 12s of client-ID scan when IB Gateway is offline
    _host = os.getenv("IBKR_HOST", "127.0.0.1")
    _port = int(os.getenv("IBKR_PORT", "4001"))
    try:
        with socket.create_connection((_host, _port), timeout=0.5):
            pass
    except OSError:
        logger.debug("fetch_live_iv_hv_batch: IB Gateway not reachable — skipping")
        return {}
    logger.debug("fetch_live_iv_hv_batch: attempting IBKR histData batch for %d tickers", len(tickers))
    try:
        result = ib_worker.submit(
            ib_worker.provider.get_iv_hv_batch,
            tickers,
            timeout=90.0,  # reqHistoricalData: ~2s/ticker × 7 tickers × 2 calls + buffer
        )
        populated = {k: v for k, v in result.items() if v.get("iv") is not None}
        if populated:
            logger.info("fetch_live_iv_hv_batch: got IV for %d/%d tickers: %s",
                        len(populated), len(result), list(populated.keys()))
        else:
            logger.debug("fetch_live_iv_hv_batch: 0/%d tickers returned IV", len(result))
        return result
    except Exception as exc:
        logger.warning("fetch_live_iv_hv_batch failed: %s", exc)
        return {}


def scanner_cache_age_hours() -> float | None:
    """Return age of scanner cache in hours, or None if not present."""
    try:
        with open(_CACHE_PATH) as f:
            cache = json.load(f)
        generated_at_str = cache.get("generated_at", "")
        generated_at = datetime.fromisoformat(generated_at_str)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return None
