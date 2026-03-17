from __future__ import annotations

import os
import logging
from datetime import datetime
from pathlib import Path

import requests as _requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from constants import STA_BASE_URL
from data_service import DataService
from gate_engine import GateEngine
from ib_worker import IBWorker
from iv_store import IVStore
from alpaca_provider import AlpacaNotAvailableError, AlpacaProvider
from mock_provider import MockProvider
from pnl_calculator import PnLCalculator
from strategy_ranker import StrategyRanker
from yfinance_provider import YFinanceProvider

VERSION = "2.0"
load_dotenv(Path(__file__).resolve().with_name(".env"))

# Golden Rule 7: ACCOUNT_SIZE must be explicit — no silent defaults.
if not os.getenv("ACCOUNT_SIZE"):
    raise RuntimeError(
        "ACCOUNT_SIZE is not set in .env — add ACCOUNT_SIZE=<your_account_value> "
        "(Golden Rule 7: user must be conscious of their account size)"
    )

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3050"]}})
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

iv_store = IVStore()
mock_provider = MockProvider()
gate_engine = GateEngine()
strategy_ranker = StrategyRanker()
pnl_calculator = PnLCalculator()

# Phase 2+: IBWorker (single IB() thread) + DataService (cascade + SQLite cache + CB)
_ib_worker = IBWorker()
_yf_provider = YFinanceProvider()
try:
    _alpaca_provider = AlpacaProvider()
    logger.info("AlpacaProvider initialised (tier 2.5 fallback)")
except AlpacaNotAvailableError as _e:
    _alpaca_provider = None
    logger.warning("AlpacaProvider unavailable: %s", _e)
data_svc = DataService(
    ib_worker=_ib_worker,
    yf_provider=_yf_provider,
    mock_provider=mock_provider,
    alpaca_provider=_alpaca_provider,
)


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _get_live_price(ticker: str) -> float:
    """Get underlying price via IBWorker (if connected) or yfinance fallback."""
    if _ib_worker.is_connected() and _ib_worker.provider:
        try:
            return _ib_worker.submit(_ib_worker.provider.get_underlying_price, ticker, timeout=10.0)
        except Exception as exc:
            logger.warning("IBWorker get_underlying_price failed for %s: %s", ticker, exc)
    try:
        return _yf_provider.get_underlying_price(ticker)
    except Exception as exc:
        logger.warning("yfinance get_underlying_price failed for %s: %s", ticker, exc)
        return 0.0


def _chain_field_stats(chain: dict) -> dict:
    contracts = chain.get("contracts", []) or []
    total = len(contracts)
    if total == 0:
        return {"contracts": 0, "core_complete_pct": 0.0, "greeks_complete_pct": 0.0, "quote_complete_pct": 0.0}

    def _ok_num(v):
        return isinstance(v, (int, float)) and v == v and v >= 0

    core_complete = greeks_complete = quote_complete = 0
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


def _direction_track(direction: str) -> str:
    return "A" if direction in {"buy_call", "sell_call"} else "B"


def _f(v, default):
    """Parse a float from payload — treats empty string / None as missing."""
    try:
        return float(v) if v not in (None, "", "null") else default
    except (TypeError, ValueError):
        return default


def _i(v, default):
    try:
        return int(float(v)) if v not in (None, "", "null") else default
    except (TypeError, ValueError):
        return default


def _merge_swing(payload: dict, underlying: float) -> dict:
    # Golden Rule 14: Never fabricate plausible values for missing swing fields.
    # vcp_confidence and adx default to None — gate_engine's `or 0.0` pattern handles
    # None safely: float(None or 0.0) = 0.0, causing DTE gate to fail correctly.
    synthesized = []
    vcp_confidence = _f(payload.get("vcp_confidence"), None)
    adx = _f(payload.get("adx"), None)
    if vcp_confidence is None:
        synthesized.append("vcp_confidence")
    if adx is None:
        synthesized.append("adx")
    # Price targets can be synthesized safely — they don't affect gate pass/fail.
    # Signal quality fields MUST NOT be fabricated (they drive DTE gate logic).
    return {
        "signal": payload.get("swing_signal") or "BUY",
        "entry_pullback": _f(payload.get("entry_pullback"), underlying * 0.97),
        "entry_momentum": _f(payload.get("entry_momentum"), underlying),
        "stop_loss": _f(payload.get("stop_loss"), underlying * 0.92),
        "target1": _f(payload.get("target1"), underlying * 1.08),
        "target2": _f(payload.get("target2"), underlying * 1.15),
        "risk_reward": _f(payload.get("risk_reward"), 3.0),
        "vcp_pivot": _f(payload.get("vcp_pivot"), underlying * 1.01),
        "vcp_confidence": vcp_confidence,
        "adx": adx,
        "last_close": _f(payload.get("last_close"), underlying),
        "s1_support": _f(payload.get("s1_support"), underlying * 0.95),
        "spy_above_200sma": bool(payload.get("spy_above_200sma") if payload.get("spy_above_200sma") is not None else True),
        "spy_5day_return": _f(payload.get("spy_5day_return"), 0.0),
        "earnings_days_away": _i(payload.get("earnings_days_away"), 45),
        "pattern": payload.get("pattern") or "VCP",
        "source": payload.get("source") or "manual",
        "swing_data_quality": "partial" if synthesized else "full",
        "synthesized_fields": synthesized,
    }


def _extract_iv_data(ticker: str, chain: dict, provider, ib_worker=None) -> dict:
    # Golden Rule #2: IBKRProvider must ONLY be called from the ib-worker thread.
    # Use ib_worker.submit() for any IBKR calls, never call provider methods directly.
    contracts = chain.get("contracts", [])
    ivs = [float(c.get("impliedVol", 0.0)) * 100 for c in contracts if c.get("impliedVol") is not None]
    current_iv = round(sum(ivs) / len(ivs), 2) if ivs else None

    def _call_provider(fn, *args):
        """Route IBKR calls through ib_worker; call other providers directly."""
        if ib_worker is not None and provider is ib_worker.provider:
            try:
                return ib_worker.submit(fn, *args, timeout=20.0)
            except (TimeoutError, Exception) as exc:
                app.logger.warning("IBWorker IV call timed out/failed: %s", exc)
                return None if fn.__name__ == "get_historical_iv" else []
        return fn(*args)

    history = iv_store.get_iv_history(ticker, 252)
    if len(history) < 30:
        hist_source = _call_provider(provider.get_historical_iv, ticker, 365)
        if hist_source:
            source_label = "mock" if provider is mock_provider else "ibkr"
            for h in hist_source:
                iv_store.store_iv(ticker, h["date"], h["iv"], source=source_label)
            history = iv_store.get_iv_history(ticker, 252)

    ivr_pct = iv_store.compute_ivr_pct(ticker, current_iv) if current_iv is not None else None
    bars = _call_provider(provider.get_ohlcv_daily, ticker, 60) if hasattr(provider, "get_ohlcv_daily") else []
    if bars:
        iv_store.store_ohlcv(ticker, bars)
    hv_20 = iv_store.compute_hv(ticker, 20)
    ratio = round((current_iv / hv_20), 2) if (current_iv and hv_20) else None

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


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    ib_status = data_svc.ibkr_status()
    return jsonify(
        {
            "status": "ok",
            "ibkr_connected": ib_status["connected"],
            "ibkr_error": ib_status.get("error"),
            "circuit_breaker": ib_status.get("circuit_breaker"),
            "mock_mode": not ib_status["connected"],
            "version": VERSION,
        }
    )


@app.post("/api/options/analyze")
def analyze_options():
    payload = request.get_json(silent=True) or {}
    ticker_raw = payload.get("ticker", "")
    if not ticker_raw or not str(ticker_raw).strip():
        return jsonify({"error": "ticker is required"}), 400
    ticker = str(ticker_raw).upper().strip()
    if not ticker.isalpha() or not (1 <= len(ticker) <= 6):
        return jsonify({"error": f"Invalid ticker: {ticker!r}"}), 400
    try:
        return _analyze_options_inner(payload, ticker)
    except Exception as exc:
        logger.exception("analyze_options unhandled error for %s", ticker)
        return jsonify({"error": str(exc)}), 500


def _analyze_options_inner(payload: dict, ticker: str):
    direction = str(payload.get("direction", "buy_call")).strip()
    account_size = float(payload.get("account_size", os.getenv("ACCOUNT_SIZE", 25000)))
    risk_pct = float(payload.get("risk_pct", os.getenv("RISK_PCT", 0.01)))
    planned_hold_days = int(payload.get("planned_hold_days", os.getenv("PLANNED_HOLD_DAYS", 7)))
    chain_profile = str(payload.get("chain_profile", os.getenv("CHAIN_PROFILE_DEFAULT", "smart"))).strip().lower()
    if chain_profile not in {"smart", "full"}:
        chain_profile = "smart"
    try:
        min_dte = int(payload.get("min_dte", os.getenv("IBKR_MIN_DTE", "14")))
    except Exception:
        min_dte = int(os.getenv("IBKR_MIN_DTE", "14"))

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

    chain, data_source = data_svc.get_chain(
        ticker,
        profile=chain_profile,
        direction=direction,
        underlying_hint=underlying_hint,
        target_price=target_price,
        min_dte=min_dte,
    )
    underlying = float(chain.get("underlying_price") or data_svc.get_underlying_price(ticker, hint=underlying_hint))
    connected = data_source not in {"mock"}
    quality = data_svc.quality_label(data_source, chain)

    iv_provider = mock_provider
    if data_source in {"ibkr_live", "ibkr_closed", "ibkr_cache", "ibkr_stale"} and _ib_worker.provider is not None:
        iv_provider = _ib_worker.provider
    elif data_source == "yfinance":
        iv_provider = _yf_provider

    swing_data = _merge_swing(payload, underlying)
    ivr_data = _extract_iv_data(ticker, chain, iv_provider, ib_worker=_ib_worker)

    engine = GateEngine(planned_hold_days=planned_hold_days)
    strategies_preview = strategy_ranker.rank(direction, chain, swing_data, recommended_dte=45)
    selected = strategies_preview[0] if strategies_preview else {}

    # gate_engine is frozen and calls float() on all numeric fields directly.
    # None values must be coerced to 0.0 before passing — never let None reach gate_engine.
    ivr_for_gates = {k: (0.0 if v is None else v) for k, v in ivr_data.items()}

    gate_payload = {
        **ivr_for_gates,
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
        "max_gain_per_lot": float(selected.get("max_gain_per_lot") or -1.0),
        "account_size": account_size,
        "risk_pct": risk_pct,
        "fomc_days_away": _i(payload.get("fomc_days_away"), 30),
        "lots": _f(payload.get("lots"), 1.0),
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
    """Debug endpoint — returns raw chain data via DataService."""
    chain_profile = str(request.args.get("chain_profile", os.getenv("CHAIN_PROFILE_DEFAULT", "smart"))).strip().lower()
    if chain_profile not in {"smart", "full"}:
        chain_profile = "smart"
    try:
        min_dte = int(request.args.get("min_dte", os.getenv("IBKR_MIN_DTE", "14")))
    except Exception:
        min_dte = int(os.getenv("IBKR_MIN_DTE", "14"))
    direction = request.args.get("direction")
    target_price = request.args.get("target_price", type=float)
    chain, data_source = data_svc.get_chain(
        ticker.upper(),
        profile=chain_profile,
        direction=direction,
        target_price=target_price,
        min_dte=min_dte,
    )
    return jsonify({"ibkr_connected": data_source != "mock", "data_source": data_source,
                    "chain_profile": chain_profile, "min_dte": min_dte, **chain})


@app.get("/api/options/ivr/<ticker>")
def ivr_debug(ticker: str):
    """Debug endpoint — returns IV/HV data via DataService."""
    symbol = ticker.upper()
    chain, data_source = data_svc.get_chain(symbol, profile="full")
    iv_provider = (
        _ib_worker.provider
        if data_source in {"ibkr_live", "ibkr_cache", "ibkr_stale"} and _ib_worker.provider
        else _yf_provider
    )
    data = _extract_iv_data(symbol, chain, iv_provider, ib_worker=_ib_worker)
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
    trades = iv_store.list_paper_trades()
    out = []
    for t in trades:
        underlying = _get_live_price(t["ticker"])
        if t["direction"] == "sell_put":
            pnl = (float(t["premium"]) - max(0.0, float(t["strike"]) - underlying)) * 100 * float(t["lots"])
        else:
            pnl = (max(0.0, underlying - float(t["strike"])) - float(t["premium"])) * 100 * float(t["lots"])
        out.append({**t, "current_underlying": round(float(underlying), 2), "mark_to_market_pnl": round(float(pnl), 2)})
    return jsonify(out)


@app.post("/api/options/seed-iv/<ticker>")
def seed_iv(ticker: str):
    """Seeds IV history from IBWorker (if connected) or yfinance fallback."""
    symbol = ticker.upper()
    connected = _ib_worker.is_connected() and _ib_worker.provider is not None
    hist = []
    if connected:
        try:
            hist = _ib_worker.submit(_ib_worker.provider.get_historical_iv, symbol, 365, timeout=30.0)
        except Exception as exc:
            logger.warning("seed-iv IBKR failed for %s: %s", symbol, exc)
    if not hist:
        try:
            hist = _yf_provider.get_historical_iv(symbol, 365)
            connected = False
        except Exception as exc:
            logger.warning("seed-iv yfinance fallback failed for %s: %s", symbol, exc)
            hist = []
    for row in hist:
        iv_store.store_iv(symbol, row["date"], row["iv"], source="ibkr" if connected else "yfinance")
    if not hist:
        return jsonify({"seeded_days": 0, "earliest_date": None, "latest_date": None})
    return jsonify({"seeded_days": len(hist), "earliest_date": hist[0]["date"], "latest_date": hist[-1]["date"]})


@app.get("/api/integrate/sta-fetch/<ticker>")
def sta_fetch(ticker: str):
    """
    Fetch swing data from STA (localhost:5001) and return assembled fields.
    Frontend SwingImportStrip calls this to pre-fill the analysis form.
    """
    symbol = ticker.upper().strip()
    timeout = 3.0
    try:
        sr = _requests.get(f"{STA_BASE_URL}/api/sr/{symbol}", timeout=timeout).json()
        stock = _requests.get(f"{STA_BASE_URL}/api/stock/{symbol}", timeout=timeout).json()
        patterns = _requests.get(f"{STA_BASE_URL}/api/patterns/{symbol}", timeout=timeout).json()
        context = _requests.get(f"{STA_BASE_URL}/api/context/SPY", timeout=timeout).json()
        earnings = _requests.get(f"{STA_BASE_URL}/api/earnings/{symbol}", timeout=timeout).json()
    except Exception as exc:
        logger.warning("STA fetch failed for %s: %s", symbol, exc)
        return jsonify({
            "status": "offline",
            "source": "manual",
            "message": f"STA not reachable at {STA_BASE_URL} — use Manual mode",
        })

    # STA /api/sr/<ticker> uses camelCase top-level fields — no nested "levels" object
    meta = sr.get("meta", {})
    vcp = patterns.get("patterns", {}).get("vcp", {})

    # FOMC days from context cycles cards
    fomc_days = None
    for card in context.get("cycles", {}).get("cards", []):
        if "FOMC" in card.get("name", ""):
            fomc_days = card.get("raw_value")
            break

    # swing_signal from trade viability
    viable = meta.get("tradeViability", {}).get("viable", "")
    swing_signal = "BUY" if viable == "YES" else "SELL"

    # nearest support level (last = closest to price)
    support_levels = sr.get("support", [])
    s1_support = support_levels[-1] if support_levels else None

    # SPY regime — compute from yfinance (not in STA API)
    spy_above_200sma = True  # safe default: don't penalize if we can't fetch
    spy_5day_return = None
    try:
        import yfinance as yf
        spy_hist = yf.Ticker("SPY").history(period="1y", interval="1d")
        if not spy_hist.empty and len(spy_hist) >= 200:
            latest_close = float(spy_hist["Close"].iloc[-1])
            sma200 = float(spy_hist["Close"].iloc[-200:].mean())
            spy_above_200sma = latest_close > sma200
            if len(spy_hist) >= 6:
                five_day_ago = float(spy_hist["Close"].iloc[-6])
                spy_5day_return = round((latest_close - five_day_ago) / five_day_ago * 100, 2)
    except Exception as exc:
        logger.warning("SPY regime fetch failed: %s", exc)  # keep defaults — don't fail sta_fetch

    return jsonify({
        "status": "ok",
        "source": "sta_live",
        "ticker": symbol,
        "swing_signal": swing_signal,
        "entry_pullback": sr.get("suggestedEntry"),
        "entry_momentum": stock.get("currentPrice"),
        "stop_loss": sr.get("suggestedStop"),
        "target1": sr.get("suggestedTarget"),
        "target2": None,  # STA provides single target
        "risk_reward": sr.get("riskReward"),
        "vcp_pivot": vcp.get("pivot_price"),
        "vcp_confidence": vcp.get("confidence"),
        "adx": meta.get("adx", {}).get("adx"),
        "last_close": stock.get("currentPrice"),
        "s1_support": s1_support,
        "spy_above_200sma": spy_above_200sma,
        "spy_5day_return": spy_5day_return,
        "earnings_days_away": earnings.get("days_until"),
        "pattern": patterns.get("pattern"),
        "fomc_days_away": fomc_days,
    })


@app.post("/api/integrate/status")
def integrate_status():
    return jsonify({"status": "ready", "accepts_swing_data": True, "version": VERSION})


@app.get("/api/integrate/ping")
def integrate_ping():
    return jsonify({"status": "ok", "version": VERSION, "accepts_swing_data": True})


@app.get("/api/integrate/schema")
def integrate_schema():
    schema = {
        "ticker": "str", "direction": "str", "account_size": "float", "risk_pct": "float",
        "planned_hold_days": "int", "swing_signal": "str", "entry_pullback": "float",
        "entry_momentum": "float", "stop_loss": "float", "target1": "float", "target2": "float",
        "risk_reward": "float", "vcp_pivot": "float", "vcp_confidence": "float", "adx": "float",
        "last_close": "float", "s1_support": "float", "spy_above_200sma": "bool",
        "spy_5day_return": "float", "earnings_days_away": "int", "pattern": "str",
    }
    return jsonify(schema)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=False)
