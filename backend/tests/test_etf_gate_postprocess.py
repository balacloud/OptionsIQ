"""Test ETF gate post-processing adjustments from analyze_service."""
from analyze_service import apply_etf_gate_adjustments


def test_oi_zero_promoted_to_pass():
    """OI=0 platform limitation + acceptable spread → promoted from warn to pass."""
    gates = [{
        "id": "liquidity",
        "name": "Liquidity",
        "status": "warn",
        "blocking": False,
        "reason": "Low liquidity",
        "computed_value": "OI 0 [OI unavailable], Vol/OI N/A, Prem 0.48, Spread 5.20%",
    }]
    apply_etf_gate_adjustments(gates, "sell_call", 25000.0, {}, [])
    assert gates[0]["status"] == "pass"
    assert "IBKR platform limitation" in gates[0]["reason"]


def test_oi_zero_not_promoted_when_spread_too_wide():
    """OI=0 with spread above SPREAD_FAIL_PCT should stay as warn."""
    gates = [{
        "id": "liquidity",
        "name": "Liquidity",
        "status": "warn",
        "blocking": False,
        "reason": "Wide spread",
        "computed_value": "OI 0 [OI unavailable], Vol/OI N/A, Prem 0.48, Spread 25.00%",
    }]
    apply_etf_gate_adjustments(gates, "sell_call", 25000.0, {}, [])
    assert gates[0]["status"] == "warn"


def test_sell_put_max_loss_spread_recalc():
    """bull_put_spread max_loss $395 on $25k account should pass (< 10%)."""
    gates = [{
        "id": "max_loss",
        "name": "Max Loss",
        "status": "fail",
        "blocking": True,
        "reason": "Naked put max loss $13k",
        "computed_value": "$13000",
    }]
    strategies = [{"strategy_type": "bull_put_spread", "max_loss_per_lot": 395.0}]
    apply_etf_gate_adjustments(gates, "sell_put", 25000.0, {}, strategies)
    assert gates[0]["status"] == "pass"
    assert gates[0]["blocking"] is False


def test_sell_put_max_loss_still_fails_if_too_large():
    """bull_put_spread max_loss $6000 on $25k account should still fail (>20%)."""
    gates = [{
        "id": "max_loss",
        "name": "Max Loss",
        "status": "fail",
        "blocking": True,
        "reason": "Too large",
        "computed_value": "$13000",
    }]
    strategies = [{"strategy_type": "bull_put_spread", "max_loss_per_lot": 6000.0}]
    apply_etf_gate_adjustments(gates, "sell_put", 25000.0, {}, strategies)
    assert gates[0]["status"] == "fail"
    assert gates[0]["blocking"] is True


def test_sell_call_market_regime_non_blocking():
    """sell_call market_regime_seller should be demoted to non-blocking for ETFs."""
    gates = [{
        "id": "market_regime_seller",
        "name": "Market Regime (Seller)",
        "status": "fail",
        "blocking": True,
        "reason": "SPY bull market",
    }]
    apply_etf_gate_adjustments(gates, "sell_call", 25000.0, {}, [])
    assert gates[0]["blocking"] is False


def test_spread_fail_15pct_downgraded_to_warn_for_etf():
    """Spread 15% (wider than stock SPREAD_FAIL_PCT but below DATA_FAIL_PCT) → warn, non-blocking."""
    gates = [{
        "id": "liquidity",
        "name": "Liquidity Proxy",
        "status": "fail",
        "blocking": True,
        "reason": "Spread too wide for efficient execution",
        "computed_value": "OI 1500, Vol/OI 0.25, Prem 1.50, Spread 15.00%",
        "spread_pct": 15.0,
    }]
    apply_etf_gate_adjustments(gates, "sell_put", 25000.0, {}, [])
    assert gates[0]["status"] == "warn"
    assert gates[0]["blocking"] is False
    assert "review bid-ask" in gates[0]["reason"]


def test_spread_fail_27pct_stays_blocking_for_etf():
    """Spread 27% (>SPREAD_DATA_FAIL_PCT=20%) → stays fail + blocking=True (data garbage, KI-080)."""
    gates = [{
        "id": "liquidity",
        "name": "Liquidity Proxy",
        "status": "fail",
        "blocking": False,
        "reason": "Spread too wide for efficient execution",
        "computed_value": "OI 1500, Vol/OI 0.25, Prem 1.50, Spread 27.52%",
        "spread_pct": 27.52,
    }]
    apply_etf_gate_adjustments(gates, "sell_put", 25000.0, {}, [])
    assert gates[0]["status"] == "fail"
    assert gates[0]["blocking"] is True
    assert "data unreliable" in gates[0]["reason"]


def test_dte_seller_promoted_within_etf_range():
    """DTE 30 within ETF sweet spot (21-45) should promote dte_seller warn → pass."""
    gates = [{
        "id": "dte_seller",
        "name": "DTE Seller",
        "status": "warn",
        "blocking": False,
        "reason": "DTE outside stock range",
    }]
    payload = {"selected_expiry_dte": 30}
    apply_etf_gate_adjustments(gates, "sell_call", 25000.0, payload, [])
    assert gates[0]["status"] == "pass"
