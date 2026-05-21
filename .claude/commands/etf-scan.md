# /etf-scan — OptionsIQ ETF Scanner Pre-Analysis

Read the IBKR ETF screener screenshot pasted in this conversation. Extract per-ETF data, apply OptionsIQ gate criteria, output a ranked analysis, and write scanner_cache.json so the Best Setups backend can use the data.

---

## OptionsIQ ETF Universe (15 ETFs)

**Tier 1 — Primary targets (check these first):**
IWM, QQQ, XLF, XLK, XLY

**Tier 2 — Structural liquidity limit:**
XLK, XLP, XLV, XLI, XLE, XLU, XLB, XLRE, XLC, MDY, TQQQ

---

## Step 1 — Read the screenshot

Look at the image pasted in the conversation. It is an IBKR Market Screener table.

For every visible row, extract:
- **TICKER** — the symbol only (e.g. "XLF", "QQQ") — NOT the company name
- **IVR_52W** — "52 WEEK IV RANK" column — integer (e.g. 62). Null if column absent.
- **IV_HV_PCT** — "IMPLIED VOL./HIST. VOL %" or "IMPLIED VOL/HIST. VOL %" column — float (e.g. 118.3). Null if absent.
- **OPT_VOL** — "OPT. VOLUME" column — convert K suffix (e.g. 14.7K → 14700). Null if absent.
- **AVG_OPT_VOL** — "AVERAGE OPTION VOLUME" column — convert K suffix (e.g. 37.3K → 37300). Null if absent.
- **PUT_CALL_VOL** — "PUT/CALL VOLUME" column — float (e.g. 0.68). Null if absent.
- **LAST** — "LAST" column — float price. Null if absent.
- **CHANGE_PCT** — "CHANGE %" column — signed float without % sign (e.g. +2.33% → 2.33, -0.57% → -0.57). Null if absent.

---

## Step 2 — Filter to our universe

Keep only rows where TICKER matches one of the 15 ETFs above. Discard all others.

Note how many of our 15 ETFs appear in the screenshot. If 0 are found, output:
> "No OptionsIQ ETFs found in this screenshot. This appears to be a stock screener. See docs/Research/IBKR_ETF_Scanner_Day50.md for ETF screener setup instructions."
and stop.

---

## Step 3 — Apply gate criteria per ETF

For each ETF found in our universe, evaluate these 4 gates:

### Gate A — IVR Gate (from IVR_52W)
| Value | Result |
|-------|--------|
| ≥ 35 | ✅ PASS — "Elevated premium, seller edge" |
| 25–34 | ⚠️ WARN — "Moderate IV, marginal" |
| < 25 | ❌ FAIL — "Low IV, avoid selling premium" |
| null | ❓ UNKNOWN — "No scanner data" |

### Gate B — VRP Gate (from IV_HV_PCT)
| Value | Result |
|-------|--------|
| ≥ 105% | ✅ PASS — "IV > HV, volatility risk premium present" |
| 100–104% | ⚠️ WARN — "IV barely above HV" |
| < 100% | ❌ FAIL — "HV > IV, do not sell premium" |
| null | ❓ UNKNOWN |

### Gate C — Liquidity Gate (from AVG_OPT_VOL)
| Value | Result |
|-------|--------|
| ≥ 10,000 | ✅ Tier 1 — liquid |
| 1,000–9,999 | ⚠️ Tier 2 — limited |
| < 1,000 | ❌ Tier 3 — illiquid |
| null | ❓ UNKNOWN |

### Gate D — Momentum (from CHANGE_PCT)
| Value | Implication |
|-------|-------------|
| > 0% | Rising today — sell_put favorable (money flowing in) |
| -2% to 0% | Flat/slight pullback — neutral, slight caution |
| < -2% | Falling — tape-fight risk for sell_put; favorable for bear_call_spread |
| null | Unknown |

### Bonus — Sentiment (from PUT_CALL_VOL)
| Value | Signal |
|-------|--------|
| < 0.7 | Bullish skew (calls dominating) |
| 0.7–1.3 | Neutral |
| > 1.3 | Bearish skew (puts dominating) |

---

## Step 4 — Score and determine direction

Score each ETF (max 6 points):
- Gate A: PASS=2, WARN=1, FAIL/UNKNOWN=0
- Gate B: PASS=2, WARN=1, FAIL/UNKNOWN=0
- Gate C: Tier1=2, Tier2=1, Tier3/UNKNOWN=0

Determine suggested direction:
- Gate A PASS + Gate B PASS + CHANGE_PCT > -2% → **sell_put**
- Gate A PASS + Gate B PASS + CHANGE_PCT < -2% → **bear_call_spread**
- Gate A FAIL or Gate B FAIL → **wait** (no seller edge today)

---

## Step 5 — Output the analysis

Output in this exact format:

```
## ETF Scanner Pre-Analysis — [today's date]
Source: IBKR Market Screener | [N]/15 ETFs found in screenshot

### Tier 1 — Primary Targets
| ETF | 52W IVR | IV/HV% | Avg Opt Vol | Today | Direction | Score |
|-----|---------|--------|-------------|-------|-----------|-------|
| XLF | 62 ✅  | 118% ✅ | 45K ✅     | +0.4% ↑ | sell_put | 6/6 |
...

### Tier 2 — Structural Liquidity Limit
| ETF | 52W IVR | IV/HV% | Avg Opt Vol | Score |
...

---
### Quick Summary
**GO candidates (score 5–6):** [list]
**CAUTION (score 3–4):** [list]
**Wait — low IV or HV>IV:** [list]
**Not in screenshot:** [list]

### Key Observations
[2–3 sentences: what the scanner data tells you about today's vol regime, standout ETFs, any warnings]
```

---

## Step 6 — Write scanner_cache.json

Use the Write tool to create or overwrite `backend/data/scanner_cache.json` with this structure:

```json
{
  "generated_at": "<ISO 8601 datetime, e.g. 2026-05-20T16:26:05>",
  "source": "ibkr_scanner",
  "ttl_hours": 4,
  "etfs": {
    "TICKER": {
      "ivr_52w": <integer or null>,
      "iv_hv_pct": <float or null>,
      "opt_volume": <integer or null>,
      "avg_opt_volume": <integer or null>,
      "put_call_volume": <float or null>,
      "last_price": <float or null>,
      "change_pct": <float or null>
    }
  }
}
```

Include ALL 15 ETFs. For ETFs NOT found in the screenshot, set all fields to null.

After writing, confirm: `scanner_cache.json updated — [N] ETFs with live data, [15-N] set to null`

The backend reads this file automatically on the next Best Setups scan to fill in IV/HV and IVR gaps (KI-101 fix).
