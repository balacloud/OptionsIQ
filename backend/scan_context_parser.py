"""
Parses the SCAN CONTEXT block emitted by /ibkr-scan skill.
Format: KEY=VALUE on a single line, e.g.:
  TICKER=XLF  IVR=47  IV_HV=1.21  PEMA200=+3.1  PEMA50=+1.2  PC=0.85  DIRECTION=sell_put

Returns a dict consumed by analyze_service.apply_scan_context_to_gate_payload().
"""
from __future__ import annotations
import re


_PATTERNS: dict[str, str] = {
    "ticker":    r"TICKER=([A-Z]+)",
    "ivr":       r"IVR=([\d.]+)",
    "iv_hv":     r"IV_HV=([\d.]+)",
    "pema200":   r"PEMA200=([+-]?[\d.]+)",
    "pema50":    r"PEMA50=([+-]?[\d.]+)",
    "pc_ratio":  r"PC=([\d.]+)",
    "direction": r"DIRECTION=(\w+)",
    "iv_change": r"IV_CHG=([+-]?[\d.]+)",
}

_FLOAT_KEYS = {"ivr", "iv_hv", "pema200", "pema50", "pc_ratio", "iv_change"}
_STR_KEYS   = {"ticker", "direction"}


def parse_scan_context(text: str) -> dict:
    """Return a dict of parsed values from /ibkr-scan SCAN CONTEXT block.
    Unknown/missing keys are omitted — callers must handle absence gracefully.
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
        else:
            result[key] = raw.upper() if key == "ticker" else raw.lower()
    return result


def apply_scan_context_to_gate_payload(
    gate_payload: dict,
    ivr_for_gates: dict,
    ivr_confidence: str,
    payload: dict,
) -> tuple[dict, dict, str]:
    """Merge /ibkr-scan parsed values into gate_payload and ivr_for_gates.

    Returns (updated_gate_payload, updated_ivr_for_gates, updated_ivr_confidence).
    Non-destructive: only overrides keys where scan_context provides real data.
    """
    raw_ctx = payload.get("scan_context", "")
    ctx = parse_scan_context(raw_ctx)
    if not ctx:
        return gate_payload, ivr_for_gates, ivr_confidence

    # Override IVR from IBKR live value (more authoritative than stale iv_history.db)
    if "ivr" in ctx:
        ivr_for_gates = {**ivr_for_gates, "ivr_pct": ctx["ivr"]}
        ivr_confidence = "known"  # IBKR live data is authoritative

    # Override IV/HV ratio if scan context has it
    if "iv_hv" in ctx:
        ivr_for_gates = {**ivr_for_gates, "hv_iv_ratio": ctx["iv_hv"]}

    # Override put/call ratio from IBKR watchlist (fills always-passing gap)
    pc = ctx.get("pc_ratio")
    if pc is not None:
        gate_payload = {**gate_payload, "put_call_volume": pc}

    # Add trend EMA data (new — enables _trend_ema_gate)
    gate_payload = {
        **gate_payload,
        "trend_pema200": ctx.get("pema200"),
        "trend_pema50":  ctx.get("pema50"),
    }

    # Merge updated ivr_for_gates into gate_payload
    gate_payload = {**gate_payload, **ivr_for_gates}

    return gate_payload, ivr_for_gates, ivr_confidence
