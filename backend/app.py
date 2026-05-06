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
from tradier_provider import TradierProvider, TradierNotAvailableError
from marketdata_provider import MarketDataProvider
from mock_provider import MockProvider
from pnl_calculator import PnLCalculator
from strategy_ranker import StrategyRanker
from yfinance_provider import YFinanceProvider
from analyze_service import analyze_etf, get_live_price, _extract_iv_data, get_vix_status, _fetch_vix
from data_health_service import build_data_health
from batch_service import seed_iv_for_ticker, run_eod_batch, run_bod_batch, run_startup_catchup
from best_setups_service import run_one_setup

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
    logger.info("AlpacaProvider initialised (tier 3 fallback)")
except AlpacaNotAvailableError as _e:
    _alpaca_provider = None
    logger.warning("AlpacaProvider unavailable: %s", _e)

_tradier_key = os.getenv("TRADIER_KEY")
_tradier_ok: bool = False
_tradier_error: str | None = None
if _tradier_key:
    _tradier_provider = TradierProvider(_tradier_key)
    logger.info("TradierProvider initialised (tier 2 fallback — real-time)")
    try:
        _tradier_provider.get_underlying_price("QQQ")
        _tradier_ok = True
        logger.info("TradierProvider health check passed")
    except Exception as _te:
        _tradier_error = str(_te)
        logger.warning("TradierProvider health check FAILED: %s", _te)
else:
    _tradier_provider = None
    _tradier_error = "TRADIER_KEY not configured"
    logger.warning("TradierProvider: TRADIER_KEY not set — Tradier fallback disabled")

data_svc = DataService(
    ib_worker=_ib_worker,
    yf_provider=_yf_provider,
    mock_provider=mock_provider,
    alpaca_provider=_alpaca_provider,
    tradier_provider=_tradier_provider,
)
_md_provider = MarketDataProvider()
if _md_provider.available():
    logger.info("MarketDataProvider ready (OI/volume supplement for Liquidity gate)")
else:
    logger.warning("MarketDataProvider: MARKET_DATA_KEY not set — OI/volume will remain 0")

# ─── Scheduler (BOD 9:31 AM ET + EOD 4:05 PM ET, Mon-Fri) ────────────────────
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler = BackgroundScheduler(timezone="America/New_York")
_scheduler.add_job(
    lambda: run_bod_batch(ib_worker=_ib_worker, data_svc=data_svc, iv_store=iv_store),
    CronTrigger(day_of_week="mon-fri", hour=9, minute=31),
    id="bod_batch", replace_existing=True,
)
_scheduler.add_job(
    lambda: run_eod_batch(ib_worker=_ib_worker, yf_provider=_yf_provider, iv_store=iv_store),
    CronTrigger(day_of_week="mon-fri", hour=16, minute=5),
    id="eod_batch", replace_existing=True,
)
_scheduler.start()
logger.info("Scheduler started — BOD 09:31 ET, EOD 16:05 ET (Mon-Fri)")

run_startup_catchup(
    ib_worker=_ib_worker, data_svc=data_svc,
    yf_provider=_yf_provider, iv_store=iv_store,
)


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
            "tradier_ok": _tradier_ok,
            "tradier_error": _tradier_error,
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


@app.post("/api/options/seed-iv/<ticker>")
def seed_iv(ticker: str):
    """Seeds IV history for a single ticker."""
    return jsonify(seed_iv_for_ticker(
        ticker.upper(), ib_worker=_ib_worker, yf_provider=_yf_provider, iv_store=iv_store
    ))


@app.post("/api/admin/seed-iv/all")
def seed_iv_all():
    """EOD job — seeds IV history + OHLCV for all 16 ETFs. Delegates to batch_service."""
    result = run_eod_batch(ib_worker=_ib_worker, yf_provider=_yf_provider, iv_store=iv_store)
    return jsonify(result)


@app.post("/api/admin/warm-cache")
def warm_cache():
    """BOD job — pre-fetches all 16 ETF chains into SQLite cache."""
    result = run_bod_batch(ib_worker=_ib_worker, data_svc=data_svc, iv_store=iv_store)
    return jsonify(result)


@app.get("/api/admin/batch-status")
def batch_status():
    """Batch run history + next scheduled run times. Used by Data Provenance dashboard."""
    runs = iv_store.get_batch_runs(limit=10)
    bod_job = _scheduler.get_job("bod_batch")
    eod_job = _scheduler.get_job("eod_batch")
    return jsonify({
        "recent_runs": runs,
        "next_bod": bod_job.next_run_time.isoformat() if bod_job and bod_job.next_run_time else None,
        "next_eod": eod_job.next_run_time.isoformat() if eod_job and eod_job.next_run_time else None,
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
    Scan all ETFs using their sector-suggested direction, run gate analysis sequentially,
    return top GO/CAUTION results ranked by gate pass rate.
    Sequential (max_workers=1): IBWorker is single-threaded; parallel workers race against
    the 40s expiry timeout. Sequential gives every ETF full IBWorker without contention.
    """
    scan = scan_sectors(iv_store=iv_store)
    if scan.get("error"):
        return jsonify({"error": scan["error"]}), 503

    candidates = [
        s for s in scan.get("sectors", [])
        if s.get("suggested_direction") and s.get("action") == "ANALYZE"
    ]

    account_size = float(os.getenv("ACCOUNT_SIZE", 25000))
    risk_pct = float(os.getenv("RISK_PCT", 0.01))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        results = list(pool.map(
            lambda s: run_one_setup(
                s,
                data_svc=data_svc, ib_worker=_ib_worker,
                yf_provider=_yf_provider, mock_provider=mock_provider,
                strategy_ranker=strategy_ranker, pnl_calculator=pnl_calculator,
                iv_store=iv_store, spy_regime_fn=_spy_regime,
                md_provider=_md_provider,
                account_size=account_size, risk_pct=risk_pct,
            ),
            candidates,
        ))

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
