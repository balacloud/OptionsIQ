"""
batch_service.py — BOD and EOD batch jobs for OptionsIQ.

BOD (9:31 AM ET, Mon-Fri): pre-fetch all 16 ETF chains → SQLite cache
EOD (4:05 PM ET, Mon-Fri): seed IV history + OHLCV for all 16 ETFs via IBKR

Both jobs log to batch_run_log table (iv_store). Results visible in Data Provenance dashboard.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, date, timedelta, time as dtime
from zoneinfo import ZoneInfo

from constants import ETF_TICKERS

_ET = ZoneInfo("America/New_York")
_BOD_TIME = dtime(9, 31)
_EOD_TIME = dtime(16, 5)

logger = logging.getLogger(__name__)


def seed_iv_for_ticker(symbol: str, *, yf_provider, iv_store, tradier_provider=None) -> dict:
    """Seed OHLCV for one ticker (used for HV computation).

    IV history via IBKR removed (IB Gateway dead since Day 56). IV is now accumulated
    per-analyze-call via MarketData.app. Do not use yfinance HV as IV proxy —
    HV ≠ IV and contaminates IVR percentiles.

    OHLCV: Tradier primary (markets/history) → yfinance fallback.
    """
    ohlcv_rows = 0
    ohlcv_source = "none"

    if ohlcv_rows == 0 and tradier_provider is not None:
        try:
            bars = tradier_provider.get_ohlcv_daily(symbol, 90)
            if bars:
                iv_store.store_ohlcv(symbol, bars)
                ohlcv_rows = len(bars)
                ohlcv_source = "tradier"
        except Exception as exc:
            logger.warning("seed-iv OHLCV Tradier failed for %s: %s", symbol, exc)

    if ohlcv_rows == 0:
        try:
            bars = yf_provider.get_ohlcv_daily(symbol, 90) if hasattr(yf_provider, "get_ohlcv_daily") else []
            if bars:
                iv_store.store_ohlcv(symbol, bars)
                ohlcv_rows = len(bars)
                ohlcv_source = "yfinance"
        except Exception as exc:
            logger.warning("seed-iv OHLCV yfinance fallback failed for %s: %s", symbol, exc)

    return {
        "ticker": symbol,
        "seeded_days": 0,
        "source": "marketdata_app",
        "ohlcv_rows": ohlcv_rows,
        "ohlcv_source": ohlcv_source,
    }


def run_eod_batch(*, yf_provider, iv_store, tradier_provider=None) -> dict:
    """EOD: seed IV + OHLCV for all ETFs. Logs result to batch_run_log."""
    t0 = time.monotonic()
    tickers = sorted(ETF_TICKERS)
    results = []
    errors = []

    logger.info("EOD batch starting — %d ETFs", len(tickers))

    for i, ticker in enumerate(tickers):
        try:
            r = seed_iv_for_ticker(ticker, yf_provider=yf_provider,
                                   iv_store=iv_store, tradier_provider=tradier_provider)
            results.append(r)
            logger.info("EOD %s — %d IV days, %d OHLCV rows (%s)", ticker, r["seeded_days"], r["ohlcv_rows"], r["ohlcv_source"])
        except Exception as exc:
            logger.error("EOD batch: %s failed — %s", ticker, exc)
            errors.append({"ticker": ticker, "error": str(exc)})
        if i < len(tickers) - 1:
            time.sleep(1)  # Tradier rate limit: 200 req/min — 1s gap is sufficient

    duration = time.monotonic() - t0
    status = "ok" if not errors else ("partial" if results else "failed")

    iv_store.log_batch_run(
        "eod", status, duration,
        tickers_ok=len(results), tickers_failed=len(errors),
        detail={"results": results, "errors": errors},
    )

    logger.info("EOD batch done — %d ok, %d failed, %.1fs", len(results), len(errors), duration)
    return {
        "status": status,
        "tickers_ok": len(results),
        "tickers_failed": len(errors),
        "duration_sec": round(duration, 1),
        "errors": errors,
    }


def run_bod_batch(*, data_svc, iv_store) -> dict:
    """BOD: pre-fetch all 16 ETF chains into SQLite cache. Warms cache for day's analysis."""
    t0 = time.monotonic()
    tickers = sorted(ETF_TICKERS)
    ok = []
    errors = []

    logger.info("BOD batch starting — pre-fetching %d ETF chains", len(tickers))

    for ticker in tickers:
        try:
            chain, source = data_svc.get_chain(ticker, profile="smart")
            contracts = len(chain.get("contracts", []))
            ok.append({"ticker": ticker, "source": source, "contracts": contracts})
            logger.info("BOD %s — %d contracts via %s", ticker, contracts, source)
        except Exception as exc:
            logger.error("BOD batch: %s failed — %s", ticker, exc)
            errors.append({"ticker": ticker, "error": str(exc)})

    duration = time.monotonic() - t0
    status = "ok" if not errors else ("partial" if ok else "failed")

    iv_store.log_batch_run(
        "bod", status, duration,
        tickers_ok=len(ok), tickers_failed=len(errors),
        detail={"results": ok, "errors": errors},
    )

    logger.info("BOD batch done — %d ok, %d failed, %.1fs", len(ok), len(errors), duration)
    return {
        "status": status,
        "tickers_ok": len(ok),
        "tickers_failed": len(errors),
        "duration_sec": round(duration, 1),
    }


def _prev_trading_date(ref: date) -> date:
    """Return the most recent weekday before ref (Mon→Fri, Mon→previous Friday)."""
    d = ref - timedelta(days=1)
    while d.weekday() > 4:  # Sat=5, Sun=6
        d -= timedelta(days=1)
    return d


def _ran_on(runs: list, batch_type: str, date_str: str, min_duration: float = 1.0) -> bool:
    """Return True if a substantive run of batch_type exists for date_str.

    Runs under min_duration seconds are cache-hit no-ops (IBKR not connected
    at time of run) and are not counted — catchup will re-fire with a live connection.
    """
    return any(
        r["batch_type"] == batch_type
        and r["ran_at"].startswith(date_str)
        and (r.get("duration_sec") or 0.0) >= min_duration
        for r in runs
    )


def run_startup_catchup(*, data_svc, yf_provider, iv_store, tradier_provider=None) -> None:
    """
    Called once at app startup in a background thread. Fires any BOD/EOD jobs
    that were missed because the backend wasn't running at scheduled time.

    Run order (all ET timezone checks):
      1. Previous trading day EOD missing → seed IV history now (closes gap before analysis)
      2. Today's BOD missing + past 9:31 AM → pre-warm chain cache
      3. Today's EOD missing + past 4:05 PM → seed today's closing IV

    Waits 30s on startup before firing any missed jobs.
    IB Gateway auth can take 20-30s, so 10s was insufficient.
    Note: the APScheduler BOD/EOD jobs fire unconditionally at their scheduled
    times — this function only fills gaps when the app wasn't running.
    """
    def _run():
        time.sleep(30)
        now_et = datetime.now(_ET)

        if now_et.weekday() > 4:
            logger.info("Startup catch-up: weekend — skipping")
            return

        today_str = now_et.date().isoformat()
        prev_str = _prev_trading_date(now_et.date()).isoformat()
        current_time = now_et.time()
        runs = iv_store.get_batch_runs(limit=30)

        # 1. Previous trading day EOD — seeds IV history gap before any analysis
        if not _ran_on(runs, "eod", prev_str):
            logger.info("Startup catch-up: EOD missing for %s — seeding IV history now", prev_str)
            try:
                run_eod_batch(yf_provider=yf_provider,
                              iv_store=iv_store, tradier_provider=tradier_provider)
                runs = iv_store.get_batch_runs(limit=30)
            except Exception as exc:
                logger.error("Startup catch-up prev-day EOD failed: %s", exc)

        # 2. Today's BOD missed
        if current_time >= _BOD_TIME and not _ran_on(runs, "bod", today_str):
            logger.info("Startup catch-up: BOD missed today — firing now")
            try:
                run_bod_batch(data_svc=data_svc, iv_store=iv_store)
                runs = iv_store.get_batch_runs(limit=30)
            except Exception as exc:
                logger.error("Startup catch-up BOD failed: %s", exc)

        # 3. Today's EOD missed (only relevant if app starts after market close)
        if current_time >= _EOD_TIME and not _ran_on(runs, "eod", today_str):
            logger.info("Startup catch-up: EOD missed today — firing now")
            try:
                run_eod_batch(yf_provider=yf_provider,
                              iv_store=iv_store, tradier_provider=tradier_provider)
            except Exception as exc:
                logger.error("Startup catch-up today EOD failed: %s", exc)

        logger.info("Startup catch-up complete")

    threading.Thread(target=_run, name="startup-catchup", daemon=True).start()
