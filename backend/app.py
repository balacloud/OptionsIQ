from __future__ import annotations

import os
import logging
import time
from pathlib import Path

# load_dotenv MUST run before any project module imports — those modules read
# os.getenv() at import time (module-level constants). Loading .env after the
# imports means those constants are always empty string.
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().with_name(".env"))

import requests as _requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from constants import STA_BASE_URL, ETF_TICKERS
from sector_scan_service import scan_sectors, analyze_sector_etf, _spy_regime
from data_service import DataService
from gate_engine import GateEngine
from ib_worker import IBWorker
from iv_store import IVStore
from alpaca_provider import AlpacaNotAvailableError, AlpacaProvider
from marketdata_provider import MarketDataProvider
from mock_provider import MockProvider
from pnl_calculator import PnLCalculator
from strategy_ranker import StrategyRanker
from yfinance_provider import YFinanceProvider
from analyze_service import analyze_etf, get_live_price, _extract_iv_data

VERSION = "2.0"

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
_md_provider = MarketDataProvider()
if _md_provider.available():
    logger.info("MarketDataProvider ready (OI/volume supplement for Liquidity gate)")
else:
    logger.warning("MarketDataProvider: MARKET_DATA_KEY not set — OI/volume will remain 0")


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
    if ticker not in ETF_TICKERS:
        return jsonify({
            "error": f"{ticker} is not in the ETF universe",
            "etf_universe": sorted(ETF_TICKERS),
        }), 400
    try:
        result = analyze_etf(
            payload, ticker,
            data_svc=data_svc, ib_worker=_ib_worker,
            yf_provider=_yf_provider, mock_provider=mock_provider,
            strategy_ranker=strategy_ranker, pnl_calculator=pnl_calculator,
            iv_store=iv_store, spy_regime_fn=_spy_regime,
            md_provider=_md_provider,
        )
        return jsonify(result)
    except Exception as exc:
        logger.exception("analyze_options unhandled error for %s", ticker)
        return jsonify({"error": str(exc)}), 500


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
    data = _extract_iv_data(symbol, chain, iv_provider,
                            ib_worker=_ib_worker, mock_provider=mock_provider, iv_store=iv_store)
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
        underlying = get_live_price(t["ticker"], ib_worker=_ib_worker, yf_provider=_yf_provider)
        if t["direction"] == "sell_put":
            pnl = (float(t["premium"]) - max(0.0, float(t["strike"]) - underlying)) * 100 * float(t["lots"])
        else:
            pnl = (max(0.0, underlying - float(t["strike"])) - float(t["premium"])) * 100 * float(t["lots"])
        out.append({**t, "current_underlying": round(float(underlying), 2), "mark_to_market_pnl": round(float(pnl), 2)})
    return jsonify(out)


def _seed_iv_for_ticker(symbol: str) -> dict:
    """Seed IV history for one ticker. IBKR if connected, yfinance fallback."""
    connected = _ib_worker.is_connected() and _ib_worker.provider is not None
    hist = []
    source = "none"
    if connected:
        try:
            hist = _ib_worker.submit(_ib_worker.provider.get_historical_iv, symbol, 365, timeout=30.0)
            source = "ibkr"
        except Exception as exc:
            logger.warning("seed-iv IBKR failed for %s: %s", symbol, exc)
    if not hist:
        try:
            hist = _yf_provider.get_historical_iv(symbol, 365)
            source = "yfinance"
        except Exception as exc:
            logger.warning("seed-iv yfinance fallback failed for %s: %s", symbol, exc)
    for row in hist:
        iv_store.store_iv(symbol, row["date"], row["iv"], source=source)
    return {
        "ticker": symbol,
        "seeded_days": len(hist),
        "source": source,
        "earliest_date": hist[0]["date"] if hist else None,
        "latest_date": hist[-1]["date"] if hist else None,
    }


@app.post("/api/options/seed-iv/<ticker>")
def seed_iv(ticker: str):
    """Seeds IV history for a single ticker."""
    return jsonify(_seed_iv_for_ticker(ticker.upper()))


@app.post("/api/admin/seed-iv/all")
def seed_iv_all():
    """Nightly job — seeds IV history for all 16 ETFs from IBKR (yfinance fallback).
    2s pacing delay between tickers to stay within IBKR historical data limits."""
    results = []
    total_seeded = 0
    errors = []
    tickers = sorted(ETF_TICKERS)
    for i, ticker in enumerate(tickers):
        try:
            r = _seed_iv_for_ticker(ticker)
            results.append(r)
            total_seeded += r["seeded_days"]
            logger.info("seed-iv-all: %s — %d days from %s", ticker, r["seeded_days"], r["source"])
        except Exception as exc:
            logger.error("seed-iv-all: %s failed — %s", ticker, exc)
            errors.append({"ticker": ticker, "error": str(exc)})
        if i < len(tickers) - 1:
            time.sleep(2)  # IBKR pacing: max ~60 historical requests per 10 min
    sources = {r["source"] for r in results if r["source"] != "none"}
    return jsonify({
        "tickers_seeded": len(results),
        "total_iv_rows": total_seeded,
        "sources_used": sorted(sources),
        "pacing_warning": total_seeded == 0 and not errors,
        "errors": errors,
        "results": results,
    })


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

    meta = sr.get("meta", {})
    vcp = patterns.get("patterns", {}).get("vcp", {})

    fomc_days = None
    for card in context.get("cycles", {}).get("cards", []):
        if "FOMC" in card.get("name", ""):
            fomc_days = card.get("raw_value")
            break

    viable = meta.get("tradeViability", {}).get("viable", "")
    swing_signal = "BUY" if viable == "YES" else "SELL"

    support_levels = sr.get("support", [])
    s1_support = support_levels[-1] if support_levels else None

    spy_above_200sma = True
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
        logger.warning("SPY regime fetch failed: %s", exc)

    return jsonify({
        "status": "ok",
        "source": "sta_live",
        "ticker": symbol,
        "swing_signal": swing_signal,
        "entry_pullback": sr.get("suggestedEntry"),
        "entry_momentum": stock.get("currentPrice"),
        "stop_loss": sr.get("suggestedStop"),
        "target1": sr.get("suggestedTarget"),
        "target2": None,
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


# ---------------------------------------------------------------------------
# Sector Rotation ETF endpoints (Day 13)
# ---------------------------------------------------------------------------
@app.get("/api/sectors/scan")
def sectors_scan():
    """Level 1: All sector ETFs with quadrant, direction, action. < 2 sec (STA cached)."""
    result = scan_sectors(iv_store=iv_store)
    if result.get("error"):
        return jsonify(result), 503
    return jsonify(result)


@app.get("/api/sectors/analyze/<ticker>")
def sectors_analyze(ticker: str):
    """Level 2: Single ETF + IV/OI/spread overlay. 10-15 sec (IBKR)."""
    ticker = ticker.upper().strip()
    if ticker not in ETF_TICKERS:
        return jsonify({"error": f"{ticker} is not in the sector ETF universe"}), 400
    result = analyze_sector_etf(ticker, data_service=data_svc, ib_worker=_ib_worker, iv_store=iv_store)
    if result.get("error"):
        return jsonify(result), 503
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=False)
