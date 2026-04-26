"""
analyze_service.py — Core analysis business logic extracted from app.py (Day 24).

All helpers, data fetchers, payload builders, ETF gate post-processing, and the
main analyze_etf() orchestrator live here. app.py keeps only Flask setup, global
instances, and thin route handlers.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime

from constants import (
    COMPANY_EARNINGS,
    DIRECTION_TO_CHAIN_DIR,
    ETF_DTE_HIGH_IVR,
    ETF_DTE_LOW_IVR,
    ETF_DTE_SELLER_PASS_MAX,
    ETF_DTE_SELLER_PASS_MIN,
    ETF_KEY_HOLDINGS,
    ETF_MIN_PREMIUM_DOLLAR,
    ETF_TICKERS,
    FOMC_DATES,
    IVR_BUYER_PASS_PCT,
    MAX_LOSS_FAIL_PCT,
    MAX_LOSS_WARN_PCT,
    SPREAD_DATA_FAIL_PCT,
    SPREAD_FAIL_PCT,
)
from gate_engine import GateEngine

logger = logging.getLogger(__name__)


def _days_until_next_fomc() -> int:
    """Days from today to the next scheduled FOMC meeting. Falls back to 999 if list exhausted."""
    today = datetime.utcnow().date()
    for date_str in sorted(FOMC_DATES):
        meeting = datetime.strptime(date_str, "%Y-%m-%d").date()
        if meeting >= today:
            return (meeting - today).days
    return 999


def _etf_holdings_at_risk(ticker: str, expiry_date: str) -> list[dict]:
    """
    Returns key holdings for an ETF that report earnings before the option expiry.
    Each entry: {"symbol": str, "earnings_date": str, "days_away": int}.
    Returns [] for diversified ETFs (MDY/IWM/SCHB) or if expiry is missing/invalid.
    Dates in COMPANY_EARNINGS are approximate — update quarterly.
    """
    holdings = ETF_KEY_HOLDINGS.get(ticker, [])
    if not holdings or not expiry_date:
        return []
    today = datetime.utcnow().date()
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return []
    at_risk = []
    for symbol in holdings:
        for d_str in sorted(COMPANY_EARNINGS.get(symbol, [])):
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if d >= today and d <= expiry:
                at_risk.append({
                    "symbol": symbol,
                    "earnings_date": d_str,
                    "days_away": (d - today).days,
                })
                break  # only next upcoming per holding
    return sorted(at_risk, key=lambda x: x["days_away"])


# ─── Parsing helpers ─────────────────────────────────────────────────────────


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


# ─── Direction helpers ────────────────────────────────────────────────────────


def _direction_track(direction: str) -> str:
    return "A" if direction in {"buy_call", "sell_call"} else "B"


# ─── Chain quality ────────────────────────────────────────────────────────────


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


# ─── SPY regime (shared 2-min cache) ─────────────────────────────────────────

_spy_regime_cache: dict = {"data": None, "ts": 0}
_SPY_REGIME_TTL = 120  # 2 min


def _fetch_spy_regime(spy_regime_fn):
    """Fetch real SPY regime from STA, with 2-min cache. Never fabricate."""
    now = time.monotonic()
    if _spy_regime_cache["data"] and (now - _spy_regime_cache["ts"]) < _SPY_REGIME_TTL:
        return _spy_regime_cache["data"]
    regime = spy_regime_fn()
    _spy_regime_cache["data"] = regime
    _spy_regime_cache["ts"] = now
    return regime


def _spy_above_200(payload, spy_regime_fn):
    """Get spy_above_200sma: from payload if present, else fetch real data from STA."""
    v = payload.get("spy_above_200sma")
    if v is not None:
        return bool(v)
    regime = _fetch_spy_regime(spy_regime_fn)
    val = regime.get("spy_above_200sma")
    if val is not None:
        return bool(val)
    return True  # last resort if STA is offline — safe default, don't penalize


def _spy_5d_return(payload, spy_regime_fn):
    """Get spy_5day_return: from payload if present, else fetch real data from STA.
    Gate engine thresholds are in decimal form (e.g., -0.02 = -2%).
    STA and sta_fetch both return percentage form (e.g., -1.23 = -1.23%).
    We normalize to decimal here so gate comparisons are correct.
    """
    v = payload.get("spy_5day_return")
    if v is not None:
        pct = _f(v, 0.0)
        return pct / 100.0 if abs(pct) > 0.5 else pct
    regime = _fetch_spy_regime(spy_regime_fn)
    val = regime.get("spy_5day_return")
    if val is not None:
        return float(val) / 100.0  # STA returns percentage, gate expects decimal
    return 0.0  # last resort if STA is offline


# ─── Payload builders ─────────────────────────────────────────────────────────


def _etf_payload(underlying: float, spy_above: bool, spy_5d: float | None,
                 fomc_days_away: int | None, ivr_pct: float | None) -> dict:
    """
    ETF-only payload for gate_engine. No swing fields — no fabrication.
    Only real, observable values: SPY regime, IVR-based DTE hint, position params.
    """
    return {
        "signal": None,
        "spy_above_200sma": spy_above,
        "spy_5day_return": spy_5d,
        "fomc_days_away": fomc_days_away if fomc_days_away is not None else 999,
        "ivr_pct_hint": ivr_pct,
        "entry_pullback": None,
        "entry_momentum": None,
        "stop_loss": None,
        "target1": None,
        "target2": None,
        "risk_reward": None,
        "vcp_pivot": None,
        "vcp_confidence": None,
        "adx": None,
        "last_close": None,
        "s1_support": None,
        "earnings_days_away": None,
        "pattern": None,
        "source": "etf_regime",
        "swing_data_quality": "etf",
        "synthesized_fields": [],
    }


def _merge_swing(payload: dict, underlying: float, spy_regime_fn) -> dict:
    synthesized = []
    vcp_confidence = _f(payload.get("vcp_confidence"), None)
    adx = _f(payload.get("adx"), None)
    if vcp_confidence is None:
        synthesized.append("vcp_confidence")
    if adx is None:
        synthesized.append("adx")
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
        "spy_above_200sma": _spy_above_200(payload, spy_regime_fn),
        "spy_5day_return": _spy_5d_return(payload, spy_regime_fn),
        "earnings_days_away": _i(payload.get("earnings_days_away"), None),
        "pattern": payload.get("pattern") or "VCP",
        "source": payload.get("source") or "manual",
        "swing_data_quality": "partial" if synthesized else "full",
        "synthesized_fields": synthesized,
    }


# ─── IV / analytics ──────────────────────────────────────────────────────────


def _extract_iv_data(ticker: str, chain: dict, provider, *,
                     ib_worker=None, mock_provider=None, iv_store=None) -> dict:
    contracts = chain.get("contracts", [])
    ivs = [float(c.get("impliedVol", 0.0)) * 100 for c in contracts if c.get("impliedVol") is not None]
    current_iv = round(sum(ivs) / len(ivs), 2) if ivs else None

    def _call_provider(fn, *args):
        if ib_worker is not None and provider is ib_worker.provider:
            try:
                return ib_worker.submit(fn, *args, timeout=20.0)
            except (TimeoutError, Exception) as exc:
                logger.warning("IBWorker IV call timed out/failed: %s", exc)
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


# ─── Behavioral checks ───────────────────────────────────────────────────────


def _behavioral_checks(gates: list[dict], swing_data: dict, is_etf: bool = False) -> list[dict]:
    if is_etf:
        return _etf_behavioral_checks(gates, swing_data)
    pivot_gate = next((g for g in gates if g["id"] == "pivot_confirm"), None)
    pivot_msg = (
        f"Stock has not closed above VCP pivot ${swing_data['vcp_pivot']:.2f}."
        if pivot_gate and pivot_gate["status"] == "fail"
        else f"Pivot confirmed above ${swing_data['vcp_pivot']:.2f}."
    )
    timing_conflict = (swing_data.get("entry_momentum") or 0) > (swing_data.get("entry_pullback") or 0) * 1.1
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
            "message": "Vol risk premium can hurt outcomes even when directional view is correct.",
        },
        {
            "id": "lottery_bias",
            "type": "warning",
            "label": "Lottery Bias",
            "message": "Pick Δ0.68, not highest % return.",
        },
    ]


def _etf_behavioral_checks(gates: list[dict], swing_data: dict) -> list[dict]:
    """ETF-specific advisory checks. No swing/VCP fields — pure regime and IV context."""
    checks = []

    ivr = swing_data.get("ivr_pct_hint")
    if ivr is not None:
        if ivr > 70:
            checks.append({
                "id": "ivr_context",
                "type": "warning",
                "label": "IV Rank Elevated",
                "message": f"IVR {ivr:.0f}% — premium is expensive. Selling strategies have edge; buying options carries IV crush risk.",
            })
        elif ivr < 20:
            checks.append({
                "id": "ivr_context",
                "type": "info",
                "label": "IV Rank Low",
                "message": f"IVR {ivr:.0f}% — premium is cheap. Buying calls/puts has favorable IV entry; credit spreads collect thin premium.",
            })
        else:
            checks.append({
                "id": "ivr_context",
                "type": "info",
                "label": "IV Rank Neutral",
                "message": f"IVR {ivr:.0f}% — neutral premium environment. Both buying and selling are viable.",
            })

    spy_5d = swing_data.get("spy_5day_return")
    spy_above = swing_data.get("spy_above_200sma")
    if spy_5d is not None:
        if spy_5d < -0.03:
            checks.append({
                "id": "spy_regime",
                "type": "warning",
                "label": "Market Pullback",
                "message": f"SPY down {spy_5d:.1%} this week. Bullish calls carry elevated gap risk — consider spreads for defined risk.",
            })
        elif not spy_above:
            checks.append({
                "id": "spy_regime",
                "type": "warning",
                "label": "SPY Below 200-Day SMA",
                "message": "Broad market in downtrend. Reduce bullish ETF exposure; bear directions have structural tailwind.",
            })

    checks.append({
        "id": "delta_discipline",
        "type": "info",
        "label": "Delta Discipline",
        "message": "For buying: target Δ0.68 (ITM) for high probability. For selling: target Δ0.30 short leg for optimal credit-to-risk.",
    })

    return checks


# ─── ETF gate post-processing ────────────────────────────────────────────────


def apply_etf_gate_adjustments(gates: list[dict], direction: str,
                               account_size: float, gate_payload: dict,
                               strategies_preview: list[dict]) -> None:
    """
    Consolidates all ETF-specific gate post-processing into one function.
    Mutates `gates` in place.
    """
    # 1. Liquidity fail → warn only if spread is in the "naturally wider ETF" range.
    #    At >SPREAD_DATA_FAIL_PCT (20%) the bid-ask gap is wide enough that the
    #    underlying delta/strike data is unreliable — keep blocking to prevent
    #    bad data driving the wrong strike selection (KI-080).
    for g in gates:
        if g["id"] == "liquidity" and g["status"] == "fail":
            if "Spread too wide" in str(g.get("reason", "")):
                raw_spread = g.get("spread_pct")
                if raw_spread is not None and raw_spread > SPREAD_DATA_FAIL_PCT:
                    g["blocking"] = True
                    g["reason"] = (
                        f"Bid-ask spread {raw_spread:.1f}% — data unreliable at this width; "
                        "do not trade until spread narrows"
                    )
                else:
                    g["status"] = "warn"
                    g["blocking"] = False
                    g["reason"] = "ETF OTM spread wider than stock threshold — review bid-ask before entry"

    # 2. sell_call market_regime_seller → non-blocking
    if direction == "sell_call":
        for g in gates:
            if g["id"] == "market_regime_seller" and g.get("blocking"):
                g["blocking"] = False
                g["reason"] = (g.get("reason", "") +
                               " — sector RS/momentum weakness overrides SPY trend for ETF relative shorts")

    # 3. sell_put max_loss re-eval for bull_put_spread
    if direction == "sell_put":
        top_strat = strategies_preview[0] if strategies_preview else {}
        if top_strat.get("strategy_type") == "bull_put_spread":
            actual_max_loss = float(top_strat.get("max_loss_per_lot") or 0.0)
            total_risk = actual_max_loss
            for g in gates:
                if g["id"] == "max_loss":
                    if total_risk <= account_size * MAX_LOSS_WARN_PCT:
                        g["status"] = "pass"
                        g["reason"] = "Spread max loss within 10% of account (defined-risk spread)"
                        g["blocking"] = False
                    elif total_risk <= account_size * MAX_LOSS_FAIL_PCT:
                        g["status"] = "warn"
                        g["reason"] = "Spread max loss elevated vs account (still defined risk)"
                        g["blocking"] = False
                    else:
                        g["status"] = "fail"
                        g["reason"] = "Spread max loss exceeds 20% of account — reduce lot size"
                        g["blocking"] = True
                    g["computed_value"] = f"${total_risk:.2f} (spread max loss)"

    # 4. DTE seller 21-45 → pass
    if direction in ("sell_call", "sell_put"):
        dte_val = int(gate_payload.get("selected_expiry_dte", 0) or 0)
        for g in gates:
            if g["id"] == "dte_seller" and g["status"] == "warn":
                if ETF_DTE_SELLER_PASS_MIN <= dte_val <= ETF_DTE_SELLER_PASS_MAX:
                    g["status"] = "pass"
                    g["reason"] = f"ETF seller sweet spot — DTE {dte_val} within 21-45 range"

    # 5. OI=0 platform limitation → pass when spread OK
    for g in gates:
        if g["id"] == "liquidity" and g["status"] == "warn":
            computed = g.get("computed_value", "")
            oi_absent = "OI unavailable" in computed
            spread_val, prem_val = None, None
            try:
                if "Spread " in computed:
                    spread_val = float(computed.split("Spread ")[1].rstrip("%"))
                if "Prem " in computed:
                    prem_val = float(computed.split("Prem ")[1].split(",")[0].split(" ")[0])
            except (ValueError, IndexError):
                pass
            spread_ok = (spread_val is None) or (spread_val < SPREAD_FAIL_PCT)
            is_spread_direction = direction in ("sell_call", "sell_put")
            prem_ok = is_spread_direction or (prem_val is None) or (prem_val >= ETF_MIN_PREMIUM_DOLLAR)
            if oi_absent and spread_ok and prem_ok:
                g["status"] = "pass"
                g["reason"] = ("OI unavailable (IBKR platform limitation — confirmed Day 12). "
                               "ETF has confirmed market liquidity; bid-ask spread acceptable.")


# ─── Main orchestrator ────────────────────────────────────────────────────────


def get_live_price(ticker: str, *, ib_worker, yf_provider) -> float:
    """Get underlying price via IBWorker (if connected) or yfinance fallback."""
    if ib_worker.is_connected() and ib_worker.provider:
        try:
            return ib_worker.submit(ib_worker.provider.get_underlying_price, ticker, timeout=10.0)
        except Exception as exc:
            logger.warning("IBWorker get_underlying_price failed for %s: %s", ticker, exc)
    try:
        return yf_provider.get_underlying_price(ticker)
    except Exception as exc:
        logger.warning("yfinance get_underlying_price failed for %s: %s", ticker, exc)
        return 0.0


def analyze_etf(payload: dict, ticker: str, *,
                data_svc, ib_worker, yf_provider, mock_provider,
                strategy_ranker, pnl_calculator, iv_store,
                spy_regime_fn, md_provider=None) -> dict:
    """
    Main analysis orchestrator. Returns a dict (caller jsonifies).
    Extracted from app.py _analyze_options_inner() on Day 24.
    """
    _raw_dir = str(payload.get("direction", "buy_call")).strip()
    direction = DIRECTION_TO_CHAIN_DIR.get(_raw_dir, _raw_dir)
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
    if data_source in {"ibkr_live", "ibkr_closed", "ibkr_cache", "ibkr_stale"} and ib_worker.provider is not None:
        iv_provider = ib_worker.provider
    elif data_source == "yfinance":
        iv_provider = yf_provider

    is_etf = ticker in ETF_TICKERS
    ivr_data = _extract_iv_data(ticker, chain, iv_provider,
                                ib_worker=ib_worker, mock_provider=mock_provider, iv_store=iv_store)

    if is_etf:
        spy_regime = _fetch_spy_regime(spy_regime_fn)
        _spy_above_raw = spy_regime.get("spy_above_200sma")
        swing_data = _etf_payload(
            underlying=underlying,
            spy_above=bool(_spy_above_raw) if _spy_above_raw is not None else True,
            spy_5d=float(spy_regime["spy_5day_return"] / 100.0) if spy_regime.get("spy_5day_return") is not None else None,
            fomc_days_away=_i(payload.get("fomc_days_away"), None) or _days_until_next_fomc(),
            ivr_pct=ivr_data.get("ivr_pct"),
        )
    else:
        swing_data = _merge_swing(payload, underlying, spy_regime_fn)

    engine = GateEngine(planned_hold_days=planned_hold_days)
    if is_etf:
        ivr_hint = ivr_data.get("ivr_pct")
        preview_dte = ETF_DTE_LOW_IVR if (ivr_hint is None or ivr_hint < IVR_BUYER_PASS_PCT) else ETF_DTE_HIGH_IVR
    else:
        preview_dte = 45
    strategies_preview = strategy_ranker.rank(direction, chain, swing_data, recommended_dte=preview_dte)
    selected = strategies_preview[0] if strategies_preview else {}

    # MarketData.app OI/volume supplement — fills the IBKR platform gap (OI always 0 via reqMktData).
    # Non-blocking: if lookup fails or times out, gate_payload falls back to OI=0 (existing behaviour).
    _md_oi_volume: dict = {}
    if md_provider and selected and is_etf:
        _side = "put" if direction in ("buy_put", "sell_put") else "call"
        _md_result = md_provider.get_oi_volume(
            ticker,
            float(selected.get("strike", underlying)),
            _side,
            int(selected.get("dte", 21)),
        )
        if _md_result:
            _md_oi_volume = _md_result

    ivr_for_gates = {k: (0.0 if v is None else v) for k, v in ivr_data.items()}

    gate_payload = {
        **ivr_for_gates,
        **swing_data,
        "underlying_price": underlying,
        "selected_expiry_dte": int(selected.get("dte", 21)),
        "strike": float(selected.get("strike", underlying)),
        "premium": float(selected.get("premium", 0.0)),
        "theta_per_day": float(selected.get("theta_per_day", -0.2)),
        "open_interest": float(_md_oi_volume.get("open_interest") or selected.get("open_interest", 0.0)),
        "volume": float(_md_oi_volume.get("volume") or selected.get("volume", 0.0)),
        "bid": selected.get("bid"),
        "ask": selected.get("ask"),
        "max_gain_per_lot": float(selected.get("max_gain_per_lot") or -1.0),
        "account_size": account_size,
        "risk_pct": risk_pct,
        "fomc_days_away": _i(payload.get("fomc_days_away"), 999),
        "lots": _f(payload.get("lots"), 1.0),
        "etf_holdings_at_risk": (
            _etf_holdings_at_risk(ticker, selected.get("expiry") or selected.get("expiry_display", ""))
            if is_etf else []
        ),
    }

    gates = engine.run(direction, gate_payload, etf_mode=is_etf)

    if is_etf:
        apply_etf_gate_adjustments(gates, direction, account_size, gate_payload, strategies_preview)

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

    return {
        "ticker": ticker,
        "direction": direction,
        "is_etf": is_etf,
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
        "behavioral_checks": _behavioral_checks(gates, swing_data, is_etf=is_etf),
        "top_strategies": strategies,
        "pnl_table": pnl_table,
        "ivr_data": ivr_data,
        "put_call_ratio": _put_call_ratio(chain),
        "max_pain_strike": _max_pain(chain),
        "recommended_dte": recommended_dte,
        "direction_locked": [] if is_etf else (
            ["sell_call", "buy_put"] if swing_data.get("signal") == "BUY" else
            ["buy_call", "sell_put"] if swing_data.get("signal") == "SELL" else []
        ),
    }
