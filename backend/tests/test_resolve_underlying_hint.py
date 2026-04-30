"""Tests for _resolve_underlying_hint helper in analyze_service (KI-088)."""
from unittest.mock import MagicMock, patch

from analyze_service import _resolve_underlying_hint


def test_explicit_last_close_wins():
    """payload['last_close'] takes precedence — no STA call needed."""
    with patch("analyze_service._requests") as mock_req:
        result = _resolve_underlying_hint("XLF", {"last_close": 52.0})
    assert result == 52.0
    mock_req.get.assert_not_called()


def test_sta_fallback_when_no_explicit_price():
    """Falls back to STA currentPrice when payload has no last_close."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"currentPrice": 52.02}
    with patch("analyze_service._requests") as mock_req:
        mock_req.get.return_value = mock_resp
        result = _resolve_underlying_hint("XLF", {})
    assert result == 52.02


def test_returns_none_when_sta_unreachable():
    """Returns None gracefully when STA raises — lets downstream IBKR path run."""
    with patch("analyze_service._requests") as mock_req:
        mock_req.get.side_effect = ConnectionError("STA down")
        result = _resolve_underlying_hint("XLF", {})
    assert result is None
