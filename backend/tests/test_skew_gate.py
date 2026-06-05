"""Tests for _skew_flow_gate — institutional IV skew signal (Day 66)."""
import pytest
from helpers import make_gate_payload
from gate_engine import GateEngine


def _skew_gate(gates):
    return next((g for g in gates if g["id"] == "skew_flow"), None)


# ── sell_put ──────────────────────────────────────────────────────────────────

def test_sell_put_normal_skew_passes():
    """skew 4.5 pts (below 7 threshold) → pass for sell_put."""
    payload = make_gate_payload(skew_value=4.5)
    gates = GateEngine().run("sell_put", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "pass"
    assert g["blocking"] is False


def test_sell_put_elevated_skew_warns():
    """skew 8.0 pts (7–10 range) → warn for sell_put."""
    payload = make_gate_payload(skew_value=8.0)
    gates = GateEngine().run("sell_put", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "warn"
    assert g["blocking"] is False


def test_sell_put_heavy_skew_warns_not_blocks():
    """skew 12.0 pts (above 10 threshold) → strong warn but still not blocking."""
    payload = make_gate_payload(skew_value=12.0)
    gates = GateEngine().run("sell_put", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "warn"
    assert g["blocking"] is False
    assert "Heavy" in g["reason"]


def test_sell_put_no_skew_data_passes():
    """skew_value=None (Tradier unavailable) → pass, not a fail."""
    payload = make_gate_payload(skew_value=None)
    gates = GateEngine().run("sell_put", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "pass"
    assert g["blocking"] is False


# ── sell_call ─────────────────────────────────────────────────────────────────

def test_sell_call_normal_skew_passes():
    """skew 5.0 pts (above 2 threshold) → pass for sell_call."""
    payload = make_gate_payload(skew_value=5.0)
    gates = GateEngine().run("sell_call", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "pass"
    assert g["blocking"] is False


def test_sell_call_low_skew_warns():
    """skew 1.0 pts (at or below 2 threshold) → warn for sell_call (call momentum)."""
    payload = make_gate_payload(skew_value=1.0)
    gates = GateEngine().run("sell_call", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "warn"
    assert g["blocking"] is False


def test_sell_call_inverted_skew_warns():
    """Negative skew (calls more expensive than puts) → warn for sell_call."""
    payload = make_gate_payload(skew_value=-1.5)
    gates = GateEngine().run("sell_call", payload, etf_mode=True)
    g = _skew_gate(gates)
    assert g is not None
    assert g["status"] == "warn"
    assert g["blocking"] is False
    assert "squeeze" in g["reason"].lower() or "momentum" in g["reason"].lower()
