"""
best_setups_service.py — Single-ETF analysis worker for the Best Setups scan.

Extracted from app.py (KI-086) to keep app.py within Rule 4's 150-line limit.
"""
from __future__ import annotations

import logging
import os

from analyze_service import analyze_etf
from scanner_service import get_scanner_data  # file cache (from /etf-scan command)

logger = logging.getLogger(__name__)


def run_one_setup(
    s: dict,
    *,
    data_svc,
    ib_worker,
    yf_provider,
    mock_provider,
    strategy_ranker,
    pnl_calculator,
    iv_store,
    spy_regime_fn,
    md_provider,
    account_size: float,
    risk_pct: float,
    live_scanner: dict | None = None,
) -> dict:
    """Run gate analysis for one ETF sector candidate. Returns a result dict or error dict."""
    ticker = s["etf"]
    direction = s["suggested_direction"]
    payload = {
        "ticker": ticker,
        "direction": direction,
        "account_size": account_size,
        "risk_pct": risk_pct,
        "planned_hold_days": 21,
    }
    try:
        # Inject scanner data into payload so gate_engine can use put_call_volume.
        # Priority: live IBKR scanner > /etf-scan file cache.
        _scanner_pre = (live_scanner or {}).get(ticker) or get_scanner_data(ticker)
        if _scanner_pre.get("put_call_volume") is not None:
            payload["put_call_volume"] = float(_scanner_pre["put_call_volume"])

        result = analyze_etf(
            payload, ticker,
            data_svc=data_svc, ib_worker=ib_worker,
            yf_provider=yf_provider, mock_provider=mock_provider,
            strategy_ranker=strategy_ranker, pnl_calculator=pnl_calculator,
            iv_store=iv_store, spy_regime_fn=spy_regime_fn,
            md_provider=md_provider,
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

        # Inject scanner data when chain values are null (KI-101 fix).
        # Priority: live IBKR batch (fetched pre-scan) > /etf-scan file cache > None.
        scanner = (live_scanner or {}).get(ticker) or get_scanner_data(ticker)
        ivr = result.get("ivr_data", {}).get("ivr_pct")
        if ivr is None and scanner.get("ivr_52w") is not None:
            ivr = float(scanner["ivr_52w"])
        iv_hv_ratio = result.get("ivr_data", {}).get("hv_iv_ratio")
        if iv_hv_ratio is None and scanner.get("iv_hv_pct") is not None:
            iv_hv_ratio = round(scanner["iv_hv_pct"] / 100.0, 3)

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
            "ivr": ivr,
            "iv_hv_ratio": iv_hv_ratio,
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
