"""
OptionsIQ — yfinance Provider

Middle-tier data provider. Used when IBKR is unavailable.
Provides: underlying price, options chain (with BS-computed greeks), IV history, OHLCV.

Greek values are computed via Black-Scholes (bs_calculator) since yfinance
does not stream live greeks. Quality label: "yfinance".
"""
from __future__ import annotations

import math
from datetime import date, datetime

try:
    import numpy as np
    _NP_AVAILABLE = True
except ImportError:
    _NP_AVAILABLE = False

try:
    import yfinance as yf
    _YF_AVAILABLE = True
except ImportError:
    _YF_AVAILABLE = False

from bs_calculator import fill_missing_greeks
from constants import (
    DEFAULT_MAX_DTE,
    DEFAULT_MIN_DTE,
    FULL_MAX_EXPIRIES,
    FULL_MAX_STRIKES,
    FULL_STRIKE_WINDOW,
    RISK_FREE_RATE,
    SMART_MAX_EXPIRIES,
    SMART_MAX_STRIKES,
    SMART_STRIKE_WINDOW,
)


class YFinanceNotAvailableError(RuntimeError):
    pass


class YFinanceProvider:
    """yfinance-based fallback provider. Matches IBKRProvider public interface."""

    def get_underlying_price(self, ticker: str) -> float:
        if not _YF_AVAILABLE:
            raise YFinanceNotAvailableError("yfinance not installed")
        try:
            tk = yf.Ticker(ticker.upper())
            info = tk.fast_info
            price = (
                getattr(info, "last_price", None)
                or getattr(info, "regularMarketPrice", None)
            )
            if price and float(price) > 0:
                return round(float(price), 2)
            raise YFinanceNotAvailableError(f"No price available for {ticker}")
        except YFinanceNotAvailableError:
            raise
        except Exception as exc:
            raise YFinanceNotAvailableError(f"yfinance price error: {exc}") from exc

    def get_options_chain(
        self,
        ticker: str,
        underlying_hint: float | None = None,
        direction: str | None = None,
        target_price: float | None = None,
        chain_profile: str | None = None,
        min_dte: int | None = None,
    ) -> dict:
        if not _YF_AVAILABLE:
            raise YFinanceNotAvailableError("yfinance not installed")
        try:
            symbol = ticker.upper()
            tk = yf.Ticker(symbol)

            underlying = (
                float(underlying_hint)
                if underlying_hint and underlying_hint > 0
                else self.get_underlying_price(symbol)
            )

            profile = (chain_profile or "smart").strip().lower()
            smart = profile == "smart"
            max_expiries = SMART_MAX_EXPIRIES if smart else FULL_MAX_EXPIRIES
            max_strikes = SMART_MAX_STRIKES if smart else FULL_MAX_STRIKES
            strike_window = SMART_STRIKE_WINDOW if smart else FULL_STRIKE_WINDOW
            min_dte_val = int(min_dte if min_dte is not None else DEFAULT_MIN_DTE)
            # yfinance options expire further out; cap at 90 for smart, full range otherwise
            max_dte_val = 90 if smart else DEFAULT_MAX_DTE

            today = date.today()
            expiries_raw = tk.options  # tuple of "YYYY-MM-DD" strings
            if not expiries_raw:
                raise YFinanceNotAvailableError(f"No options data for {symbol}")

            valid_expiries: list[tuple[str, int]] = []
            for exp_str in expiries_raw:
                try:
                    d = datetime.strptime(exp_str, "%Y-%m-%d").date()
                    dte = (d - today).days
                    if min_dte_val <= dte <= max_dte_val:
                        valid_expiries.append((exp_str, dte))
                except Exception:
                    continue
            valid_expiries.sort(key=lambda x: x[1])
            selected_expiries = valid_expiries[:max_expiries]

            if not selected_expiries:
                raise YFinanceNotAvailableError(
                    f"No expiries in {min_dte_val}-{max_dte_val} DTE range for {symbol}"
                )

            center = float(target_price) if target_price and target_price > 0 else underlying
            low = center * (1.0 - strike_window)
            high = center * (1.0 + strike_window)

            # Which option sides to fetch based on direction
            fetch_calls = direction not in {"buy_put", "sell_put"}
            fetch_puts = direction not in {"buy_call", "sell_call"}
            if not fetch_calls and not fetch_puts:
                fetch_calls = fetch_puts = True

            contracts: list[dict] = []
            asof = datetime.utcnow().isoformat(timespec="seconds")

            for exp_str, dte in selected_expiries:
                opt = tk.option_chain(exp_str)
                sides = []
                if fetch_calls:
                    sides.append(("C", opt.calls))
                if fetch_puts:
                    sides.append(("P", opt.puts))

                for right_char, df in sides:
                    if df is None or df.empty:
                        continue
                    mask = (df["strike"] >= low) & (df["strike"] <= high)
                    filtered = df[mask].copy()
                    if filtered.empty:
                        continue
                    filtered["_dist"] = (filtered["strike"] - center).abs()
                    filtered = filtered.sort_values("_dist").head(max_strikes)

                    for _, row in filtered.iterrows():
                        strike = float(row["strike"])
                        bid_raw = row.get("bid", 0) or 0
                        ask_raw = row.get("ask", 0) or 0
                        last_raw = row.get("lastPrice", 0) or 0
                        bid = float(bid_raw) if float(bid_raw) > 0 else None
                        ask = float(ask_raw) if float(ask_raw) > 0 else None
                        last = float(last_raw) if float(last_raw) > 0 else None
                        mid = (
                            round((bid + ask) / 2, 4)
                            if bid is not None and ask is not None
                            else (last or 0.0)
                        )
                        iv_raw = row.get("impliedVolatility", 0) or 0
                        iv = float(iv_raw) if float(iv_raw) > 0 else None
                        oi = int(row.get("openInterest", 0) or 0)
                        vol = int(row.get("volume", 0) or 0)

                        contract: dict = {
                            "symbol": symbol,
                            "expiry": exp_str,
                            "dte": dte,
                            "right": right_char,
                            "strike": strike,
                            "bid": bid,
                            "ask": ask,
                            "last": last,
                            "mid": mid,
                            "delta": None,
                            "gamma": None,
                            "theta": None,
                            "vega": None,
                            "impliedVol": iv,
                            "optPrice": mid,
                            "undPrice": underlying,
                            "openInterest": oi,
                            "volume": vol,
                        }
                        fill_missing_greeks(contract, underlying, RISK_FREE_RATE)
                        contracts.append(contract)

            return {
                "ticker": symbol,
                "underlying_price": underlying,
                "asof": asof,
                "contracts": contracts,
            }

        except YFinanceNotAvailableError:
            raise
        except Exception as exc:
            raise YFinanceNotAvailableError(f"yfinance chain error: {exc}") from exc

    def get_historical_iv(self, ticker: str, days: int = 252) -> list[dict]:
        """
        yfinance has no direct IV history. Returns 20-day rolling realized
        volatility (HV20) as an IV proxy — sufficient for IVR percentile math.
        """
        if not _YF_AVAILABLE or not _NP_AVAILABLE:
            return []
        try:
            symbol = ticker.upper()
            tk = yf.Ticker(symbol)
            hist = tk.history(period="1y", interval="1d", auto_adjust=True)
            if hist.empty:
                return []

            closes = list(hist["Close"])
            dates = [d.strftime("%Y-%m-%d") for d in hist.index]
            window = 20
            out: list[dict] = []

            for i in range(window, len(closes)):
                window_closes = closes[i - window : i + 1]
                returns = [
                    math.log(window_closes[j] / window_closes[j - 1])
                    for j in range(1, len(window_closes))
                    if window_closes[j] > 0 and window_closes[j - 1] > 0
                ]
                if len(returns) < 2:
                    continue
                hv = float(np.std(returns, ddof=1) * math.sqrt(252) * 100)
                out.append({"date": dates[i], "iv": round(hv, 2)})

            return out
        except Exception:
            return []

    def get_ohlcv_daily(self, ticker: str, days: int = 60) -> list[dict]:
        if not _YF_AVAILABLE:
            return []
        try:
            symbol = ticker.upper()
            tk = yf.Ticker(symbol)
            hist = tk.history(period=f"{days}d", interval="1d", auto_adjust=True)
            if hist.empty:
                return []
            return [
                {
                    "date": dt.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row.get("Volume", 0) or 0),
                }
                for dt, row in hist.iterrows()
            ]
        except Exception:
            return []
