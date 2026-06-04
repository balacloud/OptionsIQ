"""
Parses the CHART CONTEXT block emitted by /chartreview skill.
Format: KEY=VALUE on a single line, e.g.:
  CHART CONTEXT  TICKER=QQQ  DIRECTION=sell_put  TREND=UPTREND  S1=710.00  S2=695.00
  R1=748.00  R2=760.00  RSI=58  ATR=8.40  CHART_VERDICT=go

Field omission = level not visible on chart (never emit S3=0 or S3=N/A).
Returns a dict consumed by apply_chart_context_to_response().
"""
from __future__ import annotations
import re


_PATTERNS: dict[str, str] = {
    "ticker":        r"TICKER=([A-Z]+)",
    "direction":     r"DIRECTION=(\w+)",
    "trend":         r"TREND=(\w+)",
    "s1":            r"S1=([\d.]+)",
    "s2":            r"S2=([\d.]+)",
    "s3":            r"S3=([\d.]+)",
    "r1":            r"R1=([\d.]+)",
    "r2":            r"R2=([\d.]+)",
    "rsi":           r"RSI=([\d.]+)",
    "atr":           r"ATR=([\d.]+)",
    "chart_verdict": r"CHART_VERDICT=(\w+)",
}

_FLOAT_KEYS = {"s1", "s2", "s3", "r1", "r2", "rsi", "atr"}
_STR_UPPER  = {"ticker"}
_STR_LOWER  = {"direction", "trend", "chart_verdict"}


def parse_chart_context(text: str) -> dict:
    """Return a dict of parsed values from /chartreview CHART CONTEXT block.
    Missing keys are omitted — absence means the level was not visible on the chart.
    """
    if not text or not isinstance(text, str):
        return {}
    result: dict = {}
    for key, pattern in _PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            continue
        raw = m.group(1)
        if key in _FLOAT_KEYS:
            try:
                result[key] = float(raw)
            except ValueError:
                pass
        elif key in _STR_UPPER:
            result[key] = raw.upper()
        else:
            result[key] = raw.lower()
    return result


def compute_strike_vs_support(
    strike: float,
    levels: dict,
    direction: str,
    underlying: float | None = None,
    atr: float | None = None,
) -> dict:
    """Compute where a strategy's short strike sits relative to chart S/R levels.

    For put-side (sell_put, buy_put): compare strike against S1/S2 support.
    For call-side (sell_call, buy_call): compare strike against R1/R2 resistance.

    Returns:
        zone: string label — "above_s1" / "between_s1_s2" / "below_s1" / "below_s2" /
                              "above_r2" / "above_r1" / "between_r1_r2" / "below_r1" / "no_data"
        label: human-readable string for display, or None when zone="no_data"
        atr_distance: distance from current price to strike in ATR units, or None
    """
    atr_dist = None
    if underlying is not None and atr and atr > 0:
        if direction in ("sell_put", "buy_put"):
            atr_dist = round((underlying - strike) / atr, 1)
        else:
            atr_dist = round((strike - underlying) / atr, 1)

    is_put_side = direction in ("sell_put", "buy_put")

    if is_put_side:
        s1 = levels.get("s1")
        s2 = levels.get("s2")
        if s1 is None:
            return {"zone": "no_data", "label": None, "atr_distance": atr_dist}

        if strike > s1:
            zone = "above_s1"
            label = (
                f"${strike:.0f} short strike sits ABOVE S1 ${s1:.0f} — "
                f"price reaches your strike before hitting support ⚠️"
            )
        elif s2 is not None and strike > s2:
            zone = "between_s1_s2"
            label = (
                f"${strike:.0f} short strike between S1 ${s1:.0f} and S2 ${s2:.0f} — "
                f"S1 must break to threaten you ✅"
            )
        elif s2 is not None:
            zone = "below_s2"
            label = (
                f"${strike:.0f} short strike below S2 ${s2:.0f} — "
                f"two support breaks needed to threaten you ✅✅"
            )
        else:
            zone = "below_s1"
            label = (
                f"${strike:.0f} short strike below S1 ${s1:.0f} — "
                f"support above provides a cushion ✅"
            )
    else:
        r1 = levels.get("r1")
        r2 = levels.get("r2")
        if r1 is None:
            return {"zone": "no_data", "label": None, "atr_distance": atr_dist}

        if r2 is not None and strike >= r2:
            zone = "above_r2"
            label = (
                f"${strike:.0f} short strike above R2 ${r2:.0f} — "
                f"two resistance breaks needed ✅✅"
            )
        elif strike >= r1:
            zone = "above_r1"
            label = (
                f"${strike:.0f} short strike above R1 ${r1:.0f} — "
                f"resistance below your strike ✅"
            )
        elif r2 is not None and strike >= r2 - (r1 * 0):  # catch-all for between
            zone = "between_r1_r2"
            label = (
                f"${strike:.0f} short strike between R1 ${r1:.0f} and R2 ${r2:.0f} — "
                f"R1 must break to threaten you ✅"
            )
        else:
            zone = "below_r1"
            label = (
                f"${strike:.0f} short strike below R1 ${r1:.0f} — "
                f"price only needs to reach your strike without breaking resistance ⚠️"
            )

    return {"zone": zone, "label": label, "atr_distance": atr_dist}


def apply_chart_context_to_response(
    response: dict,
    payload: dict,
    underlying: float,
    direction: str,
) -> dict:
    """Attach chart verdict and per-strategy strike_vs_support to the analyze response.

    Does NOT touch gate_payload — chart context is post-gate advisory only.
    A malformed chart paste cannot change a gate outcome (zero blast radius).
    """
    raw = payload.get("chart_context", "")
    ctx = parse_chart_context(raw)
    if not ctx:
        return response

    # Top-level chart context fields
    response["chart_verdict"] = {
        "verdict":  ctx.get("chart_verdict"),
        "trend":    ctx.get("trend"),
        "rsi":      ctx.get("rsi"),
        "atr":      ctx.get("atr"),
    }
    response["chart_levels"] = {
        k: ctx[k] for k in ("s1", "s2", "s3", "r1", "r2") if k in ctx
    }

    # Per-strategy strike_vs_support
    atr = ctx.get("atr")
    strategies = response.get("strategies") or []
    for s in strategies:
        strike = s.get("strike")
        if strike is not None:
            s["strike_vs_support"] = compute_strike_vs_support(
                float(strike), ctx, direction, underlying, atr
            )

    return response
