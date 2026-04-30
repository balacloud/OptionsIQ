"""
data_health_service.py — Data provenance health check.

Returns live status for every data source: IBKR, VIX, SPY regime, FOMC,
IV history DB, chain cache, Alpaca, MarketData.app.

Rule 11: Returns null for missing data — never fabricates plausible values.
Rule 4: No business logic in app.py — this module is called by a thin route.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from analyze_service import _days_until_next_fomc, get_vix_status
from constants import ETF_TICKERS, FOMC_DATES


def build_data_health(
    *,
    iv_store,
    data_svc,
    ib_worker,
    md_provider,
    alpaca_provider,
) -> dict:
    """
    Assembles provenance data for all sources. No IBKR calls — reads existing state only.
    Fast: completes in <200ms regardless of connection state.
    """
    as_of = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ── IBKR ──────────────────────────────────────────────────────────────────
    ib_status = data_svc.ibkr_status()
    cb = data_svc.cb_status()
    connected = ib_status.get("connected", False)
    ibkr_section = {
        "status": "connected" if connected else "disconnected",
        "connected": connected,
        "mode": "live" if connected else "mock",
        "error": ib_status.get("error"),
        "circuit_breaker": {
            "open": cb.get("open", False),
            "failures": cb.get("failures", 0),
            "seconds_remaining": cb.get("seconds_remaining", 0),
        },
    }

    # ── VIX ───────────────────────────────────────────────────────────────────
    vix_section = get_vix_status()

    # ── SPY Regime ────────────────────────────────────────────────────────────
    try:
        from sector_scan_service import _spy_regime
        regime = _spy_regime()
        above = regime.get("spy_above_200sma")
        ret = regime.get("spy_5day_return")
        spy_section = {
            "status": "ok" if above is not None else "null",
            "above_200sma": above,
            "five_day_return": ret,
            "regime_warning": regime.get("regime_warning"),
            "source": "sta" if above is not None else "unavailable",
        }
    except Exception:
        spy_section = {
            "status": "error", "above_200sma": None,
            "five_day_return": None, "regime_warning": None, "source": "unavailable",
        }

    # ── FOMC ──────────────────────────────────────────────────────────────────
    days_away = _days_until_next_fomc()
    today = datetime.now(timezone.utc).date()
    next_fomc = None
    for d in sorted(FOMC_DATES):
        from datetime import date as _date
        from datetime import datetime as _dt
        meeting = _dt.strptime(d, "%Y-%m-%d").date()
        if meeting >= today:
            next_fomc = d
            break
    fomc_section = {
        "status": "ok",
        "next_date": next_fomc,
        "days_away": days_away,
        "source": "constants",
    }

    # ── Third-party providers ─────────────────────────────────────────────────
    alpaca_section = {
        "status": "ok" if alpaca_provider is not None else "unavailable",
    }
    md_section = {
        "status": "ok" if (md_provider and md_provider.available()) else "unavailable",
    }

    # ── IV History (per ETF) ──────────────────────────────────────────────────
    tickers = sorted(ETF_TICKERS)
    iv_history: dict = {}
    for ticker in tickers:
        stats = iv_store.get_iv_stats(ticker)
        ohlcv = iv_store.get_ohlcv_stats(ticker)
        hv = iv_store.compute_hv(ticker, 20)
        iv_history[ticker] = {
            **stats,
            "hv_20": hv,
            "hv_status": "ok" if hv is not None else ("insufficient_bars" if ohlcv["rows"] > 0 else "no_ohlcv"),
            "ohlcv_rows": ohlcv["rows"],
        }

    # ── Chain Cache (per ETF) ─────────────────────────────────────────────────
    chain_cache = data_svc.get_cache_stats(tickers)

    # ── Field-level resolution (per ETF) ─────────────────────────────────────
    # For each analysis field: which source actually populates it right now?
    # This tells the trader exactly what data quality goes into each gate decision.
    md_ok = md_provider and md_provider.available()
    field_resolution: dict = {}
    for ticker in tickers:
        cc = chain_cache.get(ticker, {})
        ih = iv_history.get(ticker, {})

        # Chain / implied vol — from IBKR cache, or yfinance if stale/missing
        if connected:
            chain_src = "ibkr_live"
            chain_note = "live from IB Gateway"
            chain_status = "ok"
        elif cc.get("status") == "fresh":
            chain_src = "ibkr_cache"
            chain_note = f"cached {cc.get('age_minutes', '?')}m ago"
            chain_status = "ok"
        elif cc.get("status") == "stale":
            chain_src = "ibkr_stale → yfinance"
            chain_note = f"IBKR stale ({cc.get('age_minutes', '?')}m) — yfinance on next analyze"
            chain_status = "stale"
        else:
            chain_src = "yfinance"
            chain_note = "no IBKR cache — yfinance fallback"
            chain_status = "stale"

        # OI / Volume
        if md_ok:
            oi_src = "MarketData.app"
            oi_note = "REST supplement"
            oi_status = "ok"
        elif connected:
            oi_src = "IBKR (usually 0)"
            oi_note = "IBKR OI via reqMktData — typically 0 (platform limitation)"
            oi_status = "warn"
        else:
            oi_src = "unavailable"
            oi_note = "IBKR disconnected + no MarketData.app key"
            oi_status = "null"

        # HV-20
        hv_val = ih.get("hv_20")
        ohlcv_rows = ih.get("ohlcv_rows", 0)
        if hv_val is not None:
            hv_src = f"ohlcv_db ({ohlcv_rows} bars)"
            hv_note = f"{hv_val}% annualised"
            hv_status = "ok"
        elif ohlcv_rows > 0:
            hv_src = f"ohlcv_db ({ohlcv_rows} bars)"
            hv_note = "insufficient bars for 20-day window"
            hv_status = "stale"
        else:
            hv_src = "unavailable"
            hv_note = "no OHLCV data stored"
            hv_status = "null"

        # IVR
        iv_rows = ih.get("rows", 0)
        if iv_rows >= 30:
            ivr_src = f"iv_history_db ({iv_rows} rows)"
            ivr_note = "percentile rank — requires current_iv from chain on each analyze"
            ivr_status = "ok"
        elif iv_rows > 0:
            ivr_src = f"iv_history_db ({iv_rows} rows)"
            ivr_note = f"only {iv_rows} rows — need 30+ for IVR percentile"
            ivr_status = "stale"
        else:
            ivr_src = "unavailable"
            ivr_note = "no IV history — run /api/admin/seed-iv/all to populate"
            ivr_status = "null"

        # VIX — same for all ETFs, from module-level cache
        vix_src = vix_section.get("source") or "unavailable"
        vix_status = vix_section.get("status", "null")
        vix_note = f"value: {vix_section.get('value')}" if vix_section.get("value") else "not yet fetched this session"

        # SPY Regime — same for all ETFs
        spy_src = spy_section.get("source", "unavailable")
        spy_status = spy_section.get("status", "null")
        spy_note = (
            f"above_200sma={spy_section.get('above_200sma')}, "
            f"5d={spy_section.get('five_day_return')}%"
            if spy_section.get("above_200sma") is not None else "STA offline"
        )

        # FOMC — same for all ETFs
        fomc_note = f"{days_away} days to next meeting ({next_fomc})"
        fomc_status = "warn" if days_away <= 14 else "ok"

        field_resolution[ticker] = {
            "underlying_price":  {"source": "sta",    "note": f"STA /api/stock/{ticker} currentPrice — precedence: payload last_close → STA → IBKR", "status": "ok"},
            "chain_implied_vol": {"source": chain_src, "note": chain_note, "status": chain_status},
            "oi_volume":         {"source": oi_src,   "note": oi_note,   "status": oi_status},
            "hv_20":             {"source": hv_src,   "note": hv_note,   "status": hv_status},
            "ivr":               {"source": ivr_src,  "note": ivr_note,  "status": ivr_status},
            "vix":               {"source": vix_src,  "note": vix_note,  "status": vix_status},
            "spy_regime":        {"source": spy_src,  "note": spy_note,  "status": spy_status},
            "fomc":              {"source": "constants", "note": fomc_note, "status": fomc_status},
        }

    return {
        "as_of": as_of,
        "sources": {
            "ibkr": ibkr_section,
            "vix": vix_section,
            "spy_regime": spy_section,
            "fomc": fomc_section,
            "alpaca": alpaca_section,
            "marketdata_app": md_section,
        },
        "iv_history": iv_history,
        "chain_cache": chain_cache,
        "field_resolution": field_resolution,
    }
