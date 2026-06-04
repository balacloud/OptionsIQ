"""
Parses the CATALYST CONTEXT block emitted by /catalyst-check skill.
Format: KEY=VALUE on a single line, e.g.:
  CATALYST CONTEXT  TICKER=QQQ  DIRECTION=sell_put  FOMC_DAYS=16  FOMC_TIER=warn
  HOLDINGS_RISK=true  HOLDINGS_COMPANY=NVDA  HOLDINGS_DAYS=23  MACRO_COUNT=1
  CATALYST_VERDICT=caution

Rule 23: catalyst context is advisory. It provides reconciliation context for backend
gates but CANNOT override structural hard blocks (FOMC for XLF/TQQQ/XLRE within 14d).
"""
from __future__ import annotations
import re
from datetime import date, timedelta

from constants import FOMC_BLOCK_TICKERS, FOMC_BLOCK_DAYS


_PATTERNS: dict[str, str] = {
    "ticker":           r"TICKER=([A-Z]+)",
    "direction":        r"DIRECTION=(\w+)",
    "fomc_days":        r"FOMC_DAYS=(\d+)",
    "fomc_tier":        r"FOMC_TIER=(\w+)",
    "holdings_risk":    r"HOLDINGS_RISK=(true|false)",
    "holdings_company": r"HOLDINGS_COMPANY=([A-Z]+)",
    "holdings_days":    r"HOLDINGS_DAYS=(\d+)",
    "macro_count":      r"MACRO_COUNT=(\d+)",
    "catalyst_verdict": r"CATALYST_VERDICT=(\w+)",
}

_INT_KEYS  = {"fomc_days", "holdings_days", "macro_count"}
_BOOL_KEYS = {"holdings_risk"}
_STR_UPPER = {"ticker", "holdings_company"}
_STR_LOWER = {"direction", "fomc_tier", "catalyst_verdict"}


def parse_catalyst_context(text: str) -> dict:
    """Return a dict of parsed values from /catalyst-check CATALYST CONTEXT block.
    Missing keys are omitted. Absent HOLDINGS_COMPANY/HOLDINGS_DAYS is normal
    when HOLDINGS_RISK=false.
    """
    if not text or not isinstance(text, str):
        return {}
    result: dict = {}
    for key, pattern in _PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            continue
        raw = m.group(1)
        if key in _INT_KEYS:
            try:
                result[key] = int(raw)
            except ValueError:
                pass
        elif key in _BOOL_KEYS:
            result[key] = raw.lower() == "true"
        elif key in _STR_UPPER:
            result[key] = raw.upper()
        else:
            result[key] = raw.lower()
    return result


def apply_catalyst_context_to_gate_payload(
    gate_payload: dict,
    payload: dict,
) -> tuple[dict, dict]:
    """Merge /catalyst-check parsed values into gate_payload as advisory overlay.

    Returns (updated_gate_payload, catalyst_overlay_dict).

    Rule 23 enforcement:
    - Backend fomc_days_away is NOT overridden — gate_engine uses it for hard blocks.
    - catalyst_override is stored as advisory: gate_engine appends confirmation/warnings
      to reason strings but does NOT change blocking status based on catalyst tier alone.
    - Disagreement between backend calendar and catalyst is surfaced as a reconcile note.
    """
    raw = payload.get("catalyst_context", "")
    ctx = parse_catalyst_context(raw)
    if not ctx:
        return gate_payload, {}

    ticker = ctx.get("ticker", gate_payload.get("ticker", "")).upper()
    reconcile_notes: list[str] = []

    # FOMC reconciliation — detect calendar disagreement
    fomc_days_backend  = gate_payload.get("fomc_days_away")
    fomc_days_catalyst = ctx.get("fomc_days")
    fomc_tier          = ctx.get("fomc_tier", "pass")

    if fomc_days_backend is not None and fomc_days_catalyst is not None:
        if abs(fomc_days_backend - fomc_days_catalyst) > 3:
            reconcile_notes.append(
                f"FOMC date mismatch: backend={fomc_days_backend}d vs "
                f"catalyst={fomc_days_catalyst}d — backend calendar is authoritative "
                f"for hard blocks; verify constants.py FOMC_DATES"
            )

    # Holdings reconciliation — flag when catalyst and backend disagree
    at_risk = gate_payload.get("etf_holdings_at_risk", [])
    holdings_risk_catalyst = ctx.get("holdings_risk", False)
    if at_risk and not holdings_risk_catalyst:
        n = len(at_risk)
        companies = ", ".join(h.get("company", "?") for h in at_risk[:2])
        reconcile_notes.append(
            f"Holdings mismatch: backend found {n} at-risk holding(s) ({companies}) "
            f"but CATALYST CONTEXT reports HOLDINGS_RISK=false — "
            f"verify earnings calendar before trading"
        )

    catalyst_override: dict = {
        "fomc_tier":          fomc_tier,
        "catalyst_verdict":   ctx.get("catalyst_verdict", "proceed"),
        "fomc_days_catalyst": fomc_days_catalyst,
        "holdings_risk":      ctx.get("holdings_risk", False),
        "holdings_company":   ctx.get("holdings_company"),
        "holdings_days":      ctx.get("holdings_days"),
        "macro_count":        ctx.get("macro_count", 0),
        "reconcile_notes":    reconcile_notes,
    }

    # Merge advisory overlay — backend fomc_days_away is NOT touched (Rule 23)
    updated = {**gate_payload, "catalyst_override": catalyst_override}
    return updated, catalyst_override


def _strategy_catalyst_overlay(
    strategy: dict,
    holdings_days: int | None,
    holdings_company: str | None,
    today: date | None = None,
) -> dict:
    """Check whether this strategy's expiry date clears the upcoming earnings event.

    This is the highest-value feature of catalyst context: per-strategy timing check.
    'Jun 20 expiry exits before NVDA Jun 25 ✅' vs 'Jul 18 holds THROUGH NVDA Jun 25 ⚠️'

    Returns:
        clears_event: True if expiry is before earnings, False if it holds through, None if unknown
        label: human-readable string for UI display
        earnings_date: ISO date string of the computed earnings date
    """
    if today is None:
        today = date.today()

    if holdings_days is None or not strategy.get("expiry"):
        return {"clears_event": None, "label": None, "earnings_date": None}

    try:
        expiry_date = date.fromisoformat(str(strategy["expiry"]))
    except (ValueError, TypeError):
        return {"clears_event": None, "label": None, "earnings_date": None}

    earnings_date = today + timedelta(days=holdings_days)
    clears = expiry_date < earnings_date
    company = holdings_company or "earnings"

    if clears:
        label = (
            f"{expiry_date.strftime('%b %d')} expiry exits before "
            f"{company} {earnings_date.strftime('%b %d')} ✅"
        )
    else:
        label = (
            f"{expiry_date.strftime('%b %d')} expiry holds THROUGH "
            f"{company} {earnings_date.strftime('%b %d')} ⚠️"
        )

    return {
        "clears_event": clears,
        "label": label,
        "earnings_date": earnings_date.isoformat(),
    }
