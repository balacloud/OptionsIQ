"""
OptionsIQ — Black-Scholes Calculator

Used whenever IBKR's modelGreeks is None (thin contracts, delayed data,
mock/yfinance providers). Provides delta, gamma, theta, vega, and theoretical
option price using the standard Black-Scholes model.

All inputs and outputs are documented below. No silent defaults anywhere —
callers must pass all required fields explicitly.
"""

from __future__ import annotations

import math

try:
    from scipy.stats import norm as _norm
    _USE_SCIPY = True
except ImportError:
    _USE_SCIPY = False


def _cdf(x: float) -> float:
    """Cumulative normal distribution — scipy if available, else math.erf."""
    if _USE_SCIPY:
        return float(_norm.cdf(x))
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def _pdf(x: float) -> float:
    """Standard normal PDF."""
    if _USE_SCIPY:
        return float(_norm.pdf(x))
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def compute_greeks(
    S: float,      # Underlying price
    K: float,      # Strike price
    T: float,      # Time to expiry in years (DTE / 365)
    r: float,      # Risk-free rate as decimal (e.g. 0.053)
    sigma: float,  # Implied volatility as decimal (e.g. 0.22 for 22%)
    right: str,    # 'C' for call, 'P' for put
) -> dict | None:
    """
    Compute Black-Scholes greeks and theoretical price.

    Returns:
        dict with keys: delta, gamma, theta, vega, price
        All values are floats, using the trader convention for theta
        (negative = value lost per day).
        Returns None if inputs are invalid (T <= 0, sigma <= 0, S <= 0, K <= 0).
    """
    right = right.upper()
    if right not in ("C", "P"):
        return None
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return None

    try:
        sqrt_T  = math.sqrt(T)
        d1      = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2      = d1 - sigma * sqrt_T
        pdf_d1  = _pdf(d1)
        disc    = math.exp(-r * T)

        if right == "C":
            price = S * _cdf(d1) - K * disc * _cdf(d2)
            delta = _cdf(d1)
        else:
            price = K * disc * _cdf(-d2) - S * _cdf(-d1)
            delta = _cdf(d1) - 1.0  # negative for puts

        gamma  = pdf_d1 / (S * sigma * sqrt_T)
        vega   = S * pdf_d1 * sqrt_T / 100.0  # per 1% move in IV
        # Theta: daily decay (divide annual by 365)
        theta_annual = (
            -(S * pdf_d1 * sigma) / (2.0 * sqrt_T)
            - r * K * disc * (_cdf(d2) if right == "C" else _cdf(-d2))
        )
        theta = theta_annual / 365.0  # negative convention (daily loss)

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega":  round(vega, 4),
            "price": round(max(price, 0.0), 4),
        }

    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def fill_missing_greeks(contract: dict, S: float, r: float) -> dict:
    """
    Given a contract dict (from IBKR or yfinance), fill in any None greeks
    using Black-Scholes. Returns the same dict with greeks filled in-place.

    contract fields used:
        strike (float), expiry (str ISO date), right (str 'C'/'P'),
        impliedVol (float, decimal), dte (int days)
        delta, gamma, theta, vega (any may be None)

    Does NOT overwrite existing non-None values.
    """
    from constants import RISK_FREE_RATE

    # Only fill if at least one greek is missing
    needs_fill = any(contract.get(k) is None for k in ("delta", "gamma", "theta", "vega"))
    if not needs_fill:
        return contract

    K     = float(contract.get("strike", 0) or 0)
    dte   = int(contract.get("dte", 0) or 0)
    right = str(contract.get("right", "C") or "C").upper()
    iv    = contract.get("impliedVol")

    if iv is None or iv <= 0 or K <= 0 or dte <= 0 or S <= 0:
        return contract  # cannot compute — leave as None

    T      = dte / 365.0
    greeks = compute_greeks(S, K, T, r or RISK_FREE_RATE, float(iv), right)
    if greeks is None:
        return contract

    for key in ("delta", "gamma", "theta", "vega"):
        if contract.get(key) is None:
            contract[key] = greeks[key]

    # Also fill theoretical price if mid is zero/missing
    if not contract.get("mid") and greeks.get("price"):
        contract["bs_price"] = greeks["price"]

    return contract


def dte_to_years(dte: int) -> float:
    """Convert DTE (days to expiry) to years for Black-Scholes T input."""
    return max(dte, 0) / 365.0
