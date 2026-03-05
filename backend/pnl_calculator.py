from __future__ import annotations

from typing import Any


def _stock_move_pct(stock_price: float, current_price: float) -> float:
    if current_price <= 0:
        return 0.0
    return ((stock_price / current_price) - 1.0) * 100.0


def _fmt(v: float) -> float:
    return round(float(v), 2)


class PnLCalculator:
    def calculate(
        self,
        current_price: float,
        swing_data: dict,
        strategies: list[dict],
        account_size: float,
        risk_pct: float,
        gate8_passed: bool,
    ) -> dict[str, Any]:
        scenarios = [
            ("Stop Loss 🔴", float(swing_data.get("stop_loss", current_price))),
            ("Sideways / -4%", current_price * 0.96),
            ("Current Price", current_price),
            ("VCP Pivot ⚡", float(swing_data.get("vcp_pivot", current_price))),
            ("Target 1 ✅", float(swing_data.get("target1", current_price))),
            ("Target 2 🎯", float(swing_data.get("target2", current_price))),
        ]

        rows = []
        for label, stock_price in scenarios:
            row = {
                "scenario_label": label,
                "stock_price": _fmt(stock_price),
                "stock_move_pct": _fmt(_stock_move_pct(stock_price, current_price)),
            }
            for idx in range(3):
                key_pnl = f"pnl_c{idx + 1}"
                key_pct = f"pnl_pct_c{idx + 1}"
                if idx >= len(strategies) or not gate8_passed:
                    row[key_pnl] = "--"
                    row[key_pct] = "--"
                    continue
                s = strategies[idx]
                pnl = self._scenario_pnl(stock_price, s)
                denom = max(1e-9, float(s.get("premium_per_lot", 0.0)))
                row[key_pnl] = _fmt(pnl)
                row[key_pct] = _fmt((pnl / denom) * 100.0)
            rows.append(row)

        max_risk = float(account_size) * float(risk_pct)
        footer = {
            "breakevens": [_fmt(s.get("breakeven", 0.0)) for s in strategies[:3]],
            "theta_burns_7d": [_fmt(abs(float(s.get("theta_per_day", 0.0))) * 7 * 100) for s in strategies[:3]],
            "max_losses": [_fmt(s.get("max_loss_per_lot", 0.0)) for s in strategies[:3]],
            "lots_at_1pct": [
                _fmt((max_risk / float(s.get("premium_per_lot", 1e-9))) if float(s.get("premium_per_lot", 0.0)) > 0 else 0)
                for s in strategies[:3]
            ],
        }

        return {"scenarios": rows, "footer": footer}

    def _scenario_pnl(self, scenario_price: float, strategy: dict) -> float:
        st = strategy.get("strategy_type")
        if st in {"itm_call", "atm_call"}:
            strike = float(strategy["strike"])
            premium = float(strategy["premium"])
            return (max(0.0, scenario_price - strike) - premium) * 100

        if st == "spread":
            long_strike = float(strategy["long_strike"])
            short_strike = float(strategy["short_strike"])
            net_premium = float(strategy["net_premium"])
            intrinsic = min(max(0.0, scenario_price - long_strike), short_strike - long_strike)
            return (intrinsic - net_premium) * 100

        if st == "sell_put":
            strike = float(strategy["strike"])
            premium = float(strategy["premium"])
            return (premium - max(0.0, strike - scenario_price)) * 100

        return 0.0
