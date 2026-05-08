"""Shared test helpers for OptionsIQ. Importable from any test module."""


def make_chain(underlying=450.0, strikes=None, right="C", dte=30, expiry="2026-05-16"):
    """Build a synthetic chain dict for testing spread math and strategy routing."""
    if strikes is None:
        strikes = [440, 445, 448, 450, 452, 455, 460]
    contracts = []
    for s in strikes:
        moneyness = (s - underlying) / underlying
        if right == "C":
            delta = max(0.05, min(0.95, 0.5 - moneyness * 3))
        else:
            delta = -max(0.05, min(0.95, 0.5 + moneyness * 3))

        mid_val = max(0.07, abs(underlying - s) * 0.825) if abs(underlying - s) > 0.1 else 2.0
        contracts.append({
            "strike": float(s), "right": right, "dte": dte, "expiry": expiry,
            "delta": round(delta, 4),
            "theta": -0.04, "vega": 0.10, "gamma": 0.008,
            "bid": round(max(0.05, mid_val * 0.95), 2),
            "ask": round(max(0.10, mid_val * 1.05), 2),
            "mid": round(mid_val, 2),
            "impliedVol": 0.22, "openInterest": 2000, "volume": 500,
        })
    return {"underlying_price": underlying, "contracts": contracts}


def make_etf_swing_data(ivr_pct=None):
    """Minimal ETF swing_data dict (swing_data_quality='etf')."""
    return {
        "signal": None,
        "spy_above_200sma": True,
        "spy_5day_return": -0.005,
        "fomc_days_away": 999,
        "ivr_pct_hint": ivr_pct,
        "entry_pullback": None, "entry_momentum": None,
        "stop_loss": None, "target1": None, "target2": None,
        "risk_reward": None, "vcp_pivot": None, "vcp_confidence": None,
        "adx": None, "last_close": None, "s1_support": None,
        "earnings_days_away": None, "pattern": None,
        "source": "etf_regime", "swing_data_quality": "etf",
        "synthesized_fields": [],
    }


def make_gate_payload(underlying=450.0, dte=30, strike=452.0, premium=1.5,
                      ivr_pct=25.0, hv_20=18.0, spy_above=True, spy_5d=-0.005,
                      ivr_confidence=None):
    """Minimal gate_payload for ETF gate tests."""
    if ivr_confidence is None:
        ivr_confidence = "known" if ivr_pct is not None else "unknown"
    return {
        "underlying_price": underlying,
        "selected_expiry_dte": dte,
        "strike": strike,
        "premium": premium,
        "theta_per_day": -0.04,
        "open_interest": 2000.0,
        "volume": 500.0,
        "bid": 1.40,
        "ask": 1.60,
        "max_gain_per_lot": premium * 100,
        "account_size": 25000.0,
        "risk_pct": 0.01,
        "fomc_days_away": 999,
        "lots": 1.0,
        "current_iv": 22.0,
        "ivr_pct": ivr_pct,
        "ivr_confidence": ivr_confidence,
        "hv_20": hv_20,
        "hv_iv_ratio": round(22.0 / hv_20, 2) if hv_20 else 0.0,
        "history_days": 252,
        "fallback_used": False,
        "signal": None,
        "spy_above_200sma": spy_above,
        "spy_5day_return": spy_5d,
        "ivr_pct_hint": ivr_pct,
        "entry_pullback": None, "entry_momentum": None,
        "stop_loss": None, "target1": None, "target2": None,
        "risk_reward": None, "vcp_pivot": None, "vcp_confidence": None,
        "adx": None, "last_close": None, "s1_support": None,
        "earnings_days_away": None, "pattern": None,
        "source": "etf_regime", "swing_data_quality": "etf",
        "synthesized_fields": [],
    }
