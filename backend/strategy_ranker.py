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
        if direction in {"buy_call", "sell_call"}:
            return self._rank_track_a(chain, swing_data, recommended_dte)
        return self._rank_track_b(chain, swing_data)

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

    def _rank_track_a(self, chain: dict, swing_data: dict, recommended_dte: int | None) -> list[dict]:
        pref = recommended_dte if recommended_dte else 45
        calls = self._best_expiry_contracts(chain, "C", pref)
        if not calls:
            return []
        current = float(chain.get("underlying_price", 0.0))
        target1 = float(swing_data.get("target1", current))

        itm = self._closest_delta(calls, 0.68)
        atm = self._closest_delta(calls, 0.52)
        short = min(calls, key=lambda c: abs(_f(c.get("strike"), 0.0) - target1))

        itm_obj = self._build_long_call(rank=1, label=f"{int(itm['strike'])}C · {_fmt_exp(itm['expiry'])}", c=itm,
                                        why="Highest probability. Intrinsic value shields theta. Best for momentum breakouts per institutional quant review.", warning=None)

        spread_obj = self._build_spread(rank=2, long_leg=atm, short_leg=short,
                                        label=f"{int(atm['strike'])}/{int(short['strike'])} Bull Call · {_fmt_exp(atm['expiry'])}",
                                        why="Lowest cost. Short strike caps at Target 1. Best % return to T1. Lowest theta burn for slower breakouts.")

        atm_obj = self._build_long_call(rank=3, label=f"{int(atm['strike'])}C · {_fmt_exp(atm['expiry'])} ⚠️ HIGH THETA", c=atm,
                                        why="Highest gamma. Best for explosive breakouts only. Theta burns fastest — must move within 5 days.", warning="HIGH THETA")

        return [itm_obj, spread_obj, atm_obj]

    def _build_long_call(self, rank: int, label: str, c: dict, why: str, warning: str | None) -> dict:
        strike = _f(c.get("strike"), 0.0)
        premium = _f(c.get("mid", c.get("last", 0.0)), 0.0)
        expiry = c["expiry"]
        return {
            "rank": rank,
            "label": label,
            "strategy_type": "itm_call" if rank == 1 else "atm_call",
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
            "premium": premium,
            "expiry": expiry,
            "dte": int(c.get("dte", 0)),
            "bid": c.get("bid"),
            "ask": c.get("ask"),
            "open_interest": c.get("openInterest", 0),
            "volume": c.get("volume", 0),
        }

    def _build_spread(self, rank: int, long_leg: dict, short_leg: dict, label: str, why: str) -> dict:
        long_strike = _f(long_leg.get("strike"), 0.0)
        short_strike = _f(short_leg.get("strike"), 0.0)
        if short_strike <= long_strike:
            higher = [short_leg, long_leg]
            long_leg, short_leg = sorted(higher, key=lambda x: _f(x.get("strike"), 0.0))
            long_strike = _f(long_leg.get("strike"), 0.0)
            short_strike = _f(short_leg.get("strike"), 0.0)

        long_p = _f(long_leg.get("mid", long_leg.get("last", 0.0)), 0.0)
        short_p = _f(short_leg.get("mid", short_leg.get("last", 0.0)), 0.0)
        net = max(0.01, long_p - short_p)
        width = max(0.0, short_strike - long_strike)

        return {
            "rank": rank,
            "label": label,
            "strategy_type": "spread",
            "strike_display": f"{long_strike:.0f}/{short_strike:.0f}",
            "expiry_display": long_leg["expiry"],
            "premium_per_lot": round(net * 100, 2),
            "breakeven": round(long_strike + net, 2),
            "delta": round(_f(long_leg.get("delta"), 0.0) - _f(short_leg.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(long_leg.get("theta"), 0.0) - _f(short_leg.get("theta"), 0.0), 3),
            "vega": round(_f(long_leg.get("vega"), 0.0) - _f(short_leg.get("vega"), 0.0), 3),
            "gamma": round(_f(long_leg.get("gamma"), 0.0) - _f(short_leg.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(long_leg.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": round(max(0.0, (width - net) * 100), 2),
            "max_loss_per_lot": round(net * 100, 2),
            "spread_pct": _spread_pct(long_leg),
            "why": why,
            "warning": None,
            "long_strike": long_strike,
            "short_strike": short_strike,
            "net_premium": net,
            "expiry": long_leg["expiry"],
            "dte": int(long_leg.get("dte", 0)),
            "premium": net,
            "strike": long_strike,
            "bid": long_leg.get("bid"),
            "ask": long_leg.get("ask"),
            "open_interest": long_leg.get("openInterest", 0),
            "volume": long_leg.get("volume", 0),
        }

    def _rank_track_b(self, chain: dict, swing_data: dict) -> list[dict]:
        puts = [c for c in chain.get("contracts", []) if c.get("right") == "P"]
        if not puts:
            return []
        s1 = float(swing_data.get("s1_support", chain.get("underlying_price", 0.0)))

        candidates = []
        for p in puts:
            strike = _f(p.get("strike"), 0.0)
            if strike > s1:
                continue
            premium = _f(p.get("mid", p.get("last", 0.0)), 0.0)
            max_loss = max(0.01, (strike - premium) * 100)
            ratio = (premium * 100) / max_loss
            candidates.append((p, premium, ratio))

        if not candidates:
            candidates = [(p, _f(p.get("mid", p.get("last", 0.0)), 0.0), 0.0) for p in puts]

        ranked = sorted(candidates, key=lambda x: (x[1], x[2]), reverse=True)[:3]
        out = []
        for idx, (c, premium, ratio) in enumerate(ranked, start=1):
            strike = _f(c.get("strike"), 0.0)
            expiry = c["expiry"]
            out.append(
                {
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
                    "warning": None,
                    "strike": strike,
                    "premium": premium,
                    "expiry": expiry,
                    "dte": int(c.get("dte", 0)),
                    "bid": c.get("bid"),
                    "ask": c.get("ask"),
                    "open_interest": c.get("openInterest", 0),
                    "volume": c.get("volume", 0),
                }
            )
        return out
