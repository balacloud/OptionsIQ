# OptionsIQ — API Contracts
> **Last Updated:** Day 1 (March 5, 2026)
> **Backend base URL:** http://localhost:5051

---

## GET /api/health

Returns connection status of all subsystems.

**Response:**
```json
{
  "status": "ok",
  "ibkr": "connected" | "offline" | "error",
  "data_tier": "live" | "cached" | "yfinance" | "mock",
  "ib_worker": "running" | "stopped",
  "version": "1.0.0"
}
```

---

## POST /api/options/analyze

Main analysis endpoint. Takes swing data + direction, returns gates + strategies + P&L.

**Request body:**
```json
{
  "ticker": "AMD",
  "direction": "buy_call" | "sell_call" | "buy_put" | "sell_put",

  // Swing fields (from STA or manual entry)
  "swing_signal": "BUY" | "SELL",
  "entry_pullback": 204.15,
  "entry_momentum": 234.35,
  "stop_loss": 192.93,
  "target1": 254.62,
  "target2": 278.36,
  "risk_reward": 4.5,
  "vcp_pivot": 242.05,
  "vcp_confidence": 70,
  "adx": 40.2,
  "last_close": 234.35,
  "s1_support": 225.8,
  "spy_above_200sma": true,
  "spy_5day_return": 0.008,
  "earnings_days_away": 45,
  "pattern": "VCP",
  "fomc_days_away": 21
}
```

**Response:**
```json
{
  "ticker": "AMD",
  "direction": "buy_call",
  "data_quality": "live" | "cached" | "yfinance" | "mock",
  "verdict": {
    "overall": "GO" | "CAUTION" | "NO_GO",
    "gates_passed": 7,
    "gates_total": 9,
    "hard_block": false
  },
  "gates": [
    {
      "id": "ivr_check",
      "label": "IV Rank < 30%",
      "status": "pass" | "warn" | "fail",
      "value": "22.4%",
      "detail": "IVR 22.4 — cheap IV, good time to buy"
    }
  ],
  "behavioral_checks": [],
  "top_strategies": [
    {
      "rank": 1,
      "label": "ITM Call — delta 0.68",
      "strategy_type": "itm_call",
      "strike": 225.0,
      "expiry": "2026-04-17",
      "dte": 43,
      "premium": 14.20,
      "delta": 0.68,
      "theta": -0.12,
      "vega": 0.18,
      "iv": 0.38,
      "breakeven": 239.20,
      "max_loss_per_lot": 1420.0,
      "premium_per_lot": 1420.0,
      "lots_at_1pct": 1.76,
      "data_source": "ibkr_live"
    }
  ],
  "pnl_table": {
    "scenarios": [...],
    "footer": {...}
  }
}
```

---

## GET /api/integrate/sta-fetch/{ticker}

Calls STA at localhost:5001 and assembles swing fields for the given ticker.

**Response (STA connected):**
```json
{
  "status": "ok",
  "source": "sta_live",
  "ticker": "AMD",
  "swing_signal": "BUY",
  "entry_pullback": 204.15,
  "entry_momentum": 234.35,
  "stop_loss": 192.93,
  "target1": 254.62,
  "target2": 278.36,
  "risk_reward": 4.5,
  "vcp_pivot": 242.05,
  "vcp_confidence": 70,
  "adx": 40.2,
  "last_close": 234.35,
  "s1_support": 225.8,
  "spy_above_200sma": true,
  "spy_5day_return": 0.008,
  "earnings_days_away": 45,
  "pattern": "VCP",
  "fomc_days_away": 21
}
```

**Response (STA offline):**
```json
{
  "status": "offline",
  "source": "manual",
  "message": "STA not reachable at localhost:5001 — use Manual mode"
}
```

---

## GET /api/paper-trades

Returns all recorded paper trades, newest first.

**Response:**
```json
{
  "trades": [
    {
      "id": 1,
      "ticker": "AMD",
      "direction": "buy_call",
      "strategy_rank": 1,
      "strike": 225.0,
      "expiry": "2026-04-17",
      "premium": 14.20,
      "lots": 1.0,
      "account_size": 25000,
      "entry_price": 14.20,
      "mark_price": 16.45,
      "unrealized_pnl": 225.0,
      "data_quality": "live",
      "created_at": "2026-03-05T10:30:00"
    }
  ]
}
```

---

## POST /api/paper-trades

Record a new paper trade.

**Request body:**
```json
{
  "ticker": "AMD",
  "direction": "buy_call",
  "strategy_rank": 1,
  "strike": 225.0,
  "expiry": "2026-04-17",
  "premium": 14.20,
  "lots": 1.0,
  "account_size": 25000
}
```

**Response:**
```json
{
  "id": 1,
  "status": "recorded"
}
```

---

## STA Endpoints Used (Read-Only, No Modifications)

| Field | STA Endpoint | Response Key |
|-------|-------------|-------------|
| stop_loss, target1, target2, s1_support | GET localhost:5001/api/sr/{ticker} | levels |
| adx, last_close, swing_signal, spy_above_200sma, spy_5day_return | GET localhost:5001/api/stock/{ticker} | various |
| vcp_confidence, vcp_pivot, pattern | GET localhost:5001/api/patterns/{ticker} | vcp.* |
| fomc_days_away | GET localhost:5001/api/context/SPY | cycles.fomc_days |
| earnings_days_away | GET localhost:5001/api/earnings/{ticker} | days_away |
