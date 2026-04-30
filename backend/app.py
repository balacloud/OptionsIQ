from __future__ import annotations

import os
import logging
import time
import concurrent.futures
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
from analyze_service import analyze_etf, get_live_price, _extract_iv_data, get_vix_status, _fetch_vix
from data_health_service import build_data_health

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


@app.patch("/api/options/paper-trade/<int:trade_id>")
def update_paper_trade(trade_id: int):
    """Update mark price and/or mark a trade as closed."""
    body = request.get_json(silent=True) or {}
    mark_price = body.get("mark_price")
    closed = bool(body.get("closed", False))
    if mark_price is None and not closed:
        return jsonify({"success": False, "error": "Provide mark_price or closed=true"}), 400
    ok = iv_store.update_paper_trade(trade_id, mark_price=mark_price, closed=closed)
    return jsonify({"success": ok})


@app.delete("/api/options/paper-trade/<int:trade_id>")
def delete_paper_trade(trade_id: int):
    ok = iv_store.delete_paper_trade(trade_id)
    return jsonify({"success": ok})


@app.get("/api/options/paper-trades/summary")
def paper_trades_summary():
    return jsonify(iv_store.get_paper_trades_summary())


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
    """Seed IV history + OHLCV for one ticker. IBKR if connected, yfinance fallback."""
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

    # Also seed OHLCV — needed for HV-20 and McMillan stress check
    ohlcv_rows = 0
    ohlcv_source = "none"
    if connected:
        try:
            bars = _ib_worker.submit(_ib_worker.provider.get_ohlcv_daily, symbol, 90, timeout=30.0)
            if bars:
                iv_store.store_ohlcv(symbol, bars)
                ohlcv_rows = len(bars)
                ohlcv_source = "ibkr"
        except Exception as exc:
            logger.warning("seed-iv OHLCV IBKR failed for %s: %s", symbol, exc)
    if ohlcv_rows == 0:
        try:
            bars = _yf_provider.get_ohlcv_daily(symbol, 90) if hasattr(_yf_provider, "get_ohlcv_daily") else []
            if bars:
                iv_store.store_ohlcv(symbol, bars)
                ohlcv_rows = len(bars)
                ohlcv_source = "yfinance"
        except Exception as exc:
            logger.warning("seed-iv OHLCV yfinance fallback failed for %s: %s", symbol, exc)

    return {
        "ticker": symbol,
        "seeded_days": len(hist),
        "source": source,
        "earliest_date": hist[0]["date"] if hist else None,
        "latest_date": hist[-1]["date"] if hist else None,
        "ohlcv_rows": ohlcv_rows,
        "ohlcv_source": ohlcv_source,
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
    _fetch_vix()  # warm cache if cold; 5-min TTL means this is cheap on repeat calls
    result["vix"] = get_vix_status()
    return jsonify(result)


@app.get("/api/best-setups")
def best_setups():
    """
    Scan all ETFs using their sector-suggested direction, run gate analysis in parallel,
    return top GO/CAUTION results ranked by gate pass rate.
    Max 8 parallel workers — IBKR pacing safe.
    """
    scan = scan_sectors(iv_store=iv_store)
    if scan.get("error"):
        return jsonify({"error": scan["error"]}), 503

    candidates = [
        s for s in scan.get("sectors", [])
        if s.get("suggested_direction") and s.get("action") == "ANALYZE"
    ]

    account_size = float(os.getenv("ACCOUNT_SIZE", 25000))

    def _run_one(s):
        ticker = s["etf"]
        direction = s["suggested_direction"]
        # Pre-fetch underlying price from STA to bypass IBKR reqMktData snapshot call.
        # Without this, all 8 parallel scans call get_underlying_price() simultaneously
        # via IBWorker, fail (bid/ask/last all None in 1.2s window), and trip the circuit breaker.
        last_close = None
        try:
            sta_stock = _requests.get(f"{STA_BASE_URL}/api/stock/{ticker}", timeout=3)
            last_close = sta_stock.json().get("currentPrice")
        except Exception:
            pass
        payload = {
            "ticker": ticker,
            "direction": direction,
            "account_size": account_size,
            "risk_pct": float(os.getenv("RISK_PCT", 0.01)),
            "planned_hold_days": 21,
            **({"last_close": last_close} if last_close else {}),
        }
        try:
            result = analyze_etf(
                payload, ticker,
                data_svc=data_svc, ib_worker=_ib_worker,
                yf_provider=_yf_provider, mock_provider=mock_provider,
                strategy_ranker=strategy_ranker, pnl_calculator=pnl_calculator,
                iv_store=iv_store, spy_regime_fn=_spy_regime,
                md_provider=_md_provider,
            )
            verdict = result.get("verdict", {})
            gates = result.get("gates", [])
            passed = sum(1 for g in gates if g.get("status") == "pass")
            total = len(gates)
            failed = [g.get("name") or g.get("label", "?") for g in gates if g.get("status") == "fail"]
            top = (result.get("top_strategies") or [{}])[0]
            # Normalize color: gate_engine returns "amber" but frontend expects "yellow" for CAUTION
            raw_color = verdict.get("color", "red")
            color = "yellow" if raw_color == "amber" else raw_color
            label_map = {"green": "GO", "yellow": "CAUTION", "red": "BLOCKED"}
            return {
                "ticker": ticker,
                "direction": direction,
                "quadrant": s.get("quadrant"),
                "name": s.get("name"),
                "verdict_color": color,
                "verdict_label": label_map.get(color, "BLOCKED"),
                "data_source": result.get("data_source"),
                "pass_rate": round(passed / total * 100) if total else 0,
                "gates_passed": passed,
                "gates_total": total,
                "failed_gates": failed,
                "ivr": result.get("ivr_data", {}).get("ivr_pct"),
                "iv_hv_ratio": result.get("ivr_data", {}).get("hv_iv_ratio"),
                "hv_20": result.get("ivr_data", {}).get("hv_20"),
                "current_iv": result.get("ivr_data", {}).get("current_iv"),
                "premium": top.get("premium"),
                "premium_per_lot": top.get("premium_per_lot"),
                "strike_display": top.get("strike_display"),
                "expiry_display": top.get("expiry_display"),
                "credit_to_width_ratio": top.get("credit_to_width_ratio"),
                "strategy_type": top.get("strategy_type"),
                "vix": (result.get("vix") or {}).get("value"),
                "error": None,
            }
        except Exception as exc:
            logger.warning("best-setups: %s/%s failed — %s", ticker, direction, exc)
            return {"ticker": ticker, "direction": direction, "quadrant": s.get("quadrant"), "error": str(exc)}

    # max_workers=1: IBWorker is single-threaded — parallel workers just create a queue
    # where later requests race against their 40s expiry. Sequential gives every ETF
    # the full IBWorker without contention. Scan takes ~3-4 min but data quality is real.
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        results = list(pool.map(_run_one, candidates))

    order = {"green": 0, "yellow": 1, "red": 2, None: 3}
    good = [r for r in results if not r.get("error") and r.get("verdict_color") in ("green", "yellow")]
    good.sort(key=lambda r: (order.get(r["verdict_color"], 3), -r.get("pass_rate", 0)))

    return jsonify({
        "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidates_scanned": len(candidates),
        "setups": good[:8],
        "all_results": results,
    })


@app.get("/api/data-health")
def data_health():
    """Data provenance — live status of every data source. No IBKR calls; reads cached state."""
    return jsonify(build_data_health(
        iv_store=iv_store, data_svc=data_svc,
        ib_worker=_ib_worker, md_provider=_md_provider, alpaca_provider=_alpaca_provider,
    ))


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
