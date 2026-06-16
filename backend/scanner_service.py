"""
scanner_service.py — Reads scanner cache written by the /etf-scan Claude command (archived).

The /etf-scan command (archived Day 68) wrote backend/data/scanner_cache.json with
IV rank, IV/HV ratio, and option volume. This module reads that cache for
best_setups_service.py fallback (KI-101). Returns {} gracefully when cache absent.
"""
from __future__ import annotations

import json
import logging
import os
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
