# OptionsIQ — Data Subscription Research Prompt
> **Created:** Day 34 (April 30, 2026)
> **Purpose:** Paste the prompt below into Perplexity / ChatGPT / Gemini to evaluate data providers.
> **Decision needed:** Which subscription(s) to add to eliminate IBKR dependency during trading hours.

---

## Context for the researcher (do not paste — for Claude reference only)

What we already have working:
- **IBKR IB Gateway** — live options chain, historical IV seeding, OHLCV. Works. But requires IB Gateway running, prone to connection edge cases during analysis.
- **STA (localhost:5001, own system)** — underlying spot price, VIX, SPY regime. Always running.
- **MarketData.app** (key: already configured) — OI/volume supplement. Live chain test confirmed: returns IV, delta, theta, gamma, vega, bid/ask, OI, volume per contract. **No historical IV** (tested: 0 contracts for past dates).
- **Alpaca** (key: already configured) — live chain with greeks. No OI. Free.
- **EODHD** (key: already configured) — not yet tested for options. Free tier paywalls options data.
- **yfinance** — OHLCV daily, emergency chain fallback. Free. No real greeks.

What the code needs (exact spec):

| Data type | Format needed | Frequency | Min history | Used for |
|-----------|--------------|-----------|-------------|----------|
| Live options chain | Per-contract: strike, expiry, bid, ask, IV, delta, theta, gamma, vega, OI, volume | On-demand during analysis | N/A (live) | Gate analysis, strike selection, strategy ranking |
| Historical ATM IV | One number per ETF per trading day — composite 30-day ATM implied vol (like VIX but per ETF) | Nightly top-up (1 row/day) | 252 trading days (1 year) to activate IVR gate | IVR percentile calculation: current IV ranked vs past 252 days |
| OHLCV daily | Date, open, high, low, close, volume | Nightly top-up | 90 days minimum (365 preferred) | HV-20 (historical volatility), McMillan 21-day stress check |
| Underlying spot price | Single float, current price | Per analysis call | N/A (live) | ✅ SOLVED — STA provides this |
| VIX | Single float, current VIX | Per analysis call | N/A (live) | ✅ SOLVED — STA provides this |

ETF universe (16 tickers): XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, SCHB, QQQ, TQQQ

---

## RESEARCH PROMPT (paste this verbatim)

```
I am building a personal ETF options analysis tool in Python (Flask backend). I need to evaluate 
REST API data providers to replace my Interactive Brokers dependency during live trading hours.

Here is my exact data need. Please evaluate each provider listed and answer all questions.

---

MY ETF UNIVERSE (16 tickers):
XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, IWM, SCHB, QQQ, TQQQ

---

DATA REQUIREMENT 1 — Live Options Chain (most important)
Format needed per contract: strike, expiry, bid, ask, mid, IV (implied volatility), delta, theta, 
gamma, vega, open_interest, volume.
I need this for all strikes within ±10% of current price, for expirations 14 to 120 days out.
Frequency: on-demand during market hours, maybe 20-30 API calls per day total.
I already tested MarketData.app and confirmed it returns all these fields. Budget: up to $20/mo.

DATA REQUIREMENT 2 — Historical ATM Implied Volatility (critical gap, hardest to find)
Format: one single number per ETF per trading day — the composite 30-day at-the-money implied 
volatility (like how VIX is a single number for SPX 30-day IV). 
I do NOT need full historical chain snapshots. Just the daily "what was XLF's 30-day ATM IV 
on 2025-06-15?" equivalent.
I need 252 trading days (1 year) of history per ETF for initial load, then 1 new row per ETF 
per day as a nightly top-up.
This is used to compute IV Rank (IVR) = percentile of today's IV vs past 252 days.
I have confirmed MarketData.app does NOT have this — their historical chain endpoint returns 
0 contracts for past dates. IBKR has it via reqHistoricalData but I want to reduce IBKR dependency.

DATA REQUIREMENT 3 — Daily OHLCV (lower priority, have yfinance fallback)
Format: date, open, high, low, close, volume.
90 days minimum, 365 days preferred.
Used to compute 20-day historical volatility (HV-20) and a McMillan-style 21-day 
max-drawdown/max-rally check.
yfinance provides this for free — so this is only interesting if bundled with Requirements 1 or 2.

---

PROVIDERS TO EVALUATE:

1. MarketData.app — I already have a free key. Plans: Starter free, Trader $12/mo, Trader+ $29/mo.
   Questions:
   a) Does ANY paid plan include historical implied volatility (daily ATM IV per ticker)?
   b) Their /v1/options/chain/{ticker}/ endpoint returns live data. Is this 15-min delayed 
      on Starter? Real-time on Trader?
   c) Do they have a dedicated IV history endpoint (not chain snapshots)?

2. Tradier — They have a Lite free tier and Developer $10/mo.
   Questions:
   a) Does the Lite free tier give access to live options chain with greeks and IV?
   b) Do they have any historical IV data (daily 30-day ATM IV) for ETFs?
   c) What are the rate limits for options chain calls?

3. EODHD (I have a free key: 6974f36e68b450.53992638) — eodhistoricaldata.com
   Questions:
   a) Do they have historical implied volatility (daily ATM IV) for ETFs like XLK, XLF?
      I know they have historical options data but is it full chain snapshots (expensive) 
      or just the daily ATM IV summary?
   b) Does my free key give any options data access, or is it paywalled?
   c) What is the cheapest plan that gives historical IV for 16 ETFs?

4. Polygon.io — They have Options Starter at $29/mo.
   Questions:
   a) Do they provide historical implied volatility as a daily time series per ticker?
   b) Is their live options chain complete (IV, delta, theta, gamma, vega, OI, volume)?
   c) Any free tier for testing?

5. Alpaca — I have API keys (paper account). 
   Questions:
   a) Their live options chain is free — does it include IV, delta, theta, gamma, vega?
   b) Do they have historical IV data (daily ATM IV time series) for ETFs?

6. Tastytrade API — They have a free developer API.
   Questions:
   a) Can I access their options chain data (IV, greeks, OI) via REST without being 
      a Tastytrade account holder?
   b) Do they have historical IV metrics (IVR, IVP, 30-day ATM IV) available via API?

7. IVolatility.com — Known for historical volatility data.
   Questions:
   a) Do they have a REST API for historical 30-day ATM IV per ETF?
   b) What does a subscription cost for 16 ETFs, daily IV, 1 year of history?
   c) Do they have live options chain data as well?

8. ORATS (Option Research & Technology Services) — orats.com
   Questions:
   a) Do they provide daily historical 30-day ATM IV as a time series?
   b) What is their cheapest plan that covers my 16 ETFs?
   c) Do they have a REST API or is it download-only?

---

MY EXISTING SUBSCRIPTIONS / KEYS (do not recommend these as new purchases):
- Interactive Brokers (IB Gateway): works but want to reduce dependency
- MarketData.app: have free key, live chain confirmed working
- Alpaca: have free paper account key
- EODHD: have free key but untested for options

---

PLEASE ANSWER:
1. Which provider is the BEST single source for BOTH live options chain AND historical IV?
2. If no single source covers both, what is the cheapest TWO-provider combination?
3. For historical IV specifically: is the data I need (daily 30-day ATM IV) commonly called 
   something else in the industry? What is the standard terminology providers use?
4. Does EODHD's free key give access to any historical IV data worth testing before paying?
5. Does MarketData.app Trader ($12/mo) unlock any historical IV, or is it live-only at all tiers?

Budget: prefer under $30/mo total. Already paying $0 for IBKR data (included with live account).
```

---

## What to do with the research results

Paste findings back into `docs/Research/Data_Subscription_Research_Day34.md` below this line as a new section: `## LLM Research Results`.

Then bring the results to the next Claude session. The implementation plan will be:
1. If a provider has historical IV → wire it into `iv_store.store_iv()` nightly (same interface IBKR uses)
2. If MarketData.app Trader ($12/mo) covers live chain → wire it into `data_service.py` cascade above Alpaca
3. Keep IBKR as last-resort fallback — do not remove it, just deprioritize it

Key integration points in the codebase:
- Live chain: `data_service.py` → `get_chain()` cascade (lines 289–368)
- Historical IV seeding: `iv_store.store_iv(ticker, date, iv, source=...)` — any provider just needs to call this
- Nightly seed route: `POST /api/admin/seed-iv/all` → `_seed_iv_for_ticker()` in `app.py` (lines 208–258)
