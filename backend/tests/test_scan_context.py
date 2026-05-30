"""Tests for scan_context_parser and _trend_ema_gate."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scan_context_parser import parse_scan_context, apply_scan_context_to_gate_payload
from gate_engine import GateEngine
from helpers import make_gate_payload


def _find(gates, gate_id):
    return next((g for g in gates if g["id"] == gate_id), None)


# ─── parse_scan_context ────────────────────────────────────────────────────────

def test_parse_full_line():
    text = "TICKER=XLF  IVR=47  IV_HV=1.21  PEMA200=+3.1  PEMA50=+1.2  PC=0.85  DIRECTION=sell_put"
    result = parse_scan_context(text)
    assert result["ticker"] == "XLF"
    assert result["ivr"] == 47.0
    assert result["iv_hv"] == 1.21
    assert result["pema200"] == 3.1
    assert result["pema50"] == 1.2
    assert result["pc_ratio"] == 0.85
    assert result["direction"] == "sell_put"


def test_parse_negative_pema():
    text = "TICKER=QQQ  IVR=40  IV_HV=1.25  PEMA200=-2.3  PEMA50=-5.1  DIRECTION=sell_call"
    result = parse_scan_context(text)
    assert result["pema200"] == -2.3
    assert result["pema50"] == -5.1


def test_parse_empty_returns_empty():
    assert parse_scan_context("") == {}
    assert parse_scan_context(None) == {}


def test_parse_partial_line():
    text = "TICKER=GLD  IVR=35  IV_HV=1.15"
    result = parse_scan_context(text)
    assert result["ticker"] == "GLD"
    assert result["ivr"] == 35.0
    assert result["iv_hv"] == 1.15
    assert "pema200" not in result
    assert "pc_ratio" not in result


# ─── apply_scan_context_to_gate_payload ───────────────────────────────────────

def test_apply_overrides_ivr():
    gate_payload = {"put_call_volume": None, "trend_pema200": None, "trend_pema50": None}
    ivr_for_gates = {"ivr_pct": 10.0}
    payload = {"scan_context": "TICKER=XLF  IVR=47  IV_HV=1.21  PEMA200=+3.1  PEMA50=+1.2  PC=0.85  DIRECTION=sell_put"}
    gp, ivr, conf = apply_scan_context_to_gate_payload(gate_payload, ivr_for_gates, "unknown", payload)
    assert ivr["ivr_pct"] == 47.0
    assert conf == "known"
    assert gp["put_call_volume"] == 0.85
    assert gp["trend_pema200"] == 3.1
    assert gp["trend_pema50"] == 1.2


def test_apply_no_scan_context_is_noop():
    gate_payload = {"put_call_volume": None, "trend_pema200": None, "trend_pema50": None}
    ivr_for_gates = {"ivr_pct": 10.0}
    payload = {}
    gp, ivr, conf = apply_scan_context_to_gate_payload(gate_payload, ivr_for_gates, "unknown", payload)
    assert ivr["ivr_pct"] == 10.0  # unchanged
    assert conf == "unknown"        # unchanged


# ─── _trend_ema_gate ──────────────────────────────────────────────────────────

def test_trend_gate_no_data_passes():
    p = make_gate_payload()
    p["trend_pema200"] = None
    p["trend_pema50"] = None
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "sell_put")
    assert gate["status"] == "pass"


def test_trend_gate_sell_put_below_200_blocks():
    p = make_gate_payload()
    p["trend_pema200"] = -2.0
    p["trend_pema50"] = -5.0
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "sell_put")
    assert gate["status"] == "fail"
    assert gate["blocking"] is True


def test_trend_gate_sell_put_pullback_warns():
    p = make_gate_payload()
    p["trend_pema200"] = +3.0
    p["trend_pema50"] = -1.5
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "sell_put")
    assert gate["status"] == "warn"
    assert gate["blocking"] is False


def test_trend_gate_sell_put_uptrend_passes():
    p = make_gate_payload()
    p["trend_pema200"] = +5.0
    p["trend_pema50"] = +2.0
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "sell_put")
    assert gate["status"] == "pass"


def test_trend_gate_sell_call_uptrend_warns():
    p = make_gate_payload()
    p["trend_pema200"] = +5.0
    p["trend_pema50"] = +2.0
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "sell_call")
    assert gate["status"] == "warn"
    assert gate["blocking"] is False


def test_trend_gate_buy_call_below_200_blocks():
    p = make_gate_payload()
    p["trend_pema200"] = -3.0
    p["trend_pema50"] = -5.0
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "buy_call")
    assert gate["status"] == "fail"
    assert gate["blocking"] is True


def test_trend_gate_buy_put_above_200_blocks():
    p = make_gate_payload()
    p["trend_pema200"] = +5.0
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "buy_put")
    assert gate["status"] == "fail"
    assert gate["blocking"] is True


def test_trend_gate_buy_put_downtrend_passes():
    p = make_gate_payload()
    p["trend_pema200"] = -3.0
    p["trend_pema50"] = -5.0
    engine = GateEngine()
    gate = engine._trend_ema_gate(p, "buy_put")
    assert gate["status"] == "pass"


def test_trend_gate_wired_into_sell_put_track():
    """Verify trend_ema gate appears in ETF sell_put gates list."""
    p = make_gate_payload(ivr_pct=45.0, hv_20=15.0)
    p.update({"ticker": "QQQ", "put_call_volume": None,
              "trend_pema200": +5.0, "trend_pema50": +2.0,
              "macro_event_count": 0, "macro_event_score": 0,
              "macro_days_away": 999, "macro_event_name": "CPI",
              "etf_holdings_at_risk": [], "max_21d_drawdown_pct": None,
              "max_21d_rally_pct": None, "stress_bars_available": 0,
              "hv_iv_ratio": 1.22, "max_gain_per_lot": -1.0})
    engine = GateEngine()
    gates = engine.run("sell_put", p, etf_mode=True)
    trend_gate = _find(gates, "trend_ema")
    assert trend_gate is not None
    assert trend_gate["status"] == "pass"
