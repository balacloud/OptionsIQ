"""Tests for chart_context_parser."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from chart_context_parser import (
    parse_chart_context,
    compute_strike_vs_support,
    apply_chart_context_to_response,
)
from helpers import make_gate_payload


# ─── parse_chart_context ──────────────────────────────────────────────────────

def test_parse_full_line():
    text = (
        "CHART CONTEXT  TICKER=QQQ  DIRECTION=sell_put  TREND=UPTREND  "
        "S1=710.00  S2=695.00  S3=675.00  R1=748.00  R2=760.00  RSI=58  ATR=8.40  "
        "CHART_VERDICT=go"
    )
    r = parse_chart_context(text)
    assert r["ticker"] == "QQQ"
    assert r["direction"] == "sell_put"
    assert r["trend"] == "uptrend"
    assert r["s1"] == 710.0
    assert r["s2"] == 695.0
    assert r["s3"] == 675.0
    assert r["r1"] == 748.0
    assert r["r2"] == 760.0
    assert r["rsi"] == 58.0
    assert r["atr"] == 8.40
    assert r["chart_verdict"] == "go"


def test_parse_omits_missing_s3():
    """S3 absent from line → 's3' not in result (graceful 'not visible')."""
    text = "CHART CONTEXT  TICKER=QQQ  S1=710.00  S2=695.00  R1=748.00  CHART_VERDICT=go"
    r = parse_chart_context(text)
    assert "s3" not in r
    assert r["s1"] == 710.0
    assert r["s2"] == 695.0


def test_parse_only_required_fields():
    text = "CHART CONTEXT  TICKER=XLF  DIRECTION=sell_put  TREND=RANGE  CHART_VERDICT=wait"
    r = parse_chart_context(text)
    assert r["ticker"] == "XLF"
    assert r["chart_verdict"] == "wait"
    assert "s1" not in r
    assert "r1" not in r


def test_parse_empty_returns_empty():
    assert parse_chart_context("") == {}
    assert parse_chart_context(None) == {}
    assert parse_chart_context("no keys here") == {}


def test_parse_verdict_values():
    for verdict, expected in [("go", "go"), ("wait", "wait"), ("block", "block")]:
        r = parse_chart_context(f"CHART CONTEXT CHART_VERDICT={verdict}")
        assert r["chart_verdict"] == expected


# ─── compute_strike_vs_support ────────────────────────────────────────────────

class TestSellPutZones:
    def _levels(self, s1=710.0, s2=695.0, s3=None):
        d = {"s1": s1, "s2": s2}
        if s3 is not None:
            d["s3"] = s3
        return d

    def test_above_s1_is_exposed(self):
        r = compute_strike_vs_support(715.0, self._levels(), "sell_put")
        assert r["zone"] == "above_s1"
        assert "ABOVE S1" in r["label"]
        assert "⚠️" in r["label"]

    def test_between_s1_s2(self):
        r = compute_strike_vs_support(700.0, self._levels(), "sell_put")
        assert r["zone"] == "between_s1_s2"
        assert "between S1" in r["label"]
        assert "✅" in r["label"]

    def test_below_s2(self):
        r = compute_strike_vs_support(680.0, self._levels(), "sell_put")
        assert r["zone"] == "below_s2"
        assert "below S2" in r["label"]
        assert "✅✅" in r["label"]

    def test_below_s1_only(self):
        """When only S1 is known and strike is below it."""
        r = compute_strike_vs_support(700.0, {"s1": 710.0}, "sell_put")
        assert r["zone"] == "below_s1"
        assert "✅" in r["label"]

    def test_no_levels_returns_no_data(self):
        r = compute_strike_vs_support(700.0, {}, "sell_put")
        assert r["zone"] == "no_data"
        assert r["label"] is None

    def test_buy_put_uses_same_support_logic(self):
        r = compute_strike_vs_support(680.0, self._levels(), "buy_put")
        assert r["zone"] == "below_s2"


class TestSellCallZones:
    def _levels(self, r1=748.0, r2=760.0):
        return {"r1": r1, "r2": r2}

    def test_above_r2_is_best(self):
        r = compute_strike_vs_support(765.0, self._levels(), "sell_call")
        assert r["zone"] == "above_r2"
        assert "✅✅" in r["label"]

    def test_above_r1(self):
        r = compute_strike_vs_support(750.0, self._levels(), "sell_call")
        assert r["zone"] == "above_r1"
        assert "✅" in r["label"]

    def test_below_r1_is_exposed(self):
        r = compute_strike_vs_support(740.0, self._levels(), "sell_call")
        assert r["zone"] == "below_r1"
        assert "⚠️" in r["label"]

    def test_no_resistance_returns_no_data(self):
        r = compute_strike_vs_support(750.0, {}, "sell_call")
        assert r["zone"] == "no_data"
        assert r["label"] is None


class TestAtrDistance:
    def test_atr_distance_computed(self):
        r = compute_strike_vs_support(700.0, {"s1": 710.0}, "sell_put",
                                      underlying=744.0, atr=8.4)
        # distance = (744 - 700) / 8.4 = 5.24 → rounded to 1dp = 5.2
        assert r["atr_distance"] == pytest.approx(5.2, abs=0.2)

    def test_atr_none_when_no_atr(self):
        r = compute_strike_vs_support(700.0, {"s1": 710.0}, "sell_put")
        assert r["atr_distance"] is None


# ─── apply_chart_context_to_response ─────────────────────────────────────────

def test_apply_no_chart_context_is_noop():
    """Missing chart_context key → response unchanged."""
    response = {"strategies": [{"strike": 715.0, "strategy_type": "sell_put"}], "gates": []}
    result = apply_chart_context_to_response(response.copy(), {}, underlying=744.0, direction="sell_put")
    assert "chart_verdict" not in result
    assert "chart_levels" not in result
    assert "strike_vs_support" not in result["strategies"][0]


def test_apply_adds_chart_verdict_and_levels():
    text = "CHART CONTEXT TICKER=QQQ DIRECTION=sell_put TREND=UPTREND S1=710.00 S2=695.00 R1=748.00 RSI=58 ATR=8.4 CHART_VERDICT=go"
    response = {"strategies": [{"strike": 700.0, "strategy_type": "sell_put"}], "gates": []}
    result = apply_chart_context_to_response(response, {"chart_context": text}, 744.0, "sell_put")
    assert result["chart_verdict"]["verdict"] == "go"
    assert result["chart_verdict"]["trend"] == "uptrend"
    assert result["chart_levels"]["s1"] == 710.0
    assert result["chart_levels"]["s2"] == 695.0
    assert "r1" in result["chart_levels"]


def test_apply_adds_strike_vs_support_per_strategy():
    text = "CHART CONTEXT TICKER=QQQ DIRECTION=sell_put TREND=UPTREND S1=710.00 S2=695.00 CHART_VERDICT=go ATR=8.4"
    strategies = [
        {"strike": 715.0, "strategy_type": "sell_put"},  # above S1 — exposed
        {"strike": 700.0, "strategy_type": "sell_put"},  # between S1/S2
        {"strike": 680.0, "strategy_type": "sell_put"},  # below S2 — safe
    ]
    response = {"strategies": strategies, "gates": []}
    result = apply_chart_context_to_response(response, {"chart_context": text}, 744.0, "sell_put")
    zones = [s["strike_vs_support"]["zone"] for s in result["strategies"]]
    assert zones == ["above_s1", "between_s1_s2", "below_s2"]


def test_chart_never_touches_gates():
    """Chart context must not modify gate_payload — zero blast radius."""
    gate_payload_before = make_gate_payload(underlying=744.0, strike=715.0)
    gate_payload_copy = dict(gate_payload_before)
    text = "CHART CONTEXT TICKER=QQQ DIRECTION=sell_put TREND=DOWNTREND S1=710.00 CHART_VERDICT=block"
    response = {"strategies": [], "gates": []}
    apply_chart_context_to_response(response, {"chart_context": text}, 744.0, "sell_put")
    # gate_payload must be completely unchanged
    assert gate_payload_before == gate_payload_copy


def test_apply_handles_no_strike_in_strategy():
    """Strategies without a strike field do not crash."""
    text = "CHART CONTEXT TICKER=QQQ DIRECTION=sell_put S1=710.00 CHART_VERDICT=go"
    response = {"strategies": [{"strategy_type": "sell_put"}], "gates": []}
    result = apply_chart_context_to_response(response, {"chart_context": text}, 744.0, "sell_put")
    assert "strike_vs_support" not in result["strategies"][0]


# need pytest.approx
import pytest
