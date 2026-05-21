---
name: feedback-ibkr-reqmktdata
description: IBKR reqMktData limitations for stock/ETF generic ticks — snapshot=True invalid with genericTickList, tick 104 invalid for STK, market data subscription required
metadata:
  type: feedback
---

IBKR reqMktData has several constraints for STK (Stock/ETF) contracts:

1. **snapshot=True is INVALID with genericTickList** — IBKR Error 321: "Snapshot market data subscription is not applicable to generic ticks." Always use `snapshot=False` (streaming) when requesting generic ticks.

2. **Tick 104 (histVol) is invalid for STK** — Error 321 lists legal ticks for STK. Use `411` (rthistvol) for historical volatility, not `104`. Also: ticks 29 (callVolume) and 30 (putVolume) are invalid for STK — use `100` (optVolume total) instead.

3. **Market data subscription required for arbitrary ETF tickers** — Without a paid US Equity market data subscription (~$6/month per exchange), `reqMktData` returns `nan` for ALL fields (bid/ask/last) for tickers the user doesn't own. Portfolio positions receive live data automatically. reqMktData for arbitrary ETFs (XLK, XLE, etc.) requires explicit subscription in IBKR account settings.

**How to apply:** When calling `reqMktData` for stocks/ETFs: always `snapshot=False`, use `"106,411,100,105"` as tick list, and expect `{}` return if user hasn't subscribed to market data. Tradier covers the same IV/HV data for free — prefer Tradier over IBKR reqMktData for arbitrary ETF ticks.

**Why:** Discovered Day 51 while live-testing scanner integration. IBKR's market data is subscription-gated for non-owned tickers, not a code bug.
