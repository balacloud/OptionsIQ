# IBKR ETF Scanner Setup for OptionsIQ
> **Created:** Day 50 (May 20, 2026)
> **Purpose:** Configure the IBKR Market Screener to pull live IV rank, IV/HV ratio, and option volume for our 15-ETF universe. Used with the `/etf-scan` Claude command.

---

## What This Solves

| Problem | Source | Fix |
|---------|--------|-----|
| IV/HV shows `—` in Best Setups watchlist (KI-101) | chain IV null from Tradier | Scanner provides `IMPLIED VOL./HIST. VOL %` directly — IBKR pre-computed |
| IVR confidence "unknown" for new ETFs (KI-096) | sparse iv_history.db | Scanner provides `52 WEEK IV RANK` from IBKR's full 252-day history |
| MarketData.app credit usage (~33/day) | OI/volume calls | Scanner provides `OPT. VOLUME` + `AVERAGE OPTION VOLUME` — free |
| New signal: sentiment | nothing | `PUT/CALL VOLUME` ratio now available |

---

## Step 1 — Open IBKR Market Screener

In TWS or IBKR Portal:
- Click **MarketScanner** (or New Window → Market Scanner)
- Select the **ETFs** tab at the top (not US Stocks)

---

## Step 2 — Set Filters (optional but recommended)

The ETF tab already restricts to ETFs. Our 15 ETFs (IWM, QQQ, XLF, XLK, XLY, XLP, XLV, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, TQQQ) are all high-volume and will naturally sort near the top by any options-volume metric.

Optional filter to add: **Average Option Volume > 5000** — this keeps our universe visible and filters out thinly-traded ETFs.

---

## Step 3 — Add These Columns (in order)

Right-click column header → Add Column. Add exactly these:

| Column Name in IBKR | What It Provides |
|--------------------|-----------------|
| `52 WEEK IV RANK` | IVR — 0–100 integer. >35 = seller edge |
| `IMPLIED VOL./HIST. VOL %` | IV/HV ratio × 100. >105% = VRP present |
| `AVERAGE OPTION VOLUME` | Avg daily option volume. Tier 1 ≥ 10K |
| `OPT. VOLUME` | Today's option volume |
| `PUT/CALL VOLUME` | Sentiment: <0.7 bullish, >1.3 bearish |
| `LAST` | Underlying price (verification) |
| `CHANGE %` | Today's price action (for tape-fight check) |

---

## Step 4 — Set MultiSort (up to 10 allowed)

Click **MultiSort** button in top right. Set:

| Priority | Factor | Direction | Why |
|----------|--------|-----------|-----|
| 1st | `52 WEEK IV RANK` | Higher Values | Top IVR ETFs first |
| 2nd | `IMPLIED VOL./HIST. VOL %` | Higher Values | Best VRP condition first |
| 3rd | `AVERAGE OPTION VOLUME` | Higher Values | Most liquid first |

This ensures IWM, QQQ, XLF, XLK, XLY appear near the top on most days.

---

## Step 5 — Save the Screener

Click **Save** → name it **"Options-iq-ETF"**

---

## Daily Workflow

1. Open IBKR → Market Screener → "Options-iq-ETF"
2. Click **Refresh Results** (top left)
3. Take a screenshot (Cmd+Shift+4 on Mac)
4. Paste into Claude conversation
5. Type `/etf-scan`

Claude will:
- Read all visible ETF rows
- Apply IVR / VRP / liquidity gates
- Output a ranked pre-analysis
- Write `backend/data/scanner_cache.json`

On the next Best Setups scan, the backend automatically uses the scanner data to fill IV/HV and IVR gaps.

---

## Data Flow

```
IBKR Market Screener (live)
    ↓ screenshot
/etf-scan command (Claude reads image)
    ↓ extracts per-ETF: IVR, IV/HV%, opt vol, put/call, change%
backend/data/scanner_cache.json (TTL: 4 hours)
    ↓ read by scanner_service.get_scanner_data(ticker)
best_setups_service.run_one_setup()
    ↓ injects iv_hv_ratio, ivr when chain data null
Best Setups watchlist → no more "—" for IV/HV (KI-101 closed)
```

---

## Gate Thresholds Applied by /etf-scan

| Gate | Threshold | Source |
|------|-----------|--------|
| IVR PASS | 52W IV Rank ≥ 35 | `IVR_SELLER_PASS_PCT = 35` in constants.py |
| VRP PASS | IV/HV% ≥ 105% | `HV_IV_SELL_PASS_RATIO = 1.05` in constants.py |
| Liquidity Tier 1 | Avg Opt Vol ≥ 10,000 | `ETF_OPTIONS_LIQUID_TIER1` in constants.py |
| Tape-fight warn | CHANGE% < -2% | Consistent with KI-098 weekChange gate |

---

## The "Options-iq-gemini" vs "Options-iq-ETF" Distinction

- **Options-iq-gemini** (your existing screener) — scans the full stock universe for high-IV options candidates. Feeds into the STA `/ibkr-scan` workflow. Stocks only.
- **Options-iq-ETF** (this new screener) — scans only ETFs, sorted by IV conditions. Feeds into `/etf-scan` for OptionsIQ Best Setups enrichment.

Both can run simultaneously — different tabs in IBKR.
