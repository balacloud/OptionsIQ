# Options Data Provider Research — Day 10 (March 12, 2026)

> **Context:** Evaluating affordable options data APIs to complement/replace IBKR dependency.
> **Goal:** Find providers under $30/month that cover OptionsIQ's data needs.

---

## Our Specific Data Requirements

### Per-Contract Fields (options chain)
| Field | Required | Notes |
|-------|----------|-------|
| bid / ask | ✅ | For spread calculation, liquidity gate |
| delta, gamma, theta, vega | ✅ | Gate logic depends on these |
| implied_volatility (current) | ✅ | Current IV needed for IVR |
| open_interest | ✅ | Liquidity gate threshold: OI ≥ 1000 |
| volume | ✅ | Liquidity gate: vol/OI ratio |
| full chain (all strikes, DTE 14-120) | ✅ | Direction-aware filtering done client-side |

### Historical Data (the critical gap)
| Field | Required | Notes |
|-------|----------|-------|
| 252 days of daily ATM IV per underlying | ✅ **CRITICAL** | Needed for IVR = (current − 52w low) / (52w high − 52w low) |
| EOD data acceptable | ✅ | Don't need intraday IV history |
| 15-min delay acceptable | ✅ | Historical = always delayed anyway |
| ATM IV per ticker per day | ✅ | Don't need per-strike history, just composite "the IV" for the ticker |

### Non-Requirements
- Real-time data (15-min delayed is fine for swing analysis)
- Futures or forex options
- Commercial use (personal/non-commercial only)

---

## Evidence-Based Provider Testing (Day 10)

### Alpaca (Free Tier — `indicative` feed)
**Tested live with AMD, 572 contracts returned.**

| Field | Result | Evidence |
|-------|--------|----------|
| bid / ask | ✅ 87-100% | bid_price=94.7, ask_price=98.32 |
| greeks (current) | ✅ **100% within ATM ±15%** | delta=0.599, gamma=0.0086, etc. |
| IV (current) | ✅ 61% overall (100% ATM zone) | iv=0.5797 |
| open_interest | ❌ **field does not exist in OptionsSnapshot model** | `hasattr(snapshot, 'open_interest')` → False |
| volume | ❌ **field does not exist in OptionsSnapshot model** | Not in model_fields |
| historical IV | ❌ | No historical endpoint |
| underlying price | ✅ | AMD = $202.26 (StockHistoricalDataClient) |

### MarketData.app (Starter Trial — 24hr delayed, 10k credits/day)
**Tested live with AMD + AAPL (premium), chain + quotes + historical endpoints.**

| Field | Current Chain | Historical Chain | Historical Quotes |
|-------|-------------|-----------------|-------------------|
| bid / ask | ✅ bid=15.05, ask=15.80 | ✅ | ✅ 8 data points |
| greeks | ✅ delta=0.599, gamma=0.0121 | ❌ **None** | ❌ **None** |
| IV | ✅ iv=0.5422 | ❌ **None** | ❌ **None** |
| OI | ✅ 457-670 | ✅ 720-1309 | ✅ 56-594 |
| volume | ✅ 103-415 | ✅ 70-195 | ✅ 144-487 |
| underlyingPrice | ✅ 204.93 | ✅ | ✅ |

**Critical finding: Historical greeks/IV = None even for AAPL with premium access.**
This is a **confirmed platform limitation** (not a trial restriction). MarketData.app support
confirmed on March 13, 2026: *"Our historical data does not include IV/greeks at this time.
This is something we hope to add soon."* — no timeline given.

### Trial vs Paid Starter Differences
| Feature | Starter Trial (current) | Paid Starter ($12/mo) |
|---------|------------------------|----------------------|
| Credits/day | 10,000 | 10,000 |
| Stock data delay | 24 hours | Real-time |
| Options data delay | 24 hours | 15 minutes |
| Historical data | 1 year (5yr AAPL only) | 5 years |
| Premium endpoints | AAPL only | All tickers |

---

## Perplexity Research (Day 10)

| Provider | Price | Hist IV | Greeks | OI/Vol | Rate Limit | Notes |
|----------|-------|---------|--------|--------|------------|-------|
| **Tradier Pro** | $10/mo | ❌ poll-yourself | ✅ model greeks | ✅ | 120 req/min | No hist IV endpoint |
| **Polygon / Massive** | $29/mo | ❌ not explicit | ❌ must compute | ✅ | "unlimited" | 2yr chain history but no IV series |
| **Unusual Whales** | ~$125/mo | ✅ IVR endpoint | ✅ | ✅ | 20k/day | Way over budget |
| **MarketData.app** | $12/mo | ❌ **TESTED: None** | ✅ current only | ✅ | 10k/day | Hist IV = None confirmed |
| **Tastytrade API** | Free (account) | ❌ must build yourself | ✅ | ✅ | not published | Needs OAuth |
| **Cboe LiveVol** | ~$380/mo | ✅ | ✅ | ✅ | N/A | Enterprise — way over budget |
| **OptionsDX** | Pay-per-dataset | ✅ (CSV download) | ✅ pre-calc | ✅ | N/A | No API — CSV only |
| **EOD Historical Data** | $29.99/mo | ✅ 2yr daily EOD | ✅ Δ Γ Θ ν | ✅ | high on paid | Untested — claims IV in EOD |
| **Alpha Vantage** | ~$50+/mo | ✅ 15yr history | ✅ | ✅ | limited | Over budget |

**Perplexity originally claimed MarketData.app had historical IV — WRONG.** Live testing disproved it.
Corrected in table above. Always verify with live API calls.

---

## Final Evidence-Based Comparison Table

| Field | IBKR (live) | Alpaca (free, tested) | MarketData.app ($12/mo, tested) |
|---|---|---|---|
| **Current Chain** | | | |
| bid / ask | ✅ real-time | ✅ 15-min (87-100%) | ✅ 24hr trial / 15-min paid |
| greeks (δ γ θ ν) | ✅ 100% market open | ✅ 100% ATM ±15% | ✅ 100% |
| implied volatility | ✅ | ✅ 61% overall | ✅ 100% |
| open interest | ✅ (KI-035 fixed Day 10) | ❌ not in model | ✅ |
| volume | ✅ | ❌ not in model | ✅ |
| underlying price | ✅ real-time | ✅ 15-min | ✅ |
| **Historical** | | | |
| 252-day daily IV series | ✅ **direct** | ❌ | ❌ **None (tested)** |
| historical OI/volume | ✅ | ❌ | ✅ |
| historical greeks | N/A | ❌ | ❌ **None (tested)** |
| OHLCV daily bars | ✅ | ❌ | ✅ (stock candles) |
| **Operational** | | | |
| requires running process | ✅ IB Gateway | ❌ REST | ❌ REST |
| threading constraint | ✅ IBWorker only | ❌ any thread | ❌ any thread |
| cost | free (brokerage) | free | $12/mo |
| credits/day | unlimited | unlimited | 10,000 |

---

## Provider Cascade (Day 10 — Final)

```
Tier 1:   IBKR Live         — real-time, full data + historical IV for IVR
Tier 2:   IBKR Cache        — SQLite, 2-min TTL
Tier 2.5: MarketData.app    — 15-min delayed, greeks + IV + OI + volume ($12/mo)
Tier 3:   Alpaca            — free fallback, greeks but no OI/volume
Tier 4:   yfinance          — emergency, no greeks
Tier 5:   Mock              — dev/CI only
```

### Why IBKR Is Still Required
1. **Historical IV for IVR:** IBKR `reqHistoricalData(whatToShow="OPTION_IMPLIED_VOLATILITY")`
   gives 252-day IV series directly. No other provider under $30/mo provides this (tested).
2. **Your actual broker:** Live account U11574928 is at IBKR. When you execute, you use
   IBKR TWS/mobile with live prices — OptionsIQ's delay only affects the GO/NO decision.
3. **Once seeded, iv_store.db is self-sufficient:** IBKR seeds the 252-day IV history into
   SQLite. After that, IBKR is only needed for daily refresh (1 call/ticker/day).

### Why MarketData.app Above Alpaca
- OI: ✅ vs ❌ — liquidity gate works
- volume: ✅ vs ❌ — vol/OI ratio gate works
- IV coverage: 100% vs 61% — all contracts have IV
- greeks: 100% vs 100% ATM (but 52% deep ITM/OTM on Alpaca)

### Gate Impact by Data Source

| Gate | IBKR | MarketData.app | Alpaca | yfinance |
|------|------|---------------|--------|----------|
| IV/IVR gate | ✅ | ✅ (current IV only, no IVR without hist) | ⚠️ 61% | ❌ |
| Theta burn | ✅ | ✅ | ✅ ATM zone | ❌ |
| Liquidity (OI) | ✅ | ✅ | ❌ always fails | ❌ |
| Liquidity (vol/OI) | ✅ | ✅ | ❌ always fails | ❌ |
| Delta match | ✅ | ✅ | ✅ ATM zone | ❌ |
| Spread width | ✅ | ✅ | ✅ | ❌ |

---

## Perplexity Clarification Answers (sent Day 10)

**Q: EOD vs intraday IV history?**
A: End-of-day only. One daily data point per ticker per day for 252 days.

**Q: Delayed vs real-time for historical IV?**
A: Delay irrelevant for historical. Even yesterday's EOD is fine.

**Q: IV per strike vs ATM IV per day?**
A: ATM IV per underlying per day. The single composite "30-day IV" number.

**Q: Commercial vs personal use?**
A: Personal non-commercial only. Single user, no redistribution.

---

## Action Items

- [x] Perplexity research completed — provider comparison table filled
- [x] Alpaca tested live — OI/volume gap confirmed (not in OptionsSnapshot model)
- [x] MarketData.app tested live — historical IV = None confirmed (platform limitation)
- [ ] Create `marketdata_provider.py` — wire into DataService as tier 2.5 above Alpaca
- [ ] Monitor credit usage — 10k/day budget needs tracking in production
- [ ] If EODHD provides historical IV (untested) → evaluate as IVR seeding alternative to IBKR
