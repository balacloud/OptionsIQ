from __future__ import annotations

import math
from dataclasses import dataclass


def _gate(
    gate_id: str,
    name: str,
    status: str,
    computed_value: str,
    threshold: str,
    reason: str,
    blocking: bool,
) -> dict:
    return {
        "id": gate_id,
        "name": name,
        "status": status,
        "computed_value": computed_value,
        "threshold": threshold,
        "reason": reason,
        "blocking": blocking,
    }


@dataclass
class GateEngine:
    planned_hold_days: int = 7

    def run(self, direction: str, payload: dict) -> list[dict]:
        if direction in {"buy_call", "sell_call"}:
            return self._run_track_a(payload)
        return self._run_track_b(payload)

    def build_verdict(self, gates: list[dict]) -> dict:
        passed = sum(1 for g in gates if g["status"] == "pass")
        blocking_fail = next((g for g in gates if g["status"] == "fail" and g["blocking"]), None)

        if blocking_fail:
            status = "fail"
            color = "red"
            headline = f"BLOCKED — {blocking_fail['name']} failed"
            blocking_gate = blocking_fail["id"]
        else:
            warns = sum(1 for g in gates if g["status"] == "warn")
            if warns:
                status = "warn"
                color = "amber"
                headline = "CAUTION — Review warning gates"
            else:
                status = "pass"
                color = "green"
                headline = "GO — All blocking gates passed"
            blocking_gate = None

        return {
            "status": status,
            "gates_passed": passed,
            "gates_total": len(gates),
            "blocking_gate": blocking_gate,
            "score_label": f"{passed}/{len(gates)}",
            "headline": headline,
            "color": color,
        }

    def _run_track_a(self, p: dict) -> list[dict]:
        out = []
        ivr = p.get("ivr_pct")
        current_iv = float(p.get("current_iv", 0.0))
        hist_days = int(p.get("history_days", 0))

        if ivr is None or hist_days < 30:
            if current_iv < 20:
                s, r = "pass", "Cheap IV — ideal for buying options"
            elif current_iv <= 35:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            out.append(
                _gate(
                    "ivr",
                    "IV Rank",
                    s,
                    f"IV {current_iv:.2f}% (fallback)",
                    "IV <20 pass, 20-35 warn, >35 fail",
                    r,
                    s == "fail",
                )
            )
        else:
            ivr = float(ivr)
            if ivr < 30:
                s, r = "pass", "Cheap IV — ideal for buying options"
            elif ivr <= 50:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            out.append(_gate("ivr", "IV Rank", s, f"IVR {ivr:.2f}", "<30 pass, 30-50 warn, >50 fail", r, s == "fail"))

        hv_20 = float(p.get("hv_20", 0.0) or 0.0)
        ratio = float(p.get("hv_iv_ratio", 0.0) or 0.0)
        if hv_20 < 15.0:
            if current_iv < 25:
                s, r = "pass", "Low HV regime exception: IV still acceptable"
            else:
                s, r = "fail", "Low HV regime but IV not cheap enough"
            out.append(_gate("hv_iv", "HV/IV Ratio", s, f"HV20 {hv_20:.2f}, IV {current_iv:.2f}", "HV<15 => IV<25 pass", r, s == "fail"))
        else:
            if ratio < 1.20:
                s, r = "pass", "Options fairly priced vs recent realized vol"
            elif ratio <= 1.30:
                s, r = "warn", "Paying average vol risk premium"
            else:
                s, r = "fail", "IV significantly overpriced vs HV"
            out.append(_gate("hv_iv", "HV/IV Ratio", s, f"IV/HV {ratio:.2f}", "<1.20 pass, 1.20-1.30 warn, >1.30 fail", r, s == "fail"))

        premium = float(p.get("premium", 0.0) or 0.0)
        theta = float(p.get("theta_per_day", 0.0) or 0.0)
        burn = abs(theta * self.planned_hold_days) / premium * 100 if premium > 0 else 999.0
        if burn <= 8:
            s, r = "pass", "Theta decay manageable over hold period"
        elif burn <= 12:
            s, r = "warn", "Theta notable — need fast move"
        else:
            s, r = "fail", "Theta will erode gains — use longer DTE"
        out.append(_gate("theta_burn", "Theta Burn", s, f"{burn:.2f}% over {self.planned_hold_days}d", "<=8 pass, 8-12 warn, >12 fail", r, s == "fail"))

        vcp_conf = float(p.get("vcp_confidence", 0.0) or 0.0)
        adx = float(p.get("adx", 0.0) or 0.0)
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if vcp_conf >= 80 and adx >= 40:
            rec_dte = 21
        elif vcp_conf >= 60:
            rec_dte = 45
        else:
            rec_dte = None
        p["recommended_dte"] = rec_dte

        if rec_dte is None or dte < 14:
            s, r = "fail", "Signal confidence too low or expiry too short"
        elif dte >= rec_dte - 5:
            s, r = "pass", "DTE aligned with setup strength"
        else:
            s, r = "warn", "Expiry slightly short for setup quality"
        out.append(_gate("dte", "DTE Selection", s, f"DTE {dte}, rec {rec_dte}", "vcp<60 fail; keep DTE near recommendation", r, s == "fail"))

        earn_days = int(p.get("earnings_days_away", 999) or 999)
        fomc_days = int(p.get("fomc_days_away", 999) or 999)
        if earn_days <= dte:
            s, r = "fail", "Earnings inside expiry window"
            block = True
        elif 5 <= fomc_days <= 10:
            s, r = "warn", "FOMC event near expiry"
            block = False
        else:
            s, r = "pass", "No major event conflict"
            block = False
        out.append(_gate("events", "Event Calendar", s, f"earn {earn_days}d, FOMC {fomc_days}d", "earnings > DTE and FOMC >10d", r, block))

        liq = self._liquidity_gate(p)
        out.append(liq)

        spy_above = bool(p.get("spy_above_200sma", False))
        spy_5d = float(p.get("spy_5day_return", 0.0) or 0.0)
        if spy_above and spy_5d > -0.02:
            s, r = "pass", "Risk-on regime supportive"
        elif spy_above and -0.04 <= spy_5d <= -0.02:
            s, r = "warn", "Market softening; tighten entries"
        else:
            s, r = "fail", "Market regime unsupportive"
        out.append(_gate("market_regime", "Market Regime", s, f"200SMA {spy_above}, 5d {spy_5d:.2%}", "above 200SMA and 5d>-2%", r, s == "fail"))

        pivot = float(p.get("vcp_pivot", 0.0) or 0.0)
        close = float(p.get("last_close", 0.0) or 0.0)
        if close > pivot > 0:
            s, r = "pass", "Price closed above pivot"
        else:
            s, r = "fail", "Pivot not confirmed"
        out.append(_gate("pivot_confirm", "Confirmed Close Above Pivot", s, f"close {close:.2f} vs pivot {pivot:.2f}", "close > pivot required", r, s == "fail"))

        account = float(p.get("account_size", 50000))
        risk_pct = float(p.get("risk_pct", 0.01))
        max_risk = account * risk_pct
        cost = premium * 100
        lots_allowed = math.floor(max_risk / cost) if cost > 0 else 0
        if lots_allowed >= 1:
            s, r = "pass", "Position size fits risk budget"
        elif lots_allowed == 0:
            s, r = "warn", "Option cost is far above 1% risk"
        else:
            s, r = "warn", "Position sizing is borderline for risk budget"
        out.append(_gate("position_size", "Position Sizing", s, f"lots_allowed={lots_allowed}", "lots>=1 pass; cost>1.5x risk warn", r, False))

        return out

    def _run_track_b(self, p: dict) -> list[dict]:
        out = []
        ivr = float(p.get("ivr_pct", 0.0) or 0.0)
        if ivr >= 50:
            s, r = "pass", "Premium expensive — ideal for selling"
        elif ivr >= 30:
            s, r = "warn", "Minimum viable IV for put selling"
        else:
            s, r = "fail", "IV too cheap — insufficient premium"
        out.append(_gate("ivr_seller", "IV Rank (Seller)", s, f"IVR {ivr:.2f}", ">=50 pass, 30-49 warn, <30 fail", r, s == "fail"))

        strike = float(p.get("strike", 0.0) or 0.0)
        s1 = float(p.get("s1_support", 0.0) or 0.0)
        if strike <= s1 * 0.995:
            s, r = "pass", "Strike safely below S1 support"
        elif strike <= s1:
            s, r = "warn", "Strike close to support"
        else:
            s, r = "fail", "Strike above support"
        out.append(_gate("strike_safety", "Strike Safety", s, f"strike {strike:.2f}, S1 {s1:.2f}", "strike <= 0.995*S1 pass", r, s == "fail"))

        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if 14 <= dte <= 21:
            s, r = "pass", "Optimal theta decay window"
        elif 21 < dte <= 35:
            s, r = "warn", "Tradable, but slower decay"
        elif dte > 45 or dte < 7:
            s, r = "fail", "Outside acceptable seller DTE window"
        else:
            s, r = "warn", "Suboptimal DTE window"
        out.append(_gate("dte_seller", "DTE (Seller)", s, f"DTE {dte}", "14-21 pass; 21-35 warn; >45 or <7 fail", r, s == "fail"))

        earn_days = int(p.get("earnings_days_away", 999) or 999)
        fomc_days = int(p.get("fomc_days_away", 999) or 999)
        if earn_days <= dte:
            s, r = "fail", "Earnings inside expiry window"
            block = True
        elif 5 <= fomc_days <= 10:
            s, r = "warn", "FOMC event near expiry"
            block = False
        else:
            s, r = "pass", "No major event conflict"
            block = False
        out.append(_gate("events", "Event Calendar", s, f"earn {earn_days}d, FOMC {fomc_days}d", "earnings > DTE and FOMC >10d", r, block))

        out.append(self._liquidity_gate(p))

        spy_above = bool(p.get("spy_above_200sma", False))
        spy_5d = float(p.get("spy_5day_return", 0.0) or 0.0)
        if spy_above and spy_5d > -0.01:
            s, r = "pass", "Market stable enough for put selling"
        elif -0.02 <= spy_5d <= -0.01:
            s, r = "warn", "Regime weakening for premium selling"
        else:
            s, r = "fail", "Downside regime too risky for put selling"
        out.append(_gate("market_regime_seller", "Market Regime (Seller)", s, f"200SMA {spy_above}, 5d {spy_5d:.2%}", "above 200SMA and 5d>-1%", r, s == "fail"))

        premium = float(p.get("premium", 0.0) or 0.0)
        lots = max(1.0, float(p.get("lots", 1.0) or 1.0))
        account = float(p.get("account_size", 50000))
        max_loss = (strike - premium) * 100
        total = max_loss * lots
        if total <= account * 0.10:
            s, r = "pass", "Max loss within 10% account"
        elif total <= account * 0.20:
            s, r = "warn", "Max loss elevated vs account size"
        else:
            s, r = "fail", "Max loss exceeds 20% account"
        out.append(_gate("max_loss", "Max Loss Defined", s, f"${total:.2f}", "<=10% pass, 10-20% warn, >20% fail", r, s == "fail"))

        return out

    def _liquidity_gate(self, p: dict) -> dict:
        oi = float(p.get("open_interest", 0.0) or 0.0)
        vol = float(p.get("volume", 0.0) or 0.0)
        premium = float(p.get("premium", 0.0) or 0.0)
        strike = float(p.get("strike", 0.0) or 0.0)
        und = float(p.get("underlying_price", 0.0) or 0.0)
        bid = p.get("bid")
        ask = p.get("ask")

        fails = 0
        fails += 0 if oi > 1000 else 1
        fails += 0 if (oi > 0 and vol / oi > 0.10) else 1
        fails += 0 if premium >= 2.00 else 1
        fails += 0 if (und > 0 and abs(strike - und) / und <= 0.05) else 1

        spread_pct = None
        spread_fail_block = False
        if bid is not None and ask is not None:
            bidf, askf = float(bid), float(ask)
            mid = (bidf + askf) / 2 if (bidf + askf) > 0 else 0
            if mid > 0:
                spread_pct = (askf - bidf) / mid * 100
                if spread_pct > 15:
                    spread_fail_block = True

        if spread_pct is not None and spread_pct > 10:
            s, r = "fail", "Spread too wide for efficient execution"
        elif fails >= 2:
            s, r = "fail", "Liquidity checks failed in multiple areas"
        elif spread_pct is not None and 5 <= spread_pct <= 10:
            s, r = "warn", "Spread acceptable but not tight"
        elif fails == 1:
            s, r = "warn", "One liquidity check is marginal"
        else:
            s, r = "pass", "Liquidity acceptable"

        computed = f"OI {oi:.0f}, Vol/OI {(vol / oi) if oi else 0:.2f}, Prem {premium:.2f}"
        if spread_pct is not None:
            computed += f", Spread {spread_pct:.2f}%"

        return _gate(
            "liquidity",
            "Liquidity Proxy",
            s,
            computed,
            "4-part liquidity + spread check",
            r,
            (fails >= 2) or spread_fail_block,
        )
