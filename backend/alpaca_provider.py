"""
OptionsIQ — Alpaca Data Provider (tier 2.5)

REST fallback between IBKR stale cache and yfinance.
Uses alpaca-py SDK (pip install alpaca-py).
- OptionHistoricalDataClient → greeks, bid/ask, IV, OI per contract
- Feed: "indicative" (15-min delayed, free tier)

Output format matches ibkr_provider.get_options_chain() exactly.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime

from constants import (
    BUYER_DIRECTIONS,
    BUYER_SWEET_MAX_DTE,
    BUYER_SWEET_MIN_DTE,
    BUY_CALL_STRIKE_HIGH_PCT,
    BUY_CALL_STRIKE_LOW_PCT,
    BUY_PUT_STRIKE_HIGH_PCT,
    BUY_PUT_STRIKE_LOW_PCT,
    DEFAULT_MAX_DTE,
    DEFAULT_MIN_DTE,
    DIRECTION_BUY_CALL,
    DIRECTION_BUY_PUT,
    DIRECTION_SELL_CALL,
    DIRECTION_SELL_PUT,
    FULL_MAX_CONTRACTS,
    SELL_CALL_STRIKE_HIGH_PCT,
    SELL_CALL_STRIKE_LOW_PCT,
    SELL_PUT_STRIKE_HIGH_PCT,
    SELL_PUT_STRIKE_LOW_PCT,
    SELLER_DIRECTIONS,
    SELLER_SWEET_MAX_DTE,
    SELLER_SWEET_MIN_DTE,
    SMART_MAX_CONTRACTS,
    SMART_STRIKE_WINDOW,
)

logger = logging.getLogger(__name__)


class AlpacaNotAvailableError(RuntimeError):
    pass


class AlpacaProvider:
    """
    Alpaca options data provider.
    Safe to call from any thread — no event loop, pure HTTP via alpaca-py SDK.
    """

    def __init__(self) -> None:
        self._key = os.getenv("APLACA_KEY", "")
        self._secret = os.getenv("APLACA_SECRET", "")
        if not self._key or not self._secret:
            raise AlpacaNotAvailableError("Alpaca credentials not configured (APLACA_KEY / APLACA_SECRET)")
        # Lazy-init: avoid import cost at startup if alpaca-py not installed
        self._data_client = None

    def _ensure_client(self) -> None:
        if self._data_client is None:
            try:
                from alpaca.data.historical.option import OptionHistoricalDataClient
            except ImportError as exc:
                raise AlpacaNotAvailableError("alpaca-py not installed — run: pip install alpaca-py") from exc
            self._data_client = OptionHistoricalDataClient(self._key, self._secret)

    # ─── OCC symbol parsing ───────────────────────────────────────────────────

    @staticmethod
    def _parse_occ_symbol(occ: str) -> tuple[str, str, str, float]:
        """
        Parse OCC symbol into (ticker, expiry_iso, right, strike).
        Format: <ticker padded to 6><YYMMDD><C|P><8-digit strike * 1000>
        Example: AMD260402C00210000 → ("AMD", "2026-04-02", "C", 210.0)
        Parses from the right to handle variable-length tickers.
        """
        strike = int(occ[-8:]) / 1000.0
        right = occ[-9]
        date_str = occ[-15:-9]
        ticker = occ[:-15].strip()
        expiry = datetime.strptime("20" + date_str, "%Y%m%d").date().isoformat()
        return ticker, expiry, right, strike

    # ─── Direction helpers (mirrors ibkr_provider) ────────────────────────────

    @staticmethod
    def _dte_window(direction: str | None) -> tuple[int, int]:
        if direction in BUYER_DIRECTIONS:
            return (BUYER_SWEET_MIN_DTE, BUYER_SWEET_MAX_DTE)
        if direction in SELLER_DIRECTIONS:
            return (SELLER_SWEET_MIN_DTE, SELLER_SWEET_MAX_DTE)
        return (DEFAULT_MIN_DTE, DEFAULT_MAX_DTE)

    @staticmethod
    def _strike_window(direction: str | None, underlying: float) -> tuple[float, float]:
        u = underlying
        if direction == DIRECTION_BUY_CALL:
            return (u * (1.0 - BUY_CALL_STRIKE_LOW_PCT), u * (1.0 - BUY_CALL_STRIKE_HIGH_PCT))
        if direction == DIRECTION_BUY_PUT:
            return (u * (1.0 + BUY_PUT_STRIKE_LOW_PCT), u * (1.0 + BUY_PUT_STRIKE_HIGH_PCT))
        if direction == DIRECTION_SELL_CALL:
            return (u * (1.0 - SELL_CALL_STRIKE_LOW_PCT), u * (1.0 + SELL_CALL_STRIKE_HIGH_PCT))
        if direction == DIRECTION_SELL_PUT:
            return (u * (1.0 - SELL_PUT_STRIKE_LOW_PCT), u * (1.0 + SELL_PUT_STRIKE_HIGH_PCT))
        return (u * (1.0 - SMART_STRIKE_WINDOW), u * (1.0 + SMART_STRIKE_WINDOW))

    # ─── Underlying price ─────────────────────────────────────────────────────

    def get_underlying_price(self, ticker: str) -> float:
        try:
            from alpaca.data.historical.stock import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest

            stock_client = StockHistoricalDataClient(self._key, self._secret)
            req = StockLatestQuoteRequest(symbol_or_symbols=ticker.upper())
            resp = stock_client.get_stock_latest_quote(req)
            quote = resp.get(ticker.upper())
            if quote and quote.ask_price and quote.bid_price:
                return round((float(quote.ask_price) + float(quote.bid_price)) / 2, 2)
            if quote and quote.ask_price:
                return round(float(quote.ask_price), 2)
        except Exception as exc:
            logger.warning("AlpacaProvider: underlying price error for %s: %s", ticker, exc)
        raise AlpacaNotAvailableError(f"Cannot get underlying price for {ticker} via Alpaca")

    # ─── Options chain ────────────────────────────────────────────────────────

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
            self._ensure_client()
            symbol = ticker.upper()

            # Underlying price
            if underlying_hint and float(underlying_hint) > 0:
                underlying = float(underlying_hint)
            else:
                underlying = self.get_underlying_price(symbol)

            # DTE + strike windows
            profile = (chain_profile or "smart").lower()
            max_contracts = SMART_MAX_CONTRACTS if profile == "smart" else FULL_MAX_CONTRACTS
            min_dte_val = int(min_dte if min_dte is not None else DEFAULT_MIN_DTE)

            dte_min, dte_max = self._dte_window(direction)
            dte_min = max(dte_min, min_dte_val)
            dte_max = min(dte_max, DEFAULT_MAX_DTE)
            strike_low, strike_high = self._strike_window(direction, underlying)

            today = date.today()
            exp_from = today.__class__.fromordinal(today.toordinal() + dte_min)
            exp_to = today.__class__.fromordinal(today.toordinal() + dte_max)

            # Right filter for server-side reduction
            if direction in {DIRECTION_BUY_CALL, DIRECTION_SELL_CALL}:
                type_filter = "call"
                rights = {"C"}
            elif direction in {DIRECTION_BUY_PUT, DIRECTION_SELL_PUT}:
                type_filter = "put"
                rights = {"P"}
            else:
                type_filter = None
                rights = {"C", "P"}

            # Fetch chain — server-side filter on expiry + strike + right
            from alpaca.data.requests import OptionChainRequest

            req_kwargs: dict = dict(
                underlying_symbol=symbol,
                feed="indicative",
                expiration_date_gte=exp_from,
                expiration_date_lte=exp_to,
                strike_price_gte=str(strike_low),
                strike_price_lte=str(strike_high),
            )
            if type_filter:
                req_kwargs["type"] = type_filter

            chain_data = self._data_client.get_option_chain(OptionChainRequest(**req_kwargs))

            if not chain_data:
                logger.info("AlpacaProvider: empty chain for %s (direction=%s)", symbol, direction)
                return {
                    "ticker": symbol,
                    "underlying_price": underlying,
                    "asof": datetime.utcnow().isoformat(timespec="seconds"),
                    "contracts": [],
                }

            # Parse + filter each snapshot
            out = []
            for occ_sym, snapshot in chain_data.items():
                try:
                    _, expiry_iso, right, strike = self._parse_occ_symbol(occ_sym)
                except Exception:
                    logger.debug("AlpacaProvider: failed to parse OCC symbol %s", occ_sym)
                    continue

                if right not in rights:
                    continue

                dte = (date.fromisoformat(expiry_iso) - today).days
                if not (dte_min <= dte <= dte_max):
                    continue

                greeks = getattr(snapshot, "greeks", None)
                quote = getattr(snapshot, "latest_quote", None)
                trade = getattr(snapshot, "latest_trade", None)

                bid_raw = float(quote.bid_price) if quote and getattr(quote, "bid_price", None) else None
                ask_raw = float(quote.ask_price) if quote and getattr(quote, "ask_price", None) else None
                last_raw = float(trade.price) if trade and getattr(trade, "price", None) else None

                bid = bid_raw if bid_raw and bid_raw > 0 else None
                ask = ask_raw if ask_raw and ask_raw > 0 else None
                last = last_raw if last_raw and last_raw > 0 else None
                mid = (
                    round((bid + ask) / 2, 4)
                    if bid is not None and ask is not None
                    else (last or 0.0)
                )

                iv_raw = getattr(snapshot, "implied_volatility", None)
                iv = float(iv_raw) if iv_raw is not None else None

                oi_raw = getattr(snapshot, "open_interest", None)
                oi = int(oi_raw) if oi_raw is not None else 0

                def _g(attr):
                    val = getattr(greeks, attr, None) if greeks else None
                    try:
                        return float(val) if val is not None else None
                    except Exception:
                        return None

                out.append({
                    "symbol": symbol,
                    "expiry": expiry_iso,
                    "dte": dte,
                    "right": right,
                    "strike": strike,
                    "bid": bid,
                    "ask": ask,
                    "last": last,
                    "mid": mid,
                    "delta": _g("delta"),
                    "gamma": _g("gamma"),
                    "theta": _g("theta"),
                    "vega": _g("vega"),
                    "impliedVol": iv,
                    "optPrice": mid,
                    "undPrice": underlying,
                    "openInterest": oi,
                    "volume": 0,  # not in Alpaca option snapshot
                })

            # Direction-aware sort (mirrors ibkr_provider)
            if direction == DIRECTION_SELL_CALL:
                out.sort(key=lambda c: c["strike"])
            elif direction == DIRECTION_SELL_PUT:
                out.sort(key=lambda c: -c["strike"])
            else:
                center = float(target_price) if target_price and float(target_price) > 0 else underlying
                out.sort(key=lambda c: abs(c["strike"] - center))

            out = out[:max_contracts]

            logger.info(
                "AlpacaProvider: %s direction=%s → %d contracts (underlying=%.2f)",
                symbol, direction, len(out), underlying,
            )

            return {
                "ticker": symbol,
                "underlying_price": underlying,
                "asof": datetime.utcnow().isoformat(timespec="seconds"),
                "contracts": out,
            }

        except AlpacaNotAvailableError:
            raise
        except Exception as exc:
            raise AlpacaNotAvailableError(f"Alpaca unavailable for {ticker}: {exc}") from exc
