# OptionsIQ — Intelligent Data Retrieval Plan
> **Created:** Day 26 (April 20, 2026)
> **Status:** Draft — for refinement
> **Context:** ETF-only mode (16 ETFs). Primary feed is IBKR live. Three targeted gaps to close.

---

## Prior Research (Day 10)
See `docs/Research/Options_Data_Provider_Research_Day10.md` for the full evidence base.

Key confirmed findings that inform this plan:
- **IBKR `reqHistoricalData(OPTION_IMPLIED_VOLATILITY)` confirmed working** — gives 252-day daily IV series per ETF. This validates Option 1 below as a proven, not speculative, path.
- **MarketData.app historical IV = None** — live-tested and confirmed platform limitation (KI-037). Not a viable IVR source at any price tier.
- **Alpaca OI/volume = not in model** — `OptionsSnapshot` has no `open_interest` or `volume` field (live-tested). Alpaca cannot fix the Liquidity gate.
- **EODHD was flagged "untested" in Day 10** — Day 10 Perplexity table lists it as "claims IV in EOD, untested." The recommendation in Option 3 below is based on that claim — must verify before committing $30.
- **Tradier was in Day 10's table as $10/mo paid** — The new angle here is Tradier's FREE data access via a brokerage account. Day 10 didn't explore the free-account path.

---

## The Problem Statement

OptionsIQ has three real data gaps that degrade trade quality:

| Gap | Symptom in UI | Gate Affected |
|-----|--------------|---------------|
| IVR cold-start | IVR unreliable on tickers not recently analyzed | `ivr`, `ivr_seller` |
| OI always 0 | Liquidity gate permanently warns on ALL analyses | `liquidity` |
| FOMC = 999 | Events gate always passes, even 3 days before Fed meeting | `events` |

The OI and IVR gaps are the two that hurt real decisions. A PAUSE verdict from Liquidity on XLK is meaningless noise — XLK options trade millions of contracts a day.

---

## Option 1 — Nightly IB `reqHistoricalData` Pull

**Cost:** Free (uses existing IBKR subscription)
**Fixes:** IVR — makes it real and self-sustaining over time
**Timeline to value:** 30 days (partial), 90 days (reliable), 252 days (full 52-week range)

### What it does
Calls `reqHistoricalData(whatToShow='OPTION_IMPLIED_VOLATILITY')` on all 16 ETFs every night at market close. Stores one daily IV row per ETF into `iv_store.db`. IVR percentile calculation then has real historical data instead of a sparse hand-built dataset.

```python
# Conceptual call (must go through IBWorker.submit())
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 Y',
    barSizeSetting='1 day',
    whatToShow='OPTION_IMPLIED_VOLATILITY',
    useRTH=True
)
```

### What it fixes
- `ivr` gate: "Is IV cheap enough to buy?" → real percentile
- `ivr_seller` gate: "Is premium expensive enough to sell?" → real percentile
- IVR scan in sector scanner (L2) → consistent with L3 analysis (fixes KI-064 partially)

### What it does NOT fix
- OI=0 (Liquidity gate still warns)
- FOMC gate (still =999)

### Architecture constraint (CRITICAL)
The nightly call MUST go through `IBWorker.submit()`. Cannot call ib_insync from a cron thread directly — asyncio event-loop conflict (Golden Rule 2). Correct pattern:

```
cron job (nightly 4:30pm ET)
  → curl POST localhost:5051/api/admin/seed_iv
  → Flask route → IBWorker.submit(fetch_iv_history, ticker)
  → appends to iv_store.db
```

### Build estimate
~1 day. New Flask route `POST /api/admin/seed_iv`, IBWorker task for `reqHistoricalData`, iv_store write helper, simple shell cron.

---

## Option 2 — Tradier Brokerage Account

**Cost:** Free (requires opening a Tradier brokerage account)
**Fixes:** OI and Volume — Liquidity gate becomes meaningful
**Timeline to value:** Immediate after wiring

### What it does
Tradier's REST API returns live options chain data including OI and volume per strike — for free to account holders. Wire it as a supplemental call during analysis: IBKR provides greeks/pricing, Tradier provides the two fields IBKR can't surface (OI, volume). Not a replacement — a targeted supplement.

### What it fixes
- `liquidity` gate: "Can I get in and out of this trade easily?" → real OI and Vol/OI ratio
- Removes false PAUSE verdicts on liquid ETFs caused purely by OI=0
- `Vol/OI N/A` becomes a real ratio in the UI

### What it does NOT fix
- IVR (Tradier has no IV history)
- FOMC gate
- Greeks (IBKR is still better source)

### Integration point
In `analyze_service.py`, after IBKR chain fetch, make a Tradier REST call for OI/volume on the two spread strikes. Merge into the gate_payload before calling gate_engine. Keep it non-blocking — if Tradier call fails, fall back to OI=0 (current behavior).

```
IBKR chain fetch → [Tradier OI/volume for spread strikes] → gate_payload → gate_engine
```

### Build estimate
~half a day. New `tradier_provider.py`, env vars for API key, one call in `analyze_service.py`, fallback guard.

### Open question
- Does Tradier REST return per-strike OI/volume for ETF options chains? Needs live test before committing.
- Rate limits for 16 ETFs on free tier?

---

## Option 3 — EODHD One-Time Historical IV Backfill

**Cost:** $29.99 for 1 month, then cancel
**Fixes:** IVR working on day 1 — skips Option 1's 90-day cold-start
**Timeline to value:** Immediate after import

### What it does
EODHD has 20+ years of historical options data with daily IV per underlying. Pay for 1 month, pull 1 year of daily IV for all 16 ETFs, import into `iv_store.db`, cancel. IVR is immediately accurate from the first analysis of any ETF.

### What it fixes
Same gates as Option 1 (`ivr`, `ivr_seller`) — but instantly instead of waiting 90 days.

### What it does NOT fix
- OI=0 (no live OI from EODHD)
- FOMC gate

### Relationship to Option 1
Option 3 is an accelerator for Option 1, not a replacement. After EODHD backfill, Option 1's nightly job maintains the dataset going forward. You pay $30 once to avoid 90 days of cold-start.

### Build estimate
~half a day. One-time `import_eodhd_iv.py` script: fetch EODHD endpoint for each of 16 ETFs, parse daily IV, write rows to `iv_store.db`. Verify IVR output before canceling subscription.

### Open question (unresolved since Day 10)
- EODHD daily IV: is this the underlying's IV (like VIX for SPY) or per-strike IV? Need to verify it maps correctly to `iv_store.py` schema.
- Which EODHD endpoint? `/api/options/{ticker}.json?api_token=...` — check if it includes historical daily IV series.
- **Do not pay for EODHD until a free-tier or trial confirms the IV field exists and is the right format.** Day 10 flagged this as "untested — claims IV in EOD." That claim has not been verified.

---

## Combined Effect

| Gate | Current State | After Options 1+2+3 |
|------|--------------|---------------------|
| `ivr` / `ivr_seller` | Unreliable (sparse history) | Real percentile, works day 1 |
| `liquidity` | Always warns (OI=0) | Real OI — warns only when genuinely illiquid |
| `events` (earnings) | Works via yfinance | Unchanged |
| `events` (FOMC) | Always passes (=999) | **Still broken** — fix separately (hardcode 6 dates in constants.py) |
| `market_regime` | Works via yfinance | Unchanged |
| greeks | Live from IBKR | Unchanged |

---

## Separate Fix: FOMC Gate (Not a Data Provider Problem)

FOMC meeting dates are published months in advance by the Federal Reserve. The correct fix is:
- Add `FOMC_DATES = ['2026-05-07', '2026-06-18', ...]` to `constants.py`
- In gate logic, compute `days_until_next_fomc` from today's date
- Replace the `fomc_days_away=999` default

This takes ~30 minutes and is completely independent of any data provider. It should be done before any of the 3 options above.

---

## Recommended Build Order

1. **FOMC hardcode** (30 min, free, immediate impact) — fix KI-008 properly
2. **Option 3: EODHD backfill** (half day, $30 one-time) — IVR works immediately
3. **Option 1: Nightly IB pull** (1 day, free) — self-sustaining IVR, cancel EODHD
4. **Option 2: Tradier OI** (half day, free) — Liquidity gate becomes real

Total cost after cancel: $0/mo. Total build time: ~2.5 days.

---

## Open Questions Before Building

1. Does `reqHistoricalData(whatToShow='OPTION_IMPLIED_VOLATILITY')` work in ib_insync for ETFs during after-hours? (Need to test.)
2. Does Tradier free tier provide per-strike OI/volume for ETF options, and what are the rate limits?
3. Does EODHD historical IV series map to `iv_store.py`'s schema (daily underlying IV, not per-strike)?
4. What is the `iv_store.db` schema? Verify before writing any import script.

---

*Source: Multi-LLM research synthesis (Day 26) + system audit of known data gaps*
*Next review: after live-testing Option 2 (Tradier) open questions*
