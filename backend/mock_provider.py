from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass
class MockProvider:
    ticker_price: float = 234.35

    def is_connected(self) -> bool:
        return False

    def get_underlying_price(self, ticker: str) -> float:
        return float(self.ticker_price)

    def get_historical_iv(self, ticker: str, days: int = 252) -> list[dict]:
        horizon = min(days, 180)
        today = date.today()
        series = []
        for i in range(horizon):
            d = today - timedelta(days=(horizon - 1 - i))
            base = 0.215 + 0.035 * __import__("math").sin(i / 11.0)
            wobble = 0.008 * __import__("math").cos(i / 5.0)
            iv = max(0.15, min(0.28, base + wobble))
            series.append({"date": d.isoformat(), "iv": round(iv * 100, 2)})
        return series

    def get_ohlcv_daily(self, ticker: str, days: int = 60) -> list[dict]:
        today = date.today()
        bars = []
        price = 205.0
        for i in range(days):
            d = today - timedelta(days=(days - 1 - i))
            drift = 0.18
            noise = 1.3 * __import__("math").sin(i / 3.1)
            close = max(10.0, price + drift + noise)
            open_px = close - 0.8
            high = close + 1.1
            low = close - 1.4
            volume = int(1_500_000 + (i % 8) * 120_000)
            bars.append(
                {
                    "date": d.isoformat(),
                    "open": round(open_px, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": volume,
                }
            )
            price = close
        return bars

    def get_options_chain(self, ticker: str) -> dict:
        underlying = self.ticker_price
        today = date.today()
        expiries = [
            date(2026, 3, 21),
            date(2026, 4, 17),
        ]
        strikes = [220, 225, 230, 235, 240, 245, 250, 255, 260]

        def build_option(expiry: date, strike: float, right: str, dte: int) -> dict:
            intrinsic = max(0.0, underlying - strike) if right == "C" else max(0.0, strike - underlying)
            dist = abs(strike - underlying)
            time_val = max(0.45, 8.5 - dist * 0.35 + (dte / 55.0))
            mid = intrinsic + time_val
            if right == "P":
                mid = max(0.45, time_val * 0.92 + max(0.0, strike - underlying) * 0.85)
            spread = max(0.08, mid * 0.04)
            bid = round(max(0.05, mid - spread / 2), 2)
            ask = round(max(0.06, mid + spread / 2), 2)
            last = round((bid + ask) / 2, 2)
            mny = (underlying - strike) / underlying
            if right == "C":
                delta = max(0.08, min(0.92, 0.52 + (mny * 2.1)))
            else:
                delta = -max(0.08, min(0.92, 0.48 - (mny * 2.1)))
            gamma = max(0.006, 0.026 - dist / 5000)
            theta = -max(0.04, 0.09 + dist / 320 - dte / 700)
            vega = max(0.08, 0.18 + dte / 300 - dist / 650)
            iv = max(0.15, min(0.28, 0.18 + dist / 1400 + dte / 2400))
            oi = int(max(700, 12500 - dist * 180))
            vol = int(max(120, oi * 0.24))

            return {
                "symbol": ticker.upper(),
                "expiry": expiry.isoformat(),
                "dte": dte,
                "right": right,
                "strike": float(strike),
                "bid": bid,
                "ask": ask,
                "last": last,
                "mid": round((bid + ask) / 2, 2),
                "delta": round(delta, 3),
                "gamma": round(gamma, 3),
                "theta": round(theta, 3),
                "vega": round(vega, 3),
                "impliedVol": round(iv, 3),
                "optPrice": last,
                "undPrice": underlying,
                "openInterest": oi,
                "volume": vol,
            }

        contracts = []
        for expiry in expiries:
            dte = (expiry - today).days
            for strike in strikes:
                contracts.append(build_option(expiry, strike, "C", dte))
                contracts.append(build_option(expiry, strike, "P", dte))

        # force exact values requested by prompt
        for c in contracts:
            if c["expiry"] == date(2026, 4, 17).isoformat() and c["right"] == "C":
                if c["strike"] == 230:
                    c.update({"bid": 9.60, "ask": 10.00, "last": 9.80, "mid": 9.80, "delta": 0.68, "gamma": 0.021, "theta": -0.18, "vega": 0.28, "impliedVol": 0.184, "optPrice": 9.80, "openInterest": 12400, "volume": 3100})
                elif c["strike"] == 235:
                    c.update({"bid": 6.20, "ask": 6.60, "last": 6.40, "mid": 6.40, "delta": 0.52, "gamma": 0.025, "theta": -0.22, "vega": 0.34, "impliedVol": 0.187, "optPrice": 6.40, "openInterest": 8200, "volume": 2100})
                elif c["strike"] == 255:
                    c.update({"bid": 1.90, "ask": 2.10, "last": 2.00, "mid": 2.00, "delta": 0.24, "gamma": 0.016, "theta": -0.11, "vega": 0.21, "impliedVol": 0.195, "optPrice": 2.00, "openInterest": 4100, "volume": 800})

        return {
            "ticker": ticker.upper(),
            "underlying_price": underlying,
            "asof": datetime.utcnow().isoformat(timespec="seconds"),
            "contracts": contracts,
        }
