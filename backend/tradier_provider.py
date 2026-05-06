"""
tradier_provider.py — Tradier brokerage REST API provider.

Cascade slot: after stale IBKR cache, before Alpaca.
With a live brokerage account the data is real-time (not delayed).

Endpoints used:
  GET /v1/markets/quotes              — underlying price
  GET /v1/markets/options/expirations — available expiry dates
  GET /v1/markets/options/chains      — option chain with greeks
  GET /v1/markets/history             — daily OHLCV (for EOD batch fallback)

API key: TRADIER_KEY env var.
Rate limit: 200 req/min on production API — well within our sequential usage.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

import requests as _requests

from constants import (
    DEFAULT_MAX_DTE,
    DEFAULT_MIN_DTE,
    FULL_MAX_EXPIRIES,
    FULL_MAX_STRIKES,
    FULL_STRIKE_WINDOW,
    SKEW_DTE_MAX,
    SKEW_DTE_MIN,
    SKEW_TARGET_DELTA,
    SMART_MAX_EXPIRIES,
    SMART_MAX_STRIKES,
    SMART_STRIKE_WINDOW,
)

logger = logging.getLogger(__name__)

_BASE = "https://api.tradier.com/v1"


class TradierNotAvailableError(Exception):
    pass


def _f(v, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except Exception:
        return default


class TradierProvider:
    def __init__(self, api_key: str) -> None:
        self._key = api_key
        self._session = _requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        })

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            r = self._session.get(f"{_BASE}{path}", params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except _requests.RequestException as exc:
            raise TradierNotAvailableError(f"Tradier API error: {exc}") from exc

    def get_underlying_price(self, ticker: str) -> float:
        data = self._get("/markets/quotes", {"symbols": ticker.upper()})
        quote = data.get("quotes", {}).get("quote", {})
        if isinstance(quote, list):
            quote = quote[0] if quote else {}
        bid = _f(quote.get("bid"))
        ask = _f(quote.get("ask"))
        last = _f(quote.get("last"))
        if bid > 0 and ask > 0:
            return round((bid + ask) / 2, 2)
        if last > 0:
            return round(last, 2)
        raise TradierNotAvailableError(f"No price for {ticker}")

    def get_options_chain(
        self,
        ticker: str,
        underlying_hint: float | None = None,
        direction: str | None = None,
        target_price: float | None = None,
        chain_profile: str | None = None,
        min_dte: int | None = None,
    ) -> dict:
        symbol = ticker.upper()
        profile = (chain_profile or "smart").strip().lower()
        smart = profile == "smart"
        max_expiries = SMART_MAX_EXPIRIES if smart else FULL_MAX_EXPIRIES
        max_strikes = SMART_MAX_STRIKES if smart else FULL_MAX_STRIKES
        strike_window = SMART_STRIKE_WINDOW if smart else FULL_STRIKE_WINDOW
        min_dte_val = int(min_dte if min_dte is not None else DEFAULT_MIN_DTE)

        underlying = (
            float(underlying_hint)
            if underlying_hint and float(underlying_hint) > 0
            else self.get_underlying_price(symbol)
        )

        # Expirations
        exp_data = self._get("/markets/options/expirations", {
            "symbol": symbol, "includeAllRoots": "false",
        })
        exp_dates = (exp_data.get("expirations") or {}).get("date") or []
        if not exp_dates:
            raise TradierNotAvailableError(f"No expirations for {symbol}")

        today = date.today()
        valid: list[tuple[str, int]] = []
        for d in exp_dates:
            try:
                dte = (datetime.strptime(d, "%Y-%m-%d").date() - today).days
                if min_dte_val <= dte <= DEFAULT_MAX_DTE:
                    valid.append((d, dte))
            except Exception:
                continue

        if not valid:
            raise TradierNotAvailableError(
                f"No expiries in {min_dte_val}-{DEFAULT_MAX_DTE} DTE for {symbol}"
            )

        selected = valid[:max_expiries]

        # Strike window centered on target or underlying
        center = float(target_price) if target_price and float(target_price) > 0 else underlying
        low = center * (1.0 - strike_window)
        high = center * (1.0 + strike_window)

        # Which sides to fetch
        fetch_calls = direction not in {"buy_put", "sell_put"}
        fetch_puts = direction not in {"buy_call", "sell_call"}
        if not fetch_calls and not fetch_puts:
            fetch_calls = fetch_puts = True

        per_expiry: dict[str, list[dict]] = defaultdict(list)
        asof = datetime.utcnow().isoformat(timespec="seconds")

        for exp_str, dte in selected:
            chain_data = self._get("/markets/options/chains", {
                "symbol": symbol, "expiration": exp_str, "greeks": "true",
            })
            options = (chain_data.get("options") or {}).get("option") or []
            if isinstance(options, dict):
                options = [options]

            for opt in options:
                opt_type = opt.get("option_type", "")
                if opt_type == "call" and not fetch_calls:
                    continue
                if opt_type == "put" and not fetch_puts:
                    continue

                strike = _f(opt.get("strike"))
                if strike <= 0 or strike < low or strike > high:
                    continue

                # Direction-aware OTM filter (mirrors KI-067 fix in ibkr_provider)
                if direction == "sell_put" and strike > underlying:
                    continue  # exclude ITM puts
                if direction == "sell_call" and strike < underlying:
                    continue  # exclude ITM calls

                right = "C" if opt_type == "call" else "P"
                bid = _f(opt.get("bid")); bid = bid if bid > 0 else None
                ask = _f(opt.get("ask")); ask = ask if ask > 0 else None
                last = _f(opt.get("last")); last = last if last > 0 else None
                mid = (
                    round((bid + ask) / 2, 4)
                    if bid is not None and ask is not None
                    else (last or 0.0)
                )

                g = opt.get("greeks") or {}
                # smv_vol = smoothed surface vol — best for IVR; fall back to mid_iv
                iv = _f(g.get("smv_vol")) or _f(g.get("mid_iv")) or None
                if iv is not None and iv <= 0:
                    iv = None

                per_expiry[exp_str].append({
                    "symbol": symbol,
                    "expiry": exp_str,
                    "dte": dte,
                    "right": right,
                    "strike": strike,
                    "bid": bid,
                    "ask": ask,
                    "last": last,
                    "mid": mid,
                    "delta": float(g["delta"]) if g.get("delta") is not None else None,
                    "gamma": float(g["gamma"]) if g.get("gamma") is not None else None,
                    "theta": float(g["theta"]) if g.get("theta") is not None else None,
                    "vega": float(g["vega"]) if g.get("vega") is not None else None,
                    "impliedVol": iv,
                    "optPrice": mid,
                    "undPrice": underlying,
                    "openInterest": int(opt.get("open_interest") or 0),
                    "volume": int(opt.get("volume") or 0),
                })

        # Cap to max_strikes per expiry (proximity sort)
        contracts: list[dict] = []
        for exp_str, _ in selected:
            exp_contracts = per_expiry.get(exp_str, [])
            exp_contracts.sort(key=lambda c: abs(c["strike"] - underlying))
            contracts.extend(exp_contracts[:max_strikes])

        if not contracts:
            raise TradierNotAvailableError(f"No contracts in window for {symbol}")

        logger.info("Tradier chain: %s — %d contracts (%s)", symbol, len(contracts), profile)
        return {
            "ticker": symbol,
            "underlying_price": underlying,
            "asof": asof,
            "contracts": contracts,
        }

    def compute_skew(self, ticker: str, underlying: float | None = None) -> dict | None:
        """
        30-delta IV skew: put_iv_30d - call_iv_30d from the nearest SKEW_DTE_MIN–SKEW_DTE_MAX expiry.

        Positive skew = puts more expensive than calls = market pricing in downside tail risk.
        Negative skew = calls more expensive (rare; seen in meme stocks or supply squeezes).

        Returns None if no valid expiry or insufficient delta coverage.
        Makes 2 API calls (expirations + single chain fetch).
        """
        symbol = ticker.upper()
        if underlying is None:
            underlying = self.get_underlying_price(symbol)

        exp_data = self._get("/markets/options/expirations", {
            "symbol": symbol, "includeAllRoots": "false",
        })
        exp_dates = (exp_data.get("expirations") or {}).get("date") or []

        today = date.today()
        target_exp: str | None = None
        target_dte: int | None = None
        for d in exp_dates:
            try:
                dte = (datetime.strptime(d, "%Y-%m-%d").date() - today).days
                if SKEW_DTE_MIN <= dte <= SKEW_DTE_MAX:
                    target_exp = d
                    target_dte = dte
                    break
            except Exception:
                continue

        if not target_exp:
            logger.debug("Skew: no expiry in %d-%d DTE for %s", SKEW_DTE_MIN, SKEW_DTE_MAX, symbol)
            return None

        chain_data = self._get("/markets/options/chains", {
            "symbol": symbol, "expiration": target_exp, "greeks": "true",
        })
        options = (chain_data.get("options") or {}).get("option") or []
        if isinstance(options, dict):
            options = [options]

        calls: list[dict] = []
        puts: list[dict] = []
        for opt in options:
            g = opt.get("greeks") or {}
            if g.get("delta") is None:
                continue
            try:
                delta = float(g["delta"])
            except Exception:
                continue
            iv_raw = _f(g.get("smv_vol")) or _f(g.get("mid_iv"))
            if iv_raw <= 0:
                continue
            strike = _f(opt.get("strike"))
            if strike <= 0:
                continue
            entry = {"strike": strike, "delta": delta, "iv": round(iv_raw * 100, 2)}
            if opt.get("option_type") == "call":
                calls.append(entry)
            elif opt.get("option_type") == "put":
                puts.append(entry)

        if not calls or not puts:
            return None

        # Nearest to 30-delta: calls have positive delta (~0.30), puts negative (~-0.30)
        best_call = min(calls, key=lambda c: abs(c["delta"] - SKEW_TARGET_DELTA))
        best_put = min(puts, key=lambda c: abs(c["delta"] - (-SKEW_TARGET_DELTA)))

        skew = round(best_put["iv"] - best_call["iv"], 2)
        logger.info(
            "Skew %s: put_iv=%.1f%% (Δ%.2f @ %.2f) — call_iv=%.1f%% (Δ%.2f @ %.2f) → skew=%.2f%%",
            symbol, best_put["iv"], best_put["delta"], best_put["strike"],
            best_call["iv"], best_call["delta"], best_call["strike"], skew,
        )
        return {
            "skew": skew,
            "put_iv_30d": best_put["iv"],
            "call_iv_30d": best_call["iv"],
            "put_delta": round(best_put["delta"], 3),
            "call_delta": round(best_call["delta"], 3),
            "put_strike": best_put["strike"],
            "call_strike": best_call["strike"],
            "expiry": target_exp,
            "dte": target_dte,
        }

    def get_ohlcv_daily(self, ticker: str, days: int = 90) -> list[dict]:
        """Daily OHLCV bars via Tradier history. Used as EOD batch fallback."""
        symbol = ticker.upper()
        end = date.today()
        start = end - timedelta(days=days + 14)  # buffer for weekends/holidays
        data = self._get("/markets/history", {
            "symbol": symbol,
            "interval": "daily",
            "start": start.isoformat(),
            "end": end.isoformat(),
        })
        history = (data.get("history") or {})
        days_data = history.get("day") or []
        if isinstance(days_data, dict):
            days_data = [days_data]

        out: list[dict] = []
        for d in days_data[-days:]:
            try:
                out.append({
                    "date": d["date"],
                    "open": float(d["open"]),
                    "high": float(d["high"]),
                    "low": float(d["low"]),
                    "close": float(d["close"]),
                    "volume": int(d.get("volume") or 0),
                })
            except Exception:
                continue
        return out
