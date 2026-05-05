"""
best_setups_service.py — Single-ETF analysis worker for the Best Setups scan.

Extracted from app.py (KI-086) to keep app.py within Rule 4's 150-line limit.
"""
from __future__ import annotations

import logging
import os

from analyze_service import analyze_etf

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
