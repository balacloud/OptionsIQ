"""
marketdata_provider.py — Supplemental OI + volume lookup via MarketData.app REST API.

Used as a targeted supplement to IBKR: IBKR provides live greeks and pricing,
MarketData.app fills the two fields IBKR cannot surface (open_interest, volume).

Integration point: analyze_service.py calls get_oi_volume() after the top strategy
is selected, before gate_payload is built. Non-blocking — if this call fails or
times out, the caller falls back to OI=0 (existing behaviour).

API docs: https://api.marketdata.app/v1/options/chain/{ticker}/
"""
from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

_BASE = os.getenv("MARKET_DATA_OPTIONS_EP", "https://api.marketdata.app/v1/options/")
_KEY = os.getenv("MARKET_DATA_KEY", "")
_TIMEOUT = 5.0  # seconds — must not block the Flask request for long


class MarketDataProvider:
    """Thin REST wrapper around the MarketData.app options chain endpoint."""

    def __init__(self) -> None:
        if not _KEY:
            logger.warning("MARKET_DATA_KEY not set — MarketDataProvider will return None for all lookups")
        self._headers = {"Authorization": f"Token {_KEY}"} if _KEY else {}

    def available(self) -> bool:
        return bool(_KEY)

    def get_oi_volume(
        self,
        ticker: str,
        strike: float,
        side: str,           # "call" or "put"
        dte_target: int,
    ) -> dict | None:
        """
        Returns {open_interest, volume} for the closest matching contract, or None.

        Queries a narrow DTE window (±3 days) around dte_target to avoid pulling
        a large chain payload. Only the first matched contract is used.
        """
        if not _KEY:
            return None
        try:
            url = f"{_BASE}chain/{ticker}/"
            params = {
                "strike": strike,
                "side": side,
                "minDte": max(0, dte_target - 3),
                "maxDte": dte_target + 3,
                "limit": 1,
            }
            resp = requests.get(url, params=params, headers=self._headers, timeout=_TIMEOUT)
            if not resp.ok:
                logger.warning("MarketData.app %s/%s: HTTP %s", ticker, side, resp.status_code)
                return None
            data = resp.json()
            if data.get("s") != "ok":
                logger.warning("MarketData.app %s/%s: s=%s err=%s",
                               ticker, side, data.get("s"), data.get("errmsg", ""))
                return None
            oi_list = data.get("openInterest") or []
            vol_list = data.get("volume") or []
            if not oi_list:
                return None
            oi = oi_list[0]
            vol = vol_list[0] if vol_list else 0
            if oi is None:
                return None
            logger.info("MarketData.app %s %s $%.2f ~%dd: OI=%s vol=%s", ticker, side, strike, dte_target, oi, vol)
            return {"open_interest": float(oi), "volume": float(vol) if vol is not None else 0.0}
        except requests.exceptions.Timeout:
            logger.warning("MarketData.app timeout for %s", ticker)
            return None
        except Exception as exc:
            logger.warning("MarketData.app lookup failed for %s: %s", ticker, exc)
            return None
