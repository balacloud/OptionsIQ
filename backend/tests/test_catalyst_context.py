"""Tests for catalyst_context_parser — including Rule 23 reconciliation tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from catalyst_context_parser import (
    parse_catalyst_context,
    apply_catalyst_context_to_gate_payload,
    _strategy_catalyst_overlay,
)
from helpers import make_gate_payload


# ─── parse_catalyst_context ───────────────────────────────────────────────────

def test_parse_full_line():
    text = (
        "CATALYST CONTEXT  TICKER=QQQ  DIRECTION=sell_put  FOMC_DAYS=16  FOMC_TIER=warn  "
        "HOLDINGS_RISK=true  HOLDINGS_COMPANY=NVDA  HOLDINGS_DAYS=23  MACRO_COUNT=1  "
        "CATALYST_VERDICT=caution"
    )
    r = parse_catalyst_context(text)
    assert r["ticker"] == "QQQ"
    assert r["direction"] == "sell_put"
    assert r["fomc_days"] == 16
    assert r["fomc_tier"] == "warn"
    assert r["holdings_risk"] is True
    assert r["holdings_company"] == "NVDA"
    assert r["holdings_days"] == 23
    assert r["macro_count"] == 1
    assert r["catalyst_verdict"] == "caution"


def test_parse_bool_false():
    text = "CATALYST CONTEXT TICKER=QQQ HOLDINGS_RISK=false CATALYST_VERDICT=proceed"
    r = parse_catalyst_context(text)
    assert r["holdings_risk"] is False


def test_parse_omitted_holdings_when_no_risk():
    """When HOLDINGS_RISK=false the company/days fields are absent — both omitted."""
    text = "CATALYST CONTEXT TICKER=QQQ FOMC_DAYS=16 FOMC_TIER=warn HOLDINGS_RISK=false MACRO_COUNT=0 CATALYST_VERDICT=proceed"
    r = parse_catalyst_context(text)
    assert "holdings_company" not in r
    assert "holdings_days" not in r


def test_parse_int_fields():
    text = "CATALYST CONTEXT FOMC_DAYS=5 HOLDINGS_DAYS=14 MACRO_COUNT=3"
    r = parse_catalyst_context(text)
    assert isinstance(r["fomc_days"], int)
    assert isinstance(r["holdings_days"], int)
    assert isinstance(r["macro_count"], int)


def test_parse_empty_returns_empty():
    assert parse_catalyst_context("") == {}
    assert parse_catalyst_context(None) == {}
    assert parse_catalyst_context("nothing here") == {}


def test_parse_verdict_values():
    for v in ("proceed", "caution", "abort"):
        r = parse_catalyst_context(f"CATALYST CONTEXT CATALYST_VERDICT={v}")
        assert r["catalyst_verdict"] == v


# ─── apply_catalyst_context_to_gate_payload ───────────────────────────────────

def test_apply_noop_when_no_context():
    gate = make_gate_payload()
    gate_copy = dict(gate)
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, {})
    assert updated == gate_copy
    assert overlay == {}


def test_apply_adds_catalyst_override():
    gate = make_gate_payload()
    payload = {"catalyst_context": "CATALYST CONTEXT TICKER=QQQ FOMC_DAYS=16 FOMC_TIER=warn HOLDINGS_RISK=false MACRO_COUNT=1 CATALYST_VERDICT=caution"}
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, payload)
    assert "catalyst_override" in updated
    assert updated["catalyst_override"]["fomc_tier"] == "warn"
    assert updated["catalyst_override"]["catalyst_verdict"] == "caution"
    assert updated["catalyst_override"]["macro_count"] == 1


# ─── Rule 23 reconciliation tests (critical) ──────────────────────────────────

def test_catalyst_pass_does_not_modify_fomc_days():
    """Rule 23: catalyst FOMC_TIER=pass cannot override backend fomc_days_away.
    The backend fomc_days_away must be unchanged — gate_engine uses it for hard blocks.
    """
    gate = make_gate_payload(underlying=51.0, strike=49.0)
    gate["ticker"] = "XLF"
    gate["fomc_days_away"] = 10  # within BLOCK window (FOMC_BLOCK_DAYS=14)
    payload = {
        "catalyst_context": (
            "CATALYST CONTEXT TICKER=XLF DIRECTION=sell_put "
            "FOMC_DAYS=12 FOMC_TIER=pass HOLDINGS_RISK=false MACRO_COUNT=0 "
            "CATALYST_VERDICT=proceed"
        )
    }
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, payload)
    # fomc_days_away in gate_payload MUST NOT be changed
    assert updated["fomc_days_away"] == 10
    # The tier=pass is stored in overlay (advisory) but doesn't touch the backend's days
    assert overlay["fomc_tier"] == "pass"


def test_catalyst_confirms_warn_when_tiers_agree():
    """When catalyst tier agrees with backend assessment, overlay records confirmation."""
    gate = make_gate_payload()
    gate["fomc_days_away"] = 16  # backend says 16 days
    payload = {
        "catalyst_context": (
            "CATALYST CONTEXT TICKER=QQQ FOMC_DAYS=16 FOMC_TIER=warn "
            "HOLDINGS_RISK=false MACRO_COUNT=0 CATALYST_VERDICT=caution"
        )
    }
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, payload)
    # No reconcile notes — they agree (diff = 0 ≤ 3)
    assert len(overlay["reconcile_notes"]) == 0
    assert overlay["fomc_tier"] == "warn"


def test_fomc_date_mismatch_surfaces_reconcile_note():
    """Rule 11: disagreement between backend calendar and catalyst is surfaced, never silenced."""
    gate = make_gate_payload()
    gate["fomc_days_away"] = 10
    payload = {
        "catalyst_context": (
            "CATALYST CONTEXT TICKER=QQQ FOMC_DAYS=20 FOMC_TIER=pass "
            "HOLDINGS_RISK=false MACRO_COUNT=0 CATALYST_VERDICT=proceed"
        )
    }
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, payload)
    # diff = |10 - 20| = 10 > 3 → reconcile note generated
    assert len(overlay["reconcile_notes"]) == 1
    assert "mismatch" in overlay["reconcile_notes"][0].lower()
    assert "backend" in overlay["reconcile_notes"][0].lower()


def test_holdings_disagreement_surfaces_note():
    """Rule 11: backend found holdings at risk, catalyst says false → reconcile note."""
    gate = make_gate_payload(underlying=744.0, strike=715.0)
    gate["etf_holdings_at_risk"] = [
        {"company": "NVDA", "etf_pct": 8.0, "earnings_days": 23}
    ]
    payload = {
        "catalyst_context": (
            "CATALYST CONTEXT TICKER=QQQ DIRECTION=sell_put FOMC_DAYS=16 FOMC_TIER=warn "
            "HOLDINGS_RISK=false MACRO_COUNT=1 CATALYST_VERDICT=proceed"
        )
    }
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, payload)
    assert any("Holdings mismatch" in note for note in overlay["reconcile_notes"])
    assert any("NVDA" in note for note in overlay["reconcile_notes"])


def test_no_reconcile_note_when_holdings_agree():
    """When both backend and catalyst report holdings risk, no mismatch note."""
    gate = make_gate_payload()
    gate["etf_holdings_at_risk"] = [{"company": "NVDA", "etf_pct": 8.0, "earnings_days": 23}]
    payload = {
        "catalyst_context": (
            "CATALYST CONTEXT TICKER=QQQ FOMC_DAYS=16 FOMC_TIER=warn "
            "HOLDINGS_RISK=true HOLDINGS_COMPANY=NVDA HOLDINGS_DAYS=23 "
            "MACRO_COUNT=0 CATALYST_VERDICT=caution"
        )
    }
    updated, overlay = apply_catalyst_context_to_gate_payload(gate, payload)
    holdings_notes = [n for n in overlay["reconcile_notes"] if "Holdings" in n]
    assert len(holdings_notes) == 0


# ─── _strategy_catalyst_overlay ───────────────────────────────────────────────

def test_overlay_clears_event_true():
    """Expiry before earnings → clears_event=True."""
    strategy = {"expiry": "2026-06-20", "strike": 715.0}
    today = date(2026, 6, 2)
    r = _strategy_catalyst_overlay(strategy, holdings_days=23, holdings_company="NVDA", today=today)
    # earnings_date = 2026-06-02 + 23d = 2026-06-25
    # expiry = 2026-06-20 < 2026-06-25 → clears
    assert r["clears_event"] is True
    assert "Jun 20" in r["label"]
    assert "Jun 25" in r["label"]
    assert "✅" in r["label"]
    assert "NVDA" in r["label"]


def test_overlay_holds_through_event():
    """Expiry after earnings → clears_event=False with ⚠️ label."""
    strategy = {"expiry": "2026-07-18", "strike": 715.0}
    today = date(2026, 6, 2)
    r = _strategy_catalyst_overlay(strategy, holdings_days=23, holdings_company="NVDA", today=today)
    # earnings_date = 2026-06-25, expiry = 2026-07-18 >= 2026-06-25 → holds through
    assert r["clears_event"] is False
    assert "⚠️" in r["label"]
    assert "THROUGH" in r["label"]


def test_overlay_expiry_same_day_as_earnings():
    """Expiry on same day as earnings → holds through (not before)."""
    strategy = {"expiry": "2026-06-25"}
    today = date(2026, 6, 2)
    r = _strategy_catalyst_overlay(strategy, holdings_days=23, holdings_company="NVDA", today=today)
    assert r["clears_event"] is False


def test_overlay_no_holdings_days_returns_unknown():
    strategy = {"expiry": "2026-06-20"}
    r = _strategy_catalyst_overlay(strategy, holdings_days=None, holdings_company=None)
    assert r["clears_event"] is None
    assert r["label"] is None


def test_overlay_no_expiry_returns_unknown():
    r = _strategy_catalyst_overlay({}, holdings_days=23, holdings_company="NVDA")
    assert r["clears_event"] is None


def test_overlay_earnings_date_field():
    strategy = {"expiry": "2026-06-20"}
    today = date(2026, 6, 2)
    r = _strategy_catalyst_overlay(strategy, holdings_days=23, holdings_company="NVDA", today=today)
    assert r["earnings_date"] == "2026-06-25"
