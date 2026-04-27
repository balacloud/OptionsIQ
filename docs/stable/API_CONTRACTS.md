# OptionsIQ — API Contracts
> **Last Updated:** Day 29 (April 27, 2026)
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
  "data_source": "ibkr_live" | "ibkr_closed" | "ibkr_cache" | "ibkr_stale" | "alpaca" | "yfinance" | "mock",
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

**ETF-only enforcement:** Non-ETF tickers return HTTP 400 `{"error": "XYZ is not in the ETF universe", "etf_universe": [...]}`.

**OI/Volume source:** `open_interest` and `volume` in strategies are supplemented from MarketData.app REST API when available. Falls back to 0 if MarketData.app times out or is unreachable. IBKR `reqMktData` does not return per-contract OI (platform limitation KI-035).

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

Seeds IV history for a single ticker from IBKR (yfinance fallback if disconnected).

**Response:**
```json
{
  "ticker": "XLK",
  "seeded_days": 365,
  "source": "ibkr" | "yfinance" | "none",
  "earliest_date": "2024-11-01",
  "latest_date": "2026-04-20"
}
```

---

## POST /api/admin/seed-iv/all

Batch IV seeding for all 16 ETFs. Designed for nightly cron or manual trigger from UI.
Uses IBKR `reqHistoricalData(OPTION_IMPLIED_VOLATILITY)` per ticker, yfinance fallback.
2s pacing delay between tickers to stay within IBKR historical data rate limits.

**Response:**
```json
{
  "tickers_seeded": 16,
  "total_iv_rows": 5840,
  "sources_used": ["ibkr"],
  "pacing_warning": false,
  "errors": [],
  "results": [
    {
      "ticker": "XLK",
      "seeded_days": 365,
      "source": "ibkr",
      "earliest_date": "2024-11-01",
      "latest_date": "2026-04-20"
    }
  ]
}
```

**`pacing_warning: true`** means IBKR returned 0 rows for all tickers — hit the ~60 req/10min historical data limit. Wait ~10 min and retry. Existing IV data is intact (upsert, never deletes).

**`sources_used`** lists which providers actually returned data: `["ibkr"]`, `["yfinance"]`, or `["ibkr", "yfinance"]` (mixed).

---

## GET /api/sectors/scan

Level 1: All sector ETFs with quadrant, direction, action. Consumes STA `/api/sectors/rotation`.

**Response:**
```json
{
  "sectors": [
    {
      "etf": "XLK",
      "name": "Technology",
      "rank": 1,
      "rs_ratio": 105.2,
      "rs_momentum": 1.3,
      "quadrant": "Leading",
      "price": 215.40,
      "week_change": 2.1,
      "month_change": 5.8,
      "suggested_direction": "buy_call",
      "action": "ANALYZE",
      "catalyst_warnings": []
    }
  ],
  "sector_count": 16,
  "size_signal": "Risk-On",
  "size_bias": "Cyclicals favored (XLI, XLY, XLB)",
  "spy_regime": {
    "spy_above_200sma": true,
    "spy_5day_return": 0.85,
    "regime_warning": null
  },
  "market_regime": "NORMAL",
  "timestamp": "2026-03-20T15:30:00+00:00",
  "sta_status": "ok"
}
```

**Error (STA offline):** 503 `{"error": "STA not reachable at ..."}`

---

## GET /api/sectors/analyze/{ticker}

Level 2: Single ETF + IV/OI/spread overlay from IBKR chain.

**Path param:** `ticker` — must be in ETF_TICKERS (15 tickers + TQQQ)

**Response:**
```json
{
  "etf": "XLK",
  "name": "Technology",
  "quadrant": "Leading",
  "price": 215.40,
  "rs_ratio": 105.2,
  "rs_momentum": 1.3,
  "suggested_direction": "bull_call_spread",
  "action": "ANALYZE",
  "iv_current": 22.5,
  "iv_percentile": 45,
  "hv_20": 18.3,
  "suggested_dte": 30,
  "atm_bid": 3.20,
  "atm_ask": 3.45,
  "atm_spread_pct": 7.69,
  "atm_oi": 12500,
  "atm_volume": 3200,
  "catalyst_warnings": [],
  "ivr_bear_warning": null,
  "data_source": "ibkr_live",
  "level": 2,
  "note": "L3 deep dive: POST /api/options/analyze with ticker and suggested_direction"
}
```

**Error (invalid ticker):** 400 `{"error": "XYZ is not in the sector ETF universe"}`
**Error (STA offline):** 503 `{"error": "STA not reachable at ..."}`

**Dependencies:** `data_service` (chain fetch), `iv_store` (IVR + HV20). IVR requires seeded IV history (≥30 days).

---

## STA Endpoints Used (Read-Only, No Modifications)

> **Updated Day 5:** STA API uses camelCase top-level fields — no nested `levels` object.
> **Updated Day 16:** `spy_above_200sma` and `spy_5day_return` computed from STA `/api/stock/SPY` `priceHistory` (Day 16 — replaced yfinance to avoid rate limiting).

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
| spy_above_200sma | GET localhost:5001/api/stock/SPY | `priceHistory[-1].close > mean(priceHistory[-200:].close)` |
| spy_5day_return | GET localhost:5001/api/stock/SPY | `(priceHistory[-1].close - priceHistory[-6].close) / priceHistory[-6].close × 100` |

---

## GET /api/best-setups

Scans all ETFs using their sector-suggested direction in parallel (max 6 workers). Returns GO/CAUTION setups ranked by gate pass rate.

**Response:**
```json
{
  "as_of": "2026-04-27T20:00:00Z",
  "candidates_scanned": 8,
  "setups": [...],
  "all_results": [
    {
      "ticker": "XLK",
      "direction": "sell_put",
      "quadrant": "Leading",
      "name": "Tech",
      "verdict_color": "green",
      "verdict_label": "GO",
      "pass_rate": 90,
      "gates_passed": 9,
      "gates_total": 10,
      "failed_gates": [],
      "ivr": 85.2,
      "premium": 1.45,
      "premium_per_lot": 145.0,
      "strike_display": "$185 / $180",
      "expiry_display": "May 16",
      "credit_to_width_ratio": 0.38,
      "strategy_type": "bull_put_spread",
      "vix": 19.4,
      "error": null
    }
  ]
}
```

---

## GET /api/data-health

Full data provenance report — source status, IV history per ETF, chain cache per ETF, field-level source resolution. No IBKR calls; reads cached/DB state only. Fast (<200ms).

**Response:**
```json
{
  "as_of": "2026-04-27T20:17:06+00:00",
  "sources": {
    "ibkr": {
      "status": "connected|disconnected",
      "connected": false,
      "mode": "live|mock",
      "error": null,
      "circuit_breaker": { "open": false, "failures": 0, "seconds_remaining": 0 }
    },
    "vix": { "status": "ok|stale|null", "value": 19.4, "source": "yfinance_intraday", "age_seconds": 120 },
    "spy_regime": { "status": "ok|null|error", "above_200sma": true, "five_day_return": 0.73, "source": "sta" },
    "fomc": { "status": "ok", "next_date": "2026-04-29", "days_away": 2, "source": "constants" },
    "alpaca": { "status": "ok|unavailable" },
    "marketdata_app": { "status": "ok|unavailable" }
  },
  "iv_history": {
    "XLK": {
      "rows": 390, "first_date": "2024-10-04", "last_date": "2026-04-27",
      "status": "ok|sparse|empty", "hv_20": 23.0, "hv_status": "ok|insufficient_bars|no_ohlcv",
      "ohlcv_rows": 80
    }
  },
  "chain_cache": {
    "XLK": {
      "status": "fresh|stale|missing",
      "saved_at": "2026-04-27T17:23:32",
      "age_minutes": 5.2,
      "expires_in_minutes": 0.0,
      "entries": 6
    }
  },
  "field_resolution": {
    "XLK": {
      "chain_implied_vol": { "source": "ibkr_stale → yfinance", "status": "stale", "note": "IBKR stale 185m — yfinance on next analyze" },
      "oi_volume":         { "source": "MarketData.app", "status": "ok", "note": "REST supplement" },
      "hv_20":             { "source": "ohlcv_db (80 bars)", "status": "ok", "note": "22.68% annualised" },
      "ivr":               { "source": "iv_history_db (390 rows)", "status": "ok", "note": "percentile rank — requires current_iv from chain" },
      "vix":               { "source": "unavailable", "status": "null", "note": "not yet fetched this session" },
      "spy_regime":        { "source": "sta", "status": "ok", "note": "above_200sma=True, 5d=0.73%" },
      "fomc":              { "source": "constants", "status": "warn", "note": "2 days to next meeting (2026-04-29)" }
    }
  }
}
```
