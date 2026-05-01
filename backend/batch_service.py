"""
batch_service.py — BOD and EOD batch jobs for OptionsIQ.

BOD (9:31 AM ET, Mon-Fri): pre-fetch all 16 ETF chains → SQLite cache
EOD (4:05 PM ET, Mon-Fri): seed IV history + OHLCV for all 16 ETFs via IBKR

Both jobs log to batch_run_log table (iv_store). Results visible in Data Provenance dashboard.
"""
from __future__ import annotations

import logging
import time

from constants import ETF_TICKERS

logger = logging.getLogger(__name__)


def seed_iv_for_ticker(symbol: str, *, ib_worker, yf_provider, iv_store) -> dict:
    """Seed IV history + OHLCV for one ticker. IBKR primary, yfinance fallback."""
    connected = ib_worker.is_connected() and ib_worker.provider is not None
    hist = []
    source = "none"

    if connected:
        try:
            hist = ib_worker.submit(ib_worker.provider.get_historical_iv, symbol, 365, timeout=30.0)
            source = "ibkr"
        except Exception as exc:
            logger.warning("seed-iv IBKR failed for %s: %s", symbol, exc)

    if not hist:
        try:
            hist = yf_provider.get_historical_iv(symbol, 365)
            source = "yfinance"
        except Exception as exc:
            logger.warning("seed-iv yfinance fallback failed for %s: %s", symbol, exc)

    for row in hist:
        iv_store.store_iv(symbol, row["date"], row["iv"], source=source)

    ohlcv_rows = 0
    ohlcv_source = "none"
    if connected:
        try:
            bars = ib_worker.submit(ib_worker.provider.get_ohlcv_daily, symbol, 90, timeout=30.0)
            if bars:
                iv_store.store_ohlcv(symbol, bars)
                ohlcv_rows = len(bars)
                ohlcv_source = "ibkr"
        except Exception as exc:
            logger.warning("seed-iv OHLCV IBKR failed for %s: %s", symbol, exc)

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
        "seeded_days": len(hist),
        "source": source,
        "earliest_date": hist[0]["date"] if hist else None,
        "latest_date": hist[-1]["date"] if hist else None,
        "ohlcv_rows": ohlcv_rows,
        "ohlcv_source": ohlcv_source,
    }


def run_eod_batch(*, ib_worker, yf_provider, iv_store) -> dict:
    """EOD: seed IV + OHLCV for all 16 ETFs. Logs result to batch_run_log."""
    t0 = time.monotonic()
    tickers = sorted(ETF_TICKERS)
    results = []
    errors = []

    logger.info("EOD batch starting — %d ETFs", len(tickers))

    for i, ticker in enumerate(tickers):
        try:
            r = seed_iv_for_ticker(ticker, ib_worker=ib_worker, yf_provider=yf_provider, iv_store=iv_store)
            results.append(r)
            logger.info("EOD %s — %d IV days, %d OHLCV rows", ticker, r["seeded_days"], r["ohlcv_rows"])
        except Exception as exc:
            logger.error("EOD batch: %s failed — %s", ticker, exc)
            errors.append({"ticker": ticker, "error": str(exc)})
        if i < len(tickers) - 1:
            time.sleep(2)  # IBKR pacing: max ~60 historical requests per 10 min

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


def run_bod_batch(*, ib_worker, data_svc, iv_store) -> dict:
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
