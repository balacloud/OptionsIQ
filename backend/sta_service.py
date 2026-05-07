"""
sta_service.py — STA integration: fetch swing data + SPY metrics for a ticker.

Extracted from app.py (KI-086) so the /api/integrate/sta-fetch route stays thin.
"""
from __future__ import annotations

import logging

import requests
import yfinance as yf

from constants import STA_BASE_URL

logger = logging.getLogger(__name__)


def fetch_sta_swing_data(symbol: str) -> dict:
    """
    Fetch swing data from STA + SPY regime metrics.
    Returns a flat dict ready for jsonify(). On STA offline returns status='offline'.
    """
    timeout = 3.0
    try:
        sr       = requests.get(f"{STA_BASE_URL}/api/sr/{symbol}",        timeout=timeout).json()
        stock    = requests.get(f"{STA_BASE_URL}/api/stock/{symbol}",     timeout=timeout).json()
        patterns = requests.get(f"{STA_BASE_URL}/api/patterns/{symbol}",  timeout=timeout).json()
        context  = requests.get(f"{STA_BASE_URL}/api/context/SPY",        timeout=timeout).json()
        earnings = requests.get(f"{STA_BASE_URL}/api/earnings/{symbol}",  timeout=timeout).json()
    except Exception as exc:
        logger.warning("STA fetch failed for %s: %s", symbol, exc)
        return {
            "status": "offline",
            "source": "manual",
            "message": f"STA not reachable at {STA_BASE_URL} — use Manual mode",
        }

    meta = sr.get("meta", {})
    vcp  = patterns.get("patterns", {}).get("vcp", {})

    fomc_days = None
    for card in context.get("cycles", {}).get("cards", []):
        if "FOMC" in card.get("name", ""):
            fomc_days = card.get("raw_value")
            break

    viable       = meta.get("tradeViability", {}).get("viable", "")
    swing_signal = "BUY" if viable == "YES" else "SELL"

    support_levels = sr.get("support", [])
    s1_support     = support_levels[-1] if support_levels else None

    spy_above_200sma = True
    spy_5day_return  = None
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y", interval="1d")
        if not spy_hist.empty and len(spy_hist) >= 200:
            latest_close     = float(spy_hist["Close"].iloc[-1])
            sma200           = float(spy_hist["Close"].iloc[-200:].mean())
            spy_above_200sma = latest_close > sma200
            if len(spy_hist) >= 6:
                five_day_ago    = float(spy_hist["Close"].iloc[-6])
                spy_5day_return = round((latest_close - five_day_ago) / five_day_ago * 100, 2)
    except Exception as exc:
        logger.warning("SPY regime fetch failed: %s", exc)

    return {
        "status":            "ok",
        "source":            "sta_live",
        "ticker":            symbol,
        "swing_signal":      swing_signal,
        "entry_pullback":    sr.get("suggestedEntry"),
        "entry_momentum":    stock.get("currentPrice"),
        "stop_loss":         sr.get("suggestedStop"),
        "target1":           sr.get("suggestedTarget"),
        "target2":           None,
        "risk_reward":       sr.get("riskReward"),
        "vcp_pivot":         vcp.get("pivot_price"),
        "vcp_confidence":    vcp.get("confidence"),
        "adx":               meta.get("adx", {}).get("adx"),
        "last_close":        stock.get("currentPrice"),
        "s1_support":        s1_support,
        "spy_above_200sma":  spy_above_200sma,
        "spy_5day_return":   spy_5day_return,
        "earnings_days_away": earnings.get("days_until"),
        "pattern":           patterns.get("pattern"),
        "fomc_days_away":    fomc_days,
    }
