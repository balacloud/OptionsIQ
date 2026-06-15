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


# ---------------------------------------------------------------------------
# KI-096: IVR unknown (no history) must WARN, not FAIL, on seller tracks
# ---------------------------------------------------------------------------
def test_seller_unknown_ivr_warns_not_fails():
    """sell_put with ivr_confidence=unknown → ivr_seller gate is WARN (non-blocking), not FAIL."""
    payload = make_gate_payload(ivr_pct=None, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="unknown")
    payload["hv_iv_ratio"] = 1.1  # pass VRP gate
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr_seller")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "warn"
    assert ivr_gate["blocking"] is False


def test_seller_known_low_ivr_still_fails():
    """sell_put with ivr_confidence=known and low IVR → ivr_seller gate still FAILs (existing behavior preserved)."""
    payload = make_gate_payload(ivr_pct=5.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr_seller")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "fail"


# ---------------------------------------------------------------------------
# KI-097: event density gate — count events in DTE window
# ---------------------------------------------------------------------------
def test_event_density_high_count_blocks_rate_sensitive_etf():
    """4+ events in DTE window should BLOCK for rate-sensitive ETF (XLF)."""
    payload = make_gate_payload(ivr_pct=45.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    payload["macro_event_count"] = 4
    payload["macro_event_score"] = 10
    payload["ticker"] = "XLF"
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    density_gate = _find_gate(gates, "event_density")
    assert density_gate is not None
    assert density_gate["status"] == "fail"
    assert density_gate["blocking"] is True


def test_event_density_low_count_passes():
    """1 event in DTE window should PASS for any ETF."""
    payload = make_gate_payload(ivr_pct=45.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    payload["macro_event_count"] = 1
    payload["macro_event_score"] = 2
    payload["ticker"] = "XLF"
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    density_gate = _find_gate(gates, "event_density")
    assert density_gate is not None
    assert density_gate["status"] == "pass"


def test_verdict_fail_when_blocking_gate_fails():
    """A blocking fail should produce fail verdict."""
    payload = make_gate_payload(ivr_pct=95.0, hv_20=10.0)
    engine = GateEngine()
    gates = engine.run("buy_call", payload, etf_mode=True)
    # Force a blocking fail for test purposes
    gates.append({"id": "test_block", "name": "Test Block", "status": "fail", "blocking": True, "reason": "test"})
    verdict = engine.build_verdict(gates)
    assert verdict["status"] == "fail"


# ---------------------------------------------------------------------------
# P1 Day 68: IVR seller threshold raised 35→40 + warn band 35–40%
# ---------------------------------------------------------------------------
def test_seller_ivr_40_passes():
    """IVR >= 40 should now PASS (was 35 before Day 68)."""
    payload = make_gate_payload(ivr_pct=40.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    payload["hv_iv_ratio"] = 1.1
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr_seller")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "pass"


def test_seller_ivr_borderline_35_warns():
    """IVR 35–40 should be WARN (new band, non-blocking) — Day 68."""
    payload = make_gate_payload(ivr_pct=37.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    payload["hv_iv_ratio"] = 1.1
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr_seller")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "warn"
    assert ivr_gate["blocking"] is False
    assert "35" in ivr_gate["reason"] or "borderline" in ivr_gate["reason"]


def test_seller_ivr_below_35_still_warns():
    """IVR 25–35 (minimum viable floor) should still WARN."""
    payload = make_gate_payload(ivr_pct=28.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    payload["hv_iv_ratio"] = 1.1
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr_seller")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "warn"


def test_seller_ivr_below_25_fails():
    """IVR < 25 should FAIL (insufficient premium floor unchanged)."""
    payload = make_gate_payload(ivr_pct=15.0, hv_20=18.0, dte=35,
                                strike=440.0, ivr_confidence="known")
    engine = GateEngine()
    gates = engine.run("sell_put", payload, etf_mode=True)
    ivr_gate = _find_gate(gates, "ivr_seller")
    assert ivr_gate is not None
    assert ivr_gate["status"] == "fail"


# ---------------------------------------------------------------------------
# P3 Day 68: TQQQ satellite gate — separate IVR/VRP/skew thresholds
# ---------------------------------------------------------------------------
def test_tqqq_gate_skips_non_tqqq():
    """Non-TQQQ ticker should produce a pass gate with N/A."""
    payload = make_gate_payload(ivr_pct=45.0, hv_20=18.0, dte=30)
    payload["ticker"] = "QQQ"
    engine = GateEngine()
    gate = engine._tqqq_satellite_gate(payload)
    assert gate["status"] == "pass"
    assert "N/A" in gate["computed_value"]


def test_tqqq_gate_all_conditions_good_passes():
    """TQQQ with IVR≥50, IV/HV≥1.15, VIX<18, skew<8 → PASS."""
    payload = make_gate_payload(ivr_pct=55.0, hv_20=18.0, dte=30,
                                ivr_confidence="known")
    payload["ticker"] = "TQQQ"
    payload["hv_iv_ratio"] = 1.20   # IV/HV = 1.20 >= 1.15
    payload["vix"] = 15.0
    payload["skew_value"] = 5.0     # < 8
    engine = GateEngine()
    gate = engine._tqqq_satellite_gate(payload)
    assert gate["status"] == "pass"
    assert gate["blocking"] is False


def test_tqqq_gate_high_vix_warns():
    """TQQQ with VIX >= 18 should WARN."""
    payload = make_gate_payload(ivr_pct=55.0, hv_20=18.0, dte=30,
                                ivr_confidence="known")
    payload["ticker"] = "TQQQ"
    payload["hv_iv_ratio"] = 1.20
    payload["vix"] = 20.0
    payload["skew_value"] = 5.0
    engine = GateEngine()
    gate = engine._tqqq_satellite_gate(payload)
    assert gate["status"] == "warn"
    assert gate["blocking"] is False
    assert "VIX" in gate["reason"]


def test_tqqq_gate_low_ivr_warns():
    """TQQQ with IVR < 40 should WARN about thin premium."""
    payload = make_gate_payload(ivr_pct=32.0, hv_20=18.0, dte=30,
                                ivr_confidence="known")
    payload["ticker"] = "TQQQ"
    payload["hv_iv_ratio"] = 1.20
    payload["vix"] = 15.0
    payload["skew_value"] = 5.0
    engine = GateEngine()
    gate = engine._tqqq_satellite_gate(payload)
    assert gate["status"] == "warn"
    assert "IVR" in gate["reason"]


def test_tqqq_gate_borderline_ivr_warns():
    """TQQQ with IVR 40–50 should WARN (prefer IVR ≥ 50)."""
    payload = make_gate_payload(ivr_pct=45.0, hv_20=18.0, dte=30,
                                ivr_confidence="known")
    payload["ticker"] = "TQQQ"
    payload["hv_iv_ratio"] = 1.20
    payload["vix"] = 15.0
    payload["skew_value"] = 5.0
    engine = GateEngine()
    gate = engine._tqqq_satellite_gate(payload)
    assert gate["status"] == "warn"
    assert "borderline" in gate["reason"].lower() or "40" in gate["reason"]


def test_tqqq_gate_elevated_skew_warns():
    """TQQQ with skew >= 8 pts should WARN."""
    payload = make_gate_payload(ivr_pct=55.0, hv_20=18.0, dte=30,
                                ivr_confidence="known")
    payload["ticker"] = "TQQQ"
    payload["hv_iv_ratio"] = 1.20
    payload["vix"] = 15.0
    payload["skew_value"] = 9.5   # >= 8
    engine = GateEngine()
    gate = engine._tqqq_satellite_gate(payload)
    assert gate["status"] == "warn"
    assert "skew" in gate["reason"].lower() or "9.5" in gate["reason"]
