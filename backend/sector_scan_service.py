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

import copy
import logging
import time
import requests
from datetime import datetime, date, timezone

from constants import (
    STA_BASE_URL, STA_TIMEOUT_SEC,
    ETF_TICKERS, TQQQ_MAX_DTE,
    ETF_DTE_LOW_IVR, ETF_DTE_HIGH_IVR, ETF_DTE_DEFAULT,
    FOMC_HIGH_SENSITIVITY, FOMC_WARN_DAYS, FOMC_DATES,
    HIGH_DIVIDEND_ETFS, DIVIDEND_WARN_DAYS,
    CYCLICAL_SECTORS, DEFENSIVE_SECTORS,
    QUADRANT_ANALYZE, QUADRANT_WATCH, QUADRANT_SKIP,
    IVR_BUYER_PASS_PCT,
    RS_LAGGING_BEAR_RS, RS_LAGGING_BEAR_MOM,
    BROAD_SELLOFF_SECTOR_PCT, IVR_BEAR_SPREAD_WARN,
    DIRECTION_TO_CHAIN_DIR,
)

logger = logging.getLogger(__name__)

# Module-level scan cache (C3 fix: avoid N+1 STA calls from L2)
_scan_cache = {"data": None, "ts": 0}
_SCAN_CACHE_TTL = 60  # seconds — L1 data is STA-sourced, 1 min freshness is fine


# ---------------------------------------------------------------------------
# Quadrant → direction mapping (research-verified Day 13, Phase 7b Day 19)
# ---------------------------------------------------------------------------
def quadrant_to_direction(quadrant, ivr=None, rs_ratio=None, rs_momentum=None):
    """
    Research-verified mapping (3-model consensus Day 13 + Phase 7b Day 19):
    - Leading   → buy_call (bull_call_spread if IVR > 50)
    - Improving → bull_call_spread (defined risk, 60 DTE)
    - Weakening → None (WAIT — still RS>100, not bearish)
    - Lagging   → bear_call_spread if RS < 98 AND momentum < -0.5
                   (defined risk credit spread on sustained underperformance)
                   Otherwise None (SKIP — may be bottoming or mean-reverting)
    """
    if quadrant == "Leading":
        if ivr is not None and ivr >= 50:
            return "bull_call_spread"
        return "buy_call"
    elif quadrant == "Improving":
        return "bull_call_spread"
    elif quadrant == "Lagging":
        # Phase 7b: bear_call_spread for sustained underperformers
        # RS < 98 = underperforming SPY by 2+ points (not borderline)
        # mom < -0.5 = still declining (not bottoming)
        if (rs_ratio is not None and rs_ratio < RS_LAGGING_BEAR_RS
                and rs_momentum is not None and rs_momentum < RS_LAGGING_BEAR_MOM):
            return "bear_call_spread"
        return None
    # Weakening: no position (still RS>100, not bearish)
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


def _spy_regime():
    """
    Q3: SPY regime check — RS momentum is lagging (weeks), SPY 5-day is leading (days).
    Returns dict with spy_above_200sma, spy_5day_return, regime_warning (or None).
    Uses STA /api/stock/SPY (priceHistory) — already fetched for sector scan, no yfinance rate limit.
    """
    try:
        url = f"{STA_BASE_URL}/api/stock/SPY"
        resp = requests.get(url, timeout=STA_TIMEOUT_SEC)
        resp.raise_for_status()
        data = resp.json()

        hist = data.get("priceHistory", [])
        if len(hist) < 200:
            return {"spy_above_200sma": None, "spy_5day_return": None, "regime_warning": None}

        closes = [h["close"] for h in hist]
        latest = closes[-1]
        sma200 = sum(closes[-200:]) / 200
        above_200 = latest > sma200

        spy_5d = None
        if len(closes) >= 6:
            five_ago = closes[-6]
            spy_5d = round((latest - five_ago) / five_ago * 100, 2)

        # Regime warning thresholds (from constants.py SPY gates)
        warning = None
        if spy_5d is not None and spy_5d <= -2.0:
            warning = f"SPY down {spy_5d}% this week — bullish sector calls carry elevated risk."
        elif not above_200:
            warning = "SPY below 200-day SMA — broad market in downtrend. Reduce bullish exposure."

        return {
            "spy_above_200sma": above_200,
            "spy_5day_return": spy_5d,
            "regime_warning": warning,
        }
    except Exception as exc:
        logger.warning("SPY regime check failed: %s", exc)
        return {"spy_above_200sma": None, "spy_5day_return": None, "regime_warning": None}


# ---------------------------------------------------------------------------
# Broad market regime detection (Phase 7b — Day 19)
# ---------------------------------------------------------------------------
def _detect_regime(sectors, spy_regime):
    """
    Detect broad selloff: >50% sectors Weakening/Lagging AND SPY below 200 SMA.
    Returns "BROAD_SELLOFF" or "NORMAL".
    """
    total = len(sectors)
    if total == 0:
        return "NORMAL"
    weak_lag = sum(1 for s in sectors if s.get("quadrant") in ("Weakening", "Lagging"))
    pct = weak_lag / total
    above_200 = spy_regime.get("spy_above_200sma", True) if spy_regime else True
    if pct >= BROAD_SELLOFF_SECTOR_PCT and not above_200:
        return "BROAD_SELLOFF"
    return "NORMAL"


# ---------------------------------------------------------------------------
# Level 1: Quick Scan (< 2 sec — STA data + SPY regime)
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
        rs = s.get("rsRatio")
        mom = s.get("rsMomentum")
        direction = quadrant_to_direction(quadrant, rs_ratio=rs, rs_momentum=mom)
        # If a direction is suggested (including bear), action = ANALYZE
        action = "ANALYZE" if direction is not None else quadrant_to_action(quadrant)
        catalyst = _catalyst_warnings(etf)

        sectors.append({
            "etf": etf,
            "name": s.get("name", ""),
            "rank": s.get("rank", 99),
            "rs_ratio": rs,
            "rs_momentum": mom,
            "quadrant": quadrant,
            "price": s.get("price"),
            "week_change": s.get("weekChange"),
            "month_change": s.get("monthChange"),
            "suggested_direction": direction,
            "action": action,
            "catalyst_warnings": catalyst,
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

        direction = quadrant_to_direction(quad, rs_ratio=rs, rs_momentum=mom)
        action = "ANALYZE" if direction is not None else quadrant_to_action(quad)
        catalyst = _catalyst_warnings(etf)

        sectors.append({
            "etf": etf,
            "name": f"Cap-Size ({etf})",
            "rank": None,
            "rs_ratio": rs,
            "rs_momentum": mom,
            "quadrant": quad,
            "price": sr.get("price"),
            "week_change": sr.get("weekChange"),
            "month_change": sr.get("monthChange"),
            "suggested_direction": direction,
            "action": action,
            "catalyst_warnings": catalyst,
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
        # TQQQ: buy_call, sell_call, bull/bear_call_spread OK; no naked puts on 3x leverage
        if tqqq["suggested_direction"] not in (
            "buy_call", "sell_call", "bull_call_spread", "bear_call_spread", None
        ):
            tqqq["suggested_direction"] = None
            tqqq["action"] = "SKIP"
        sectors.append(tqqq)

    # Q3: SPY regime — leading indicator vs lagging RS momentum
    regime = _spy_regime()

    # Phase 7b: broad selloff detection
    market_regime = _detect_regime(sectors, regime)

    result = {
        "sectors": sectors,
        "sector_count": len(sectors),
        "size_signal": size_signal,
        "size_bias": _size_bias_label(size_signal),
        "spy_regime": regime,
        "market_regime": market_regime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sta_status": "ok",
    }

    # Cache for L2 reuse (C3 fix)
    _scan_cache["data"] = result
    _scan_cache["ts"] = time.monotonic()

    return result


# ---------------------------------------------------------------------------
# Level 2: Standard Analysis (single ETF — adds IV/OI/spread from IBKR)
# ---------------------------------------------------------------------------
def analyze_sector_etf(ticker, data_service=None, ib_worker=None, iv_store=None):
    """
    Level 2 analysis for a single sector ETF.
    Adds IV overlay, bid-ask spread, suggested DTE, catalyst warnings.

    data_service: DataService instance (for chain fetch)
    ib_worker: IBWorker instance (for IVR/HV — currently reserved for future IV history seeding)
    iv_store: IVStore instance (for IVR percentile + HV20 computation)
    """
    ticker = ticker.upper().strip()
    if ticker not in ETF_TICKERS:
        return {"error": f"{ticker} is not in the sector ETF universe"}

    # Use cached L1 scan if fresh, otherwise fetch (C3 fix: no N+1 STA calls)
    # Q4: deep copy prevents L2 mutations from poisoning cached data
    if _scan_cache["data"] and (time.monotonic() - _scan_cache["ts"]) < _SCAN_CACHE_TTL:
        scan = copy.deepcopy(_scan_cache["data"])
    else:
        scan = scan_sectors()
        if scan.get("error"):
            return scan

    etf_data = next((s for s in scan["sectors"] if s["etf"] == ticker), None)
    if not etf_data:
        return {"error": f"{ticker} not found in STA rotation data"}

    # ── Chain fetch + IV/liquidity extraction ──
    iv_current = None
    ivr = None
    hv_20 = None
    data_source = None
    atm_bid = None
    atm_ask = None
    atm_spread_pct = None
    atm_oi = None
    atm_volume = None

    if data_service:
        try:
            raw_dir = etf_data.get("suggested_direction")
            # Map display hints to core directions; skip chain fetch if None (SKIP/WATCH)
            chain_dir = DIRECTION_TO_CHAIN_DIR.get(raw_dir) if raw_dir else None
            chain = None
            if chain_dir:
                chain, data_source = data_service.get_chain(ticker, direction=chain_dir)
            if chain:
                contracts = chain.get("contracts", [])
                underlying = chain.get("underlying_price") or etf_data.get("price")

                if contracts and underlying:
                    # Find ATM contract (closest strike to underlying)
                    atm = min(contracts, key=lambda c: abs(c.get("strike", 0) - underlying))

                    # Q1: IV from ATM contract (field is "impliedVol", not "iv")
                    raw_iv = atm.get("impliedVol")
                    if raw_iv and raw_iv > 0:
                        iv_current = round(raw_iv * 100, 1)

                    # Q2: Liquidity from ATM contract
                    atm_bid = atm.get("bid")
                    atm_ask = atm.get("ask")
                    if atm_bid and atm_ask and atm_ask > 0:
                        mid = (atm_bid + atm_ask) / 2
                        if mid > 0:
                            atm_spread_pct = round((atm_ask - atm_bid) / mid * 100, 2)
                    atm_oi = atm.get("openInterest")
                    atm_volume = atm.get("volume")

        except Exception as exc:
            logger.warning("L2 chain fetch failed for %s: %s", ticker, exc)

    # Q1: IVR + HV20 from iv_store (requires seeded IV history — honest None if < 30 days)
    if iv_store and iv_current is not None:
        try:
            ivr = iv_store.compute_ivr_pct(ticker, iv_current)
        except Exception:
            logger.warning("IVR computation failed for %s", ticker)
    if iv_store:
        try:
            hv_20 = iv_store.compute_hv(ticker, 20)
        except Exception:
            logger.warning("HV20 computation failed for %s", ticker)

    # Q1: Feed IVR into DTE model (research-verified tastylive 2-tier)
    dte = suggested_dte(ivr, ticker)

    # Q1: Re-evaluate direction with IVR + RS context (Phase 7b: also feeds bear logic)
    quadrant = etf_data.get("quadrant", "Lagging")
    rs_ratio = etf_data.get("rs_ratio")
    rs_momentum = etf_data.get("rs_momentum")
    direction_with_ivr = quadrant_to_direction(
        quadrant, ivr=ivr, rs_ratio=rs_ratio, rs_momentum=rs_momentum,
    )

    # Phase 7b: IVR soft warning for bear credit spreads
    ivr_bear_warning = None
    if direction_with_ivr == "bear_call_spread" and ivr is not None and ivr < IVR_BEAR_SPREAD_WARN:
        ivr_bear_warning = (
            f"IV rank {ivr:.0f}% is below {IVR_BEAR_SPREAD_WARN}% — "
            "premium may be thin for bear call spread. Wait for volatility to expand."
        )

    catalyst = _catalyst_warnings(ticker)

    # Map bear_call_spread to sell_call for L3 deep dive note
    l3_dir = DIRECTION_TO_CHAIN_DIR.get(direction_with_ivr, direction_with_ivr)

    return {
        **etf_data,
        "suggested_direction": direction_with_ivr,  # override L1 direction with IVR-aware version
        "iv_current": iv_current,
        "iv_percentile": ivr,
        "hv_20": round(hv_20, 1) if hv_20 is not None else None,
        "suggested_dte": dte,
        # Q2: Liquidity data — trader must know if they can get in/out
        "atm_bid": atm_bid,
        "atm_ask": atm_ask,
        "atm_spread_pct": atm_spread_pct,
        "atm_oi": atm_oi,
        "atm_volume": atm_volume,
        "ivr_bear_warning": ivr_bear_warning,
        "catalyst_warnings": catalyst,
        "data_source": data_source,
        "level": 2,
        "note": f"L3 deep dive: POST /api/options/analyze with ticker={ticker} and direction={l3_dir}"
            if l3_dir else "No direction suggested — L3 deep dive not applicable",
    }
