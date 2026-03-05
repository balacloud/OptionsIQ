from __future__ import annotations

import os
import math
from datetime import date, datetime


class IBKRNotAvailableError(RuntimeError):
    pass


class IBKRProvider:
    def __init__(self) -> None:
        from ib_insync import IB, util

        util.patchAsyncio()

        self.host = os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = int(os.getenv("IBKR_PORT", "7497"))
        self.client_id = int(os.getenv("IBKR_CLIENT_ID", "10"))
        self.client_id_scan = int(os.getenv("IBKR_CLIENT_ID_SCAN", "6"))
        self.market_data_type = int(os.getenv("IBKR_MARKET_DATA_TYPE", "3"))  # 3=delayed
        self.ib = IB()

    def _ensure_connected(self) -> None:
        try:
            if not self.ib.isConnected():
                # readonly avoids open/completed-orders sync overhead in data-only usage.
                last_exc = None
                for cid in range(self.client_id, self.client_id + max(1, self.client_id_scan)):
                    try:
                        self.ib.connect(self.host, self.port, clientId=cid, timeout=2, readonly=True)
                        self.client_id = cid
                        self.ib.reqMarketDataType(self.market_data_type)
                        return
                    except Exception as exc:
                        last_exc = exc
                        try:
                            self.ib.disconnect()
                        except Exception:
                            pass
                raise last_exc if last_exc else RuntimeError("Unable to connect to IB Gateway")
        except Exception as exc:
            raise IBKRNotAvailableError("IB Gateway not available") from exc

    def is_connected(self) -> bool:
        try:
            return self.ib.isConnected()
        except Exception:
            return False

    def get_underlying_price(self, ticker: str) -> float:
        try:
            from ib_insync import Stock

            self._ensure_connected()
            stock = Stock(ticker.upper(), "SMART", "USD")
            self.ib.qualifyContracts(stock)
            tk = self.ib.reqMktData(stock, "", snapshot=True, regulatorySnapshot=False)
            self.ib.sleep(1.2)
            bid = float(tk.bid) if tk.bid and tk.bid > 0 else None
            ask = float(tk.ask) if tk.ask and tk.ask > 0 else None
            last = float(tk.last) if tk.last and tk.last > 0 else None
            self.ib.cancelMktData(stock)
            if bid and ask:
                return round((bid + ask) / 2, 2)
            if last:
                return round(last, 2)
            raise IBKRNotAvailableError("Unable to fetch underlying price")
        except IBKRNotAvailableError:
            raise
        except Exception as exc:
            raise IBKRNotAvailableError("IB Gateway not available") from exc

    def get_options_chain(
        self,
        ticker: str,
        underlying_hint: float | None = None,
        direction: str | None = None,
        target_price: float | None = None,
        chain_profile: str | None = None,
        min_dte: int | None = None,
    ) -> dict:
        try:
            from ib_insync import Option, Stock

            profile = (chain_profile or "smart").strip().lower()
            smart_profile = profile == "smart"
            max_expiries = int(os.getenv("IBKR_SMART_MAX_EXPIRIES", "1")) if smart_profile else int(os.getenv("IBKR_FULL_MAX_EXPIRIES", os.getenv("IBKR_MAX_EXPIRIES", "2")))
            max_strikes = int(os.getenv("IBKR_SMART_MAX_STRIKES", "4")) if smart_profile else int(os.getenv("IBKR_FULL_MAX_STRIKES", os.getenv("IBKR_MAX_STRIKES_PER_EXPIRY", "8")))
            max_contracts = int(os.getenv("IBKR_SMART_MAX_CONTRACTS", "12")) if smart_profile else int(os.getenv("IBKR_FULL_MAX_CONTRACTS", os.getenv("IBKR_MAX_CONTRACTS", "40")))
            batch_size = int(os.getenv("IBKR_BATCH_SIZE", "20"))
            strike_window_pct = float(os.getenv("IBKR_SMART_STRIKE_WINDOW_PCT", "0.10")) if smart_profile else float(os.getenv("IBKR_FULL_STRIKE_WINDOW_PCT", os.getenv("IBKR_STRIKE_WINDOW_PCT", "0.12")))
            min_dte_val = int(min_dte if min_dte is not None else os.getenv("IBKR_MIN_DTE", "14"))
            max_dte_val = int(os.getenv("IBKR_SMART_MAX_DTE", "120")) if smart_profile else int(os.getenv("IBKR_FULL_MAX_DTE", "90"))

            self._ensure_connected()
            symbol = ticker.upper()
            stock = Stock(symbol, "SMART", "USD")
            qualified = self.ib.qualifyContracts(stock)
            if not qualified:
                raise IBKRNotAvailableError(f"Unable to qualify stock contract for {symbol}")
            stock = qualified[0]

            underlying = float(underlying_hint) if underlying_hint and underlying_hint > 0 else self.get_underlying_price(symbol)
            params = self.ib.reqSecDefOptParams(symbol, "", stock.secType, stock.conId)
            if not params:
                raise IBKRNotAvailableError(f"No options params for {symbol}")

            # Prefer SMART chain; fallback to first response.
            chain = next((p for p in params if getattr(p, "exchange", "") == "SMART"), params[0])
            today = date.today()
            expiries = []
            for exp in sorted(chain.expirations):
                try:
                    d = datetime.strptime(exp, "%Y%m%d").date()
                    dte = (d - today).days
                    if min_dte_val <= dte <= max_dte_val:
                        expiries.append((exp, dte))
                except Exception:
                    continue
            expiries = sorted(expiries, key=lambda x: x[1])
            if smart_profile:
                # Smart profile: pick exactly one nearest valid expiry at/above min DTE.
                expiries = expiries[:1]
            else:
                expiries = expiries[:max_expiries]

            center = float(target_price) if target_price and target_price > 0 else underlying
            low = center * (1.0 - strike_window_pct)
            high = center * (1.0 + strike_window_pct)
            strikes = [float(s) for s in chain.strikes if low <= float(s) <= high]
            strikes = sorted(strikes, key=lambda s: abs(s - center))[:max_strikes]

            contracts = []
            primary_rights = ("C", "P")
            if direction in {"buy_call", "sell_call"}:
                primary_rights = ("C",)
            elif direction in {"buy_put", "sell_put"}:
                primary_rights = ("P",)

            for exp, dte in expiries:
                for strike in strikes:
                    for right in primary_rights:
                        contracts.append((Option(symbol, exp, strike, right, "SMART"), dte))

            # Add one opposite-side ATM anchor per expiry for basic cross-side context.
            if strikes and len(primary_rights) == 1:
                opposite = "P" if primary_rights[0] == "C" else "C"
                atm = min(strikes, key=lambda s: abs(s - center))
                for exp, dte in expiries:
                    contracts.append((Option(symbol, exp, atm, opposite, "SMART"), dte))
            contracts = contracts[:max_contracts]

            if not contracts:
                return {"ticker": symbol, "underlying_price": underlying, "asof": datetime.utcnow().isoformat(timespec="seconds"), "contracts": []}

            qual = self.ib.qualifyContracts(*[c for c, _ in contracts])
            dte_map = {(c.lastTradeDateOrContractMonth, float(c.strike), c.right): dte for c, dte in contracts}

            out = []
            def _num(v):
                try:
                    f = float(v)
                    if not math.isfinite(f):
                        return None
                    return f
                except Exception:
                    return None

            def _num0(v, ndigits: int | None = None):
                f = _num(v)
                if f is None:
                    return 0.0
                return round(f, ndigits) if ndigits is not None else f

            def _int0(v):
                f = _num(v)
                if f is None:
                    return 0
                return int(f)

            for i in range(0, len(qual), max(1, batch_size)):
                chunk_contracts = qual[i : i + max(1, batch_size)]
                tickers = self.ib.reqTickers(*chunk_contracts)
                for tk in tickers:
                    qc = tk.contract
                    greeks = tk.modelGreeks
                    bid_raw = _num(tk.bid)
                    ask_raw = _num(tk.ask)
                    last_raw = _num(tk.last)
                    bid = bid_raw if bid_raw is not None and bid_raw > 0 else None
                    ask = ask_raw if ask_raw is not None and ask_raw > 0 else None
                    last = last_raw if last_raw is not None and last_raw > 0 else None
                    mid = round((bid + ask) / 2, 4) if bid is not None and ask is not None else (last if last is not None else 0.0)
                    iv = _num(greeks.impliedVol) if greeks and getattr(greeks, "impliedVol", None) is not None else _num(getattr(tk, "impliedVolatility", None))
                    oi = getattr(tk, "callOpenInterest", None) if qc.right == "C" else getattr(tk, "putOpenInterest", None)

                    out.append(
                        {
                            "symbol": symbol,
                            "expiry": datetime.strptime(qc.lastTradeDateOrContractMonth, "%Y%m%d").date().isoformat(),
                            "dte": int(dte_map.get((qc.lastTradeDateOrContractMonth, float(qc.strike), qc.right), 0)),
                            "right": qc.right,
                            "strike": float(qc.strike),
                            "bid": bid,
                            "ask": ask,
                            "last": last,
                            "mid": _num0(mid, 4),
                            "delta": _num(greeks.delta) if greeks else None,
                            "gamma": _num(greeks.gamma) if greeks else None,
                            "theta": _num(greeks.theta) if greeks else None,
                            "vega": _num(greeks.vega) if greeks else None,
                            "impliedVol": iv,
                            "optPrice": _num0(getattr(tk, "optPrice", mid) or mid or 0.0),
                            "undPrice": _num0(getattr(tk, "undPrice", underlying) or underlying),
                            "openInterest": _int0(oi),
                            "volume": _int0(getattr(tk, "volume", 0)),
                        }
                    )

            return {
                "ticker": symbol,
                "underlying_price": underlying,
                "asof": datetime.utcnow().isoformat(timespec="seconds"),
                "contracts": out,
            }
        except IBKRNotAvailableError:
            raise
        except Exception as exc:
            raise IBKRNotAvailableError("IB Gateway not available") from exc

    def get_historical_iv(self, ticker: str, days: int = 252) -> list[dict]:
        try:
            from ib_insync import Stock

            self._ensure_connected()
            stock = Stock(ticker.upper(), "SMART", "USD")
            self.ib.qualifyContracts(stock)
            bars = self.ib.reqHistoricalData(
                stock,
                endDateTime="",
                durationStr=f"{int(days)} D",
                barSizeSetting="1 day",
                whatToShow="OPTION_IMPLIED_VOLATILITY",
                useRTH=True,
                formatDate=1,
            )
            out = []
            for b in bars:
                iv = float(b.close)
                if iv <= 1.5:
                    iv *= 100.0
                out.append({"date": str(b.date)[:10], "iv": round(iv, 2)})
            return out
        except Exception as exc:
            raise IBKRNotAvailableError("IB Gateway not available") from exc

    def get_ohlcv_daily(self, ticker: str, days: int = 60) -> list[dict]:
        try:
            from ib_insync import Stock

            self._ensure_connected()
            stock = Stock(ticker.upper(), "SMART", "USD")
            self.ib.qualifyContracts(stock)
            bars = self.ib.reqHistoricalData(
                stock,
                endDateTime="",
                durationStr=f"{int(days)} D",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            return [
                {
                    "date": str(b.date)[:10],
                    "open": float(b.open),
                    "high": float(b.high),
                    "low": float(b.low),
                    "close": float(b.close),
                    "volume": int(b.volume),
                }
                for b in bars
            ]
        except Exception:
            return []
