"""Test spread math: max_loss, max_gain, breakeven for bear_call and bull_put spreads."""
from helpers import make_chain
from strategy_ranker import StrategyRanker, _credit_width
from constants import MIN_CREDIT_WIDTH_RATIO


ranker = StrategyRanker()


def test_bear_call_spread_math():
    """Bear call spread: net_credit, max_loss, breakeven must be correct."""
    # Chain: OTM calls at 53 and 55 for underlying at 50
    chain = make_chain(underlying=50.0, strikes=[50, 51, 52, 53, 54, 55, 56, 57], right="C", dte=30)
    swing = {"swing_data_quality": "etf"}
    results = ranker.rank("sell_call", chain, swing, recommended_dte=30)

    assert len(results) > 0
    top = results[0]
    assert top["strategy_type"] == "bear_call_spread"
    assert top["short_strike"] < top["long_strike"], "Short strike must be below long strike for bear call"

    width = top["long_strike"] - top["short_strike"]
    net_credit = top["net_premium"]
    assert net_credit > 0, "Bear call spread must have positive net credit"
    assert abs(top["max_gain_per_lot"] - net_credit * 100) < 0.02
    assert abs(top["max_loss_per_lot"] - (width - net_credit) * 100) < 0.02
    assert abs(top["breakeven"] - (top["short_strike"] + net_credit)) < 0.02


def test_bull_put_spread_math():
    """Bull put spread: net_credit, max_loss, breakeven must be correct."""
    # Chain: OTM puts at 130, 132, 134, 136, 138 for underlying at 140
    chain = make_chain(underlying=140.0, strikes=[128, 130, 132, 134, 136, 138], right="P", dte=30)
    swing = {"swing_data_quality": "etf"}
    results = ranker.rank("sell_put", chain, swing, recommended_dte=30)

    assert len(results) > 0
    top = results[0]
    assert top["strategy_type"] == "bull_put_spread"
    assert top["short_strike"] > top["long_strike"], "Short strike must be above long strike for bull put"

    width = top["short_strike"] - top["long_strike"]
    net_credit = top["net_premium"]
    assert net_credit > 0, "Bull put spread must have positive net credit"
    assert abs(top["max_gain_per_lot"] - net_credit * 100) < 0.02
    assert abs(top["max_loss_per_lot"] - (width - net_credit) * 100) < 0.02
    assert abs(top["breakeven"] - (top["short_strike"] - net_credit)) < 0.02


def test_credit_width_ratio_pass():
    """credit_to_width_ratio present and >= 0.33 → no warning."""
    ratio, warn = _credit_width(0.40, 1.00)   # 40% — passes
    assert ratio == 0.4
    assert warn is None


def test_credit_width_ratio_fail():
    """credit_to_width_ratio < 0.33 → warning is set."""
    ratio, warn = _credit_width(0.05, 1.00)   # 5% — KI-082 scenario
    assert ratio == 0.05
    assert warn is not None
    assert "33%" in warn


def test_credit_width_ratio_zero_width():
    """Zero width → ratio is None, no warning."""
    ratio, warn = _credit_width(0.10, 0.0)
    assert ratio is None
    assert warn is None


def test_spread_strategies_have_cw_ratio():
    """All spread strategies expose credit_to_width_ratio field."""
    chain = make_chain(underlying=140.0, strikes=[128, 130, 132, 134, 136, 138], right="P", dte=30)
    results = ranker.rank("sell_put", chain, {"swing_data_quality": "etf"}, recommended_dte=30)
    for r in results:
        if r.get("strategy_type") == "bull_put_spread":
            assert "credit_to_width_ratio" in r, f"Rank {r['rank']} missing credit_to_width_ratio"


def test_spread_max_loss_bounded():
    """Max loss must be (width - credit) * 100 — never negative, never exceed width * 100."""
    chain = make_chain(underlying=50.0, strikes=[48, 49, 50, 51, 52, 53, 54], right="C", dte=30)
    results = ranker.rank("sell_call", chain, {"swing_data_quality": "etf"}, recommended_dte=30)
    for r in results:
        if r.get("strategy_type") == "bear_call_spread":
            width_dollars = (r["long_strike"] - r["short_strike"]) * 100
            assert 0 <= r["max_loss_per_lot"] <= width_dollars
