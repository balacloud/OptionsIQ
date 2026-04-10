from __future__ import annotations

import math
from dataclasses import dataclass

from constants import (
    ADX_HIGH_THRESH,
    DEFAULT_ACCOUNT_SIZE,
    DEFAULT_MIN_DTE,
    DEFAULT_RISK_PCT,
    DTE_GATE_TOLERANCE,
    DTE_REC_HIGH_SIGNAL,
    DTE_REC_MED_SIGNAL,
    ETF_DTE_HIGH_IVR,
    ETF_DTE_LOW_IVR,
    HV_IV_PASS_RATIO,
    HV_IV_WARN_RATIO,
    HV_LOW_REGIME_PCT,
    IV_ABS_BUYER_PASS_PCT,
    IV_ABS_BUYER_WARN_PCT,
    IV_ABS_LOW_HV_PASS_PCT,
    IVR_BUYER_PASS_PCT,
    IVR_BUYER_WARN_PCT,
    IVR_SELLER_MIN_PCT,
    IVR_SELLER_PASS_PCT,
    MAX_LOSS_FAIL_PCT,
    MAX_LOSS_WARN_PCT,
    MIN_OPEN_INTEREST,
    MIN_PREMIUM_DOLLAR,
    MIN_VOLUME_OI_RATIO,
    SELL_CALL_OTM_PASS_PCT,
    SPY_BULL_5D_FAIL,
    SPY_BULL_5D_WARN,
    SPY_BUYPUT_5D_PASS,
    SPY_BUYPUT_5D_WARN,
    SPY_SELLCALL_5D_PASS,
    SPY_SELLCALL_5D_WARN,
    SPY_SELLPUT_5D_FAIL,
    SPY_SELLPUT_5D_WARN,
    SPREAD_BLOCK_PCT,
    SPREAD_FAIL_PCT,
    SPREAD_WARN_PCT,
    STRIKE_NEARNESS_PCT,
    STRIKE_SAFETY_RATIO,
    THETA_BURN_PASS_PCT,
    THETA_BURN_WARN_PCT,
    VCP_HIGH_CONF_PCT,
    VCP_MED_CONF_PCT,
)


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

    def run(self, direction: str, payload: dict, etf_mode: bool = False) -> list[dict]:
        # ETF mode: use IVR/HV/theta/liquidity/regime tracks — no VCP/ADX/pivot/breakdown.
        # Stock mode: full swing-pattern tracks (VCP, ADX, pivot_confirm, breakdown_confirm).
        if etf_mode:
            if direction == "buy_call":
                return self._run_etf_buy_call(payload)
            if direction == "sell_call":
                return self._run_sell_call(payload)  # already ETF-clean
            if direction == "buy_put":
                return self._run_etf_buy_put(payload)
            return self._run_etf_sell_put(payload)   # sell_put ETF track
        # Stock mode (legacy — all 4 original tracks)
        if direction == "buy_call":
            return self._run_track_a(payload)
        if direction == "sell_call":
            return self._run_sell_call(payload)
        if direction == "buy_put":
            return self._run_buy_put(payload)
        return self._run_track_b(payload)  # sell_put

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
            if current_iv < IV_ABS_BUYER_PASS_PCT:
                s, r = "pass", "Cheap IV — ideal for buying options"
            elif current_iv <= IV_ABS_BUYER_WARN_PCT:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            out.append(
                _gate(
                    "ivr",
                    "IV Rank",
                    s,
                    f"IV {current_iv:.2f}% (fallback)",
                    f"IV <{IV_ABS_BUYER_PASS_PCT} pass, {IV_ABS_BUYER_PASS_PCT}-{IV_ABS_BUYER_WARN_PCT} warn, >{IV_ABS_BUYER_WARN_PCT} fail",
                    r,
                    s == "fail",
                )
            )
        else:
            ivr = float(ivr)
            if ivr < IVR_BUYER_PASS_PCT:
                s, r = "pass", "Cheap IV — ideal for buying options"
            elif ivr <= IVR_BUYER_WARN_PCT:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            out.append(_gate("ivr", "IV Rank", s, f"IVR {ivr:.2f}", f"<{IVR_BUYER_PASS_PCT} pass, {IVR_BUYER_PASS_PCT}-{IVR_BUYER_WARN_PCT} warn, >{IVR_BUYER_WARN_PCT} fail", r, s == "fail"))

        hv_20 = float(p.get("hv_20", 0.0) or 0.0)
        ratio = float(p.get("hv_iv_ratio", 0.0) or 0.0)
        if hv_20 < HV_LOW_REGIME_PCT:
            if current_iv < IV_ABS_LOW_HV_PASS_PCT:
                s, r = "pass", "Low HV regime exception: IV still acceptable"
            else:
                s, r = "fail", "Low HV regime but IV not cheap enough"
            out.append(_gate("hv_iv", "HV/IV Ratio", s, f"HV20 {hv_20:.2f}, IV {current_iv:.2f}", f"HV<{HV_LOW_REGIME_PCT} => IV<{IV_ABS_LOW_HV_PASS_PCT} pass", r, s == "fail"))
        else:
            if ratio < HV_IV_PASS_RATIO:
                s, r = "pass", "Options fairly priced vs recent realized vol"
            elif ratio <= HV_IV_WARN_RATIO:
                s, r = "warn", "Paying average vol risk premium"
            else:
                s, r = "fail", "IV significantly overpriced vs HV"
            out.append(_gate("hv_iv", "HV/IV Ratio", s, f"IV/HV {ratio:.2f}", f"<{HV_IV_PASS_RATIO} pass, {HV_IV_PASS_RATIO}-{HV_IV_WARN_RATIO} warn, >{HV_IV_WARN_RATIO} fail", r, s == "fail"))

        premium = float(p.get("premium", 0.0) or 0.0)
        theta = float(p.get("theta_per_day", 0.0) or 0.0)
        burn = abs(theta * self.planned_hold_days) / premium * 100 if premium > 0 else 999.0
        if burn <= THETA_BURN_PASS_PCT:
            s, r = "pass", "Theta decay manageable over hold period"
        elif burn <= THETA_BURN_WARN_PCT:
            s, r = "warn", "Theta notable — need fast move"
        else:
            s, r = "fail", "Theta will erode gains — use longer DTE"
        out.append(_gate("theta_burn", "Theta Burn", s, f"{burn:.2f}% over {self.planned_hold_days}d", f"<={THETA_BURN_PASS_PCT} pass, {THETA_BURN_PASS_PCT}-{THETA_BURN_WARN_PCT} warn, >{THETA_BURN_WARN_PCT} fail", r, s == "fail"))

        vcp_conf = float(p.get("vcp_confidence", 0.0) or 0.0)
        adx = float(p.get("adx", 0.0) or 0.0)
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if vcp_conf >= VCP_HIGH_CONF_PCT and adx >= ADX_HIGH_THRESH:
            rec_dte = DTE_REC_HIGH_SIGNAL
        elif vcp_conf >= VCP_MED_CONF_PCT:
            rec_dte = DTE_REC_MED_SIGNAL
        else:
            rec_dte = None
        p["recommended_dte"] = rec_dte

        if rec_dte is None or dte < DEFAULT_MIN_DTE:
            s, r = "fail", "Signal confidence too low or expiry too short"
        elif dte >= rec_dte - DTE_GATE_TOLERANCE:
            s, r = "pass", "DTE aligned with setup strength"
        else:
            s, r = "warn", "Expiry slightly short for setup quality"
        out.append(_gate("dte", "DTE Selection", s, f"DTE {dte}, rec {rec_dte}", f"vcp<{VCP_MED_CONF_PCT} fail; keep DTE near recommendation", r, s == "fail"))

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

        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            s, r = "warn", "SPY regime unavailable — verify STA connection"
            out.append(_gate("market_regime", "Market Regime", s, "SPY regime unavailable", "above 200SMA required", r, False))
        else:
            spy_above = bool(p.get("spy_above_200sma", False))
            spy_5d = float(spy_5d_raw)
            if spy_above and spy_5d > SPY_BULL_5D_WARN:
                s, r = "pass", "Risk-on regime supportive"
            elif spy_above and SPY_BULL_5D_FAIL <= spy_5d <= SPY_BULL_5D_WARN:
                s, r = "warn", "Market softening; tighten entries"
            else:
                s, r = "fail", "Market regime unsupportive"
            out.append(_gate("market_regime", "Market Regime", s, f"200SMA {spy_above}, 5d {spy_5d:.2%}", f"above 200SMA and 5d>{SPY_BULL_5D_WARN:.0%}", r, s == "fail"))

        pivot = float(p.get("vcp_pivot", 0.0) or 0.0)
        close = float(p.get("last_close", 0.0) or 0.0)
        if close > pivot > 0:
            s, r = "pass", "Price closed above pivot"
        else:
            s, r = "fail", "Pivot not confirmed"
        out.append(_gate("pivot_confirm", "Confirmed Close Above Pivot", s, f"close {close:.2f} vs pivot {pivot:.2f}", "close > pivot required", r, s == "fail"))

        account = float(p.get("account_size", DEFAULT_ACCOUNT_SIZE))
        risk_pct = float(p.get("risk_pct", DEFAULT_RISK_PCT))
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
        if ivr >= IVR_SELLER_PASS_PCT:
            s, r = "pass", "Premium expensive — ideal for selling"
        elif ivr >= IVR_SELLER_MIN_PCT:
            s, r = "warn", "Minimum viable IV for put selling"
        else:
            s, r = "fail", "IV too cheap — insufficient premium"
        out.append(_gate("ivr_seller", "IV Rank (Seller)", s, f"IVR {ivr:.2f}", f">={IVR_SELLER_PASS_PCT} pass, {IVR_SELLER_MIN_PCT}-{IVR_SELLER_PASS_PCT-1} warn, <{IVR_SELLER_MIN_PCT} fail", r, s == "fail"))

        strike = float(p.get("strike", 0.0) or 0.0)
        s1 = float(p.get("s1_support", 0.0) or 0.0)
        if strike <= s1 * STRIKE_SAFETY_RATIO:
            s, r = "pass", "Strike safely below S1 support"
        elif strike <= s1:
            s, r = "warn", "Strike close to support"
        else:
            s, r = "fail", "Strike above support"
        out.append(_gate("strike_safety", "Strike Safety", s, f"strike {strike:.2f}, S1 {s1:.2f}", f"strike <= {STRIKE_SAFETY_RATIO}*S1 pass", r, s == "fail"))

        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if DEFAULT_MIN_DTE <= dte <= DTE_REC_HIGH_SIGNAL:
            s, r = "pass", "Optimal theta decay window"
        elif DTE_REC_HIGH_SIGNAL < dte <= 35:
            s, r = "warn", "Tradable, but slower decay"
        elif dte > DTE_REC_MED_SIGNAL or dte < 7:
            s, r = "fail", "Outside acceptable seller DTE window"
        else:
            s, r = "warn", "Suboptimal DTE window"
        out.append(_gate("dte_seller", "DTE (Seller)", s, f"DTE {dte}", f"{DEFAULT_MIN_DTE}-{DTE_REC_HIGH_SIGNAL} pass; {DTE_REC_HIGH_SIGNAL}-35 warn; >{DTE_REC_MED_SIGNAL} or <7 fail", r, s == "fail"))

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

        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            s, r = "warn", "SPY regime unavailable — verify STA connection"
            out.append(_gate("market_regime_seller", "Market Regime (Seller)", s, "SPY regime unavailable", "above 200SMA and stable 5d required", r, False))
        else:
            spy_above = bool(p.get("spy_above_200sma", False))
            spy_5d = float(spy_5d_raw)
            if spy_above and spy_5d > SPY_SELLPUT_5D_WARN:
                s, r = "pass", "Market stable enough for put selling"
            elif SPY_SELLPUT_5D_FAIL <= spy_5d <= SPY_SELLPUT_5D_WARN:
                s, r = "warn", "Regime weakening for premium selling"
            else:
                s, r = "fail", "Downside regime too risky for put selling"
            out.append(_gate("market_regime_seller", "Market Regime (Seller)", s, f"200SMA {spy_above}, 5d {spy_5d:.2%}", f"above 200SMA and 5d>{SPY_SELLPUT_5D_WARN:.0%}", r, s == "fail"))

        premium = float(p.get("premium", 0.0) or 0.0)
        lots = max(1.0, float(p.get("lots", 1.0) or 1.0))
        account = float(p.get("account_size", DEFAULT_ACCOUNT_SIZE))
        max_loss = (strike - premium) * 100
        total = max_loss * lots
        if total <= account * MAX_LOSS_WARN_PCT:
            s, r = "pass", "Max loss within 10% account"
        elif total <= account * MAX_LOSS_FAIL_PCT:
            s, r = "warn", "Max loss elevated vs account size"
        else:
            s, r = "fail", "Max loss exceeds 20% account"
        out.append(_gate("max_loss", "Max Loss Defined", s, f"${total:.2f}", f"<={MAX_LOSS_WARN_PCT:.0%} pass, {MAX_LOSS_WARN_PCT:.0%}-{MAX_LOSS_FAIL_PCT:.0%} warn, >{MAX_LOSS_FAIL_PCT:.0%} fail", r, s == "fail"))

        return out

    def _run_sell_call(self, p: dict) -> list[dict]:
        """Gate track for sell_call: premium seller, wants HIGH IV, OTM strike, flat/bearish regime."""
        out = []

        # Gate 1: IVR — sellers want HIGH IV to maximize premium collected
        ivr = float(p.get("ivr_pct", 0.0) or 0.0)
        if ivr >= IVR_SELLER_PASS_PCT:
            s, r = "pass", "Premium expensive — ideal for selling calls"
        elif ivr >= IVR_SELLER_MIN_PCT:
            s, r = "warn", "Minimum viable IV for call selling"
        else:
            s, r = "fail", "IV too cheap — insufficient premium for call selling"
        out.append(_gate("ivr_seller", "IV Rank (Seller)", s, f"IVR {ivr:.2f}", f">={IVR_SELLER_PASS_PCT} pass, {IVR_SELLER_MIN_PCT}-{IVR_SELLER_PASS_PCT-1} warn, <{IVR_SELLER_MIN_PCT} fail", r, s == "fail"))

        # Gate 2: Strike OTM check — sell_call strike must be above current price
        strike = float(p.get("strike", 0.0) or 0.0)
        und = float(p.get("underlying_price", 0.0) or 0.0)
        if und > 0:
            otm_pct = (strike - und) / und * 100
            if otm_pct >= SELL_CALL_OTM_PASS_PCT:
                s, r = "pass", f"Strike {otm_pct:.1f}% OTM — safe for call selling"
            elif otm_pct >= 0:
                s, r = "warn", "Strike near ATM — elevated assignment risk"
            else:
                s, r = "fail", "Strike is ITM — call selling into immediate loss"
        else:
            s, r = "warn", "Unable to verify strike vs underlying"
        out.append(_gate("strike_otm", "Strike OTM Check", s, f"strike {strike:.2f}, und {und:.2f}", f">={SELL_CALL_OTM_PASS_PCT}% OTM pass; ATM warn; ITM fail", r, s == "fail"))

        # Gate 3: DTE seller window
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if DEFAULT_MIN_DTE <= dte <= DTE_REC_HIGH_SIGNAL:
            s, r = "pass", "Optimal theta decay window"
        elif DTE_REC_HIGH_SIGNAL < dte <= DTE_REC_MED_SIGNAL:
            s, r = "warn", "Tradable, but slower decay"
        elif dte > 60 or dte < 7:
            s, r = "fail", "Outside acceptable seller DTE window"
        else:
            s, r = "warn", "Suboptimal DTE window"
        out.append(_gate("dte_seller", "DTE (Seller)", s, f"DTE {dte}", f"{DEFAULT_MIN_DTE}-{DTE_REC_HIGH_SIGNAL} pass; {DTE_REC_HIGH_SIGNAL}-{DTE_REC_MED_SIGNAL} warn; >60 or <7 fail", r, s == "fail"))

        # Gate 4: Events
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

        # Gate 5: Liquidity
        out.append(self._liquidity_gate(p))

        # Gate 6: Market regime — call sellers want flat or bearish market
        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            s, r = "warn", "SPY regime unavailable — verify STA connection"
            out.append(_gate("market_regime_seller", "Market Regime (Seller)", s, "SPY regime unavailable", "flat/weak market required", r, False))
        else:
            spy_above = bool(p.get("spy_above_200sma", False))
            spy_5d = float(spy_5d_raw)
            if not spy_above or spy_5d < SPY_SELLCALL_5D_PASS:
                s, r = "pass", "Market flat/weak — favorable for call selling"
            elif spy_above and spy_5d < SPY_SELLCALL_5D_WARN:
                s, r = "warn", "Market bullish but contained — monitor closely"
            else:
                s, r = "fail", "Strong bull market — elevated call assignment risk"
            out.append(_gate("market_regime_seller", "Market Regime (Seller)", s, f"200SMA {spy_above}, 5d {spy_5d:.2%}", f"flat/weak (5d<{SPY_SELLCALL_5D_PASS:.0%}) pass; strong bull (5d>={SPY_SELLCALL_5D_WARN:.0%}) fail", r, s == "fail"))

        # Gate 7: Risk defined — spread (defined max loss) is better than naked
        max_gain = float(p.get("max_gain_per_lot", -1.0) or -1.0)
        premium = float(p.get("premium", 0.0) or 0.0)
        if max_gain > 0:
            s, r = "pass", f"Defined risk spread — max gain ${max_gain:.2f}"
        elif premium > 0:
            s, r = "warn", "Naked call — uncapped upside risk; confirm sizing"
        else:
            s, r = "warn", "Unable to verify risk definition"
        out.append(_gate("risk_defined", "Risk Defined", s, f"max_gain_per_lot={max_gain:.2f}", "spread pass; naked warn", r, False))

        return out

    def _run_buy_put(self, p: dict) -> list[dict]:
        """Gate track for buy_put: bearish buyer, wants LOW IV, breakdown confirmed, bearish regime."""
        out = []
        current_iv = float(p.get("current_iv", 0.0))
        hist_days = int(p.get("history_days", 0))

        # Gate 1: IVR — buyers want LOW IV (same logic as buy_call, mirrored for puts)
        ivr = p.get("ivr_pct")
        if ivr is None or hist_days < 30:
            if current_iv < IV_ABS_BUYER_PASS_PCT:
                s, r = "pass", "Cheap IV — ideal for buying puts"
            elif current_iv <= IV_ABS_BUYER_WARN_PCT:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            out.append(_gate("ivr", "IV Rank", s, f"IV {current_iv:.2f}% (fallback)", f"IV <{IV_ABS_BUYER_PASS_PCT} pass, {IV_ABS_BUYER_PASS_PCT}-{IV_ABS_BUYER_WARN_PCT} warn, >{IV_ABS_BUYER_WARN_PCT} fail", r, s == "fail"))
        else:
            ivr = float(ivr)
            if ivr < IVR_BUYER_PASS_PCT:
                s, r = "pass", "Cheap IV — ideal for buying puts"
            elif ivr <= IVR_BUYER_WARN_PCT:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            out.append(_gate("ivr", "IV Rank", s, f"IVR {ivr:.2f}", f"<{IVR_BUYER_PASS_PCT} pass, {IVR_BUYER_PASS_PCT}-{IVR_BUYER_WARN_PCT} warn, >{IVR_BUYER_WARN_PCT} fail", r, s == "fail"))

        # Gate 2: HV/IV Ratio (same as buy_call)
        hv_20 = float(p.get("hv_20", 0.0) or 0.0)
        ratio = float(p.get("hv_iv_ratio", 0.0) or 0.0)
        if hv_20 < HV_LOW_REGIME_PCT:
            if current_iv < IV_ABS_LOW_HV_PASS_PCT:
                s, r = "pass", "Low HV regime exception: IV still acceptable"
            else:
                s, r = "fail", "Low HV regime but IV not cheap enough"
            out.append(_gate("hv_iv", "HV/IV Ratio", s, f"HV20 {hv_20:.2f}, IV {current_iv:.2f}", f"HV<{HV_LOW_REGIME_PCT} => IV<{IV_ABS_LOW_HV_PASS_PCT} pass", r, s == "fail"))
        else:
            if ratio < HV_IV_PASS_RATIO:
                s, r = "pass", "Options fairly priced vs recent realized vol"
            elif ratio <= HV_IV_WARN_RATIO:
                s, r = "warn", "Paying average vol risk premium"
            else:
                s, r = "fail", "IV significantly overpriced vs HV"
            out.append(_gate("hv_iv", "HV/IV Ratio", s, f"IV/HV {ratio:.2f}", f"<{HV_IV_PASS_RATIO} pass, {HV_IV_PASS_RATIO}-{HV_IV_WARN_RATIO} warn, >{HV_IV_WARN_RATIO} fail", r, s == "fail"))

        # Gate 3: Theta Burn (same as buy_call)
        premium = float(p.get("premium", 0.0) or 0.0)
        theta = float(p.get("theta_per_day", 0.0) or 0.0)
        burn = abs(theta * self.planned_hold_days) / premium * 100 if premium > 0 else 999.0
        if burn <= THETA_BURN_PASS_PCT:
            s, r = "pass", "Theta decay manageable over hold period"
        elif burn <= THETA_BURN_WARN_PCT:
            s, r = "warn", "Theta notable — need fast move"
        else:
            s, r = "fail", "Theta will erode gains — use longer DTE"
        out.append(_gate("theta_burn", "Theta Burn", s, f"{burn:.2f}% over {self.planned_hold_days}d", f"<={THETA_BURN_PASS_PCT} pass, {THETA_BURN_PASS_PCT}-{THETA_BURN_WARN_PCT} warn, >{THETA_BURN_WARN_PCT} fail", r, s == "fail"))

        # Gate 4: DTE buyer (same logic as buy_call)
        vcp_conf = float(p.get("vcp_confidence", 0.0) or 0.0)
        adx = float(p.get("adx", 0.0) or 0.0)
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if vcp_conf >= VCP_HIGH_CONF_PCT and adx >= ADX_HIGH_THRESH:
            rec_dte = DTE_REC_HIGH_SIGNAL
        elif vcp_conf >= VCP_MED_CONF_PCT:
            rec_dte = DTE_REC_MED_SIGNAL
        else:
            rec_dte = None
        p["recommended_dte"] = rec_dte
        if rec_dte is None or dte < DEFAULT_MIN_DTE:
            s, r = "fail", "Signal confidence too low or expiry too short"
        elif dte >= rec_dte - DTE_GATE_TOLERANCE:
            s, r = "pass", "DTE aligned with setup strength"
        else:
            s, r = "warn", "Expiry slightly short for setup quality"
        out.append(_gate("dte", "DTE Selection", s, f"DTE {dte}, rec {rec_dte}", f"vcp<{VCP_MED_CONF_PCT} fail; keep DTE near recommendation", r, s == "fail"))

        # Gate 5: Events
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

        # Gate 6: Liquidity
        out.append(self._liquidity_gate(p))

        # Gate 7: Market Regime — bearish (want SPY weak for put buying)
        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            s, r = "warn", "SPY regime unavailable — verify STA connection"
            out.append(_gate("market_regime", "Market Regime", s, "SPY regime unavailable", "below 200SMA and weak 5d required", r, False))
        else:
            spy_above = bool(p.get("spy_above_200sma", False))
            spy_5d = float(spy_5d_raw)
            if not spy_above and spy_5d < SPY_BUYPUT_5D_PASS:
                s, r = "pass", "Bearish regime — supportive for put buying"
            elif spy_5d < SPY_BUYPUT_5D_WARN:
                s, r = "warn", "Market weakening — reasonable for defensive puts"
            else:
                s, r = "fail", "Market regime not supportive for put buying"
            out.append(_gate("market_regime", "Market Regime", s, f"200SMA {spy_above}, 5d {spy_5d:.2%}", f"below 200SMA and 5d<{SPY_BUYPUT_5D_PASS:.0%} pass", r, s == "fail"))

        # Gate 8: Breakdown Confirm — bearish equivalent of pivot_confirm
        # For puts: want price to have broken below S1 support
        close = float(p.get("last_close", 0.0) or 0.0)
        s1 = float(p.get("s1_support", 0.0) or 0.0)
        if s1 > 0 and close < s1:
            s, r = "pass", "Price closed below S1 — breakdown confirmed"
        elif s1 > 0 and close <= s1 * 1.02:
            s, r = "warn", "Price near S1 — monitoring breakdown"
        else:
            s, r = "fail", "Price above support — breakdown not confirmed"
        out.append(_gate("breakdown_confirm", "Confirmed Close Below Support", s, f"close {close:.2f} vs S1 {s1:.2f}", "close < S1 required", r, s == "fail"))

        # Gate 9: Position Size (same as buy_call)
        account = float(p.get("account_size", DEFAULT_ACCOUNT_SIZE))
        risk_pct = float(p.get("risk_pct", DEFAULT_RISK_PCT))
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

    def _liquidity_gate(self, p: dict) -> dict:
        oi = float(p.get("open_interest", 0.0) or 0.0)
        vol = float(p.get("volume", 0.0) or 0.0)
        premium = float(p.get("premium", 0.0) or 0.0)
        strike = float(p.get("strike", 0.0) or 0.0)
        und = float(p.get("underlying_price", 0.0) or 0.0)
        bid = p.get("bid")
        ask = p.get("ask")

        # OI data availability check (Rule 11: missing data ≠ fail).
        # When OI=0 but Vol>0, the contract IS tradeable — OI just wasn't delivered
        # by the data provider (IBKR tick type 101 limitation confirmed Day 12).
        # When OI=0 AND Vol=0, both fields are absent — still don't hard-block,
        # but warn and skip OI-related fail counts.
        oi_data_available = oi > 0
        vol_data_available = vol > 0

        fails = 0
        oi_note = ""
        if oi_data_available:
            fails += 0 if oi > MIN_OPEN_INTEREST else 1
            fails += 0 if vol / oi > MIN_VOLUME_OI_RATIO else 1
        else:
            # OI unavailable — skip OI checks, note it in output
            oi_note = " [OI unavailable]"

        fails += 0 if premium >= MIN_PREMIUM_DOLLAR else 1
        fails += 0 if (und > 0 and abs(strike - und) / und <= STRIKE_NEARNESS_PCT) else 1

        spread_pct = None
        spread_fail_block = False
        if bid is not None and ask is not None:
            bidf, askf = float(bid), float(ask)
            mid = (bidf + askf) / 2 if (bidf + askf) > 0 else 0
            if mid > 0:
                spread_pct = (askf - bidf) / mid * 100
                if spread_pct > SPREAD_BLOCK_PCT:
                    spread_fail_block = True

        if spread_pct is not None and spread_pct > SPREAD_FAIL_PCT:
            s, r = "fail", "Spread too wide for efficient execution"
        elif fails >= 2:
            s, r = "fail", "Liquidity checks failed in multiple areas"
        elif not oi_data_available and not vol_data_available:
            s, r = "warn", "OI/Volume data unavailable — verify liquidity manually before trading"
        elif not oi_data_available:
            # Volume present but OI missing — treat as warn, not block
            if fails >= 1:
                s, r = "warn", "OI data unavailable and one other liquidity check marginal"
            else:
                s, r = "warn", "OI data unavailable — verify open interest before trading"
        elif spread_pct is not None and SPREAD_WARN_PCT <= spread_pct <= SPREAD_FAIL_PCT:
            s, r = "warn", "Spread acceptable but not tight"
        elif fails == 1:
            s, r = "warn", "One liquidity check is marginal"
        else:
            s, r = "pass", "Liquidity acceptable"

        vol_oi_str = f"{vol / oi:.2f}" if oi_data_available else "N/A"
        computed = f"OI {oi:.0f}{oi_note}, Vol/OI {vol_oi_str}, Prem {premium:.2f}"
        if spread_pct is not None:
            computed += f", Spread {spread_pct:.2f}%"

        return _gate(
            "liquidity",
            "Liquidity Proxy",
            s,
            computed,
            "4-part liquidity + spread check",
            r,
            spread_fail_block,  # only block on wide spread; missing OI is a warn
        )

    # -------------------------------------------------------------------------
    # ETF Gate Tracks (no VCP / ADX / pivot / breakdown — pure quant signals)
    # -------------------------------------------------------------------------

    def _etf_ivr_buyer_gate(self, p: dict) -> dict:
        """Shared IVR gate for ETF buyers (buy_call + buy_put): wants LOW IV."""
        ivr = p.get("ivr_pct")
        current_iv = float(p.get("current_iv", 0.0))
        hist_days = int(p.get("history_days", 0))
        if ivr is None or hist_days < 30:
            iv = current_iv
            if iv < IV_ABS_BUYER_PASS_PCT:
                s, r = "pass", "IV cheap — good entry for buying options"
            elif iv <= IV_ABS_BUYER_WARN_PCT:
                s, r = "warn", "Moderate IV — acceptable"
            else:
                s, r = "fail", "IV elevated — IV crush risk on entry"
            return _gate("ivr", "IV Rank", s, f"IV {iv:.2f}% (fallback)",
                         f"IV <{IV_ABS_BUYER_PASS_PCT} pass, >{IV_ABS_BUYER_WARN_PCT} fail", r, s == "fail")
        ivr = float(ivr)
        if ivr < IVR_BUYER_PASS_PCT:
            s, r = "pass", "IV rank low — ideal for buying options"
        elif ivr <= IVR_BUYER_WARN_PCT:
            s, r = "warn", "Moderate IV rank — acceptable"
        else:
            s, r = "fail", "IV rank elevated — IV crush risk on entry"
        return _gate("ivr", "IV Rank", s, f"IVR {ivr:.1f}%",
                     f"<{IVR_BUYER_PASS_PCT} pass, {IVR_BUYER_PASS_PCT}–{IVR_BUYER_WARN_PCT} warn, >{IVR_BUYER_WARN_PCT} fail", r, s == "fail")

    def _etf_hv_iv_gate(self, p: dict) -> dict:
        """HV/IV ratio gate — same math for all 4 ETF directions."""
        current_iv = float(p.get("current_iv", 0.0))
        hv_20 = float(p.get("hv_20", 0.0) or 0.0)
        ratio = float(p.get("hv_iv_ratio", 0.0) or 0.0)
        if hv_20 < HV_LOW_REGIME_PCT:
            if current_iv < IV_ABS_LOW_HV_PASS_PCT:
                s, r = "pass", "Low HV regime: IV still acceptable"
            else:
                s, r = "fail", "Low HV regime but IV not cheap enough"
        else:
            if ratio < HV_IV_PASS_RATIO:
                s, r = "pass", "Options fairly priced vs realized vol"
            elif ratio <= HV_IV_WARN_RATIO:
                s, r = "warn", "Paying average vol risk premium"
            else:
                s, r = "fail", "IV significantly overpriced vs HV"
        return _gate("hv_iv", "HV/IV Ratio", s, f"IV/HV {ratio:.2f}",
                     f"<{HV_IV_PASS_RATIO} pass, {HV_IV_PASS_RATIO}–{HV_IV_WARN_RATIO} warn, >{HV_IV_WARN_RATIO} fail", r, s == "fail")

    def _etf_theta_gate(self, p: dict) -> dict:
        """Theta burn gate for buyers — same math, no swing dependency."""
        premium = float(p.get("premium", 0.0) or 0.0)
        theta = float(p.get("theta_per_day", 0.0) or 0.0)
        burn = abs(theta * self.planned_hold_days) / premium * 100 if premium > 0 else 999.0
        if burn <= THETA_BURN_PASS_PCT:
            s, r = "pass", "Theta decay manageable over hold period"
        elif burn <= THETA_BURN_WARN_PCT:
            s, r = "warn", "Theta notable — need a fast move"
        else:
            s, r = "fail", "Theta will erode gains — use longer DTE"
        return _gate("theta_burn", "Theta Burn", s, f"{burn:.1f}% over {self.planned_hold_days}d",
                     f"<={THETA_BURN_PASS_PCT} pass, >{THETA_BURN_WARN_PCT} fail", r, s == "fail")

    def _etf_dte_buyer_gate(self, p: dict) -> dict:
        """
        IVR-based DTE gate for ETF buyers (tastylive research-verified):
            IVR < 30  → target 60 DTE
            IVR >= 30 → target 30 DTE
        Tolerance: ±10 DTE from target is still a pass.
        """
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        ivr = p.get("ivr_pct")
        rec_dte = int(p.get("recommended_dte") or (ETF_DTE_LOW_IVR if (ivr is None or float(ivr) < IVR_BUYER_PASS_PCT) else ETF_DTE_HIGH_IVR))
        p["recommended_dte"] = rec_dte
        if dte < DEFAULT_MIN_DTE:
            s, r = "fail", "DTE too short — expiry risk too high"
        elif abs(dte - rec_dte) <= DTE_GATE_TOLERANCE:
            s, r = "pass", f"DTE aligned with IV rank (target {rec_dte}d)"
        elif dte > rec_dte + DTE_GATE_TOLERANCE:
            s, r = "warn", f"DTE longer than optimal — theta burn reduced but capital tied up"
        else:
            s, r = "warn", f"DTE slightly short for current IV rank"
        return _gate("dte", "DTE Selection", s, f"DTE {dte}, target {rec_dte}",
                     f"IVR-based: <{IVR_BUYER_PASS_PCT} → 60 DTE, >={IVR_BUYER_PASS_PCT} → 30 DTE", r, s == "fail")

    def _etf_fomc_gate(self, p: dict, dte: int) -> dict:
        """FOMC proximity check — ETFs have no earnings, FOMC is the primary event."""
        fomc_days = int(p.get("fomc_days_away", 999) or 999)
        if 5 <= fomc_days <= 10:
            s, r, block = "warn", "FOMC event near expiry — rate-sensitive ETFs may gap", False
        elif fomc_days < 5:
            s, r, block = "warn", "FOMC imminent — consider reducing size", False
        else:
            s, r, block = "pass", "No FOMC event conflict", False
        return _gate("events", "Event Calendar", s, f"FOMC {fomc_days}d",
                     "FOMC >10d clear; 5–10d warn; <5d caution", r, block)

    def _etf_spy_regime_bull_gate(self, p: dict) -> dict:
        """SPY regime gate for bullish ETF buyers (buy_call)."""
        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            return _gate("market_regime", "Market Regime", "warn", "SPY unavailable",
                         "above 200SMA required", "SPY regime unavailable — verify STA", False)
        spy_above = bool(p.get("spy_above_200sma", False))
        spy_5d = float(spy_5d_raw)
        if spy_above and spy_5d > SPY_BULL_5D_WARN:
            s, r = "pass", "Bull regime — supportive for call buying"
        elif spy_above and SPY_BULL_5D_FAIL <= spy_5d <= SPY_BULL_5D_WARN:
            s, r = "warn", "Market softening — tighten entries"
        else:
            s, r = "fail", "Market regime unsupportive for call buying"
        return _gate("market_regime", "Market Regime", s,
                     f"200SMA {'above' if spy_above else 'below'}, 5d {spy_5d:.2%}",
                     f"above 200SMA and 5d>{SPY_BULL_5D_WARN:.0%}", r, s == "fail")

    def _etf_spy_regime_bear_gate(self, p: dict) -> dict:
        """SPY regime gate for bearish ETF buyers (buy_put)."""
        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            return _gate("market_regime", "Market Regime", "warn", "SPY unavailable",
                         "weak market preferred", "SPY regime unavailable — verify STA", False)
        spy_above = bool(p.get("spy_above_200sma", False))
        spy_5d = float(spy_5d_raw)
        if not spy_above and spy_5d < SPY_BUYPUT_5D_PASS:
            s, r = "pass", "Bear regime — supportive for put buying"
        elif spy_5d < SPY_BUYPUT_5D_WARN:
            s, r = "warn", "Market weakening — reasonable for defensive puts"
        else:
            s, r = "fail", "Market regime not supportive for put buying"
        return _gate("market_regime", "Market Regime", s,
                     f"200SMA {'above' if spy_above else 'below'}, 5d {spy_5d:.2%}",
                     f"below 200SMA and 5d<{SPY_BUYPUT_5D_PASS:.0%} pass", r, s == "fail")

    def _etf_position_size_gate(self, p: dict) -> dict:
        """Position sizing gate — same math for all directions."""
        premium = float(p.get("premium", 0.0) or 0.0)
        account = float(p.get("account_size", DEFAULT_ACCOUNT_SIZE))
        risk_pct = float(p.get("risk_pct", DEFAULT_RISK_PCT))
        max_risk = account * risk_pct
        cost = premium * 100
        lots = math.floor(max_risk / cost) if cost > 0 else 0
        if lots >= 1:
            s, r = "pass", f"Up to {lots} lot(s) within risk budget"
        else:
            s, r = "warn", "Option cost exceeds 1% risk budget — size down or skip"
        return _gate("position_size", "Position Sizing", s, f"lots_allowed={lots}",
                     "lots>=1 pass; 0 warn", r, False)

    def _run_etf_buy_call(self, p: dict) -> list[dict]:
        """
        ETF buy_call gate track.
        Replaces _run_track_a for ETFs — no VCP, ADX, pivot_confirm.
        Gates: IVR buyer, HV/IV, theta burn, DTE (IVR-based), FOMC, liquidity,
               SPY regime (bull), position sizing.
        """
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        return [
            self._etf_ivr_buyer_gate(p),
            self._etf_hv_iv_gate(p),
            self._etf_theta_gate(p),
            self._etf_dte_buyer_gate(p),
            self._etf_fomc_gate(p, dte),
            self._liquidity_gate(p),
            self._etf_spy_regime_bull_gate(p),
            self._etf_position_size_gate(p),
        ]

    def _run_etf_buy_put(self, p: dict) -> list[dict]:
        """
        ETF buy_put gate track.
        Replaces _run_buy_put for ETFs — no VCP, ADX, breakdown_confirm.
        Gates: IVR buyer, HV/IV, theta burn, DTE (IVR-based), FOMC, liquidity,
               SPY regime (bear), position sizing.
        """
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        return [
            self._etf_ivr_buyer_gate(p),
            self._etf_hv_iv_gate(p),
            self._etf_theta_gate(p),
            self._etf_dte_buyer_gate(p),
            self._etf_fomc_gate(p, dte),
            self._liquidity_gate(p),
            self._etf_spy_regime_bear_gate(p),
            self._etf_position_size_gate(p),
        ]

    def _run_etf_sell_put(self, p: dict) -> list[dict]:
        """
        ETF sell_put gate track.
        Replaces _run_track_b for ETFs — no s1_support strike_safety gate.
        Uses IVR seller logic, delta-based strike check, SPY regime for sellers.
        """
        out = []

        # Gate 1: IVR seller — wants HIGH IV
        ivr = float(p.get("ivr_pct", 0.0) or 0.0)
        if ivr >= IVR_SELLER_PASS_PCT:
            s, r = "pass", "Premium expensive — ideal for put selling"
        elif ivr >= IVR_SELLER_MIN_PCT:
            s, r = "warn", "Minimum viable IV for put selling"
        else:
            s, r = "fail", "IV too cheap — insufficient premium to sell puts"
        out.append(_gate("ivr_seller", "IV Rank (Seller)", s, f"IVR {ivr:.1f}%",
                         f">={IVR_SELLER_PASS_PCT} pass, {IVR_SELLER_MIN_PCT}–{IVR_SELLER_PASS_PCT-1} warn, <{IVR_SELLER_MIN_PCT} fail", r, s == "fail"))

        # Gate 2: Strike delta check — ETF sell_put should be OTM (delta < -0.30 abs)
        strike = float(p.get("strike", 0.0) or 0.0)
        und = float(p.get("underlying_price", 0.0) or 0.0)
        if und > 0:
            otm_pct = (und - strike) / und * 100  # positive = OTM for puts
            if otm_pct >= 3.0:
                s, r = "pass", f"Strike {otm_pct:.1f}% OTM — safe cushion for put selling"
            elif otm_pct >= 0:
                s, r = "warn", "Strike near ATM — elevated assignment risk"
            else:
                s, r = "fail", "Strike above underlying — ITM put, immediate intrinsic loss"
        else:
            s, r = "warn", "Unable to verify strike vs underlying"
        out.append(_gate("strike_otm", "Strike OTM Check", s,
                         f"strike {strike:.2f}, und {und:.2f}",
                         ">=3% OTM pass; ATM warn; ITM fail", r, s == "fail"))

        # Gate 3: DTE seller window
        dte = int(p.get("selected_expiry_dte", 0) or 0)
        if DEFAULT_MIN_DTE <= dte <= DTE_REC_HIGH_SIGNAL:
            s, r = "pass", "Optimal theta decay window"
        elif DTE_REC_HIGH_SIGNAL < dte <= DTE_REC_MED_SIGNAL:
            s, r = "warn", "Tradable but slower decay"
        elif dte > 60 or dte < 7:
            s, r = "fail", "Outside seller DTE window"
        else:
            s, r = "warn", "Suboptimal DTE window"
        out.append(_gate("dte_seller", "DTE (Seller)", s, f"DTE {dte}",
                         f"{DEFAULT_MIN_DTE}–{DTE_REC_HIGH_SIGNAL} pass; >60 or <7 fail", r, s == "fail"))

        # Gate 4: FOMC event
        out.append(self._etf_fomc_gate(p, dte))

        # Gate 5: Liquidity
        out.append(self._liquidity_gate(p))

        # Gate 6: SPY regime — put sellers want stable/bull market
        spy_5d_raw = p.get("spy_5day_return")
        if spy_5d_raw is None:
            out.append(_gate("market_regime_seller", "Market Regime (Seller)", "warn",
                             "SPY unavailable", "stable/bull market required",
                             "SPY regime unavailable — verify STA", False))
        else:
            spy_above = bool(p.get("spy_above_200sma", False))
            spy_5d = float(spy_5d_raw)
            if spy_above and spy_5d > SPY_SELLPUT_5D_WARN:
                s, r = "pass", "Market stable — favorable for put selling"
            elif SPY_SELLPUT_5D_FAIL <= spy_5d <= SPY_SELLPUT_5D_WARN:
                s, r = "warn", "Regime softening for premium selling"
            else:
                s, r = "fail", "Downside regime too risky for put selling"
            out.append(_gate("market_regime_seller", "Market Regime (Seller)", s,
                             f"200SMA {'above' if spy_above else 'below'}, 5d {spy_5d:.2%}",
                             f"above 200SMA and 5d>{SPY_SELLPUT_5D_WARN:.0%}", r, s == "fail"))

        # Gate 7: Max loss check
        premium = float(p.get("premium", 0.0) or 0.0)
        lots = max(1.0, float(p.get("lots", 1.0) or 1.0))
        account = float(p.get("account_size", DEFAULT_ACCOUNT_SIZE))
        max_loss = (strike - premium) * 100
        total = max_loss * lots
        if total <= account * MAX_LOSS_WARN_PCT:
            s, r = "pass", "Max loss within 10% of account"
        elif total <= account * MAX_LOSS_FAIL_PCT:
            s, r = "warn", "Max loss elevated vs account size"
        else:
            s, r = "fail", "Max loss exceeds 20% of account"
        out.append(_gate("max_loss", "Max Loss Defined", s, f"${total:.2f}",
                         f"<={MAX_LOSS_WARN_PCT:.0%} pass, >{MAX_LOSS_FAIL_PCT:.0%} fail", r, s == "fail"))

        return out
