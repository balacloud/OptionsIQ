from __future__ import annotations

import os
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from gate_engine import GateEngine
from iv_store import IVStore
from mock_provider import MockProvider
from pnl_calculator import PnLCalculator
from strategy_ranker import StrategyRanker

VERSION = "2.0"
load_dotenv(Path(__file__).resolve().with_name(".env"))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3050"]}})
logging.basicConfig(level=logging.INFO)

iv_store = IVStore()
mock_provider = MockProvider()
gate_engine = GateEngine()
strategy_ranker = StrategyRanker()
pnl_calculator = PnLCalculator()

IBKRProvider = None
IBKRNotAvailableError = Exception
ibkr_provider = None
ibkr_init_error: str | None = None
_chain_cache: dict[str, dict] = {}
_chain_cache_lock = threading.Lock()
_ib_chain_failures = 0
_ib_chain_open_until = 0.0
_ib_chain_lock = threading.Lock()
_refreshing_tickers: set[str] = set()
_refresh_lock = threading.Lock()


def _chain_cache_key(ticker: str, chain_profile: str = "smart", direction: str | None = None) -> str:
    p = (chain_profile or "smart").strip().lower()
    d = (direction or "all").strip().lower()
    return f"{ticker.upper()}::{p}::{d}"


def _load_ibkr_provider() -> None:
    global IBKRProvider, IBKRNotAvailableError, ibkr_provider, ibkr_init_error
    try:
        from ibkr_provider import IBKRNotAvailableError as _IBKRNotAvailableError, IBKRProvider as _IBKRProvider

        IBKRProvider = _IBKRProvider
        IBKRNotAvailableError = _IBKRNotAvailableError
        ibkr_provider = IBKRProvider()
        ibkr_init_error = None
    except Exception as exc:
        ibkr_provider = None
        ibkr_init_error = f"{type(exc).__name__}: {exc}"


_load_ibkr_provider()


def _provider_pair(ensure_connected: bool = True):
    connected = False
    if ibkr_provider is None:
        _load_ibkr_provider()
        if ibkr_init_error:
            app.logger.warning("IBKR provider init failed: %s", ibkr_init_error)
    if ibkr_provider is not None:
        try:
            if ensure_connected and not ibkr_provider.is_connected() and hasattr(ibkr_provider, "_ensure_connected"):
                ibkr_provider._ensure_connected()
            connected = ibkr_provider.is_connected()
        except Exception as exc:
            connected = False
            app.logger.warning("IBKR connect check failed: %s: %s", type(exc).__name__, exc)
    if not ensure_connected and ibkr_provider is not None:
        return ibkr_provider, connected
    if not connected:
        app.logger.info("IB Gateway not available — using mock data")
    return (ibkr_provider if connected else mock_provider), connected


def _get_chain_with_timeout(
    provider,
    ticker: str,
    timeout_sec: float = 12.0,
    underlying_hint: float | None = None,
    direction: str | None = None,
    target_price: float | None = None,
    chain_profile: str | None = None,
    min_dte: int | None = None,
) -> dict:
    if provider is mock_provider:
        return provider.get_options_chain(ticker)
    if not _ib_chain_allowed():
        raise IBKRNotAvailableError("IB chain circuit open")
    ex = ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(provider.get_options_chain, ticker, underlying_hint, direction, target_price, chain_profile, min_dte)
    try:
        chain = fut.result(timeout=timeout_sec)
        _ib_chain_record(success=True)
        return chain
    except FutureTimeoutError:
        app.logger.warning("IB chain request timed out after %.1fs", timeout_sec)
        fut.cancel()
        ex.shutdown(wait=False, cancel_futures=True)
        _ib_chain_record(success=False)
        raise IBKRNotAvailableError("IB chain timeout")
    except Exception:
        _ib_chain_record(success=False)
        raise
    finally:
        ex.shutdown(wait=False, cancel_futures=True)


def _fetch_chain_with_retry(
    provider,
    ticker: str,
    timeout_sec: float,
    underlying_hint: float | None = None,
    direction: str | None = None,
    target_price: float | None = None,
    chain_profile: str | None = None,
    min_dte: int | None = None,
) -> dict:
    attempts = max(1, int(os.getenv("IB_CHAIN_RETRY_ATTEMPTS", "2")))
    backoff = float(os.getenv("IB_CHAIN_RETRY_BACKOFF_SEC", "0.6"))
    last_err = None
    for i in range(attempts):
        try:
            return _get_chain_with_timeout(
                provider,
                ticker,
                timeout_sec=timeout_sec,
                underlying_hint=underlying_hint,
                direction=direction,
                target_price=target_price,
                chain_profile=chain_profile,
                min_dte=min_dte,
            )
        except Exception as exc:
            last_err = exc
            if i < attempts - 1:
                time.sleep(backoff)
    raise last_err if last_err else IBKRNotAvailableError("IB chain unavailable")


def _ib_chain_allowed() -> bool:
    with _ib_chain_lock:
        return time.time() >= _ib_chain_open_until


def _ib_chain_record(success: bool) -> None:
    global _ib_chain_failures, _ib_chain_open_until
    threshold = int(os.getenv("IB_CHAIN_CB_FAILURE_THRESHOLD", "2"))
    cooldown = int(os.getenv("IB_CHAIN_CB_COOLDOWN_SEC", "45"))
    with _ib_chain_lock:
        if success:
            _ib_chain_failures = 0
            _ib_chain_open_until = 0.0
            return
        _ib_chain_failures += 1
        if _ib_chain_failures >= threshold:
            _ib_chain_open_until = time.time() + cooldown
            app.logger.warning("IB chain circuit OPEN for %ss after %s failures", cooldown, _ib_chain_failures)


def _cache_chain_set(ticker: str, chain: dict, chain_profile: str = "smart", direction: str | None = None) -> None:
    ttl = int(os.getenv("CHAIN_CACHE_TTL_SEC", "120"))
    key = _chain_cache_key(ticker, chain_profile=chain_profile, direction=direction)
    with _chain_cache_lock:
        _chain_cache[key] = {
            "saved_at": time.time(),
            "expires_at": time.time() + ttl,
            "chain": deepcopy(chain),
        }


def _cache_chain_get(ticker: str, allow_stale: bool = False, chain_profile: str = "smart", direction: str | None = None) -> dict | None:
    key = _chain_cache_key(ticker, chain_profile=chain_profile, direction=direction)
    now = time.time()
    with _chain_cache_lock:
        entry = _chain_cache.get(key)
        if not entry:
            return None
        if (not allow_stale) and now > float(entry["expires_at"]):
            _chain_cache.pop(key, None)
            return None
        return deepcopy(entry["chain"])


def _chain_field_stats(chain: dict) -> dict:
    contracts = chain.get("contracts", []) or []
    total = len(contracts)
    if total == 0:
        return {"contracts": 0, "core_complete_pct": 0.0, "greeks_complete_pct": 0.0, "quote_complete_pct": 0.0}

    def _ok_num(v):
        return isinstance(v, (int, float)) and v == v and v >= 0

    core_complete = 0
    greeks_complete = 0
    quote_complete = 0
    for c in contracts:
        if all(c.get(k) is not None for k in ("expiry", "dte", "right", "strike")):
            core_complete += 1
        if all(_ok_num(c.get(k)) for k in ("delta", "gamma", "vega")):
            greeks_complete += 1
        if all(_ok_num(c.get(k)) for k in ("bid", "ask")):
            quote_complete += 1

    return {
        "contracts": total,
        "core_complete_pct": round((core_complete / total) * 100, 1),
        "greeks_complete_pct": round((greeks_complete / total) * 100, 1),
        "quote_complete_pct": round((quote_complete / total) * 100, 1),
    }


def _quality_label(data_source: str, chain: dict) -> str:
    if data_source == "mock":
        return "mock"
    if data_source == "ibkr_partial":
        return "partial"
    if data_source == "ibkr_cache":
        return "cached"

    stats = _chain_field_stats(chain)
    if stats["contracts"] == 0:
        return "partial"
    if stats["quote_complete_pct"] >= 70.0 and stats["greeks_complete_pct"] >= 70.0:
        return "full"
    if stats["greeks_complete_pct"] >= 40.0:
        return "degraded"
    return "partial"


def _timeout_for_profile(chain_profile: str) -> float:
    p = (chain_profile or "smart").strip().lower()
    if p == "full":
        return float(os.getenv("ANALYZE_TIMEOUT_FULL_SEC", os.getenv("ANALYZE_TIMEOUT_SEC", "18")))
    return float(os.getenv("ANALYZE_TIMEOUT_SMART_SEC", os.getenv("ANALYZE_TIMEOUT_SEC", "18")))


def _refresh_chain_async(ticker: str, chain_profile: str = "smart", direction: str | None = None) -> None:
    key = _chain_cache_key(ticker, chain_profile=chain_profile, direction=direction)
    with _refresh_lock:
        if key in _refreshing_tickers:
            return
        _refreshing_tickers.add(key)

    def _run():
        try:
            provider, _ = _provider_pair(ensure_connected=False)
            if provider is mock_provider:
                return
            chain = _fetch_chain_with_retry(
                provider,
                ticker.upper(),
                timeout_sec=_timeout_for_profile(chain_profile),
                direction=direction,
                target_price=None,
                chain_profile=chain_profile,
                min_dte=int(os.getenv("IBKR_MIN_DTE", "14")),
            )
            _cache_chain_set(ticker, chain, chain_profile=chain_profile, direction=direction)
        except Exception as exc:
            app.logger.info("Background chain refresh skipped for %s: %s", key, exc)
        finally:
            with _refresh_lock:
                _refreshing_tickers.discard(key)

    threading.Thread(target=_run, daemon=True).start()


def _warm_cache_startup() -> None:
    tickers = [t.strip().upper() for t in os.getenv("WARM_TICKERS", "AME").split(",") if t.strip()]
    for t in tickers:
        _refresh_chain_async(t, chain_profile="smart", direction=None)


def _build_partial_chain_from_ib(
    ticker: str,
    underlying: float,
    chain_profile: str = "smart",
    direction: str | None = None,
    min_dte: int = 14,
) -> dict:
    """Use mock structure but anchor to live underlying when options chain is unavailable."""
    chain = mock_provider.get_options_chain(ticker)
    contracts = chain.get("contracts", [])
    contracts = [c for c in contracts if int(c.get("dte", 0)) >= int(min_dte)]

    if direction in {"buy_call", "sell_call"}:
        rights = {"C", "P"}  # keep put anchors
        contracts = [c for c in contracts if c.get("right") in rights]
    elif direction in {"buy_put", "sell_put"}:
        rights = {"P", "C"}  # keep call anchors
        contracts = [c for c in contracts if c.get("right") in rights]

    if (chain_profile or "smart").lower() == "smart":
        expiries = sorted({c.get("expiry") for c in contracts})
        if expiries:
            keep = expiries[0]
            contracts = [c for c in contracts if c.get("expiry") == keep]
        contracts = contracts[:12]

    chain["contracts"] = contracts
    chain["underlying_price"] = round(float(underlying), 2)
    for c in chain.get("contracts", []):
        c["undPrice"] = chain["underlying_price"]
        c["symbol"] = ticker.upper()
    chain["partial"] = True
    return chain


def _direction_track(direction: str) -> str:
    return "A" if direction in {"buy_call", "sell_call"} else "B"


def _merge_swing(payload: dict, underlying: float) -> dict:
    return {
        "signal": payload.get("swing_signal", "BUY"),
        "entry_pullback": float(payload.get("entry_pullback", underlying * 0.97)),
        "entry_momentum": float(payload.get("entry_momentum", underlying)),
        "stop_loss": float(payload.get("stop_loss", underlying * 0.92)),
        "target1": float(payload.get("target1", underlying * 1.08)),
        "target2": float(payload.get("target2", underlying * 1.15)),
        "risk_reward": float(payload.get("risk_reward", 3.0)),
        "vcp_pivot": float(payload.get("vcp_pivot", underlying * 1.01)),
        "vcp_confidence": float(payload.get("vcp_confidence", 70)),
        "adx": float(payload.get("adx", 35.0)),
        "last_close": float(payload.get("last_close", underlying)),
        "s1_support": float(payload.get("s1_support", underlying * 0.95)),
        "spy_above_200sma": bool(payload.get("spy_above_200sma", True)),
        "spy_5day_return": float(payload.get("spy_5day_return", 0.0)),
        "earnings_days_away": int(payload.get("earnings_days_away", 45)),
        "pattern": payload.get("pattern", "VCP"),
        "source": payload.get("source", "manual"),
    }


def _extract_iv_data(ticker: str, chain: dict, provider) -> dict:
    quick_mode = str(os.getenv("QUICK_ANALYZE_MODE", "1")).lower() in {"1", "true", "yes"}
    contracts = chain.get("contracts", [])
    ivs = [float(c.get("impliedVol", 0.0)) * 100 for c in contracts if c.get("impliedVol") is not None]
    current_iv = round(sum(ivs) / len(ivs), 2) if ivs else 20.0

    history = iv_store.get_iv_history(ticker, 252)
    if len(history) < 30:
        hist_source = mock_provider.get_historical_iv(ticker, 365) if quick_mode else provider.get_historical_iv(ticker, 365)
        for h in hist_source:
            iv_store.store_iv(ticker, h["date"], h["iv"], source="mock" if provider is mock_provider else "ibkr")
        history = iv_store.get_iv_history(ticker, 252)

    ivr_pct = iv_store.compute_ivr_pct(ticker, current_iv)
    bars_provider = mock_provider if quick_mode else provider
    bars = bars_provider.get_ohlcv_daily(ticker, 60) if hasattr(bars_provider, "get_ohlcv_daily") else []
    if bars:
        iv_store.store_ohlcv(ticker, bars)
    hv_20 = iv_store.compute_hv(ticker, 20)
    if hv_20 is None:
        hv_20 = 17.1
    ratio = round((current_iv / hv_20), 2) if hv_20 else 0.0

    return {
        "current_iv": current_iv,
        "ivr_pct": ivr_pct,
        "hv_20": hv_20,
        "hv_iv_ratio": ratio,
        "history_days": len(history),
        "fallback_used": ivr_pct is None,
    }


def _put_call_ratio(chain: dict) -> float:
    puts = sum(float(c.get("openInterest", 0.0)) for c in chain.get("contracts", []) if c.get("right") == "P")
    calls = sum(float(c.get("openInterest", 0.0)) for c in chain.get("contracts", []) if c.get("right") == "C")
    if calls <= 0:
        return 0.0
    return round(puts / calls, 2)


def _max_pain(chain: dict) -> float:
    strikes = sorted({float(c["strike"]) for c in chain.get("contracts", [])})
    if not strikes:
        return 0.0

    def pain(px: float) -> float:
        total = 0.0
        for c in chain.get("contracts", []):
            oi = float(c.get("openInterest", 0.0))
            strike = float(c["strike"])
            if c.get("right") == "C":
                total += max(0.0, px - strike) * oi
            else:
                total += max(0.0, strike - px) * oi
        return total

    return round(min(strikes, key=pain), 2)


def _behavioral_checks(gates: list[dict], swing_data: dict) -> list[dict]:
    pivot_gate = next((g for g in gates if g["id"] == "pivot_confirm"), None)
    pivot_msg = (
        f"Stock has not closed above VCP pivot ${swing_data['vcp_pivot']:.2f}."
        if pivot_gate and pivot_gate["status"] == "fail"
        else f"Pivot confirmed above ${swing_data['vcp_pivot']:.2f}."
    )
    timing_conflict = swing_data["entry_momentum"] > swing_data["entry_pullback"] * 1.1

    return [
        {
            "id": "gate8_block",
            "type": "hard_block" if pivot_gate and pivot_gate["status"] == "fail" else "info",
            "label": "Hard Block: Pivot Not Confirmed",
            "message": pivot_msg,
        },
        {
            "id": "entry_timing",
            "type": "warning" if timing_conflict else "info",
            "label": "Entry Timing Conflict",
            "message": "Momentum entry is stretched above pullback anchor." if timing_conflict else "Entry timing is within normal pullback/momentum bounds.",
        },
        {
            "id": "vrp_headwind",
            "type": "warning",
            "label": "VRP Headwind",
            "message": "53.78% stock win does not guarantee options win. Vol risk premium can still hurt outcomes.",
        },
        {
            "id": "lottery_bias",
            "type": "warning",
            "label": "Lottery Bias",
            "message": "Pick Δ0.68, not highest % return.",
        },
    ]


@app.get("/api/health")
def health():
    _, connected = _provider_pair()
    return jsonify(
        {
            "status": "ok",
            "ibkr_connected": connected,
            "mock_mode": not connected,
            "version": VERSION,
        }
    )


@app.post("/api/options/analyze")
def analyze_options():
    payload = request.get_json(silent=True) or {}
    ticker = str(payload.get("ticker", "AME")).upper().strip()
    direction = str(payload.get("direction", "buy_call")).strip()
    account_size = float(payload.get("account_size", os.getenv("ACCOUNT_SIZE", 50000)))
    risk_pct = float(payload.get("risk_pct", os.getenv("RISK_PCT", 0.01)))
    planned_hold_days = int(payload.get("planned_hold_days", os.getenv("PLANNED_HOLD_DAYS", 7)))
    chain_profile = str(payload.get("chain_profile", os.getenv("CHAIN_PROFILE_DEFAULT", "smart"))).strip().lower()
    if chain_profile not in {"smart", "full"}:
        chain_profile = "smart"
    try:
        min_dte = int(payload.get("min_dte", os.getenv("IBKR_MIN_DTE", "14")))
    except Exception:
        min_dte = int(os.getenv("IBKR_MIN_DTE", "14"))

    provider, connected = _provider_pair(ensure_connected=False)
    data_source = "mock"
    quality = "mock"
    cache_first = str(os.getenv("ANALYZE_CACHE_FIRST", "1")).lower() in {"1", "true", "yes"}
    underlying_hint = payload.get("last_close")
    try:
        underlying_hint = float(underlying_hint) if underlying_hint is not None else None
    except Exception:
        underlying_hint = None
    target_price = payload.get("entry_momentum", underlying_hint)
    try:
        target_price = float(target_price) if target_price is not None else None
    except Exception:
        target_price = underlying_hint

    cached_chain = _cache_chain_get(ticker, chain_profile=chain_profile, direction=direction) if cache_first else None
    if cached_chain is not None:
        chain = cached_chain
        underlying = float(chain.get("underlying_price", mock_provider.get_underlying_price(ticker)))
        connected = True
        data_source = "ibkr_cache"
        quality = _quality_label(data_source, chain)
        provider = mock_provider
        _refresh_chain_async(ticker, chain_profile=chain_profile, direction=direction)
    else:
        try:
            chain = _fetch_chain_with_retry(
                provider,
                ticker,
                timeout_sec=_timeout_for_profile(chain_profile),
                underlying_hint=underlying_hint,
                direction=direction,
                target_price=target_price,
                chain_profile=chain_profile,
                min_dte=min_dte,
            )
            underlying = float(chain.get("underlying_price") or provider.get_underlying_price(ticker))
            connected = provider is not mock_provider
            data_source = "ibkr" if connected else "mock"
            quality = _quality_label(data_source, chain)
            if connected:
                _cache_chain_set(ticker, chain, chain_profile=chain_profile, direction=direction)
        except IBKRNotAvailableError:
            cached_chain = _cache_chain_get(ticker, chain_profile=chain_profile, direction=direction)
            if cached_chain is not None:
                chain = cached_chain
                underlying = float(chain.get("underlying_price", mock_provider.get_underlying_price(ticker)))
                connected = True
                data_source = "ibkr_cache"
                quality = _quality_label(data_source, chain)
                provider = mock_provider
                _refresh_chain_async(ticker, chain_profile=chain_profile, direction=direction)
            elif (stale_chain := _cache_chain_get(ticker, allow_stale=True, chain_profile=chain_profile, direction=direction)) is not None:
                chain = stale_chain
                underlying = float(chain.get("underlying_price", mock_provider.get_underlying_price(ticker)))
                connected = True
                data_source = "ibkr_cache"
                quality = "stale_cache"
                provider = mock_provider
                _refresh_chain_async(ticker, chain_profile=chain_profile, direction=direction)
            elif ibkr_provider is not None and ibkr_provider.is_connected():
                underlying = float(payload.get("last_close", mock_provider.get_underlying_price(ticker)))
                chain = _build_partial_chain_from_ib(
                    ticker,
                    underlying,
                    chain_profile=chain_profile,
                    direction=direction,
                    min_dte=min_dte,
                )
                connected = True
                data_source = "ibkr_partial"
                quality = _quality_label(data_source, chain)
                provider = mock_provider
            else:
                chain = mock_provider.get_options_chain(ticker)
                underlying = float(chain.get("underlying_price"))
                connected = False
                data_source = "mock"
                quality = _quality_label(data_source, chain)
                provider = mock_provider

    swing_data = _merge_swing(payload, underlying)
    ivr_data = _extract_iv_data(ticker, chain, provider)

    engine = GateEngine(planned_hold_days=planned_hold_days)
    strategies_preview = strategy_ranker.rank(direction, chain, swing_data, recommended_dte=45)
    selected = strategies_preview[0] if strategies_preview else {}

    gate_payload = {
        **ivr_data,
        **swing_data,
        "underlying_price": underlying,
        "selected_expiry_dte": int(selected.get("dte", 21)),
        "strike": float(selected.get("strike", underlying)),
        "premium": float(selected.get("premium", 0.0)),
        "theta_per_day": float(selected.get("theta_per_day", -0.2)),
        "open_interest": float(selected.get("open_interest", 0.0)),
        "volume": float(selected.get("volume", 0.0)),
        "bid": selected.get("bid"),
        "ask": selected.get("ask"),
        "account_size": account_size,
        "risk_pct": risk_pct,
        "fomc_days_away": int(payload.get("fomc_days_away", 30)),
        "lots": float(payload.get("lots", 1.0)),
    }

    gates = engine.run(direction, gate_payload)
    verdict = engine.build_verdict(gates)
    recommended_dte = gate_payload.get("recommended_dte")

    strategies = strategy_ranker.rank(direction, chain, swing_data, recommended_dte=recommended_dte)
    gate8 = next((g for g in gates if g["id"] == "pivot_confirm"), {"status": "pass"})
    pnl_table = pnl_calculator.calculate(
        current_price=underlying,
        swing_data=swing_data,
        strategies=strategies,
        account_size=account_size,
        risk_pct=risk_pct,
        gate8_passed=gate8["status"] == "pass",
    )

    response = {
        "ticker": ticker,
        "direction": direction,
        "track": _direction_track(direction),
        "underlying_price": round(underlying, 2),
        "data_source": data_source,
        "chain_profile": chain_profile,
        "min_dte": min_dte,
        "quality": quality,
        "chain_quality": _chain_field_stats(chain),
        "ibkr_connected": connected,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        "swing_data": swing_data,
        "verdict": verdict,
        "gates": gates,
        "behavioral_checks": _behavioral_checks(gates, swing_data),
        "top_strategies": strategies,
        "pnl_table": pnl_table,
        "ivr_data": ivr_data,
        "put_call_ratio": _put_call_ratio(chain),
        "max_pain_strike": _max_pain(chain),
        "recommended_dte": recommended_dte,
        "direction_locked": ["sell_call", "buy_put"] if swing_data.get("signal") == "BUY" else [],
    }
    return jsonify(response)


@app.get("/api/options/chain/<ticker>")
def chain_debug(ticker: str):
    provider, connected = _provider_pair(ensure_connected=False)
    data_source = "mock"
    chain_profile = str(request.args.get("chain_profile", os.getenv("CHAIN_PROFILE_DEFAULT", "smart"))).strip().lower()
    if chain_profile not in {"smart", "full"}:
        chain_profile = "smart"
    try:
        min_dte = int(request.args.get("min_dte", os.getenv("IBKR_MIN_DTE", "14")))
    except Exception:
        min_dte = int(os.getenv("IBKR_MIN_DTE", "14"))
    direction = request.args.get("direction")
    target_price = request.args.get("target_price", type=float)
    try:
        chain = _fetch_chain_with_retry(
            provider,
            ticker.upper(),
            timeout_sec=_timeout_for_profile(chain_profile),
            direction=direction,
            target_price=target_price,
            chain_profile=chain_profile,
            min_dte=min_dte,
        )
        connected = provider is not mock_provider
        data_source = "ibkr" if connected else "mock"
        if connected:
            _cache_chain_set(ticker, chain, chain_profile=chain_profile, direction=direction)
    except Exception:
        cached_chain = _cache_chain_get(ticker, chain_profile=chain_profile, direction=direction)
        if cached_chain is not None:
            chain = cached_chain
            connected = True
            data_source = "ibkr_cache"
        else:
            chain = mock_provider.get_options_chain(ticker)
            connected = False
            data_source = "mock"
    return jsonify({"ibkr_connected": connected, "data_source": data_source, "chain_profile": chain_profile, "min_dte": min_dte, **chain})


@app.get("/api/options/ivr/<ticker>")
def ivr_debug(ticker: str):
    provider, _ = _provider_pair(ensure_connected=False)
    try:
        chain = _fetch_chain_with_retry(
            provider,
            ticker.upper(),
            timeout_sec=_timeout_for_profile("full"),
            direction=None,
            target_price=None,
        )
    except Exception:
        chain = _cache_chain_get(ticker) or mock_provider.get_options_chain(ticker)
        provider = mock_provider
    data = _extract_iv_data(ticker.upper(), chain, provider)
    return jsonify(data)


@app.post("/api/options/paper-trade")
def save_paper_trade():
    payload = request.get_json(silent=True) or {}
    required = ["ticker", "direction", "strategy_rank", "strike", "expiry", "premium", "lots", "account_size"]
    for key in required:
        if key not in payload:
            return jsonify({"success": False, "error": f"Missing field: {key}"}), 400
    trade_id = iv_store.save_paper_trade(payload)
    return jsonify({"success": True, "trade_id": trade_id})


@app.get("/api/options/paper-trades")
def list_paper_trades():
    provider, _ = _provider_pair()
    trades = iv_store.list_paper_trades()
    out = []
    for t in trades:
        underlying = provider.get_underlying_price(t["ticker"])
        if t["direction"] == "sell_put":
            pnl = (float(t["premium"]) - max(0.0, float(t["strike"]) - underlying)) * 100 * float(t["lots"])
        else:
            pnl = (max(0.0, underlying - float(t["strike"])) - float(t["premium"])) * 100 * float(t["lots"])
        out.append({**t, "current_underlying": round(float(underlying), 2), "mark_to_market_pnl": round(float(pnl), 2)})
    return jsonify(out)


@app.post("/api/options/seed-iv/<ticker>")
def seed_iv(ticker: str):
    provider, connected = _provider_pair()
    hist = provider.get_historical_iv(ticker.upper(), 365)
    for row in hist:
        iv_store.store_iv(ticker.upper(), row["date"], row["iv"], source="ibkr" if connected else "mock")
    if not hist:
        return jsonify({"seeded_days": 0, "earliest_date": None, "latest_date": None})
    return jsonify(
        {
            "seeded_days": len(hist),
            "earliest_date": hist[0]["date"],
            "latest_date": hist[-1]["date"],
        }
    )


@app.post("/api/integrate/status")
def integrate_status():
    return jsonify({"status": "ready", "accepts_swing_data": True, "version": VERSION})


@app.get("/api/integrate/ping")
def integrate_ping():
    return jsonify({"status": "ok", "version": VERSION, "accepts_swing_data": True})


@app.get("/api/integrate/schema")
def integrate_schema():
    schema = {
        "ticker": "str",
        "direction": "str",
        "account_size": "float",
        "risk_pct": "float",
        "planned_hold_days": "int",
        "swing_signal": "str",
        "entry_pullback": "float",
        "entry_momentum": "float",
        "stop_loss": "float",
        "target1": "float",
        "target2": "float",
        "risk_reward": "float",
        "vcp_pivot": "float",
        "vcp_confidence": "float",
        "adx": "float",
        "last_close": "float",
        "s1_support": "float",
        "spy_above_200sma": "bool",
        "spy_5day_return": "float",
        "earnings_days_away": "int",
        "pattern": "str",
    }
    return jsonify(schema)


if __name__ == "__main__":
    _warm_cache_startup()
    app.run(host="0.0.0.0", port=5051, debug=False)
