"""Test direction normalization and strategy routing."""
from helpers import make_chain
from constants import DIRECTION_TO_CHAIN_DIR
from strategy_ranker import StrategyRanker
from sector_scan_service import quadrant_to_direction


ranker = StrategyRanker()


# ---------------------------------------------------------------------------
# KI-098: absolute trend gate — weekChange blocks tape-fighting bear_call_spread
# ---------------------------------------------------------------------------
def test_lagging_sector_down_on_week_returns_bear_call_spread():
    """Lagging + week_change negative → bear_call_spread allowed."""
    result = quadrant_to_direction(
        "Lagging", rs_ratio=96.0, rs_momentum=-0.8, week_change=-1.5
    )
    assert result == "bear_call_spread"


def test_lagging_sector_up_on_week_blocked():
    """Lagging + week_change positive → tape-fighting, return None."""
    result = quadrant_to_direction(
        "Lagging", rs_ratio=96.0, rs_momentum=-0.8, week_change=2.1
    )
    assert result is None


def test_lagging_sector_week_change_zero_returns_bear_call_spread():
    """Lagging + week_change exactly 0 → flat week, allow (not rising)."""
    result = quadrant_to_direction(
        "Lagging", rs_ratio=96.0, rs_momentum=-0.8, week_change=0.0
    )
    assert result == "bear_call_spread"


def test_lagging_sector_week_change_none_returns_bear_call_spread():
    """Lagging + week_change None (size ETF, data unavailable) → gate bypassed."""
    result = quadrant_to_direction(
        "Lagging", rs_ratio=96.0, rs_momentum=-0.8, week_change=None
    )
    assert result == "bear_call_spread"


def test_bear_call_spread_normalizes_to_sell_call():
    assert DIRECTION_TO_CHAIN_DIR["bear_call_spread"] == "sell_call"


def test_bull_put_spread_normalizes_to_sell_put():
    assert DIRECTION_TO_CHAIN_DIR.get("bull_put_spread", "sell_put") == "sell_put"


def test_sell_call_routes_to_bear_call_spread():
    chain = make_chain(underlying=50.0, strikes=[49, 50, 51, 52, 53, 54, 55], right="C", dte=30)
    results = ranker.rank("sell_call", chain, {"swing_data_quality": "etf"}, recommended_dte=30)
    assert len(results) > 0
    assert results[0]["strategy_type"] == "bear_call_spread"


def test_sell_put_etf_routes_to_bull_put_spread():
    chain = make_chain(underlying=140.0, strikes=[130, 132, 134, 136, 138], right="P", dte=30)
    results = ranker.rank("sell_put", chain, {"swing_data_quality": "etf"}, recommended_dte=30)
    assert len(results) > 0
    assert results[0]["strategy_type"] == "bull_put_spread"


def test_buy_call_returns_strategies():
    chain = make_chain(underlying=100.0, strikes=[90, 92, 95, 98, 100, 102, 105], right="C", dte=60)
    results = ranker.rank("buy_call", chain, {"swing_data_quality": "etf"}, recommended_dte=60)
    assert len(results) > 0
    assert results[0]["right"] == "C"


def test_buy_put_returns_strategies():
    chain = make_chain(underlying=100.0, strikes=[95, 98, 100, 102, 105, 108, 110], right="P", dte=60)
    results = ranker.rank("buy_put", chain, {"swing_data_quality": "etf"}, recommended_dte=60)
    assert len(results) > 0
    assert results[0]["right"] == "P"
