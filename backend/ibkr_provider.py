from __future__ import annotations

import logging
import math
import os
import threading
import time
from datetime import date, datetime
from typing import NamedTuple

logger = logging.getLogger(__name__)

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
    FULL_MAX_EXPIRIES,
    FULL_MAX_STRIKES,
    SELL_CALL_STRIKE_HIGH_PCT,
    SELL_CALL_STRIKE_LOW_PCT,
    SELL_PUT_STRIKE_HIGH_PCT,
    SELL_PUT_STRIKE_LOW_PCT,
    SELLER_DIRECTIONS,
    SELLER_SWEET_MAX_DTE,
    SELLER_SWEET_MIN_DTE,
    SMART_MAX_CONTRACTS,
    SMART_MAX_EXPIRIES,
    SMART_MAX_STRIKES,
    SMART_STRIKE_WINDOW,
    STRUCT_CACHE_TTL_SEC_4H,
)


class IBKRNotAvailableError(RuntimeError):
    pass


class _StructCacheEntry(NamedTuple):
    expiries: list[tuple[str, int]]  # [(expiry_str, dte), ...]
    strikes: list[float]
    saved_at: float
    underlying_at_cache: float = 0.0  # underlying price when cache was built


class IBKRProvider:
    """
    IBKR data provider.
    MUST be called ONLY from the ib-worker thread (Golden Rule #2).
    Never call this directly from Flask routes.
    """

    def __init__(self) -> None:
        from ib_insync import IB, util

        util.patchAsyncio()

        self.host = os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = int(os.getenv("IBKR_PORT", "7497"))
        self.client_id = int(os.getenv("IBKR_CLIENT_ID", "10"))
        self.client_id_scan = int(os.getenv("IBKR_CLIENT_ID_SCAN", "6"))
        # Golden Rule #1: live data is always the default.
        self.market_data_type = 1
        self.ib = IB()

        # Structure cache: (ticker.upper()) → _StructCacheEntry
        # Stores reqSecDefOptParams result for 4h — avoids repeated slow qualification
        self._struct_cache: dict[str, _StructCacheEntry] = {}
        self._struct_lock = threading.Lock()

    # ─── Connection ──────────────────────────────────────────────────────────

    def _ensure_connected(self) -> None:
        try:
            if not self.ib.isConnected():
                last_exc = None
                for cid in range(self.client_id, self.client_id + max(1, self.client_id_scan)):
                    try:
                        self.ib.connect(self.host, self.port, clientId=cid, timeout=2, readonly=False)
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

    # ─── Direction-aware targeting helpers ───────────────────────────────────

    @staticmethod
    def _dte_target(direction: str | None) -> tuple[int, int]:
        """
        Return (min_dte, max_dte) for the sweet-spot DTE range by direction.
        Buyers: 45-90 DTE — time for move to develop.
        Sellers: 21-45 DTE — theta decay accelerating.
        Falls back to the global [DEFAULT_MIN_DTE, DEFAULT_MAX_DTE] window.
        """
        if direction in BUYER_DIRECTIONS:
            return (BUYER_SWEET_MIN_DTE, BUYER_SWEET_MAX_DTE)   # 45-90
        if direction in SELLER_DIRECTIONS:
            return (SELLER_SWEET_MIN_DTE, SELLER_SWEET_MAX_DTE)  # 21-45
        return (DEFAULT_MIN_DTE, DEFAULT_MAX_DTE)

    @staticmethod
    def _strike_window(direction: str | None, underlying: float) -> tuple[float, float]:
        """
        Return (low_strike, high_strike) based on direction.

        Buyers (buy_call, buy_put): target ITM strikes near delta 0.68.
          - buy_call: strikes 8-20% below underlying
          - buy_put:  strikes 8-20% above underlying

        Sellers (sell_call, sell_put): target ATM zone.
          - sell_call: 2% below to 8% above underlying
          - sell_put:  8% below to 2% above underlying

        Falls back to ±10% window when no direction.
        """
        u = underlying
        if direction == DIRECTION_BUY_CALL:
            return (u * (1.0 - BUY_CALL_STRIKE_LOW_PCT), u * (1.0 - BUY_CALL_STRIKE_HIGH_PCT))
        if direction == DIRECTION_BUY_PUT:
            return (u * (1.0 + BUY_PUT_STRIKE_LOW_PCT), u * (1.0 + BUY_PUT_STRIKE_HIGH_PCT))
        if direction == DIRECTION_SELL_CALL:
            return (u * (1.0 - SELL_CALL_STRIKE_LOW_PCT), u * (1.0 + SELL_CALL_STRIKE_HIGH_PCT))
        if direction == DIRECTION_SELL_PUT:
            return (u * (1.0 - SELL_PUT_STRIKE_LOW_PCT), u * (1.0 + SELL_PUT_STRIKE_HIGH_PCT))
        # No direction — ±SMART_STRIKE_WINDOW around underlying
        return (u * (1.0 - SMART_STRIKE_WINDOW), u * (1.0 + SMART_STRIKE_WINDOW))

    @staticmethod
    def _primary_rights(direction: str | None) -> tuple[str, ...]:
        """Returns the right(s) to fetch for the primary leg of this direction."""
        if direction in {DIRECTION_BUY_CALL, DIRECTION_SELL_CALL}:
            return ("C",)
        if direction in {DIRECTION_BUY_PUT, DIRECTION_SELL_PUT}:
            return ("P",)
        return ("C", "P")

    # ─── Structure cache ─────────────────────────────────────────────────────

    def _struct_cached(self, ticker: str, underlying: float = 0.0) -> _StructCacheEntry | None:
        with self._struct_lock:
            entry = self._struct_cache.get(ticker)
        if entry is None:
            return None
        if time.time() - entry.saved_at > STRUCT_CACHE_TTL_SEC_4H:
            with self._struct_lock:
                self._struct_cache.pop(ticker, None)
            return None
        # Invalidate cache if underlying moved >15% since cache was built (e.g. split, large gap)
        if underlying > 0 and entry.underlying_at_cache > 0:
            price_drift = abs(underlying - entry.underlying_at_cache) / entry.underlying_at_cache
            if price_drift > 0.15:
                logger.info("_struct_cached: invalidating %s — price drifted %.1f%% (%.2f → %.2f)",
                            ticker, price_drift * 100, entry.underlying_at_cache, underlying)
                with self._struct_lock:
                    self._struct_cache.pop(ticker, None)
                return None
        return entry

    def _struct_store(self, ticker: str, expiries: list, strikes: list, underlying: float = 0.0) -> None:
        with self._struct_lock:
            self._struct_cache[ticker] = _StructCacheEntry(
                expiries=expiries, strikes=strikes, saved_at=time.time(),
                underlying_at_cache=underlying,
            )

    # ─── Market hours ─────────────────────────────────────────────────────────

    @staticmethod
    def _market_is_open() -> bool:
        """Returns True if US stock market is currently open (9:30am–4:00pm ET, Mon–Fri)."""
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]
        now_et = datetime.now(ZoneInfo("America/New_York"))
        if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now_et < market_close

    @staticmethod
    def _get_hv_estimate(ticker: str) -> float:
        """20-day historical volatility as IV proxy for closed-market BS greeks."""
        try:
            import yfinance as yf
            hist = yf.Ticker(ticker).history(period="30d", interval="1d", auto_adjust=True)
            if hist.empty or len(hist) < 5:
                return 0.30
            closes = list(hist["Close"])
            returns = [
                math.log(closes[i] / closes[i - 1])
                for i in range(1, len(closes))
                if closes[i] > 0 and closes[i - 1] > 0
            ]
            if len(returns) < 2:
                return 0.30
            mean = sum(returns) / len(returns)
            variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
            hv = math.sqrt(variance) * math.sqrt(252)
            return max(0.05, min(hv, 2.0))
        except Exception:
            return 0.30

    # ─── Phase 1: Chain structure (fast, 2-3s) ───────────────────────────────

    def _fetch_structure(
        self,
        ticker: str,
        direction: str | None,
        min_dte: int,
        max_dte: int,
        underlying: float,
        max_expiries: int,
        max_strikes: int,
    ) -> tuple[list[tuple[str, int]], list[float], list[tuple[str, int]], list[float]]:
        """
        Returns (chosen_expiries, chosen_strikes, all_expiries, all_strikes).
        chosen_*: direction-filtered selection for this request.
        all_*:    full universe from reqSecDefOptParams (for broad retry fallback).
        expiries: [(expiry_str, dte), ...] sorted ascending by DTE.
        strikes:  floats sorted by proximity to underlying center.
        """
        # DTE sweet-spot range
        sweet_min, sweet_max = self._dte_target(direction)
        # For the fallback range, clamp to global window
        hard_min = max(DEFAULT_MIN_DTE, min_dte)
        hard_max = min(DEFAULT_MAX_DTE, max_dte)

        # Try structure cache first (invalidated if underlying drifted >15%)
        cached = self._struct_cached(ticker, underlying)
        if cached is not None:
            all_expiries = cached.expiries
            all_strikes = cached.strikes
        else:
            from ib_insync import Stock

            stock = Stock(ticker, "SMART", "USD")
            qualified = self.ib.qualifyContracts(stock)
            if not qualified:
                raise IBKRNotAvailableError(f"Cannot qualify {ticker}")
            stock = qualified[0]

            params = self.ib.reqSecDefOptParams(ticker, "", stock.secType, stock.conId)
            if not params:
                raise IBKRNotAvailableError(f"No options params for {ticker}")

            chain_params = next(
                (p for p in params if getattr(p, "exchange", "") == "SMART"), params[0]
            )
            today = date.today()
            all_expiries = []
            for exp in sorted(chain_params.expirations):
                try:
                    d = datetime.strptime(exp, "%Y%m%d").date()
                    dte = (d - today).days
                    if hard_min <= dte <= hard_max:
                        all_expiries.append((exp, dte))
                except Exception:
                    continue
            all_expiries = sorted(all_expiries, key=lambda x: x[1])
            all_strikes = sorted(float(s) for s in chain_params.strikes)
            self._struct_store(ticker, all_expiries, all_strikes, underlying)

        # ── Select expiries for this request ──────────────────────────────────
        # Primary: find expiries in the direction's DTE sweet spot
        sweet_expiries = [(e, d) for e, d in all_expiries if sweet_min <= d <= sweet_max]
        fallback_expiries = [(e, d) for e, d in all_expiries if hard_min <= d <= hard_max]

        if sweet_expiries:
            chosen_expiries = sweet_expiries[:max_expiries]
        elif fallback_expiries:
            # No sweet-spot expiry — use nearest valid expiry
            chosen_expiries = fallback_expiries[:max_expiries]
        else:
            chosen_expiries = all_expiries[:max_expiries]

        # ── Select strikes in direction-aware window ───────────────────────────
        low, high = self._strike_window(direction, underlying)
        window_strikes = [s for s in all_strikes if low <= s <= high]

        if not window_strikes:
            # Widen to ±15% if direction window had no strikes (thinly traded stock)
            window_strikes = [s for s in all_strikes if underlying * 0.85 <= s <= underlying * 1.15]

        # Sort strategy:
        # - Sell directions need ATM short-leg AND far-OTM protection-leg in the same fetch.
        #   Proximity sort wastes slots on near-ATM $2.5-increment stubs that fail qualify,
        #   preventing the protection-leg strikes from reaching the cap. Use range order instead.
        # - Buy directions: proximity sort still correct (we want the nearest ITM strike to
        #   underlying as the primary anchor).
        if direction == DIRECTION_SELL_CALL:
            window_strikes.sort()           # ascending: ATM edge → OTM end
        elif direction == DIRECTION_SELL_PUT:
            window_strikes.sort(reverse=True)  # descending: ATM edge → OTM end (puts go lower)
        else:
            window_strikes.sort(key=lambda s: abs(s - underlying))
        chosen_strikes = window_strikes[:max_strikes]

        # Fallback: if direction-aware window yielded too few strikes, supplement
        # from the broader ±SMART_STRIKE_WINDOW to ensure minimum viable analysis.
        if len(chosen_strikes) < 3:
            broad = [
                s for s in all_strikes
                if underlying * (1.0 - SMART_STRIKE_WINDOW) <= s <= underlying * (1.0 + SMART_STRIKE_WINDOW)
                and s not in chosen_strikes
            ]
            broad.sort(key=lambda s: abs(s - underlying))
            chosen_strikes = (chosen_strikes + broad)[:max_strikes]

        return chosen_expiries, chosen_strikes, all_expiries, all_strikes

    # ─── Underlying price ────────────────────────────────────────────────────

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

    # ─── Options chain (main) ────────────────────────────────────────────────

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
            from ib_insync import Option

            profile = (chain_profile or "smart").strip().lower()
            is_smart = profile == "smart"
            max_expiries = SMART_MAX_EXPIRIES if is_smart else FULL_MAX_EXPIRIES
            max_strikes = SMART_MAX_STRIKES if is_smart else FULL_MAX_STRIKES
            max_contracts = SMART_MAX_CONTRACTS if is_smart else FULL_MAX_CONTRACTS
            min_dte_val = int(min_dte if min_dte is not None else DEFAULT_MIN_DTE)

            self._ensure_connected()
            symbol = ticker.upper()

            # ── Phase 1: Get underlying price ─────────────────────────────────
            if underlying_hint and float(underlying_hint) > 0:
                underlying = float(underlying_hint)
            else:
                underlying = self.get_underlying_price(symbol)

            # ── Phase 2: Get chain structure (cached 4h) ──────────────────────
            hard_min = max(DEFAULT_MIN_DTE, min_dte_val)
            expiries, strikes, all_expiries, all_strikes = self._fetch_structure(
                ticker=symbol,
                direction=direction,
                min_dte=min_dte_val,
                max_dte=DEFAULT_MAX_DTE,
                underlying=underlying,
                max_expiries=max_expiries,
                max_strikes=max_strikes,
            )

            if not expiries or not strikes:
                return {
                    "ticker": symbol,
                    "underlying_price": underlying,
                    "asof": datetime.utcnow().isoformat(timespec="seconds"),
                    "contracts": [],
                }

            # ── Phase 3: Build contract list ──────────────────────────────────
            primary_rights = self._primary_rights(direction)
            center = float(target_price) if target_price and float(target_price) > 0 else underlying

            contracts_to_fetch: list[tuple] = []  # (Option, dte)
            for exp, dte in expiries:
                for strike in strikes:
                    for right in primary_rights:
                        contracts_to_fetch.append((Option(symbol, exp, strike, right, "SMART"), dte))

            # Add one ATM anchor for opposite side (cross-side context for gates)
            if strikes and len(primary_rights) == 1:
                opposite = "P" if primary_rights[0] == "C" else "C"
                atm = min(strikes, key=lambda s: abs(s - center))
                for exp, dte in expiries:
                    contracts_to_fetch.append((Option(symbol, exp, atm, opposite, "SMART"), dte))

            contracts_to_fetch = contracts_to_fetch[:max_contracts]

            # ── Phase 4: Qualify + price selected contracts ───────────────────
            qual = self.ib.qualifyContracts(*[c for c, _ in contracts_to_fetch])

            # If too few contracts qualified (<3), the chosen expiry likely has sparse strikes.
            # Retry with the broader fallback expiry list (all_expiries) before giving up.
            if len(qual) < 3:
                logger.warning(
                    "get_options_chain: only %d contracts qualified for %s — "
                    "retrying with ±15%% broad strike window across all valid expiries",
                    len(qual),
                    symbol,
                )
                broad_expiries = [(e, d) for e, d in all_expiries if hard_min <= d <= hard_max][:3]
                broad_strikes = [
                    s for s in all_strikes
                    if underlying * 0.85 <= s <= underlying * 1.15
                ]
                broad_strikes.sort(key=lambda s: abs(s - underlying))
                broad_strikes = broad_strikes[:8]
                retry_contracts = [
                    (Option(symbol, exp, strike, right, "SMART"), dte)
                    for exp, dte in broad_expiries
                    for strike in broad_strikes
                    for right in primary_rights
                ][:max_contracts]
                retry_qual = self.ib.qualifyContracts(*[c for c, _ in retry_contracts])
                if len(retry_qual) > len(qual):
                    qual = retry_qual
                    contracts_to_fetch = retry_contracts  # update for dte_map below

            if not qual:
                return {
                    "ticker": symbol,
                    "underlying_price": underlying,
                    "asof": datetime.utcnow().isoformat(timespec="seconds"),
                    "contracts": [],
                }

            dte_map = {
                (c.lastTradeDateOrContractMonth, float(c.strike), c.right): dte
                for c, dte in contracts_to_fetch
            }

            # ── Phase 4b: Market hours check ─────────────────────────────────
            # When market is closed, reqTickers returns zero quotes (bid=ask=greeks=None).
            # Instead: compute Black-Scholes greeks using 20-day HV as IV proxy.
            # Returns "market_closed": True — data_service will set source "ibkr_closed".
            if not self._market_is_open():
                from bs_calculator import compute_greeks
                from constants import RISK_FREE_RATE
                iv_sigma = self._get_hv_estimate(symbol)
                logger.info(
                    "get_options_chain: market closed for %s — using BS greeks (HV=%.1f%%)",
                    symbol, iv_sigma * 100,
                )
                out = []
                for qc in qual:
                    dte_val = int(dte_map.get(
                        (qc.lastTradeDateOrContractMonth, float(qc.strike), qc.right), 0
                    ))
                    T = max(dte_val, 1) / 365.0
                    bs = compute_greeks(underlying, float(qc.strike), T, RISK_FREE_RATE, iv_sigma, qc.right)
                    out.append({
                        "symbol": symbol,
                        "expiry": datetime.strptime(
                            qc.lastTradeDateOrContractMonth, "%Y%m%d"
                        ).date().isoformat(),
                        "dte": dte_val,
                        "right": qc.right,
                        "strike": float(qc.strike),
                        "bid": None,
                        "ask": None,
                        "last": None,
                        "mid": bs["price"] if bs else 0.0,
                        "delta": bs["delta"] if bs else None,
                        "gamma": bs["gamma"] if bs else None,
                        "theta": bs["theta"] if bs else None,
                        "vega": bs["vega"] if bs else None,
                        "impliedVol": iv_sigma,
                        "optPrice": bs["price"] if bs else 0.0,
                        "undPrice": underlying,
                        "openInterest": 0,
                        "volume": 0,
                        "bs_greeks": True,
                    })
                return {
                    "ticker": symbol,
                    "underlying_price": underlying,
                    "asof": datetime.utcnow().isoformat(timespec="seconds"),
                    "contracts": out,
                    "market_closed": True,
                }

            # ── Phase 4c: reqMktData (streaming — fires tickOptionComputation) ──
            # reqTickers() is a snapshot wrapper that does NOT reliably trigger
            # tickOptionComputation (tick type 13 = modelGreeks). Must use
            # reqMktData(snapshot=False) and wait for the async callback to fire.
            def _num(v):
                try:
                    f = float(v)
                    return f if math.isfinite(f) else None
                except Exception:
                    return None

            def _num0(v, ndigits: int | None = None):
                f = _num(v)
                if f is None:
                    return 0.0
                return round(f, ndigits) if ndigits is not None else f

            def _int0(v):
                f = _num(v)
                return 0 if f is None else int(f)

            def _extract(qc, tk) -> dict:
                greeks = tk.modelGreeks
                bid_raw = _num(tk.bid)
                ask_raw = _num(tk.ask)
                last_raw = _num(tk.last)
                bid = bid_raw if bid_raw is not None and bid_raw > 0 else None
                ask = ask_raw if ask_raw is not None and ask_raw > 0 else None
                last = last_raw if last_raw is not None and last_raw > 0 else None
                mid = (
                    round((bid + ask) / 2, 4)
                    if bid is not None and ask is not None
                    else (last if last is not None else 0.0)
                )
                iv = (
                    _num(greeks.impliedVol)
                    if greeks and getattr(greeks, "impliedVol", None) is not None
                    else _num(getattr(tk, "impliedVolatility", None))
                )
                # optOpenInterest (tick 22) is the per-contract OI field for individual options.
                # callOpenInterest / putOpenInterest are aggregate fields on the underlying stock
                # ticker — they are always None on an individual option contract subscription.
                oi = getattr(tk, "optOpenInterest", None)
                return {
                    "symbol": symbol,
                    "expiry": datetime.strptime(
                        qc.lastTradeDateOrContractMonth, "%Y%m%d"
                    ).date().isoformat(),
                    "dte": int(dte_map.get(
                        (qc.lastTradeDateOrContractMonth, float(qc.strike), qc.right), 0
                    )),
                    "right": qc.right,
                    "strike": float(qc.strike),
                    "bid": bid, "ask": ask, "last": last,
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

            # Subscribe all contracts — tickOptionComputation fires async
            subs = {}
            out = []
            try:
                for qc in qual:
                    subs[qc] = self.ib.reqMktData(qc, genericTickList="101", snapshot=False,
                                                   regulatorySnapshot=False)

                # Wait for tickOptionComputation (tick type 13) callbacks to arrive
                self.ib.sleep(3)
                out = [_extract(qc, subs[qc]) for qc in qual]

                # ── Phase 4d: extended wait if greeks not yet populated ────────────
                # usopt warm-up: tickOptionComputation may arrive later on first connect.
                greeks_ok = sum(1 for c in out if c.get("delta") is not None)
                if greeks_ok == 0 and out:
                    logger.info(
                        "get_options_chain: %s — 0%% greeks after 3s, waiting 5s more (usopt warming up)",
                        symbol,
                    )
                    self.ib.sleep(5)
                    out = [_extract(qc, subs[qc]) for qc in qual]
                    logger.info(
                        "get_options_chain: %s — after extended wait: %d/%d contracts have greeks",
                        symbol,
                        sum(1 for c in out if c.get("delta") is not None),
                        len(out),
                    )
            finally:
                # Always cancel subscriptions — prevents IB Gateway zombie subscription buildup
                for qc in subs:
                    try:
                        self.ib.cancelMktData(qc)
                    except Exception:
                        pass

            # ── Phase 4e: BS fallback if usopt still providing no greeks ──────
            # If usopt never connected, reqTickers returns contracts with delta=None.
            # Fall back to Black-Scholes with HV estimate so the app is usable.
            greeks_after_retry = sum(1 for c in out if c.get("delta") is not None)
            if greeks_after_retry == 0 and out:
                from bs_calculator import compute_greeks
                from constants import RISK_FREE_RATE
                iv_sigma = self._get_hv_estimate(symbol)
                logger.warning(
                    "get_options_chain: %s — usopt not delivering greeks after retry, "
                    "falling back to BS greeks (HV=%.1f%%)",
                    symbol, iv_sigma * 100,
                )
                out_bs = []
                for c in out:
                    dte_val = int(c.get("dte", 0))
                    T = max(dte_val, 1) / 365.0
                    bs = compute_greeks(underlying, c["strike"], T, RISK_FREE_RATE, iv_sigma, c["right"])
                    out_bs.append({
                        **c,
                        "mid": bs["price"] if bs else c.get("mid", 0.0),
                        "delta": bs["delta"] if bs else None,
                        "gamma": bs["gamma"] if bs else None,
                        "theta": bs["theta"] if bs else None,
                        "vega": bs["vega"] if bs else None,
                        "impliedVol": iv_sigma,
                        "bs_greeks": True,
                    })
                out = out_bs

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

    # ─── Historical IV ────────────────────────────────────────────────────────

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

    # ─── Order staging (transmit=False — appears in TWS blotter, not sent) ─────

    def stage_spread_order(
        self,
        ticker: str,
        right: str,          # "C" or "P"
        expiry: str,         # ISO date e.g. "2026-05-15"
        short_strike: float,
        long_strike: float,
        net_credit: float,   # lmtPrice (net credit per share)
        qty: int = 1,
    ) -> dict:
        """
        Stage a vertical spread in TWS order blotter (transmit=False).
        The order appears in TWS for user review — NOT sent to market until
        user manually clicks Transmit in TWS.

        bear_call_spread: SELL short_call + BUY long_call (long_strike > short_strike)
        bull_put_spread:  SELL short_put  + BUY long_put  (long_strike < short_strike)
        """
        from ib_insync import Contract, Option
        from ib_insync.objects import ComboLeg
        from ib_insync.order import LimitOrder

        self._ensure_connected()
        symbol = ticker.upper()
        expiry_yyyymmdd = expiry.replace("-", "")  # "2026-05-15" → "20260515"

        # Qualify both legs to get conIds
        short_opt = Option(symbol, expiry_yyyymmdd, float(short_strike), right, "SMART")
        long_opt  = Option(symbol, expiry_yyyymmdd, float(long_strike),  right, "SMART")
        qual = self.ib.qualifyContracts(short_opt, long_opt)

        if len(qual) < 2:
            raise IBKRNotAvailableError(
                f"Could not qualify both legs for {symbol} {expiry} "
                f"{short_strike}/{long_strike} {right}"
            )

        short_q = next((q for q in qual if abs(float(q.strike) - float(short_strike)) < 0.01), None)
        long_q  = next((q for q in qual if abs(float(q.strike) - float(long_strike))  < 0.01), None)

        if not short_q or not long_q:
            raise IBKRNotAvailableError("Could not match qualified option contracts to requested strikes")

        # Build BAG (combo) contract
        bag = Contract()
        bag.symbol   = symbol
        bag.secType  = "BAG"
        bag.currency = "USD"
        bag.exchange = "SMART"

        sell_leg = ComboLeg()
        sell_leg.conId    = short_q.conId
        sell_leg.ratio    = 1
        sell_leg.action   = "SELL"
        sell_leg.exchange = "SMART"

        buy_leg = ComboLeg()
        buy_leg.conId    = long_q.conId
        buy_leg.ratio    = 1
        buy_leg.action   = "BUY"
        buy_leg.exchange = "SMART"

        bag.comboLegs = [sell_leg, buy_leg]

        # Limit order — SELL the spread for net credit; transmit=False prevents auto-send
        order = LimitOrder("SELL", qty, round(float(net_credit), 2))
        order.transmit = False
        order.tif = "DAY"
        order.account = ""  # use default account

        trade = self.ib.placeOrder(bag, order)
        self.ib.sleep(0.5)  # allow IB Gateway to acknowledge

        return {
            "order_id": trade.order.orderId,
            "status": "staged",
            "message": (
                f"Order #{trade.order.orderId} staged in TWS. "
                "Open TWS → Order Management → review and click Transmit to send."
            ),
        }

    # ─── OHLCV daily ─────────────────────────────────────────────────────────

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
