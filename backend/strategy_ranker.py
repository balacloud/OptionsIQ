from __future__ import annotations

from datetime import datetime


def _f(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _spread_pct(c: dict) -> float | None:
    bid = c.get("bid")
    ask = c.get("ask")
    if bid is None or ask is None:
        return None
    bidf, askf = float(bid), float(ask)
    mid = (bidf + askf) / 2
    if mid <= 0:
        return None
    return round(((askf - bidf) / mid) * 100, 2)


def _fmt_exp(expiry: str) -> str:
    dt = datetime.fromisoformat(expiry)
    return dt.strftime("%b %Y")


class StrategyRanker:
    def rank(self, direction: str, chain: dict, swing_data: dict, recommended_dte: int | None = None) -> list[dict]:
        if direction == "buy_call":
            return self._rank_buy_call(chain, swing_data, recommended_dte)
        if direction == "sell_call":
            return self._rank_sell_call(chain, swing_data, recommended_dte)
        if direction == "buy_put":
            return self._rank_buy_put(chain, swing_data, recommended_dte)
        if direction == "sell_put":
            is_etf = (swing_data or {}).get("swing_data_quality") == "etf"
            if is_etf:
                return self._rank_sell_put_etf(chain, swing_data, recommended_dte)
            return self._rank_track_b(chain, swing_data)
        return []

    def _best_expiry_contracts(self, chain: dict, right: str, preferred_dte: int) -> list[dict]:
        contracts = [c for c in chain.get("contracts", []) if c.get("right") == right]
        if not contracts:
            return []
        expiries = {}
        for c in contracts:
            expiries.setdefault(c["expiry"], int(c.get("dte", 0)))
        best_expiry = min(expiries.items(), key=lambda x: abs(x[1] - preferred_dte))[0]
        return [c for c in contracts if c["expiry"] == best_expiry]

    def _closest_delta(self, contracts: list[dict], target: float, abs_delta: bool = True) -> dict:
        if abs_delta:
            return min(contracts, key=lambda c: abs(abs(_f(c.get("delta"), 0.0)) - target))
        return min(contracts, key=lambda c: abs(_f(c.get("delta"), 0.0) - target))

    # ─── sell_put (single-leg, ETF mode) ──────────────────────────────────────

    def _rank_sell_put_etf(self, chain: dict, _swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """Single-leg sell_put for ETFs. R1: delta 0.20, R2: delta 0.15, R3: delta 0.28."""
        pref = recommended_dte if recommended_dte else 30
        puts = self._best_expiry_contracts(chain, "P", pref)
        if not puts:
            return []
        current = float(chain.get("underlying_price", 0.0))
        otm_puts = sorted(
            [c for c in puts if _f(c.get("strike"), 0.0) < current],
            key=lambda c: _f(c.get("strike"), 0.0), reverse=True,
        )
        if not otm_puts:
            otm_puts = sorted(puts, key=lambda c: _f(c.get("strike"), 0.0), reverse=True)

        d20 = self._closest_delta(otm_puts, 0.20)
        d15 = self._closest_delta(otm_puts, 0.15)
        d28 = self._closest_delta(otm_puts, 0.28)

        results = []
        seen = set()

        configs = [
            (d20, 0.20, "Standard — best premium/risk balance. PoP ~80%.", None),
            (d15, 0.15, "Conservative — lower premium, PoP ~85%. Use when IV cooling or regime uncertain.", None),
            (d28, 0.28, "Aggressive — higher credit, PoP ~72%. Use only when IVR ≥75% and trend strong.",
             "Higher delta — confirm strike is outside expected move before entry."),
        ]
        for c, target_delta, why, warning in configs:
            strike = _f(c.get("strike"), 0.0)
            if strike in seen:
                continue
            seen.add(strike)
            premium = _f(c.get("mid", c.get("last", 0.0)), 0.0)
            results.append({
                "rank": len(results) + 1,
                "label": f"Sell {int(strike)}P · {_fmt_exp(c['expiry'])}",
                "strategy_type": "sell_put",
                "strike_display": f"{strike:.0f}P",
                "expiry_display": c["expiry"],
                "premium_per_lot": round(premium * 100, 2),
                "breakeven": round(strike - premium, 2),
                "delta": round(_f(c.get("delta"), 0.0), 3),
                "theta_per_day": round(_f(c.get("theta"), 0.0), 3),
                "vega": round(_f(c.get("vega"), 0.0), 3),
                "gamma": round(_f(c.get("gamma"), 0.0), 3),
                "implied_vol": round(_f(c.get("impliedVol"), 0.0) * 100, 2),
                "max_gain_per_lot": round(premium * 100, 2),
                "max_loss_per_lot": round(strike * 100, 2),
                "spread_pct": _spread_pct(c),
                "why": why,
                "warning": warning,
                "strike": strike,
                "right": "P",
                "net_premium": premium,
                "premium": premium,
                "expiry": c["expiry"],
                "dte": int(c.get("dte", 0)),
                "bid": c.get("bid"),
                "ask": c.get("ask"),
                "open_interest": c.get("openInterest", 0),
                "volume": c.get("volume", 0),
            })

        return results[:3]

    # ─── sell_call (single-leg) ────────────────────────────────────────────────

    def _rank_sell_call(self, chain: dict, _swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """Single-leg sell_call. R1: delta 0.20, R2: delta 0.15, R3: delta 0.25."""
        pref = recommended_dte if recommended_dte else 30
        calls = self._best_expiry_contracts(chain, "C", pref)
        if not calls:
            return []
        current = float(chain.get("underlying_price", 0.0))
        otm_calls = sorted(
            [c for c in calls if _f(c.get("strike"), 0.0) >= current],
            key=lambda c: _f(c.get("strike"), 0.0),
        )
        if not otm_calls:
            otm_calls = sorted(calls, key=lambda c: _f(c.get("strike"), 0.0))

        d20 = self._closest_delta(otm_calls, 0.20)
        d15 = self._closest_delta(otm_calls, 0.15)
        d25 = self._closest_delta(otm_calls, 0.25)

        results = []
        seen = set()

        configs = [
            (d20, "Standard — OTM call at delta 0.20. PoP ~80%.", None),
            (d15, "Conservative — further OTM, PoP ~85%. Use in weak downtrend.", None),
            (d25, "Aggressive — higher credit, PoP ~75%. Use when IVR elevated and trend clearly down.",
             "Confirm strike is outside expected move upside before entry."),
        ]
        for c, why, warning in configs:
            strike = _f(c.get("strike"), 0.0)
            if strike in seen:
                continue
            seen.add(strike)
            premium = _f(c.get("mid", c.get("last", 0.0)), 0.0)
            results.append({
                "rank": len(results) + 1,
                "label": f"Sell {int(strike)}C · {_fmt_exp(c['expiry'])}",
                "strategy_type": "sell_call",
                "strike_display": f"{strike:.0f}C",
                "expiry_display": c["expiry"],
                "premium_per_lot": round(premium * 100, 2),
                "breakeven": round(strike + premium, 2),
                "delta": round(_f(c.get("delta"), 0.0), 3),
                "theta_per_day": round(_f(c.get("theta"), 0.0), 3),
                "vega": round(_f(c.get("vega"), 0.0), 3),
                "gamma": round(_f(c.get("gamma"), 0.0), 3),
                "implied_vol": round(_f(c.get("impliedVol"), 0.0) * 100, 2),
                "max_gain_per_lot": round(premium * 100, 2),
                "max_loss_per_lot": None,
                "spread_pct": _spread_pct(c),
                "why": why,
                "warning": warning,
                "strike": strike,
                "right": "C",
                "net_premium": premium,
                "premium": premium,
                "expiry": c["expiry"],
                "dte": int(c.get("dte", 0)),
                "bid": c.get("bid"),
                "ask": c.get("ask"),
                "open_interest": c.get("openInterest", 0),
                "volume": c.get("volume", 0),
            })

        return results[:3]

    # ─── buy_call (single-leg directional) ────────────────────────────────────

    def _rank_buy_call(self, chain: dict, _swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """Single-leg buy_call. R1: delta 0.68 ITM, R2: delta 0.50 ATM, R3: delta 0.30 OTM."""
        pref = recommended_dte if recommended_dte else 45
        calls = self._best_expiry_contracts(chain, "C", pref)
        if not calls:
            return []

        d68 = self._closest_delta(calls, 0.68)
        d50 = self._closest_delta(calls, 0.50)
        d30 = self._closest_delta(calls, 0.30)

        configs = [
            (d68, "itm_call", "ITM call — delta 0.68. Intrinsic value shields theta. Best for sustained directional moves.", None),
            (d50, "atm_call", "ATM call — delta 0.50. Balanced cost and leverage. Standard entry for moderate moves.", None),
            (d30, "otm_call", "OTM call — delta 0.30. High leverage, highest risk. Requires strong breakout confirmation.",
             "OTM — theta burns fast. Needs quick directional move. Size small."),
        ]

        results = []
        seen = set()
        for c, stype, why, warning in configs:
            strike = _f(c.get("strike"), 0.0)
            if strike in seen:
                continue
            seen.add(strike)
            results.append(self._build_long_call(
                rank=len(results) + 1,
                label=f"{int(strike)}C · {_fmt_exp(c['expiry'])}",
                strategy_type=stype,
                c=c, why=why, warning=warning,
            ))

        return results[:3]

    # ─── buy_put (single-leg directional) ─────────────────────────────────────

    def _rank_buy_put(self, chain: dict, _swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """Single-leg buy_put. R1: delta 0.68 ITM, R2: delta 0.50 ATM, R3: delta 0.30 OTM."""
        pref = recommended_dte if recommended_dte else 45
        puts = self._best_expiry_contracts(chain, "P", pref)
        if not puts:
            return []

        d68 = self._closest_delta(puts, 0.68)
        d50 = self._closest_delta(puts, 0.50)
        d30 = self._closest_delta(puts, 0.30)

        configs = [
            (d68, "itm_put", "ITM put — delta 0.68. Intrinsic value shields theta. Best for momentum breakdowns.", None),
            (d50, "atm_put", "ATM put — delta 0.50. Balanced cost and leverage. Standard entry for confirmed downtrends.", None),
            (d30, "otm_put", "OTM put — delta 0.30. High leverage, highest risk. Requires strong breakdown confirmation.",
             "OTM — theta burns fast. Needs quick move lower. Size small."),
        ]

        results = []
        seen = set()
        for c, stype, why, warning in configs:
            strike = _f(c.get("strike"), 0.0)
            if strike in seen:
                continue
            seen.add(strike)
            results.append(self._build_long_put(
                rank=len(results) + 1,
                label=f"{int(strike)}P · {_fmt_exp(c['expiry'])}",
                strategy_type=stype,
                c=c, why=why, warning=warning,
            ))

        return results[:3]

    # ─── builders ─────────────────────────────────────────────────────────────

    def _build_long_call(self, rank: int, label: str, strategy_type: str,
                         c: dict, why: str, warning: str | None) -> dict:
        strike = _f(c.get("strike"), 0.0)
        premium = _f(c.get("mid", c.get("last", 0.0)), 0.0)
        expiry = c["expiry"]
        return {
            "rank": rank,
            "label": label,
            "strategy_type": strategy_type,
            "strike_display": f"{strike:.0f}C",
            "expiry_display": expiry,
            "premium_per_lot": round(premium * 100, 2),
            "breakeven": round(strike + premium, 2),
            "delta": round(_f(c.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(c.get("theta"), 0.0), 3),
            "vega": round(_f(c.get("vega"), 0.0), 3),
            "gamma": round(_f(c.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(c.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": None,
            "max_loss_per_lot": round(premium * 100, 2),
            "spread_pct": _spread_pct(c),
            "why": why,
            "warning": warning,
            "strike": strike,
            "right": "C",
            "net_premium": premium,
            "premium": premium,
            "expiry": expiry,
            "dte": int(c.get("dte", 0)),
            "bid": c.get("bid"),
            "ask": c.get("ask"),
            "open_interest": c.get("openInterest", 0),
            "volume": c.get("volume", 0),
        }

    def _build_long_put(self, rank: int, label: str, strategy_type: str,
                        c: dict, why: str, warning: str | None) -> dict:
        strike = _f(c.get("strike"), 0.0)
        premium = _f(c.get("mid", c.get("last", 0.0)), 0.0)
        expiry = c["expiry"]
        return {
            "rank": rank,
            "label": label,
            "strategy_type": strategy_type,
            "strike_display": f"{strike:.0f}P",
            "expiry_display": expiry,
            "premium_per_lot": round(premium * 100, 2),
            "breakeven": round(strike - premium, 2),
            "delta": round(_f(c.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(c.get("theta"), 0.0), 3),
            "vega": round(_f(c.get("vega"), 0.0), 3),
            "gamma": round(_f(c.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(c.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": None,
            "max_loss_per_lot": round(premium * 100, 2),
            "spread_pct": _spread_pct(c),
            "why": why,
            "warning": warning,
            "strike": strike,
            "right": "P",
            "net_premium": premium,
            "premium": premium,
            "expiry": expiry,
            "dte": int(c.get("dte", 0)),
            "bid": c.get("bid"),
            "ask": c.get("ask"),
            "open_interest": c.get("openInterest", 0),
            "volume": c.get("volume", 0),
        }

    # ─── sell_put naked (stock mode — not ETF) ────────────────────────────────

    def _rank_track_b(self, chain: dict, swing_data: dict) -> list[dict]:
        puts = [c for c in chain.get("contracts", []) if c.get("right") == "P"]
        if not puts:
            return []
        current = float(chain.get("underlying_price", 0.0))
        is_etf = swing_data.get("swing_data_quality") == "etf" if swing_data else False
        s1_raw = swing_data.get("s1_support") if swing_data else None

        candidates = []
        for p in puts:
            strike = _f(p.get("strike"), 0.0)
            if is_etf:
                if strike >= current:
                    continue
            else:
                if s1_raw is not None and strike > float(s1_raw):
                    continue
            premium = _f(p.get("mid", p.get("last", 0.0)), 0.0)
            max_loss = max(0.01, (strike - premium) * 100)
            ratio = (premium * 100) / max_loss
            candidates.append((p, premium, ratio))

        if not candidates:
            candidates = [(p, _f(p.get("mid", p.get("last", 0.0)), 0.0), 0.0) for p in puts]

        ranked = sorted(candidates, key=lambda x: (x[1], x[2]), reverse=True)[:3]
        out = []
        for idx, (c, premium, _ratio) in enumerate(ranked, start=1):
            strike = _f(c.get("strike"), 0.0)
            expiry = c["expiry"]
            out.append({
                "rank": idx,
                "label": f"Sell {int(strike)}P · {_fmt_exp(expiry)}",
                "strategy_type": "sell_put",
                "strike_display": f"{strike:.0f}P",
                "expiry_display": expiry,
                "premium_per_lot": round(premium * 100, 2),
                "breakeven": round(strike - premium, 2),
                "delta": round(_f(c.get("delta"), 0.0), 3),
                "theta_per_day": round(_f(c.get("theta"), 0.0), 3),
                "vega": round(_f(c.get("vega"), 0.0), 3),
                "gamma": round(_f(c.get("gamma"), 0.0), 3),
                "implied_vol": round(_f(c.get("impliedVol"), 0.0) * 100, 2),
                "max_gain_per_lot": round(premium * 100, 2),
                "max_loss_per_lot": round((strike - premium) * 100, 2),
                "spread_pct": _spread_pct(c),
                "why": "Higher premium with safer strike and better credit-to-risk.",
                "warning": "NAKED PUT — max loss = strike × 100. Cash-secured margin required.",
                "strike": strike,
                "right": "P",
                "net_premium": premium,
                "premium": premium,
                "expiry": expiry,
                "dte": int(c.get("dte", 0)),
                "bid": c.get("bid"),
                "ask": c.get("ask"),
                "open_interest": c.get("openInterest", 0),
                "volume": c.get("volume", 0),
            })
        return out
