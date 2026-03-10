# OptionsIQ — API Contracts
> **Last Updated:** Day 5 (March 10, 2026)
> **Backend base URL:** http://localhost:5051

---

## GET /api/health

Returns connection status of all subsystems.

**Response:**
```json
{
  "status": "ok",
  "ibkr_connected": true,
  "ibkr_error": null,
  "circuit_breaker": {
    "open": false,
    "failures": 0,
    "open_until": null,
    "seconds_remaining": 0.0
  },
  "mock_mode": false,
  "version": "2.0"
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
  "chain_profile": "smart" | "full",
  "account_size": 25000,
  "risk_pct": 0.01,
  "planned_hold_days": 7,
  "min_dte": 14,

  // Swing fields (from STA or manual entry — all optional, defaults computed from underlying)
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
  "fomc_days_away": 21,
  "lots": 1.0
}
```
**Note:** Empty strings `""` are treated as missing (same as omitting the field).

**Response:**
```json
{
  "ticker": "AMD",
  "direction": "buy_call",
  "track": "A",
  "underlying_price": 198.53,
  "data_source": "ibkr_live" | "ibkr_closed" | "ibkr_cache" | "ibkr_stale" | "yfinance" | "mock",
  "chain_profile": "smart",
  "min_dte": 14,
  "quality": "live" | "closed" | "cached" | "stale" | "yfinance" | "degraded" | "partial" | "mock",
  "chain_quality": {
    "contracts": 8,
    "core_complete_pct": 100.0,
    "greeks_complete_pct": 87.5,
    "quote_complete_pct": 0.0
  },
  "ibkr_connected": true,
  "timestamp": "2026-03-06T11:30:00",
  "swing_data": { ... },
  "verdict": {
    "color": "green" | "amber" | "red",
    "score_label": "GO",
    "headline": "Strong setup — IV cheap, momentum confirmed",
    "pass": 7,
    "warn": 1,
    "fail": 1,
    "total": 9
  },
  "gates": [
    {
      "id": "ivr_check",
      "name": "IV Rank",
      "status": "pass" | "warn" | "fail",
      "value": "22.4%",
      "detail": "IVR 22.4 — cheap IV, good time to buy"
    }
  ],
  "behavioral_checks": [
    {
      "id": "gate8_block",
      "type": "hard_block" | "warning" | "info",
      "label": "Hard Block: Pivot Not Confirmed",
      "message": "..."
    }
  ],
  "top_strategies": [
    {
      "rank": 1,
      "label": "ITM Call — delta 0.68",
      "strategy_type": "itm_call",
      "strike": 180.0,
      "expiry": "2026-04-24",
      "dte": 49,
      "premium": 14.20,
      "delta": 0.731,
      "theta": -0.12,
      "vega": 0.18,
      "iv": 0.38
    }
  ],
  "pnl_table": { ... },
  "ivr_data": {
    "current_iv": 56.87,
    "ivr_pct": 60.61,
    "hv_20": 58.56,
    "hv_iv_ratio": 0.97,
    "history_days": 231,
    "fallback_used": false
  },
  "put_call_ratio": 0.85,
  "max_pain_strike": 195.0,
  "recommended_dte": 49,
  "direction_locked": []
}
```

---

## GET /api/options/chain/{ticker}

Debug endpoint — returns raw chain data for a ticker.

**Query params:** `chain_profile=smart|full`, `min_dte=14`, `direction=buy_call|...`, `target_price=float`

**Response:** chain dict with `ibkr_connected`, `data_source`, `contracts[]`

---

## GET /api/options/ivr/{ticker}

Debug endpoint — returns IV/HV data for a ticker.

**Response:** same structure as `ivr_data` in analyze response.

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
  "message": "STA not reachable at http://localhost:5001 — use Manual mode"
}
```

---

## GET /api/integrate/ping

Health check for STA integration.

**Response:** `{"status": "ok", "version": "2.0", "accepts_swing_data": true}`

---

## POST /api/integrate/status

**Response:** `{"status": "ready", "accepts_swing_data": true, "version": "2.0"}`

---

## GET /api/integrate/schema

Returns expected field names and types for the POST /api/options/analyze body.

---

## POST /api/options/paper-trade

Record a new paper trade.

**Request body:**
```json
{
  "ticker": "AMD",
  "direction": "buy_call",
  "strategy_rank": 1,
  "strike": 180.0,
  "expiry": "2026-04-24",
  "premium": 14.20,
  "lots": 1.0,
  "account_size": 25000
}
```

**Response:** `{"success": true, "trade_id": 1}`

---

## GET /api/options/paper-trades

Returns all recorded paper trades with mark-to-market P&L.

**Response:** Array of trade objects with `current_underlying` and `mark_to_market_pnl`.

---

## POST /api/options/seed-iv/{ticker}

Seeds IV history for a ticker from IBKR (or mock fallback).

**Response:** `{"seeded_days": 231, "earliest_date": "2025-03-05", "latest_date": "2026-03-05"}`

---

## STA Endpoints Used (Read-Only, No Modifications)

> **Updated Day 5:** STA API uses camelCase top-level fields — no nested `levels` object.
> `spy_above_200sma` and `spy_5day_return` are NOT in STA — computed from yfinance SPY.

| Field | STA Endpoint | Actual Response Key |
|-------|-------------|---------------------|
| entry_pullback | GET localhost:5001/api/sr/{ticker} | `suggestedEntry` (top-level) |
| stop_loss | GET localhost:5001/api/sr/{ticker} | `suggestedStop` (top-level) |
| target1 | GET localhost:5001/api/sr/{ticker} | `suggestedTarget` (top-level) |
| risk_reward | GET localhost:5001/api/sr/{ticker} | `riskReward` (top-level) |
| s1_support | GET localhost:5001/api/sr/{ticker} | `support[-1]` (last/nearest support level) |
| adx | GET localhost:5001/api/sr/{ticker} | `meta.adx.adx` |
| swing_signal | GET localhost:5001/api/sr/{ticker} | derived: `meta.tradeViability.viable == "YES"` → "BUY" else "SELL" |
| last_close / entry_momentum | GET localhost:5001/api/stock/{ticker} | `currentPrice` |
| vcp_confidence | GET localhost:5001/api/patterns/{ticker} | `patterns.vcp.confidence` |
| vcp_pivot | GET localhost:5001/api/patterns/{ticker} | `patterns.vcp.pivot_price` |
| pattern | GET localhost:5001/api/patterns/{ticker} | `pattern` (top-level, may be null) |
| fomc_days_away | GET localhost:5001/api/context/SPY | `cycles.cards[name="FOMC Proximity"].raw_value` |
| earnings_days_away | GET localhost:5001/api/earnings/{ticker} | `days_until` (NOT `days_away`) |
| spy_above_200sma | yfinance SPY (computed in backend) | SPY close > 200-day SMA |
| spy_5day_return | yfinance SPY (computed in backend) | (close[-1] - close[-6]) / close[-6] × 100 |
