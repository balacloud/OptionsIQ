from __future__ import annotations

from datetime import datetime

from constants import MIN_CREDIT_WIDTH_RATIO


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


def _credit_width(net_credit: float, width: float) -> tuple[float | None, str | None]:
    """Returns (ratio, warning_or_None). warning is set when credit < 33% of width."""
    if width <= 0:
        return None, None
    ratio = net_credit / width
    if ratio < MIN_CREDIT_WIDTH_RATIO:
        return round(ratio, 3), (
            f"Credit-to-width {ratio:.0%} < 33% minimum — thin premium, negative expectancy. "
            "Consider a wider spread or skip this setup."
        )
    return round(ratio, 3), None


def _fmt_exp(expiry: str) -> str:
    dt = datetime.fromisoformat(expiry)
    return dt.strftime("%b %Y")


class StrategyRanker:
    def rank(self, direction: str, chain: dict, swing_data: dict, recommended_dte: int | None = None) -> list[dict]:
        if direction == "buy_call":
            return self._rank_track_a(chain, swing_data, recommended_dte)
        if direction == "sell_call":
            return self._rank_sell_call(chain, swing_data, recommended_dte)
        if direction == "buy_put":
            return self._rank_buy_put(chain, swing_data, recommended_dte)
        # sell_put: ETF mode → bull_put_spread (defined risk); stock mode → naked put
        is_etf = (swing_data or {}).get("swing_data_quality") == "etf"
        if direction == "sell_put" and is_etf:
            return self._rank_sell_put_spread(chain, swing_data, recommended_dte)
        return self._rank_track_b(chain, swing_data)  # sell_put naked (stock)

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

        itm = self._closest_delta(calls, 0.68)
        atm = self._closest_delta(calls, 0.52)

        # Spread short leg: use delta 0.30 (ETF-clean, no swing target dependency).
        # Swing target1 is only used as a fallback hint if available and non-fabricated.
        target1_raw = swing_data.get("target1") if swing_data else None
        if (target1_raw is not None and swing_data.get("swing_data_quality") != "etf"
                and float(target1_raw) > current):
            # Stock mode: short leg at swing target
            short = min(calls, key=lambda c: abs(_f(c.get("strike"), 0.0) - float(target1_raw)))
        else:
            # ETF mode (or no target): short leg at delta ~0.30 (defined-risk standard)
            short = self._closest_delta(calls, 0.30)

        itm_obj = self._build_long_call(rank=1, label=f"{int(itm['strike'])}C · {_fmt_exp(itm['expiry'])}", c=itm,
                                        why="Highest probability. Delta 0.68 — intrinsic value shields theta decay. Best for sustained directional moves.", warning=None)

        spread_obj = self._build_spread(rank=2, long_leg=atm, short_leg=short,
                                        label=f"{int(atm['strike'])}/{int(short['strike'])} Bull Call · {_fmt_exp(atm['expiry'])}",
                                        why="Defined risk. Long ATM delta 0.52, short OTM delta 0.30. Lowest cost basis, best risk/reward for moderate moves.")

        atm_obj = self._build_long_call(rank=3, label=f"{int(atm['strike'])}C · {_fmt_exp(atm['expiry'])} HIGH THETA", c=atm,
                                        why="Highest gamma. Best for explosive breakouts only. Theta burns fastest — must move within 5 days.", warning="HIGH THETA")

        return [itm_obj, spread_obj, atm_obj]

    def _rank_sell_call(self, chain: dict, _swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """Bear call spread / short call strategies for sell_call direction."""
        pref = recommended_dte if recommended_dte else 30
        calls = self._best_expiry_contracts(chain, "C", pref)
        if not calls:
            return []
        current = float(chain.get("underlying_price", 0.0))

        # Sort calls by strike ascending for OTM ordering
        otm_calls = sorted([c for c in calls if _f(c.get("strike"), 0.0) >= current],
                           key=lambda c: _f(c.get("strike"), 0.0))
        if not otm_calls:
            otm_calls = sorted(calls, key=lambda c: _f(c.get("strike"), 0.0))

        # Short leg: delta ~0.30 (slightly OTM) — highest credit
        short_30 = self._closest_delta(otm_calls, 0.30)
        short_30_strike = _f(short_30.get("strike"), 0.0)
        # Protection leg: delta ~0.15 — must be a DIFFERENT (higher) strike than the short leg.
        # If the chain is narrow and all delta targets cluster to the same strike,
        # fall back to: short = 2nd-highest OTM, protection = highest OTM.
        above_short30 = [c for c in otm_calls if _f(c.get("strike"), 0.0) > short_30_strike]
        if above_short30:
            protection_15 = self._closest_delta(above_short30, 0.15)
        elif len(otm_calls) >= 2:
            sorted_otm = sorted(otm_calls, key=lambda c: _f(c.get("strike"), 0.0))
            short_30 = sorted_otm[-2]   # lower of the two highest strikes → sold leg
            protection_15 = sorted_otm[-1]  # highest strike → bought protection
            short_30_strike = _f(short_30.get("strike"), 0.0)
        else:
            protection_15 = short_30  # forces same-strike guard below to skip spread
        # Higher short leg: delta ~0.20 — less credit but higher PoP
        short_20 = self._closest_delta(otm_calls, 0.20)

        results = []

        # Rank 1: Bear call spread (0.30 delta short, 0.15 delta long protection)
        if short_30.get("strike") != protection_15.get("strike"):
            short_strike = _f(short_30.get("strike"), 0.0)
            long_strike = _f(protection_15.get("strike"), 0.0)
            # Ensure long_strike > short_strike
            if long_strike < short_strike:
                short_30, protection_15 = protection_15, short_30
                short_strike = _f(short_30.get("strike"), 0.0)
                long_strike = _f(protection_15.get("strike"), 0.0)
            short_p = _f(short_30.get("mid", short_30.get("last", 0.0)), 0.0)
            long_p = _f(protection_15.get("mid", protection_15.get("last", 0.0)), 0.0)
            net_credit = max(0.01, short_p - long_p)
            width = max(0.0, long_strike - short_strike)
            cw_ratio, cw_warn = _credit_width(net_credit, width)
            results.append({
                "rank": 1,
                "label": f"{int(short_strike)}/{int(long_strike)} Bear Call · {_fmt_exp(short_30['expiry'])}",
                "strategy_type": "bear_call_spread",
                "strike_display": f"{short_strike:.0f}/{long_strike:.0f}",
                "expiry_display": short_30["expiry"],
                "premium_per_lot": round(net_credit * 100, 2),
                "breakeven": round(short_strike + net_credit, 2),
                "delta": round(_f(short_30.get("delta"), 0.0) - _f(protection_15.get("delta"), 0.0), 3),
                "theta_per_day": round(_f(short_30.get("theta"), 0.0) - _f(protection_15.get("theta"), 0.0), 3),
                "vega": round(_f(short_30.get("vega"), 0.0) - _f(protection_15.get("vega"), 0.0), 3),
                "gamma": round(_f(short_30.get("gamma"), 0.0) - _f(protection_15.get("gamma"), 0.0), 3),
                "implied_vol": round(_f(short_30.get("impliedVol"), 0.0) * 100, 2),
                "max_gain_per_lot": round(net_credit * 100, 2),
                "max_loss_per_lot": round(max(0.0, (width - net_credit) * 100), 2),
                "spread_pct": _spread_pct(short_30),
                "credit_to_width_ratio": cw_ratio,
                "why": "Highest credit. Defined risk. Sell ATM-adjacent call, buy OTM protection. Profit if stock stays flat or falls.",
                "warning": cw_warn,
                "short_strike": short_strike,
                "long_strike": long_strike,
                "net_premium": net_credit,
                "strike": short_strike,
                "right": "C",
                "premium": net_credit,
                "expiry": short_30["expiry"],
                "dte": int(short_30.get("dte", 0)),
                "bid": short_30.get("bid"),
                "ask": short_30.get("ask"),
                "open_interest": short_30.get("openInterest", 0),
                "volume": short_30.get("volume", 0),
            })

        # Rank 2: Higher PoP bear call spread (0.20 delta short)
        if short_20.get("strike") != short_30.get("strike"):
            s20_strike = _f(short_20.get("strike"), 0.0)
            # Find a protection leg above short_20
            above_20 = [c for c in otm_calls if _f(c.get("strike"), 0.0) > s20_strike]
            prot_leg = self._closest_delta(above_20, 0.10) if above_20 else protection_15
            prot_strike = _f(prot_leg.get("strike"), 0.0)
            if prot_strike > s20_strike:
                short_p = _f(short_20.get("mid", short_20.get("last", 0.0)), 0.0)
                long_p = _f(prot_leg.get("mid", prot_leg.get("last", 0.0)), 0.0)
                net_credit = max(0.01, short_p - long_p)
                width = max(0.0, prot_strike - s20_strike)
                cw_ratio, cw_warn = _credit_width(net_credit, width)
                results.append({
                    "rank": len(results) + 1,
                    "label": f"{int(s20_strike)}/{int(prot_strike)} Bear Call · {_fmt_exp(short_20['expiry'])}",
                    "strategy_type": "bear_call_spread",
                    "strike_display": f"{s20_strike:.0f}/{prot_strike:.0f}",
                    "expiry_display": short_20["expiry"],
                    "premium_per_lot": round(net_credit * 100, 2),
                    "breakeven": round(s20_strike + net_credit, 2),
                    "delta": round(_f(short_20.get("delta"), 0.0) - _f(prot_leg.get("delta"), 0.0), 3),
                    "theta_per_day": round(_f(short_20.get("theta"), 0.0) - _f(prot_leg.get("theta"), 0.0), 3),
                    "vega": round(_f(short_20.get("vega"), 0.0) - _f(prot_leg.get("vega"), 0.0), 3),
                    "gamma": round(_f(short_20.get("gamma"), 0.0) - _f(prot_leg.get("gamma"), 0.0), 3),
                    "implied_vol": round(_f(short_20.get("impliedVol"), 0.0) * 100, 2),
                    "max_gain_per_lot": round(net_credit * 100, 2),
                    "max_loss_per_lot": round(max(0.0, (width - net_credit) * 100), 2),
                    "spread_pct": _spread_pct(short_20),
                    "credit_to_width_ratio": cw_ratio,
                    "why": "Higher probability of profit. Less credit but stock has wider buffer before touching short strike.",
                    "warning": cw_warn,
                    "short_strike": s20_strike,
                    "long_strike": prot_strike,
                    "net_premium": net_credit,
                    "strike": s20_strike,
                    "right": "C",
                    "premium": net_credit,
                    "expiry": short_20["expiry"],
                    "dte": int(short_20.get("dte", 0)),
                    "bid": short_20.get("bid"),
                    "ask": short_20.get("ask"),
                    "open_interest": short_20.get("openInterest", 0),
                    "volume": short_20.get("volume", 0),
                })

        # Rank 3: Far OTM short call (delta ~0.15, naked or widest spread)
        far_otm = self._closest_delta(otm_calls, 0.15)
        far_strike = _f(far_otm.get("strike"), 0.0)
        far_p = _f(far_otm.get("mid", far_otm.get("last", 0.0)), 0.0)
        results.append({
            "rank": len(results) + 1,
            "label": f"{int(far_strike)}C · {_fmt_exp(far_otm['expiry'])} ⚠️ FAR OTM",
            "strategy_type": "sell_call",
            "strike_display": f"{far_strike:.0f}C",
            "expiry_display": far_otm["expiry"],
            "premium_per_lot": round(far_p * 100, 2),
            "breakeven": round(far_strike + far_p, 2),
            "delta": round(_f(far_otm.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(far_otm.get("theta"), 0.0), 3),
            "vega": round(_f(far_otm.get("vega"), 0.0), 3),
            "gamma": round(_f(far_otm.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(far_otm.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": round(far_p * 100, 2),
            "max_loss_per_lot": None,  # theoretically unlimited for naked call
            "spread_pct": _spread_pct(far_otm),
            "why": "Lowest delta. Highest probability of expiring worthless. Requires margin — consider spreading for defined risk.",
            "warning": "UNLIMITED RISK — pair with long call for defined risk",
            "strike": far_strike,
            "right": "C",
            "premium": far_p,
            "expiry": far_otm["expiry"],
            "dte": int(far_otm.get("dte", 0)),
            "bid": far_otm.get("bid"),
            "ask": far_otm.get("ask"),
            "open_interest": far_otm.get("openInterest", 0),
            "volume": far_otm.get("volume", 0),
        })

        return results[:3]

    def _rank_sell_put_spread(self, chain: dict, _swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """Bull put spread strategies for ETF sell_put direction.
        Mirror of _rank_sell_call (bear call spread) — defined risk, delta-targeted legs.
        Short put: delta ~0.30 (slightly OTM below current price) — max credit
        Long put: delta ~0.15 (further OTM, lower strike) — limits max loss
        """
        pref = recommended_dte if recommended_dte else 30
        puts = self._best_expiry_contracts(chain, "P", pref)
        if not puts:
            return []
        current = float(chain.get("underlying_price", 0.0))

        # OTM puts: strike < current price (below underlying for put sellers)
        otm_puts = sorted([c for c in puts if _f(c.get("strike"), 0.0) < current],
                          key=lambda c: _f(c.get("strike"), 0.0), reverse=True)  # highest first
        if not otm_puts:
            return []  # no OTM puts in chain — ibkr_provider fix ensures this shouldn't happen

        # Short leg: delta ~0.30 (abs) — slightly OTM, collects most credit
        short_30 = self._closest_delta(otm_puts, 0.30)
        short_30_strike = _f(short_30.get("strike"), 0.0)

        # Protection leg: delta ~0.15 at a LOWER strike than the short leg
        below_short30 = [c for c in otm_puts if _f(c.get("strike"), 0.0) < short_30_strike]
        if below_short30:
            protection_15 = self._closest_delta(below_short30, 0.15)
        elif len(otm_puts) >= 2:
            sorted_otm = sorted(otm_puts, key=lambda c: _f(c.get("strike"), 0.0), reverse=True)
            short_30 = sorted_otm[0]   # highest OTM → sold leg (most credit)
            protection_15 = sorted_otm[1]  # lower strike → bought protection
            short_30_strike = _f(short_30.get("strike"), 0.0)
        else:
            protection_15 = short_30  # forces same-strike guard to skip spread

        short_20 = self._closest_delta(otm_puts, 0.20)

        results = []

        # Rank 1: Bull put spread (0.30 delta short, 0.15 delta long below)
        if short_30.get("strike") != protection_15.get("strike"):
            short_strike = _f(short_30.get("strike"), 0.0)
            long_strike = _f(protection_15.get("strike"), 0.0)
            if long_strike > short_strike:  # ensure long is the lower strike
                short_30, protection_15 = protection_15, short_30
                short_strike = _f(short_30.get("strike"), 0.0)
                long_strike = _f(protection_15.get("strike"), 0.0)
            short_p = _f(short_30.get("mid", short_30.get("last", 0.0)), 0.0)
            long_p = _f(protection_15.get("mid", protection_15.get("last", 0.0)), 0.0)
            net_credit = max(0.01, short_p - long_p)
            width = max(0.0, short_strike - long_strike)
            cw_ratio, cw_warn = _credit_width(net_credit, width)
            results.append({
                "rank": 1,
                "label": f"{int(short_strike)}/{int(long_strike)} Bull Put · {_fmt_exp(short_30['expiry'])}",
                "strategy_type": "bull_put_spread",
                "strike_display": f"{short_strike:.0f}/{long_strike:.0f}",
                "expiry_display": short_30["expiry"],
                "premium_per_lot": round(net_credit * 100, 2),
                "breakeven": round(short_strike - net_credit, 2),
                "delta": round(_f(short_30.get("delta"), 0.0) - _f(protection_15.get("delta"), 0.0), 3),
                "theta_per_day": round(_f(short_30.get("theta"), 0.0) - _f(protection_15.get("theta"), 0.0), 3),
                "vega": round(_f(short_30.get("vega"), 0.0) - _f(protection_15.get("vega"), 0.0), 3),
                "gamma": round(_f(short_30.get("gamma"), 0.0) - _f(protection_15.get("gamma"), 0.0), 3),
                "implied_vol": round(_f(short_30.get("impliedVol"), 0.0) * 100, 2),
                "max_gain_per_lot": round(net_credit * 100, 2),
                "max_loss_per_lot": round(max(0.0, (width - net_credit) * 100), 2),
                "spread_pct": _spread_pct(short_30),
                "credit_to_width_ratio": cw_ratio,
                "why": "Highest credit. Defined risk. Sell OTM put below support, buy lower protection. Profit if ETF holds above short strike.",
                "warning": cw_warn,
                "short_strike": short_strike,
                "long_strike": long_strike,
                "net_premium": net_credit,
                "strike": short_strike,
                "right": "P",
                "premium": net_credit,
                "expiry": short_30["expiry"],
                "dte": int(short_30.get("dte", 0)),
                "bid": short_30.get("bid"),
                "ask": short_30.get("ask"),
                "open_interest": short_30.get("openInterest", 0),
                "volume": short_30.get("volume", 0),
            })

        # Rank 2: Higher PoP bull put spread (0.20 delta short)
        if short_20.get("strike") != short_30.get("strike"):
            s20_strike = _f(short_20.get("strike"), 0.0)
            below_20 = [c for c in otm_puts if _f(c.get("strike"), 0.0) < s20_strike]
            prot_leg = self._closest_delta(below_20, 0.10) if below_20 else protection_15
            prot_strike = _f(prot_leg.get("strike"), 0.0)
            if prot_strike < s20_strike:
                short_p = _f(short_20.get("mid", short_20.get("last", 0.0)), 0.0)
                long_p = _f(prot_leg.get("mid", prot_leg.get("last", 0.0)), 0.0)
                net_credit = max(0.01, short_p - long_p)
                width = max(0.0, s20_strike - prot_strike)
                cw_ratio, cw_warn = _credit_width(net_credit, width)
                results.append({
                    "rank": len(results) + 1,
                    "label": f"{int(s20_strike)}/{int(prot_strike)} Bull Put · {_fmt_exp(short_20['expiry'])}",
                    "strategy_type": "bull_put_spread",
                    "strike_display": f"{s20_strike:.0f}/{prot_strike:.0f}",
                    "expiry_display": short_20["expiry"],
                    "premium_per_lot": round(net_credit * 100, 2),
                    "breakeven": round(s20_strike - net_credit, 2),
                    "delta": round(_f(short_20.get("delta"), 0.0) - _f(prot_leg.get("delta"), 0.0), 3),
                    "theta_per_day": round(_f(short_20.get("theta"), 0.0) - _f(prot_leg.get("theta"), 0.0), 3),
                    "vega": round(_f(short_20.get("vega"), 0.0) - _f(prot_leg.get("vega"), 0.0), 3),
                    "gamma": round(_f(short_20.get("gamma"), 0.0) - _f(prot_leg.get("gamma"), 0.0), 3),
                    "implied_vol": round(_f(short_20.get("impliedVol"), 0.0) * 100, 2),
                    "max_gain_per_lot": round(net_credit * 100, 2),
                    "max_loss_per_lot": round(max(0.0, (width - net_credit) * 100), 2),
                    "spread_pct": _spread_pct(short_20),
                    "credit_to_width_ratio": cw_ratio,
                    "why": "Higher probability of profit. Less credit but wider buffer before short strike is tested.",
                    "warning": cw_warn,
                    "short_strike": s20_strike,
                    "long_strike": prot_strike,
                    "net_premium": net_credit,
                    "strike": s20_strike,
                    "right": "P",
                    "premium": net_credit,
                    "expiry": short_20["expiry"],
                    "dte": int(short_20.get("dte", 0)),
                    "bid": short_20.get("bid"),
                    "ask": short_20.get("ask"),
                    "open_interest": short_20.get("openInterest", 0),
                    "volume": short_20.get("volume", 0),
                })

        # Rank 3: Far OTM single put (delta ~0.15, naked-style fallback with defined-risk note)
        far_otm = self._closest_delta(otm_puts, 0.15)
        far_strike = _f(far_otm.get("strike"), 0.0)
        far_p = _f(far_otm.get("mid", far_otm.get("last", 0.0)), 0.0)
        results.append({
            "rank": len(results) + 1,
            "label": f"Sell {int(far_strike)}P · {_fmt_exp(far_otm['expiry'])} ⚠️ FAR OTM",
            "strategy_type": "sell_put",
            "strike_display": f"{far_strike:.0f}P",
            "expiry_display": far_otm["expiry"],
            "premium_per_lot": round(far_p * 100, 2),
            "breakeven": round(far_strike - far_p, 2),
            "delta": round(_f(far_otm.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(far_otm.get("theta"), 0.0), 3),
            "vega": round(_f(far_otm.get("vega"), 0.0), 3),
            "gamma": round(_f(far_otm.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(far_otm.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": round(far_p * 100, 2),
            "max_loss_per_lot": None,
            "spread_pct": _spread_pct(far_otm),
            "why": "Highest probability of expiring worthless. Consider pairing with lower long put for defined risk.",
            "warning": "UNLIMITED RISK — pair with long put for defined risk",
            "strike": far_strike,
            "right": "P",
            "premium": far_p,
            "expiry": far_otm["expiry"],
            "dte": int(far_otm.get("dte", 0)),
            "bid": far_otm.get("bid"),
            "ask": far_otm.get("ask"),
            "open_interest": far_otm.get("openInterest", 0),
            "volume": far_otm.get("volume", 0),
        })

        return results[:3]

    def _rank_buy_put(self, chain: dict, swing_data: dict, recommended_dte: int | None) -> list[dict]:
        """ITM put / bear put spread strategies for buy_put direction."""
        pref = recommended_dte if recommended_dte else 60
        puts = self._best_expiry_contracts(chain, "P", pref)
        if not puts:
            return []
        current = float(chain.get("underlying_price", 0.0))

        # ITM put: delta ~-0.68 (abs delta ~0.68, strike above underlying)
        itm = self._closest_delta(puts, 0.68)
        # ATM put: delta ~-0.52
        atm = self._closest_delta(puts, 0.52)

        # Bear put spread short leg: delta ~0.30 (ETF-clean, no swing target dependency).
        # Stock mode only: use downside target1 if available and non-fabricated.
        target1_raw = swing_data.get("target1") if swing_data else None
        if (target1_raw is not None and swing_data.get("swing_data_quality") != "etf"
                and float(target1_raw) < current):
            # Stock mode: short leg at downside swing target
            short_leg = min(puts, key=lambda c: abs(_f(c.get("strike"), 0.0) - float(target1_raw)))
        else:
            # ETF mode: short leg at delta ~0.30 below current (OTM put, defined risk)
            otm_puts = [c for c in puts if _f(c.get("strike"), 0.0) < current]
            short_leg = self._closest_delta(otm_puts if otm_puts else puts, 0.30)

        itm_obj = self._build_long_put(rank=1,
                                       label=f"{int(_f(itm['strike'], 0.0))}P · {_fmt_exp(itm['expiry'])}",
                                       c=itm,
                                       why="Highest probability. Intrinsic value shields theta. Best for momentum breakdowns and confirmed downtrends.",
                                       warning=None)

        spread_obj = self._build_bear_put_spread(rank=2, long_leg=atm, short_leg=short_leg,
                                                  label=f"{int(_f(atm['strike'], 0.0))}/{int(_f(short_leg['strike'], 0.0))} Bear Put · {_fmt_exp(atm['expiry'])}")

        atm_obj = self._build_long_put(rank=3,
                                       label=f"{int(_f(atm['strike'], 0.0))}P · {_fmt_exp(atm['expiry'])} ⚠️ HIGH THETA",
                                       c=atm,
                                       why="Highest gamma. Best for explosive breakdowns only. Theta burns fastest — must move within 5 days.",
                                       warning="HIGH THETA")

        return [itm_obj, spread_obj, atm_obj]

    def _build_long_put(self, rank: int, label: str, c: dict, why: str, warning: str | None) -> dict:
        strike = _f(c.get("strike"), 0.0)
        premium = _f(c.get("mid", c.get("last", 0.0)), 0.0)
        expiry = c["expiry"]
        return {
            "rank": rank,
            "label": label,
            "strategy_type": "itm_put" if rank == 1 else "atm_put",
            "strike_display": f"{strike:.0f}P",
            "expiry_display": expiry,
            "premium_per_lot": round(premium * 100, 2),
            "breakeven": round(strike - premium, 2),
            "delta": round(_f(c.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(c.get("theta"), 0.0), 3),
            "vega": round(_f(c.get("vega"), 0.0), 3),
            "gamma": round(_f(c.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(c.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": None,  # theoretically strike × 100 - premium
            "max_loss_per_lot": round(premium * 100, 2),
            "spread_pct": _spread_pct(c),
            "why": why,
            "warning": warning,
            "strike": strike,
            "right": c.get("right"),
            "premium": premium,
            "expiry": expiry,
            "dte": int(c.get("dte", 0)),
            "bid": c.get("bid"),
            "ask": c.get("ask"),
            "open_interest": c.get("openInterest", 0),
            "volume": c.get("volume", 0),
        }

    def _build_bear_put_spread(self, rank: int, long_leg: dict, short_leg: dict, label: str) -> dict:
        long_strike = _f(long_leg.get("strike"), 0.0)
        short_strike = _f(short_leg.get("strike"), 0.0)
        # Long leg must have higher strike than short leg for a bear put spread
        if long_strike < short_strike:
            long_leg, short_leg = short_leg, long_leg
            long_strike = _f(long_leg.get("strike"), 0.0)
            short_strike = _f(short_leg.get("strike"), 0.0)
        if long_strike == short_strike:
            # Can't form a spread with same strikes — fall back to single long put
            return self._build_long_put(rank=rank, label=label, c=long_leg,
                                        why="Spread legs same strike — single long put. Lowest cost. Short strike caps at Target 1.",
                                        warning=None)

        long_p = _f(long_leg.get("mid", long_leg.get("last", 0.0)), 0.0)
        short_p = _f(short_leg.get("mid", short_leg.get("last", 0.0)), 0.0)
        net = max(0.01, long_p - short_p)
        width = max(0.0, long_strike - short_strike)

        return {
            "rank": rank,
            "label": label,
            "strategy_type": "spread",
            "strike_display": f"{long_strike:.0f}/{short_strike:.0f}",
            "expiry_display": long_leg["expiry"],
            "premium_per_lot": round(net * 100, 2),
            "breakeven": round(long_strike - net, 2),
            "delta": round(_f(long_leg.get("delta"), 0.0) - _f(short_leg.get("delta"), 0.0), 3),
            "theta_per_day": round(_f(long_leg.get("theta"), 0.0) - _f(short_leg.get("theta"), 0.0), 3),
            "vega": round(_f(long_leg.get("vega"), 0.0) - _f(short_leg.get("vega"), 0.0), 3),
            "gamma": round(_f(long_leg.get("gamma"), 0.0) - _f(short_leg.get("gamma"), 0.0), 3),
            "implied_vol": round(_f(long_leg.get("impliedVol"), 0.0) * 100, 2),
            "max_gain_per_lot": round(max(0.0, (width - net) * 100), 2),
            "max_loss_per_lot": round(net * 100, 2),
            "spread_pct": _spread_pct(long_leg),
            "why": "Lowest cost. Short strike caps at Target 1. Best % return to T1. Lower theta burn for slower breakdowns.",
            "warning": None,
            "long_strike": long_strike,
            "short_strike": short_strike,
            "net_premium": net,
            "expiry": long_leg["expiry"],
            "dte": int(long_leg.get("dte", 0)),
            "premium": net,
            "strike": long_strike,
            "right": long_leg.get("right"),
            "bid": long_leg.get("bid"),
            "ask": long_leg.get("ask"),
            "open_interest": long_leg.get("openInterest", 0),
            "volume": long_leg.get("volume", 0),
        }

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
            "right": c.get("right"),
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
            "right": long_leg.get("right"),
            "bid": long_leg.get("bid"),
            "ask": long_leg.get("ask"),
            "open_interest": long_leg.get("openInterest", 0),
            "volume": long_leg.get("volume", 0),
        }

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
                # ETF mode: target delta ~0.15–0.30 OTM puts (no fabricated support filter)
                if strike >= current:
                    continue  # skip ITM puts for sell_put
            else:
                # Stock mode: strike must be below s1_support
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
                    "warning": "NAKED PUT — max loss = strike × 100. Cash-secured margin required.",
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
