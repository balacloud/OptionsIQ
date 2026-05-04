# OptionsIQ — Data Providers: Complete Decision Record
> **Last updated:** Day 37 (May 4, 2026)
> **Status:** FINAL — stack locked. No further provider evaluation needed.
> **Sources:** Day 10 live tests + Day 26 strategy + Day 34 research prompt + Day 37 live API tests

---

## The Fundamental Problem

IVR (IV Rank) percentile requires 252 days of **implied volatility** history per ETF — one scalar per
trading day representing the underlying's 30-day ATM IV. No provider under $30/mo provides this as a
pre-computed daily series except IBKR via `reqHistoricalData(whatToShow="OPTION_IMPLIED_VOLATILITY")`.

This is the constraint that drove every provider decision.

---

## FINAL STACK (locked Day 37)

```
Live chain + greeks:   IBKR IB Gateway (primary) → Alpaca (fallback) → yfinance (emergency)
OI / volume:           MarketData.app Starter $12/mo (supplements Alpaca which has no OI)
Spot IV supplement:    MarketData.app (accumulated into iv_history.db on every analyze_etf() call)
Historical IV (IVR):   IBKR only — nightly EOD batch via batch_service.py (free, already running)
OHLCV daily:           IBKR (primary) → yfinance (fallback) — both correct for price data
Underlying price:      STA localhost:5001 (always running, canonical source)
VIX:                   STA localhost:5001
```

**Total monthly cost: $12/mo** (MD.app Starter only)

---

## Provider-by-Provider Verdicts

### IBKR Interactive Brokers — KEEP (free with live account)
- **Live chain:** ✅ real-time, full chain, all strikes, greeks, IV, bid/ask
- **Historical IV:** ✅ `reqHistoricalData(whatToShow="OPTION_IMPLIED_VOLATILITY")` — 365-day daily IV series, real ATM IV. **Only source confirmed working.**
- **OHLCV:** ✅ 90-day daily bars
- **Constraint:** Requires IB Gateway running. All calls must go through `IBWorker.submit()` (asyncio isolation — Golden Rule 2). Connection edge cases exist.
- **Role in stack:** Primary live chain + sole historical IV source. Not replaceable for IV history.

### MarketData.app Starter — $12/mo — ACTIVE (purchased Day 35/36)
- **Live chain:** ✅ IV, delta, gamma, theta, vega, OI, volume per contract. 15-min delayed.
- **Spot IV:** ✅ `get_oi_volume()` returns `iv` field (decimal, e.g. 0.17 = 17%). Multiplied ×100 on store.
- **Historical IV:** ❌ **Platform limitation confirmed by support (Day 10).** Historical chain endpoint returns 0 contracts for past dates. No timeline for fix.
- **Credit limit:** 10,000/day — tracked in `marketdata_provider.py`. Non-blocking if exhausted.
- **Role:** OI/volume for liquidity gate + spot IV accumulation into iv_history.db on every analysis call. Fills IV history forward-going so IVR percentile improves daily without IBKR.
- **Implementation:** `marketdata_provider.py` → called in `analyze_service.py` after IBKR/Alpaca chain. `iv_store.store_iv(ticker, today, iv*100, source="marketdata")` idempotent via PRIMARY KEY.

### Alpaca — FREE — KEEP as fallback
- **Live chain:** ✅ greeks, IV (61% coverage overall, 100% ATM ±15%)
- **OI/volume:** ❌ `OptionsSnapshot` model has no `open_interest` or `volume` field — **confirmed by live test Day 10**. This is a model limitation, not a tier restriction.
- **Historical IV:** ❌
- **Role:** Tier 3 fallback when IBKR offline and MD.app credits exhausted. Do not use for liquidity gate.

### yfinance — FREE — KEEP for OHLCV only
- **OHLCV:** ✅ correct price data. Used for HV-20 computation and OHLCV fallback in batch.
- **IV history:** ❌ **REMOVED from IV seeding pipeline (Day 37).** `yfinance` computes rolling 20-day HV from price returns (`np.std(returns) * sqrt(252) * 100`) — this is **historical volatility, not implied volatility**. Storing HV in iv_history.db contaminates IVR percentile calculations. Only real IV (IBKR/MD.app) is stored now.
- **Role:** OHLCV daily bars only. Never IV.

### Tradier — FREE (brokerage account required) — PENDING INTEGRATION
- **Live chain:** ✅ full chain, OI, volume, bid/ask — REST API, no IB Gateway needed
- **Greeks/IV:** ✅ delta, gamma, theta, vega, rho + bid_iv/mid_iv/ask_iv/smv_vol per contract
- **Delay:** Greeks updated **once per hour** via ORATS. Acceptable for multi-week swing analysis.
- **Historical IV:** ❌ No historical ATM IV time series. Same gap as all REST providers.
- **Cost:** Free with Tradier brokerage account. No separate developer plan exists (confirmed by support Day 37).
- **Potential role:** Replace IBKR as primary live-hours chain source → eliminates IB Gateway dependency. IBKR still needed for nightly IV seeding batch.
- **Status:** Not yet integrated. Open a Tradier account → test `/v1/markets/options/chains?symbol=XLF&expiration=YYYY-MM-DD&greeks=true` live → implement `tradier_provider.py` if confirmed.
- **Integration point:** `data_service.py` cascade — insert above Alpaca when implemented.

### Massive.com — ❌ DO NOT BUY
- **Free tier:** No options data at all.
- **Paid tiers:** Real-time chain snapshot with IV + greeks — duplicates MD.app capability at higher cost (~$29/mo vs $12/mo).
- **Historical IV:** ❌ **Does not exist at any tier.** Their "historical" options data is OHLC price bars for specific contracts, not ATM IV time series. Confirmed by reading full API docs (llms.txt Day 37).
- **Auth:** `Authorization: Bearer {key}` on `api.massive.com`. Key works; plan doesn't include options.
- **Verdict:** Polygon.io clone. Same data, higher price. No unique value for OptionsIQ.

### EODHD — ❌ NOT VIABLE (free key in .env)
- **Free tier:** "Only EOD data allowed for free users" — options data paywalled.
- **Paid options:** Requires paid plan for historical options data. Expensive for what we need.
- **Historical IV claim:** Unverified. Day 10 Perplexity flagged "claims IV in EOD — untested." Day 34 tested free key → blocked. Day 37 tested again → same block.
- **Verdict:** Free key has no useful options data. Paid plan not worth evaluating — IBKR provides historical IV for free.

### Other providers evaluated (Day 10 Perplexity research)
| Provider | Verdict |
|----------|---------|
| Unusual Whales | ✅ has IVR endpoint — but $125/mo, way over budget |
| Cboe LiveVol | ✅ complete — $380/mo, enterprise only |
| OptionsDX | ✅ historical IV CSV — no API, download-only |
| Alpha Vantage | ✅ 15yr history — $50+/mo, over budget |
| IVolatility.com | Not tested — likely expensive |
| ORATS | Powers Tradier's greeks. Direct API likely expensive. |
| Tastytrade | Free but requires account + OAuth complexity |

---

## Historical IV: Why IBKR Is the Only Viable Source

Confirmed across 3 research cycles (Day 10, Day 26, Day 37):

| Provider | Historical IV? | Evidence |
|----------|---------------|---------|
| IBKR | ✅ | `reqHistoricalData(whatToShow="OPTION_IMPLIED_VOLATILITY")` — tested live, 365 rows |
| MarketData.app | ❌ | Support confirmed platform limitation Day 10 |
| Alpaca | ❌ | No historical endpoint |
| Tradier | ❌ | No historical IV API |
| Massive.com | ❌ | OHLC price bars only, confirmed from full API docs |
| EODHD | ❌ | Free tier blocked; paid unverified |
| yfinance | ❌ | Computes HV not IV — **contaminates IVR if used** |

**The forward-going accumulation pattern** (implemented Day 36): MD.app spot IV is stored on every
`analyze_etf()` call via `iv_store.store_iv(ticker, today, iv*100, source="marketdata")`. This
idempotent write accumulates real IV history over time. After 252 trading days of running the app,
IBKR's nightly batch becomes less critical for IVR accuracy. Both paths reinforce each other.

---

## Architecture Impact: What Each Provider Fixes

| Gate | Before | After full stack |
|------|--------|-----------------|
| `ivr` / `ivr_seller` | Unreliable (sparse IBKR history) | Accurate — IBKR 365-day seed + MD.app daily accumulation |
| `liquidity` (OI) | Always warns — Alpaca has no OI | Works — MD.app provides OI per contract |
| `liquidity` (vol/OI) | Always N/A | Real ratio from MD.app |
| `greeks` | IBKR only (Gateway required) | IBKR → MD.app → Alpaca cascade |
| `hv_iv_ratio` | IBKR + yfinance HV | Correct: IV from IBKR/MD.app, HV from OHLCV price data |

---

## Open Action Items

1. **Tradier integration** (when ready): Open brokerage account → test live chain call → implement `tradier_provider.py` → insert in `data_service.py` above Alpaca. Eliminates IB Gateway dependency for live-hours chain fetching. IBKR EOD batch stays.

2. **FOMC gate** (independent of providers): Hardcode 2026 FOMC dates in `constants.py`. Currently `fomc_days_away=999` — always passes. 30-minute fix. See `Day26_Data_Strategy.md` for details.

3. **Historical IV cold-start** (365-day seed): On first run after fresh install, IBKR nightly batch pulls 365 days. Until then, IVR is computed from partial history. No code change needed — the batch already handles this.

---

## Files Superseded by This Document

- `Day10_Provider_Live_Tests.md` — raw evidence base, still valid for per-field test results
- `Day26_Data_Strategy.md` — original 3-option plan (Options 1/2/3). Options 1+2 implemented as batch_service.py + MD.app. Option 3 (EODHD backfill) not needed — IBKR 365-day seed covers it.
- `Day34_Subscription_Research.md` — research prompt doc. Questions answered by Day 37 live API tests.
