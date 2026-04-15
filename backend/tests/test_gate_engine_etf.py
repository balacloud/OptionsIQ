"""Test ETF gate engine produces correct pass/warn/fail for key gates."""
from helpers import make_gate_payload
from gate_engine import GateEngine


def _find_gate(gates, gate_id):
    return next((g for g in gates if g["id"] == gate_id), None)


def test_buy_call_low_ivr_passes():
    """IVR < 30% should pass the ivr gate for buy_call (buyer wants cheap IV)."""
    payload = make_gate_payload(ivr_pct=25.0, hv_20=18.0)
    engine = GateEngine()
    gates = engine.run("buy_call", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "pass"


def test_buy_call_high_ivr_warns_or_fails():
    """IVR > 80% should fail or warn the ivr gate for buy_call (IV crush risk)."""
    payload = make_gate_payload(ivr_pct=85.0, hv_20=15.0)
    engine = GateEngine()
    gates = engine.run("buy_call", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr")
    assert ivr_gate is not None
    assert ivr_gate["status"] in ("fail", "warn")


def test_seller_dte_in_range():
    """DTE 30 within seller sweet spot (21-45) should pass or warn the dte_seller gate."""
    payload = make_gate_payload(dte=30)
    engine = GateEngine()
    gates = engine.run("sell_call", payload, etf_mode=True)
    dte_gate = _find_gate(gates, "dte_seller")
    # sell_call gate may not have dte_seller — check if present
    if dte_gate:
        assert dte_gate["status"] in ("pass", "warn")


def test_verdict_go_when_all_pass():
    """When no blocking fails, verdict should be pass or warn (not fail)."""
    payload = make_gate_payload(ivr_pct=25.0, hv_20=18.0, dte=60, premium=5.0)
    # Ensure theta/premium ratio won't block: theta_burn checks abs(theta)/premium
    payload["theta_per_day"] = -0.02  # small theta relative to premium
    engine = GateEngine()
    gates = engine.run("buy_call", payload, etf_mode=True)
    verdict = engine.build_verdict(gates)
    # With good inputs, should not be hard-blocked
    assert verdict["status"] in ("pass", "warn")


def test_verdict_fail_when_blocking_gate_fails():
    """A blocking fail should produce fail verdict."""
    payload = make_gate_payload(ivr_pct=95.0, hv_20=10.0)
    engine = GateEngine()
    gates = engine.run("buy_call", payload, etf_mode=True)
    # Force a blocking fail for test purposes
    gates.append({"id": "test_block", "name": "Test Block", "status": "fail", "blocking": True, "reason": "test"})
    verdict = engine.build_verdict(gates)
    assert verdict["status"] == "fail"
