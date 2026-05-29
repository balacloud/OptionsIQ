# IBKR Data Sources Reference — OptionsIQ
> **Last updated:** Day 56 (May 28, 2026)
> **Purpose:** Permanent reference for all IBKR data available to OptionsIQ. Do not re-explain to Claude.

---

## 1. IBKR MCP Connection (Claude.ai)

Connected via IBKR MCP to Claude.ai (not Claude Code CLI). Authenticated.

### What It Can Do

| Capability | Detail |
|------------|--------|
| Account summary | Net liq, buying power, margin, leverage |
| Cash balances | CAD/USD breakdown |
| Open positions | Cost basis, P&L live |
| Live/pending orders | View current orders |
| Saved order instructions | View saved orders |
| Real-time price snapshot | Bid/ask, last price, volume, IV, Greeks for options |
| Historical OHLCV bars | Any timeframe: 30 seconds → monthly |
| IV percentile | 52-week IV percentile, historical vol |
| Performance data | YTD, cumulative returns (1d/1w/1m/1y/3y/5y) |
| Dividend yield | Yes |
| 52-week high/low | Yes |
| Contract search | Stocks, ETFs, options, futures, crypto, bonds |
| Create order instructions | Market or limit, buy/sell, DAY/GTC (requires user confirmation in IBKR — does NOT place directly) |
| Delete order instructions | Yes |

### What It Cannot Do (Yet)

| Limitation | Workaround |
|------------|-----------|
| Place orders directly | Creates instructions → user confirms in IBKR |
| Options chain browsing | Use Tradier REST API |
| Account history / transaction history | N/A |
| Alerts or watchlists | Use IBKR web UI |
| Put/Call Volume ratio | IBKR watchlist screenshot |
| Opt Volume Change % | IBKR watchlist screenshot |

### Architecture Impact

MCP covers 6 of 9 watchlist columns directly:
- ✅ IV percentile (52wk IV Rank + Pctl)
- ✅ IV/HV ratio (derivable from IV + historical vol)
- ✅ Opt Implied Volatility %
- ✅ Price/EMA(200) + Price/EMA(50) (compute from historical OHLCV)
- ⚠️ Opt Imp Vol Change (derivable — two snapshots 30 min apart)
- ❌ Put/Call Volume — still needs watchlist screenshot
- ❌ Opt Volume Change % — still needs watchlist screenshot

---

## 2. IBKR Watchlist — Available Columns

### Options Category (full list)

| Column Name | Description |
|-------------|-------------|
| **13wk IV High** | Maximum intraday value of implied volatility over the last 13 weeks |
| **13wk IV Low** | Minimum intraday value of implied volatility over the last 13 weeks |
| **13wk IV Pctl** | % of days with IV closing below current IV (13-week window) |
| **13wk IV Rank** | Rank of current IV between 13-week intraday high and low |
| **26wk IV High** | Maximum intraday value of implied volatility over the last 26 weeks |
| **26wk IV Low** | Minimum intraday value of implied volatility over the last 26 weeks |
| **26wk IV Pctl** | % of days with IV closing below current IV (26-week window) |
| **26wk IV Rank** | Rank of current IV between 26-week intraday high and low |
| **52wk IV High** | Maximum intraday value of implied volatility over the last 52 weeks |
| **52wk IV Low** | Minimum intraday value of implied volatility over the last 52 weeks |
| **52wk IV Pctl** | % of days with IV closing below current IV (52-week window) — most robust |
| **52wk IV Rank** | Rank of current IV between 52-week intraday high and low |
| **Closing Impl Vol %** | Implied volatility of the option on closing price |
| **Hist Vol Close %** | Historical volatility based on previous close price |
| **Implied Vol %** | Implied volatility of the option (intraday) |
| **Implied Vol/Hist Vol %** | IV ÷ HV ratio expressed as percentage — core VRP signal |
| **In The Money** | Current in-the-money value for an option contract |
| **Opt Imp Vol Change** | Absolute change in IV between current value and yesterday's value |
| **Opt Implied Volatility %** | Option implied volatility (use this, not "Implied Vol %") |
| **Opt Volume** | Option volume (total contracts today) |
| **Opt Volume Change %** | Today's option volume as % of average option volume |
| **Option Open Interest** | Option open interest |
| **Put/Call Interest** | Put OI ÷ call OI for the trading day |
| **Put/Call Volume** | Put volume ÷ call volume for the trading day |
| **Time Value (%)** | Option premium in excess of intrinsic value |
| **Underlying Price** | Current price of the underlying (for derivatives) |

### Technical Indicator Category (full list)

| Column Name | Description |
|-------------|-------------|
| **EMA(20)** | Exponential moving average, N=20 (absolute value) |
| **EMA(50)** | Exponential moving average, N=50 (absolute value) |
| **EMA(100)** | Exponential moving average, N=100 (absolute value) |
| **EMA(200)** | Exponential moving average, N=200 (absolute value) |
| **Price/EMA(20)** | (Price ÷ EMA(20) − 1) × 100, displayed as % |
| **Price/EMA(50)** | (Price ÷ EMA(50) − 1) × 100, displayed as % |
| **Price/EMA(100)** | (Price ÷ EMA(100) − 1) × 100, displayed as % |
| **Price/EMA(200)** | (Price ÷ EMA(200) − 1) × 100, displayed as % |

---

## 3. Current Watchlist Configuration (Options_IQ_Claude)

**Watchlist name:** Options_IQ_Claude
**Tickers:** SPY (regime anchor), QQQ, IWM, XLF, TQQQ, GLD

### Active 9 Columns

| # | Column (IBKR exact name) | Category | Role |
|---|--------------------------|----------|------|
| 1 | 52wk IV Rank | Options | Historical vol elevation (threshold: ≥ 35) |
| 2 | 52 IV PERC. (52wk IV Pctl) | Options | Spike-adjusted rank (threshold: ≥ 45%) |
| 3 | Implied Vol./Hist. Vol % | Options | VRP signal — core sell trigger (threshold: ≥ 110%) |
| 4 | Opt. Implied Volatility % | Options | Absolute IV level — margin/sizing context |
| 5 | Opt. Imp. Vol. Change | Options | IV direction: ≤ 0 = sell window, > +1.0 = wait |
| 6 | Opt. Volume Change % | Options | Unusual activity flag (> 200% = hidden catalyst) |
| 7 | Put/Call Volume | Options | Sentiment extreme: > 1.5 = wait, < 0.5 = complacency |
| 8 | Price/EMA(200) | Technical Indicator | Regime gate — hard block if negative |
| 9 | Price/EMA(50) | Technical Indicator | Pullback detector — reduce delta if negative |

Full decision thresholds: see `docs/stable/IBKR_WATCHLIST_SETUP.md`

---

## 4. Data Source Decision Matrix

| Data Need | Source | Notes |
|-----------|--------|-------|
| IV Rank / IV Percentile | IBKR watchlist OR MCP | Watchlist = visual. MCP = programmatic. |
| IV/HV ratio | IBKR watchlist | Most reliable — IBKR computes directly |
| Current IV % | IBKR watchlist OR MCP | Both work |
| Price/EMA trend | IBKR watchlist OR MCP | MCP needs OHLCV + EMA computation |
| Put/Call Volume | IBKR watchlist only | MCP cannot provide this |
| Opt Volume Change % | IBKR watchlist only | MCP cannot provide this |
| Opt Imp Vol Change | IBKR watchlist (direct) | MCP: derivable from two snapshots |
| Options chain (strikes/deltas/premiums) | **Tradier REST API** | MCP cannot browse options chains |
| Account net liq / buying power | **IBKR MCP** | Not in watchlist |
| Open positions + P&L | **IBKR MCP** | Not in watchlist |
| Historical OHLCV | **IBKR MCP** | Can compute any EMA/SMA from this |
