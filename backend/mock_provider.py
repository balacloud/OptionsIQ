"""
OptionsIQ — Mock Provider

Generates synthetic options data anchored to the real underlying price.
Used ONLY for pytest / CI testing — never for paper trades.

Key fix (KI-003): No longer hardcoded to AME. All prices are derived
from the actual ticker's underlying price (via yfinance if available,
else $100 default). Strikes and expiries are computed dynamically.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta


def _fetch_underlying_yf(ticker: str) -> float | None:
    """Try yfinance for underlying price. Returns None on any failure."""
    try:
        import yfinance as yf  # optional dependency
        info = yf.Ticker(ticker).fast_info
        price = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
        if price and float(price) > 0:
            return round(float(price), 2)
    except Exception:
        pass
    return None


def _next_friday_on_or_after(target: date) -> date:
    """Return the next Friday on or after target date."""
    days_ahead = (4 - target.weekday()) % 7  # 4 = Friday
    return target + timedelta(days=days_ahead)


def _mock_expiries(today: date, min_dte: int = 14) -> list[tuple[date, int]]:
    """
    Return two expiries: one in the 21-45 DTE range (seller sweet spot)
    and one in the 45-90 DTE range (buyer sweet spot).
    """
    expiries = []
    search_start = today + timedelta(days=min_dte)

    # Find first expiry at/above min_dte
    first = _next_friday_on_or_after(search_start)
    # Ensure it's a third-Friday-style monthly if possible, else use nearest
    expiries.append((first, (first - today).days))

    # Find second expiry ~45 days later
    second_target = today + timedelta(days=max(45, (first - today).days + 21))
    second = _next_friday_on_or_after(second_target)
    expiries.append((second, (second - today).days))

    return expiries


def _round_to_strike(price: float) -> float:
    """Round a price to the nearest sensible strike increment."""
    if price < 20:
        return round(price / 0.5) * 0.5
    if price < 50:
        return round(price / 1.0) * 1.0
    if price < 200:
        return round(price / 2.5) * 2.5
    if price < 500:
        return round(price / 5.0) * 5.0
    return round(price / 10.0) * 10.0


def _mock_strikes(underlying: float) -> list[float]:
    """
    Generate 9 strikes centered on the underlying price:
    [-12%, -8%, -4%, -2%, ATM, +2%, +4%, +8%, +12%]
    Rounded to sensible strike increments for the price level.
    """
    offsets = [-0.12, -0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08, 0.12]
    strikes = sorted({_round_to_strike(underlying * (1 + o)) for o in offsets})
    return strikes


def _build_option(
    ticker: str,
    underlying: float,
    expiry: date,
    strike: float,
    right: str,
    dte: int,
) -> dict:
    """Build one synthetic option contract using simplified BS-like math."""
    S = underlying
    K = strike
    T = max(dte, 1) / 365.0
    sigma = 0.22  # synthetic 22% IV baseline

    # Moneyness
    mny = (S - K) / S  # positive = ITM for calls
    dist_pct = abs(mny)

    # Synthetic IV smile: OTM options have higher IV
    iv = sigma + dist_pct * 0.12 + 0.005 * math.sin(dte / 15.0)
    iv = max(0.14, min(0.45, iv))

    # Intrinsic + time value
    intrinsic = max(0.0, S - K) if right == "C" else max(0.0, K - S)
    time_val = S * iv * math.sqrt(T) * 0.40
    mid_raw = intrinsic + time_val
    mid = max(0.05, mid_raw)

    # Bid/ask spread ~3% of mid
    spread = max(0.05, mid * 0.03)
    bid = round(max(0.01, mid - spread / 2), 2)
    ask = round(mid + spread / 2, 2)
    last = round((bid + ask) / 2, 2)

    # Delta (simplified N(d1) approximation)
    if T > 0 and iv > 0:
        d1 = (math.log(S / K) + (0.053 + 0.5 * iv ** 2) * T) / (iv * math.sqrt(T))
        nd1 = (1.0 + math.erf(d1 / math.sqrt(2))) / 2.0
        delta = nd1 if right == "C" else nd1 - 1.0
    else:
        delta = 0.5 if right == "C" else -0.5
    delta = round(max(-0.99, min(0.99, delta)), 3)

    # Gamma, theta, vega (reasonable approximations)
    gamma = round(max(0.001, 0.025 - dist_pct * 0.15 + 1 / (dte + 1) * 0.3), 4)
    theta = round(-max(0.01, (mid * 0.015 + 0.02) / math.sqrt(T + 0.01)), 3)
    vega  = round(max(0.01, S * math.sqrt(T) * 0.004), 3)

    oi  = int(max(500, 15000 - dist_pct * S * 80))
    vol = int(max(100, oi * 0.18))

    return {
        "symbol":       ticker.upper(),
        "expiry":       expiry.isoformat(),
        "dte":          dte,
        "right":        right,
        "strike":       float(strike),
        "bid":          bid,
        "ask":          ask,
        "last":         last,
        "mid":          round((bid + ask) / 2, 2),
        "delta":        delta,
        "gamma":        gamma,
        "theta":        theta,
        "vega":         vega,
        "impliedVol":   round(iv, 3),
        "optPrice":     last,
        "undPrice":     round(underlying, 2),
        "openInterest": oi,
        "volume":       vol,
    }


class MockProvider:
    """
    Dynamic mock provider. All data is synthetic but anchored to the
    actual underlying price of the requested ticker.

    Price resolution order:
        1. yfinance (if installed and online)
        2. $100.00 default (never AME's hardcoded $234)
    """

    DEFAULT_PRICE = 100.0  # neutral fallback — not tied to any specific ticker

    def is_connected(self) -> bool:
        return False

    def get_underlying_price(self, ticker: str) -> float:
        price = _fetch_underlying_yf(ticker)
        return price if price else self.DEFAULT_PRICE

    def get_historical_iv(self, ticker: str, days: int = 252) -> list[dict]:  # noqa: ARG002
        """Synthetic IV history — ticker-agnostic, used for IVR seeding in tests."""
        horizon = min(days, 252)
        today = date.today()
        series = []
        for i in range(horizon):
            d = today - timedelta(days=(horizon - 1 - i))
            base   = 0.215 + 0.035 * math.sin(i / 11.0)
            wobble = 0.008 * math.cos(i / 5.0)
            iv = max(0.12, min(0.45, base + wobble))
            series.append({"date": d.isoformat(), "iv": round(iv * 100, 2)})
        return series

    def get_ohlcv_daily(self, ticker: str, days: int = 60) -> list[dict]:
        """Synthetic OHLCV anchored to the ticker's actual underlying price."""
        underlying = self.get_underlying_price(ticker)
        today = date.today()
        bars = []
        price = underlying * 0.92  # start ~8% below current to show drift
        daily_drift = (underlying - price) / days

        for i in range(days):
            d = today - timedelta(days=(days - 1 - i))
            noise = price * 0.005 * math.sin(i / 3.1)
            close = max(1.0, price + daily_drift + noise)
            open_px = round(close - abs(noise) * 0.5, 2)
            high    = round(close + abs(noise) * 1.1, 2)
            low     = round(close - abs(noise) * 1.2, 2)
            volume  = int(1_000_000 + (i % 8) * 150_000)
            bars.append({
                "date":   d.isoformat(),
                "open":   open_px,
                "high":   high,
                "low":    low,
                "close":  round(close, 2),
                "volume": volume,
            })
            price = close
        return bars

    def get_options_chain(self, ticker: str) -> dict:
        """
        Generate a synthetic options chain anchored to the ticker's actual price.
        Strikes are computed as percentages of the underlying.
        Expiries are dynamically computed from today.
        """
        underlying = self.get_underlying_price(ticker)
        today = date.today()
        expiries = _mock_expiries(today)
        strikes  = _mock_strikes(underlying)

        contracts = []
        for expiry, dte in expiries:
            if dte <= 0:
                continue
            for strike in strikes:
                for right in ("C", "P"):
                    contracts.append(
                        _build_option(ticker, underlying, expiry, strike, right, dte)
                    )

        return {
            "ticker":           ticker.upper(),
            "underlying_price": round(underlying, 2),
            "asof":             datetime.utcnow().isoformat(timespec="seconds"),
            "contracts":        contracts,
        }
