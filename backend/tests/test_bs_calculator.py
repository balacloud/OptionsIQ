"""Test Black-Scholes greeks are within expected ranges."""
from bs_calculator import compute_greeks


def test_atm_call_delta_near_half():
    g = compute_greeks(S=100, K=100, T=30 / 365, r=0.053, sigma=0.22, right="C")
    assert g is not None
    assert 0.48 <= g["delta"] <= 0.58


def test_itm_call_delta_high():
    g = compute_greeks(S=100, K=90, T=30 / 365, r=0.053, sigma=0.22, right="C")
    assert g is not None
    assert 0.80 <= g["delta"] <= 0.99


def test_otm_call_delta_low():
    g = compute_greeks(S=100, K=115, T=30 / 365, r=0.053, sigma=0.22, right="C")
    assert g is not None
    assert 0.0 < g["delta"] < 0.15


def test_put_delta_negative():
    g = compute_greeks(S=100, K=100, T=30 / 365, r=0.053, sigma=0.22, right="P")
    assert g is not None
    assert -0.55 <= g["delta"] <= -0.40


def test_theta_negative():
    g = compute_greeks(S=100, K=100, T=30 / 365, r=0.053, sigma=0.22, right="C")
    assert g is not None
    assert g["theta"] < 0, "Theta should be negative (time decay)"


def test_vega_positive():
    g = compute_greeks(S=100, K=100, T=30 / 365, r=0.053, sigma=0.22, right="C")
    assert g is not None
    assert g["vega"] > 0


def test_invalid_inputs_return_none():
    assert compute_greeks(S=0, K=100, T=30 / 365, r=0.053, sigma=0.22, right="C") is None
    assert compute_greeks(S=100, K=100, T=0, r=0.053, sigma=0.22, right="C") is None
    assert compute_greeks(S=100, K=100, T=30 / 365, r=0.053, sigma=-0.1, right="C") is None
    assert compute_greeks(S=100, K=100, T=30 / 365, r=0.053, sigma=0.22, right="X") is None
