# OptionsIQ — Sector Rotation ETF Module Research (Day 11)

> **Date:** March 16, 2026 (updated)
> **Status:** Architecture finalized. STA already provides all rotation data.
> **Goal:** Add a focused ETF options recommendation tab to OptionsIQ

---

## Key Discovery: STA Already Has Everything

STA (localhost:5001) has a fully built sector rotation API:
- `GET /api/sectors/rotation` — cached per trading day, returns instantly
- 11 GICS sectors ranked by RS Ratio vs SPY
- RRG quadrant classification (Leading/Improving/Weakening/Lagging)
- Cap-size rotation (QQQ/MDY/IWM) with Risk-On/Risk-Off/Neutral signal
- Sector→ETF reverse mapping (49 entries covering GICS + TradingView names)

**We do NOT need to build:**
- ~~sector_rotation.py~~ — STA computes RS Ratio + Momentum
- ~~RS calculation logic~~ — STA uses 6-month daily closes, normalized to 100 at midpoint
- ~~Quadrant classifier~~ — STA does this (RS≥100 + Mom≥0 = Leading, etc.)
- ~~Cap-size signal~~ — STA computes IWM-QQQ RS diff (±2 threshold)

**We DO need to build:**
- `sector_scan_service.py` — consumes STA API + adds options-specific analysis
- Backend endpoints for Level 1/2/3
- Frontend tab
- Quadrant→direction mapping logic
- TQQQ-specific rules

---

## STA API Contract

```
GET http://localhost:5001/api/sectors/rotation

Response:
{
  "sectors": [
    {
      "etf": "XLK",           // SPDR ticker
      "name": "Technology",    // Sector name
      "rank": 1,               // 1 = strongest RS Ratio
      "rsRatio": 112.45,       // 100 = parity with SPY
      "rsMomentum": 3.21,      // 10-day RS change
      "quadrant": "Leading",   // Leading/Improving/Weakening/Lagging
      "price": 198.42,         // Current ETF price
      "weekChange": 1.8,       // % change
      "monthChange": 4.2       // % change
    }, ...
  ],
  "sectorCount": 11,
  "mapping": { "Technology": "XLK", ... },  // 49 entries
  "size_rotation": [
    { "etf": "QQQ", "rsRatio": 105.2, "rsMomentum": 1.8 },
    { "etf": "MDY", "rsRatio": 98.1,  "rsMomentum": 0.4 },
    { "etf": "IWM", "rsRatio": 94.3,  "rsMomentum": -1.2 }
  ],
  "size_signal": "Risk-Off",         // Risk-On/Risk-Off/Neutral
  "size_signal_detail": "Large caps favored — defensive posture",
  "timestamp": "2026-03-16T09:30:00",
  "cached": true
}
```

### RS Formula (verified from STA source)
```python
rs_line = etf_close / spy_close                          # raw ratio
rs_normalized = (rs_line / rs_line.iloc[midpoint]) * 100  # normalize at 3-mo midpoint
rs_ratio = rs_normalized.iloc[-1]                         # current value
rs_momentum = rs_normalized.iloc[-1] - rs_normalized.iloc[-10]  # 10-day delta
```

### Quadrant Thresholds
| Quadrant | rsRatio | rsMomentum |
|----------|---------|------------|
| Leading | ≥ 100 | ≥ 0 |
| Weakening | ≥ 100 | < 0 |
| Improving | < 100 | ≥ 0 |
| Lagging | < 100 | < 0 |

### Cap Size Signal
```python
diff = iwm_rsRatio - qqq_rsRatio
if diff >= +2:  "Risk-On"    # small caps beating large
if diff <= -2:  "Risk-Off"   # large caps dominating
else:           "Neutral"
```

---

## Perplexity Research Findings (verified)

### Strategy Per Quadrant (from research — [PLAUSIBLE], needs backtest)

| Quadrant | Direction | Strategy | DTE | Rationale |
|----------|-----------|----------|-----|-----------|
| **Leading** | buy_call | Bull call spread | 30-45 | Trend confirmed, cap risk with spread |
| **Improving** | buy_call | Long call (ATM-OTM) | 45-60 | Needs time for RS to build |
| **Weakening** | sell_call | Bear call spread OR skip | 30-45 | Fading momentum, sell premium |
| **Lagging** | skip OR buy_put | No position preferred | — | ETFs mean-revert; falling knives |

**Our modification:** Weakening = `sell_call` (not "skip"). Lagging = skip by default,
allow `buy_put` only if RS momentum < -5 (strong breakdown signal).

### Cap Size Signal → Position Bias

| Signal | Interpretation | Options Bias |
|--------|---------------|-------------|
| Risk-On | Small > Large by 2+ pts | Favor cyclical sectors (XLI, XLY, XLB) calls |
| Risk-Off | Large > Small by 2+ pts | Favor defensive (XLU, XLV, XLP) or QQQ puts |
| Neutral | Mixed | No size-based bias, pure sector signals |

### TQQQ Rules (verified from research)

| Rule | Source | Details |
|------|--------|---------|
| Max DTE: 30-45 | tastylive research | Volatility decay accelerates beyond 45 days |
| No covered calls | Seeking Alpha verified | Extreme rises capped, doesn't compensate drops |
| Credit spreads OK | Market Chameleon | 7-14 DTE bear call spreads viable, exit at 50% |
| Decay formula | Mathematical | Daily decay ≈ 3 × variance² |

### DTE By IV Rank (verified — tastylive source)

| IVR Range | Recommended DTE |
|-----------|----------------|
| < 30 (low IV) | 60 DTE |
| 30-70 | 45 DTE |
| > 70 (high IV) | 30 DTE |

### ETF Liquidity (verified — apexvol.com)

| ETF | Daily Volume | OI | ATM Spread | Weekly Options |
|-----|-------------|-----|-----------|----------------|
| QQQ | 2M+ | 10M+ | $0.01-0.02 | Yes |
| IWM | 800K+ | 6M+ | $0.02-0.05 | Yes |
| XLF | 600K+ | 5M+ | $0.01-0.02 | Yes |
| XLE | 500K+ | 4M+ | $0.01-0.03 | Yes |
| XLI | 175K+ | 2M+ | $0.02-0.05 | Yes |
| XLK | 150K+ | 2M+ | $0.02-0.04 | Yes |
| XLV | 150K+ | 2M+ | $0.02-0.04 | Yes |
| MDY | 50K+ | 800K+ | $0.05-0.10 | Yes |

All 11 SPDR sector ETFs have weekly options. All are liquid enough for retail.

---

## Revised Architecture (STA-powered)

### What OptionsIQ Builds

```
STA (port 5001)                    OptionsIQ (port 5051)
┌─────────────────┐                ┌──────────────────────────┐
│ /api/sectors/    │  ──GET──►     │ sector_scan_service.py    │
│   rotation       │               │  - consumes STA data      │
│                  │               │  - adds direction mapping  │
│ Already built:   │               │  - adds IV/options layer   │
│  - RS Ratio      │               │                           │
│  - Quadrants     │               │ Level 1: /api/sectors/scan│
│  - Cap size      │               │  = STA data + direction   │
│  - Mapping       │               │  + IV percentile          │
└─────────────────┘               │                           │
                                   │ Level 2: /api/sectors/    │
                                   │   analyze/{ticker}        │
                                   │  = L1 + options chain     │
                                   │  + OI + bid-ask spread    │
                                   │                           │
                                   │ Level 3: /api/options/    │
                                   │   analyze (existing!)     │
                                   │  = full gate + strategy   │
                                   └──────────────────────────┘
```

### Level 1 — Quick Scan (< 2 sec, all 15 ETFs)

**Data source:** STA API only (+ yfinance for SPY 200SMA)

| Field | Type | Source |
|-------|------|--------|
| etf | str | STA sectors[].etf |
| name | str | STA sectors[].name |
| rank | int | STA sectors[].rank |
| rs_ratio | float | STA sectors[].rsRatio |
| rs_momentum | float | STA sectors[].rsMomentum |
| quadrant | str | STA sectors[].quadrant |
| price | float | STA sectors[].price |
| week_change | float | STA sectors[].weekChange |
| month_change | float | STA sectors[].monthChange |
| size_signal | str | STA size_signal |
| suggested_direction | str | Computed: quadrant → direction mapping |
| action | str | "ANALYZE" / "SKIP" / "WATCH" |

**Direction mapping logic:**
```python
def quadrant_to_direction(quadrant, rs_momentum, size_signal):
    if quadrant == "Leading":
        return "buy_call"
    elif quadrant == "Improving":
        return "buy_call"  # longer DTE
    elif quadrant == "Weakening":
        return "sell_call"
    elif quadrant == "Lagging":
        if rs_momentum < -5:
            return "buy_put"  # strong breakdown only
        return None  # skip
```

**Action logic:**
```python
if direction is not None and quadrant in ("Leading", "Improving"):
    action = "ANALYZE"
elif quadrant == "Weakening" and size_signal == "Risk-Off":
    action = "ANALYZE"  # sell premium in fading sectors during risk-off
else:
    action = "SKIP"
```

### Level 2 — Standard Analysis (10-15 sec per ETF)

**Data source:** STA + IBKR (reqMktData for ATM options)

| Field | Type | Source | New? |
|-------|------|--------|------|
| *all Level 1 fields* | | | |
| iv_current | float | IBKR or Alpaca | Yes |
| iv_percentile | float | IBKR reqHistoricalData | Yes |
| hv_20 | float | Computed from yfinance | Existing |
| iv_hv_ratio | float | Derived | Yes |
| atm_call_oi | int | IBKR | Yes |
| atm_put_oi | int | IBKR | Yes |
| bid_ask_spread_pct | float | IBKR | Yes |
| suggested_dte | int | IVR-based (tastylive rules) | Yes |
| catalyst_warning | str | Sector-specific (FOMC, OPEC, earnings) | Yes |

**DTE selection (from verified tastylive research):**
```python
if iv_percentile < 30:
    suggested_dte = 60
elif iv_percentile < 70:
    suggested_dte = 45
else:
    suggested_dte = 30

# TQQQ override
if etf == "TQQQ":
    suggested_dte = min(suggested_dte, 45)  # never > 45 DTE
```

### Level 3 — Full Analysis (existing endpoint)

Reuses `POST /api/options/analyze` with `ticker=XLK` and `direction=buy_call`.
**Zero new code needed.** Gate engine, strategy ranker, PnL calculator all work for ETFs.

### TQQQ Special Rules

```python
TQQQ_RULES = {
    "max_dte": 45,                    # volatility decay
    "allowed_directions": ["buy_call", "sell_call"],  # no naked puts on 3x leverage
    "sell_call_only": "bear_call_spread",  # never naked short on TQQQ
    "warning": "3x leveraged ETF — volatility decay, max 45 DTE, no covered calls",
}
```

---

## New Files Needed

```
backend/
  sector_scan_service.py   — STA consumer + quadrant→direction + IV overlay
                             ~150 lines. Endpoints: scan (L1) + analyze (L2)

frontend/src/
  components/SectorRotation.jsx   — new tab/page
  components/ETFCard.jsx          — sector card with quadrant badge + action button
  components/CapSizeStrip.jsx     — QQQ/MDY/IWM strip (reuse STA design)
```

### Backend Endpoints

```
GET  /api/sectors/scan              → Level 1 (all 15 ETFs, < 2 sec)
GET  /api/sectors/analyze/{ticker}  → Level 2 (single ETF, 10-15 sec)
POST /api/options/analyze           → Level 3 (existing, zero changes)
```

---

## Implementation Plan

```
Day 12 (market hours):
  - Behavioral audit fixes (Tier 1 + Tier 2)
  - Verify KI-035 OI fix

Day 13:
  - Create sector_scan_service.py (STA consumer + L1 + L2 endpoints)
  - Test with STA running: verify quadrant→direction mapping
  - Wire TQQQ rules

Day 14:
  - Frontend: SectorRotation tab + ETF cards
  - Integration test: L1 scan → click ETF → L2 → click "Deep Dive" → L3

No external research needed. STA provides rotation data. IBKR provides options data.
```

---

## Open Questions (resolved)

| Question | Answer |
|----------|--------|
| RS formula alignment? | ✅ STA formula verified: 6-mo closes, normalize at midpoint, 10-day delta |
| Sector ETFs liquid enough? | ✅ All 11 have weekly options, tight spreads |
| TQQQ options viable? | ✅ Buy calls OK, credit spreads 7-14 DTE, no covered calls |
| Level 3 new code? | ✅ No — reuses existing analyze endpoint |
| Need external data API? | ✅ No — IBKR + STA covers everything |
| RS recalc frequency? | Weekly (STA caches per trading day) |
