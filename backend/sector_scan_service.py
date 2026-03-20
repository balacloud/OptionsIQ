"""
OptionsIQ — Sector Rotation Scan Service
Consumes STA /api/sectors/rotation + adds options-specific analysis.

Endpoints served (wired in app.py):
    GET /api/sectors/scan             → Level 1: all ETFs with quadrant + direction
    GET /api/sectors/analyze/<ticker> → Level 2: single ETF + IV/OI/spread overlay

Level 3 reuses existing POST /api/options/analyze — zero new code.

Design: docs/Research/Sector_Rotation_ETF_Module_Day11.md
Research: docs/Research/Sector_ETF_Options_Research_Prompt_Day13.md
"""

import logging
import requests
from datetime import datetime, date

from constants import (
    STA_BASE_URL, STA_TIMEOUT_SEC,
    ETF_TICKERS, TQQQ_MAX_DTE,
    ETF_DTE_LOW_IVR, ETF_DTE_HIGH_IVR, ETF_DTE_DEFAULT,
    FOMC_HIGH_SENSITIVITY, FOMC_WARN_DAYS, FOMC_DATES,
    HIGH_DIVIDEND_ETFS, DIVIDEND_WARN_DAYS,
    CYCLICAL_SECTORS, DEFENSIVE_SECTORS,
    QUADRANT_ANALYZE, QUADRANT_WATCH, QUADRANT_SKIP,
    IVR_BUYER_PASS_PCT,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Quadrant → direction mapping (research-verified Day 13)
# ---------------------------------------------------------------------------
def quadrant_to_direction(quadrant, ivr=None):
    """
    Research-verified mapping (3-model consensus):
    - Leading  → buy_call (bull_call_spread if IVR > 50)
    - Improving → bull_call_spread (defined risk, 60 DTE)
    - Weakening → None (WAIT — still RS>100, not bearish)
    - Lagging   → None (SKIP — ETFs mean-revert too fast for puts)
    """
    if quadrant == "Leading":
        if ivr is not None and ivr >= 50:
            return "bull_call_spread"
        return "buy_call"
    elif quadrant == "Improving":
        return "bull_call_spread"
    # Weakening and Lagging: no position
    return None


def quadrant_to_action(quadrant):
    """ANALYZE / WATCH / SKIP based on research consensus."""
    if quadrant in QUADRANT_ANALYZE:
        return "ANALYZE"
    elif quadrant in QUADRANT_WATCH:
        return "WATCH"
    return "SKIP"


def suggested_dte(ivr, ticker):
    """
    tastylive 2-tier DTE (VERIFIED: Aug 2024 article):
        IVR < 30 → 60 DTE,  IVR >= 30 → 30 DTE
    TQQQ: max 45 DTE (VERIFIED: volatility decay)
    """
    if ivr is None:
        dte = ETF_DTE_DEFAULT
    elif ivr < IVR_BUYER_PASS_PCT:
        dte = ETF_DTE_LOW_IVR
    else:
        dte = ETF_DTE_HIGH_IVR

    if ticker == "TQQQ":
        dte = min(dte, TQQQ_MAX_DTE)
    return dte


def _size_bias_label(size_signal):
    """Advisory label only — NOT a gate or direction override (research: unvalidated as options signal)."""
    if size_signal == "Risk-On":
        return "Cyclicals favored (XLI, XLY, XLB)"
    elif size_signal == "Risk-Off":
        return "Defensives favored (XLU, XLV, XLP) + QQQ"
    return None


def _catalyst_warnings(ticker):
    """Build catalyst warnings for FOMC and dividend proximity."""
    warnings = []
    today = date.today()

    # FOMC proximity (VERIFIED: QuantSeeker)
    if ticker in FOMC_HIGH_SENSITIVITY:
        for d in FOMC_DATES:
            fomc_date = date.fromisoformat(d)
            days_until = (fomc_date - today).days
            if 0 <= days_until <= FOMC_WARN_DAYS:
                warnings.append(
                    f"FOMC in {days_until}d — {ticker} is highly rate-sensitive. "
                    "Expect 2-4% move. Consider spreads over naked positions."
                )
                break

    # Dividend ex-date: we don't have the exact dates, so just flag high-yield ETFs
    if ticker in HIGH_DIVIDEND_ETFS:
        warnings.append(
            f"{ticker} pays quarterly dividends (yield >1.4%). "
            "Check ex-date before selling calls — early assignment risk if ITM."
        )

    # TQQQ decay warning
    if ticker == "TQQQ":
        warnings.append(
            "3x leveraged ETF — volatility decay ~3×σ²/day. "
            "Max 45 DTE. No covered calls. Bear call spreads preferred."
        )

    return warnings


# ---------------------------------------------------------------------------
# Level 1: Quick Scan (< 2 sec — STA data only)
# ---------------------------------------------------------------------------
def scan_sectors():
    """
    Fetch all sector rotation data from STA and add options-layer annotations.
    Returns dict with sectors, size_rotation, size_signal, size_bias.
    """
    try:
        resp = requests.get(
            f"{STA_BASE_URL}/api/sectors/rotation",
            timeout=STA_TIMEOUT_SEC + 2,  # slightly longer for bulk data
        )
        resp.raise_for_status()
        sta_data = resp.json()
    except Exception as exc:
        logger.warning("STA sectors/rotation fetch failed: %s", exc)
        return {
            "error": f"STA not reachable at {STA_BASE_URL}",
            "sta_status": "offline",
        }

    sectors_raw = sta_data.get("sectors", [])
    size_rotation = sta_data.get("size_rotation", [])
    size_signal = sta_data.get("size_signal", "Neutral")

    sectors = []
    for s in sectors_raw:
        etf = s.get("etf", "")
        quadrant = s.get("quadrant", "Lagging")
        direction = quadrant_to_direction(quadrant)
        action = quadrant_to_action(quadrant)
        catalyst = _catalyst_warnings(etf)

        sectors.append({
            "etf": etf,
            "name": s.get("name", ""),
            "rank": s.get("rank", 99),
            "rs_ratio": s.get("rsRatio", 0),
            "rs_momentum": s.get("rsMomentum", 0),
            "quadrant": quadrant,
            "price": s.get("price", 0),
            "week_change": s.get("weekChange", 0),
            "month_change": s.get("monthChange", 0),
            "suggested_direction": direction,
            "action": action,
            "catalyst_warnings": catalyst if catalyst else None,
        })

    # Add cap-size ETFs (QQQ, IWM, MDY) from size_rotation
    for sr in size_rotation:
        etf = sr.get("etf", "")
        # Cap-size ETFs don't have a quadrant — derive from RS
        rs = sr.get("rsRatio", 100)
        mom = sr.get("rsMomentum", 0)
        if rs >= 100 and mom >= 0:
            quad = "Leading"
        elif rs >= 100:
            quad = "Weakening"
        elif mom >= 0:
            quad = "Improving"
        else:
            quad = "Lagging"

        direction = quadrant_to_direction(quad)
        action = quadrant_to_action(quad)
        catalyst = _catalyst_warnings(etf)

        sectors.append({
            "etf": etf,
            "name": f"Cap-Size ({etf})",
            "rank": None,
            "rs_ratio": rs,
            "rs_momentum": mom,
            "quadrant": quad,
            "price": sr.get("price", 0),
            "week_change": sr.get("weekChange", 0),
            "month_change": sr.get("monthChange", 0),
            "suggested_direction": direction,
            "action": action,
            "catalyst_warnings": catalyst if catalyst else None,
        })

    # TQQQ: always include with special rules
    tqqq_entry = next((s for s in sectors if s["etf"] == "QQQ"), None)
    if tqqq_entry:
        tqqq = {
            **tqqq_entry,
            "etf": "TQQQ",
            "name": "3x Nasdaq (TQQQ)",
            "catalyst_warnings": _catalyst_warnings("TQQQ"),
        }
        # TQQQ: only buy_call or sell_call (no naked puts on 3x leverage)
        if tqqq["suggested_direction"] not in ("buy_call", "sell_call", "bull_call_spread", None):
            tqqq["suggested_direction"] = None
            tqqq["action"] = "SKIP"
        sectors.append(tqqq)

    return {
        "sectors": sectors,
        "sector_count": len(sectors),
        "size_signal": size_signal,
        "size_bias": _size_bias_label(size_signal),
        "timestamp": datetime.utcnow().isoformat(),
        "sta_status": "ok",
    }


# ---------------------------------------------------------------------------
# Level 2: Standard Analysis (single ETF — adds IV/OI/spread from IBKR)
# ---------------------------------------------------------------------------
def analyze_sector_etf(ticker, data_service=None, ib_worker=None):
    """
    Level 2 analysis for a single sector ETF.
    Adds IV overlay, bid-ask spread, suggested DTE, catalyst warnings.

    data_service: DataService instance (for chain fetch)
    ib_worker: IBWorker instance (for IVR/HV)
    """
    ticker = ticker.upper().strip()
    if ticker not in ETF_TICKERS:
        return {"error": f"{ticker} is not in the sector ETF universe"}

    # Start with L1 scan to get quadrant data
    scan = scan_sectors()
    if scan.get("error"):
        return scan

    etf_data = next((s for s in scan["sectors"] if s["etf"] == ticker), None)
    if not etf_data:
        return {"error": f"{ticker} not found in STA rotation data"}

    # Fetch IV data (reuse existing iv_store / data_service if available)
    iv_current = None
    ivr = None
    hv_20 = None

    if data_service:
        try:
            direction = etf_data.get("suggested_direction") or "buy_call"
            chain = data_service.get_chain(ticker, direction=direction)
            if chain and chain.get("contracts"):
                # Get ATM IV from first contract
                for c in chain["contracts"]:
                    if c.get("iv") and c["iv"] > 0:
                        iv_current = round(c["iv"] * 100, 1)
                        break
        except Exception as exc:
            logger.warning("L2 chain fetch failed for %s: %s", ticker, exc)

    # Build L2 response
    dte = suggested_dte(ivr, ticker)
    catalyst = _catalyst_warnings(ticker)

    return {
        **etf_data,
        "iv_current": iv_current,
        "iv_percentile": ivr,
        "hv_20": hv_20,
        "suggested_dte": dte,
        "catalyst_warnings": catalyst if catalyst else None,
        "level": 2,
        "note": "L3 deep dive: POST /api/options/analyze with ticker and suggested_direction",
    }
