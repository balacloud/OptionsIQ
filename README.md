# OptionsIQ

**Personal ETF options analysis tool — analysis only, zero orders sent.**

OptionsIQ pulls live options chain data from Interactive Brokers, runs a multi-gate quality framework, ranks the best strike/expiry combinations for vertical spreads, and gives you a step-by-step guide to place the trade on IBKR Client Portal. It covers all four option directions across 16 sector ETFs, with real-time SPY regime awareness and IV Rank scoring.

> **v0.19.0** — Day 27 (April 21, 2026)

---

## What It Does

- **Sector ETF Scanner** — scans 16 sector ETFs (XLK, XLF, XLV, XLE, XLU, etc.) using STA's relative strength data to find which sectors are Leading, Weakening, Improving, or Lagging
- **4-Direction Analysis** — buy call, sell call (bear call spread), buy put, sell put (bull put spread) — each with direction-aware chain fetching and gate evaluation
- **Multi-Gate Quality Framework** — 9+ gates evaluate IV Rank, theta burn, DTE selection, liquidity, market regime, position sizing before any trade recommendation
- **Defined-Risk Spreads** — automatically builds bear call spreads (delta 0.30/0.15) and bull put spreads (delta 0.30/0.15) with exact max profit, max loss, and breakeven
- **IBKR Client Portal Guide** — when verdict is GO, shows step-by-step instructions to place the exact trade on IBKR's web platform
- **Real-Time SPY Regime** — monitors SPY vs 200 SMA, 5-day return, and broad selloff detection (>50% sectors weakening + SPY below 200 SMA)
- **IV Rank Scoring** — percentile-based IVR from 252-day IV history, stored in SQLite, drives buyer/seller strategy selection
- **Paper Trading** — records trades with live mark-to-market P&L tracking

### What It Doesn't Do

- Send orders to IBKR (analysis only — you place trades manually)
- Manage a portfolio or track positions
- Work with individual stocks (ETF-only since v0.15.0)
- Replace your own judgment — it's a decision-support tool

---

## ETF Universe (16 Tickers)

| Sector ETFs | Broad/Leveraged |
|-------------|-----------------|
| XLK (Tech), XLF (Financials), XLV (Healthcare), XLE (Energy), XLU (Utilities), XLI (Industrials), XLY (Consumer Disc.), XLP (Consumer Staples), XLB (Materials), XLRE (Real Estate), XLC (Communications) | MDY (Mid-Cap), IWM (Small-Cap), SCHB (Broad Market), QQQ (Nasdaq 100), TQQQ (3x Nasdaq) |

Non-ETF tickers return HTTP 400 with the full ETF universe list.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Frontend (React, port 3050)                             │
│                                                          │
│  Signal Board UI:                                        │
│    RegimeBar (SPY status) │ ETF Scanner │ Analysis Panel │
│    Click ETF → direction selector → Run Analysis         │
│    Results: Verdict → Gates → Strategies → Execution     │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼─────────────────────────────────┐
│  Backend (Flask, port 5051)                              │
│                                                          │
│  app.py (320 lines — thin route handlers)                │
│  analyze_service.py (604 lines — business logic)         │
│    ├── analyze_etf() — main orchestrator                 │
│    ├── apply_etf_gate_adjustments() — post-processing    │
│    ├── _extract_iv_data() — IV/HV/IVR computation        │
│    └── _behavioral_checks() — regime/IV advisories       │
│                                                          │
│  DataService (provider cascade + SQLite cache)           │
│    → IBWorker (single queue → single IB() thread)        │
│      → IBKRProvider ←→ IB Gateway (port 4001)            │
│    → AlpacaProvider (REST fallback, free)                 │
│    → YFinanceProvider (emergency fallback)                │
│    → MockProvider (dev/CI only)                           │
│                                                          │
│  GateEngine — 9+ quality gates per direction             │
│  StrategyRanker — delta-targeted spread builder          │
│  PnLCalculator — price-relative P&L scenarios            │
│  IVStore — SQLite: IV history, HV, paper trades          │
│  BSCalculator — Black-Scholes greeks (off-hours)         │
└──────────────────────────────────────────────────────────┘

Optional:
  STA (Swing Trade Analyzer, port 5001) — separate project
  Provides: sector rotation data, RS ratios, SPY regime
  If offline: sector scan returns 503, analysis still works
```

### Threading Model

All IBKR calls are serialized through a single dedicated thread to avoid asyncio event-loop conflicts:

```
Flask thread → IBWorker.submit(fn, timeout=24s) → queue.Queue → "ib-worker" thread owns IB()
```

### Data Provider Hierarchy

```
[1] IBKR Live    — reqMktData(snapshot=False), live greeks + bid/ask
[2] IBKR Cache   — SQLite, 2-min TTL
[3] Alpaca       — REST fallback, greeks yes, NO OI/volume
[4] yfinance     — Emergency fallback, BS-computed greeks
[5] Mock         — Dev/CI testing ONLY
```

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.9+ | Backend (tested on 3.9.6) |
| Node.js 18+ | Frontend |
| IB Gateway or TWS | Must be running on port 4001 |
| IBKR account | Paper or live — analysis only, no orders sent |
| IBKR market data | US Options (OPRA) subscription required for greeks |

**Optional:**
- STA (Swing Trade Analyzer) at `localhost:5001` — provides sector rotation data and SPY regime

---

## Setup

```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env — ACCOUNT_SIZE is mandatory:
#   ACCOUNT_SIZE=25000

# 2. Start IB Gateway or TWS
# Settings → API → Enable ActiveX and Socket Clients
# Socket port: 4001, Allow connections from: 127.0.0.1

# 3. Start OptionsIQ
./start.sh

# Frontend:  http://localhost:3050
# Backend:   http://localhost:5051
# Health:    http://localhost:5051/api/health

# 4. Stop
./stop.sh
```

### `.env` Variables

```bash
ACCOUNT_SIZE=25000        # Required — app raises at startup if missing
IBKR_HOST=127.0.0.1       # Optional — default: 127.0.0.1
IBKR_PORT=4001             # Optional — 4001 (IB Gateway) or 7497 (TWS)
IBKR_CLIENT_ID=10          # Optional — default: 10
RISK_PCT=0.01              # Optional — max risk per trade as decimal (1%)
```

---

## How to Use

### Signal Board Workflow

1. Open `http://localhost:3050` — the Signal Board loads automatically
2. **RegimeBar** at the top shows SPY status (above/below 200 SMA, 5-day return)
3. **ETF Scanner** on the left shows all 16 ETFs with quadrant badges:
   - **Leading** (green) → buy_call direction
   - **Improving** (blue) → buy_call direction
   - **Weakening** (amber) → WAIT (no trade)
   - **Lagging** (red) → bear_call_spread direction
4. Click any ETF card → **Analysis Panel** opens on the right
5. Select direction (or use the scanner's suggested direction)
6. Click **Run Analysis** — waits 8-12 seconds for live IBKR data
7. Review results:
   - **Verdict**: GO (green) / CAUTION (amber) / BLOCKED (red)
   - **Gates**: 9+ quality checks with pass/warn/fail
   - **Top Strategies**: ranked spread recommendations with full greeks
   - **Execution Guide**: step-by-step IBKR Client Portal instructions (on GO verdict)
   - **P&L Table**: price-relative scenarios
   - **Advisories**: IV rank context, SPY regime warnings, delta discipline

### Execution Guide (How to Place the Trade)

When the verdict is **GO** and the top strategy is a spread (bear_call_spread or bull_put_spread), an **Execution Card** appears with IBKR Client Portal steps:

1. Log into Client Portal → **Trade** → **Option Chains**
2. Search for the ticker (e.g., XLF)
3. Click **View** dropdown → select **"Vertical Spread"**
4. Select the expiration shown
5. Click **Ask** on the short strike to sell, **Bid** on the long strike to buy
6. Set quantity (start with 1 contract)
7. Set order type: **Limit** at the net credit shown
8. Click **Preview** → verify legs → **Submit**

A **"Copy Trade Details"** button copies the full trade summary to clipboard.

> **Note**: Credit spread limit orders may show "riskless combination" error in Client Portal. Workaround: use TWS desktop app or market order type.

---

## The Four Directions

| Direction | Market View | Strategy Built | Strike Zone | DTE |
|-----------|------------|----------------|-------------|-----|
| buy_call | Strongly Bullish | Long ITM call | 8-20% ITM, delta ~0.68 | 45-90 |
| sell_call | Neutral/Bearish | Bear call spread | OTM, delta 0.30/0.15 | 21-45 |
| buy_put | Strongly Bearish | Long ITM put | 8-20% ITM, delta ~-0.68 | 45-90 |
| sell_put | Neutral/Bullish | Bull put spread | OTM, delta 0.30/0.15 | 21-45 |

### Spread Math (Defined Risk)

**Bear Call Spread** (sell_call direction):
- SELL call at delta ~0.30 (short leg, collects premium)
- BUY call at delta ~0.15 (protection, higher strike)
- Max Profit = net credit × 100
- Max Loss = (width - net credit) × 100
- Breakeven = short strike + net credit

**Bull Put Spread** (sell_put direction):
- SELL put at delta ~0.30 (short leg, collects premium)
- BUY put at delta ~0.15 (protection, lower strike)
- Max Profit = net credit × 100
- Max Loss = (width - net credit) × 100
- Breakeven = short strike - net credit

---

## Quality Gates

Each analysis runs 9+ gates. Every gate is PASS / WARN / FAIL.

| Gate | What It Checks | Buyer | Seller |
|------|---------------|-------|--------|
| **IV Rank** | Is IV cheap or expensive? | IVR < 30% = pass | IVR > 50% = pass |
| **HV/IV Ratio** | Options fairly priced vs realized vol? | IV/HV < 1.5 | IV/HV > 1.0 |
| **Theta Burn** | Will theta erode gains? | < 5% per 7 days | N/A (theta helps sellers) |
| **DTE Selection** | Expiry in sweet spot? | 45-90 DTE | 21-45 DTE |
| **Event Calendar** | Earnings/FOMC near expiry? | Earnings > 21d | Earnings > 21d |
| **Liquidity** | Enough OI and volume? | OI > 100, tight spread | OI > 100, tight spread |
| **Market Regime** | SPY above 200 SMA? | SPY bullish = pass | Varies by direction |
| **Pivot Confirm** | Stock above VCP pivot? | N/A for ETFs | N/A for ETFs |
| **Position Sizing** | Risk ≤ 1% of account? | lots ≥ 1 | max_loss < account % |

**ETF-specific adjustments** (applied after gate evaluation):
- OI=0 promoted to pass (confirmed IBKR platform limitation for ETFs)
- sell_call market regime downgraded to non-blocking (sector weakness overrides SPY trend)
- sell_put max_loss re-evaluated using actual spread width (not naked put math)
- DTE 21-45 promoted to pass for seller directions (ETF sweet spot)

**Verdict:**
- **GO** (green) — all blocking gates pass
- **CAUTION** (amber) — some warns, no blocking fails
- **BLOCKED** (red) — any blocking gate fails

---

## Market Hours Behavior

| Session | Hours (ET) | Data Source | Notes |
|---------|-----------|-------------|-------|
| Regular | 9:30am-4:00pm | `ibkr_live` | Full live greeks, bid/ask, all gates active |
| After-hours | 4pm-9:30am | `ibkr_closed` | BS-estimated greeks (HV proxy), no bid/ask |
| Weekend | All day | `ibkr_closed` | Setup review only — re-analyze at market open |

---

## Sector Rotation (STA-Powered)

The sector scanner uses STA's relative strength data to classify ETFs into quadrants:

| Quadrant | RS Trend | Momentum | Action |
|----------|----------|----------|--------|
| **Leading** | RS > 100, rising | Positive | buy_call |
| **Improving** | RS < 100, rising | Turning positive | buy_call |
| **Weakening** | RS > 100, falling | Turning negative | WAIT (no trade) |
| **Lagging** | RS < 98, falling < -0.5 | Negative | bear_call_spread |

**Broad Selloff Detection**: When >50% of sectors are Weakening/Lagging AND SPY is below 200 SMA, a BROAD SELLOFF banner appears.

**IVR-Driven Direction**: When IVR > 50%, scanner suggests sell_put (premium selling has edge). When IVR < 30%, suggests buy_call (cheap premium).

---

## Backend API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | System health + IBKR connection status |
| POST | `/api/options/analyze` | Main analysis — gates + strategies + verdict |
| GET | `/api/options/chain/{ticker}` | Debug — raw chain data |
| GET | `/api/options/ivr/{ticker}` | Debug — IV rank data |
| GET | `/api/sectors/scan` | L1: All ETFs with quadrant + direction |
| GET | `/api/sectors/analyze/{ticker}` | L2: Single ETF + IV/OI overlay |
| GET | `/api/integrate/sta-fetch/{ticker}` | Fetch swing data from STA |
| POST | `/api/options/paper-trade` | Record a paper trade |
| GET | `/api/options/paper-trades` | List paper trades + P&L |
| POST | `/api/options/seed-iv/{ticker}` | Seed IV history from IBKR |

Full contracts: `docs/stable/API_CONTRACTS.md`

---

## Project Structure

```
options-iq/
├── start.sh / stop.sh           # Start/stop all services
├── CLAUDE_CONTEXT.md             # AI session guide
├── README.md                     # This file
│
├── backend/
│   ├── app.py                    # Flask routes (320 lines — thin wrappers)
│   ├── analyze_service.py        # Business logic (604 lines — Day 24 extraction)
│   ├── constants.py              # All thresholds and config (single source of truth)
│   ├── gate_engine.py            # Gate calculations (frozen, verified)
│   ├── strategy_ranker.py        # Spread builder + ranking
│   ├── pnl_calculator.py         # P&L scenarios (frozen)
│   ├── bs_calculator.py          # Black-Scholes greeks
│   ├── iv_store.py               # IV history + paper trades (SQLite)
│   ├── data_service.py           # Provider cascade + cache
│   ├── ib_worker.py              # Single IBKR thread
│   ├── ibkr_provider.py          # IBKR options chain fetch (readonly)
│   ├── alpaca_provider.py        # Alpaca REST fallback
│   ├── yfinance_provider.py      # Emergency fallback
│   ├── sector_scan_service.py    # STA consumer + sector rotation logic
│   ├── tests/                    # 27 tests (pytest)
│   │   ├── test_bs_calculator.py       # Black-Scholes greeks validation
│   │   ├── test_spread_math.py         # Spread max_loss/profit/breakeven
│   │   ├── test_direction_routing.py   # Direction normalization + strategy routing
│   │   ├── test_gate_engine_etf.py     # ETF gate pass/warn/fail
│   │   └── test_etf_gate_postprocess.py # ETF post-processing adjustments
│   └── data/                     # SQLite databases (gitignored)
│
├── frontend/src/
│   ├── App.jsx                   # Signal Board layout
│   ├── index.css                 # All styles
│   ├── hooks/
│   │   ├── useOptionsData.js     # Analysis API calls
│   │   └── useSectorData.js      # Sector scan API calls
│   └── components/
│       ├── RegimeBar.jsx         # SPY regime status bar
│       ├── ETFCard.jsx           # Scanner card per ETF
│       ├── DirectionSelector.jsx # 4-direction picker
│       ├── MasterVerdict.jsx     # GO/CAUTION/BLOCKED hero
│       ├── GatesGrid.jsx         # Gate results display
│       ├── TopThreeCards.jsx     # Strategy recommendations
│       ├── ExecutionCard.jsx     # IBKR Client Portal trade guide
│       ├── PnLTable.jsx          # P&L scenarios table
│       └── PaperTradeBanner.jsx  # Paper trade recording
│
└── docs/
    ├── stable/                   # Persistent docs
    │   ├── GOLDEN_RULES.md
    │   ├── ROADMAP.md
    │   ├── API_CONTRACTS.md
    │   └── MASTER_AUDIT_FRAMEWORK.md
    ├── versioned/                # Per-session issue tracking
    │   └── KNOWN_ISSUES_DAY*.md
    ├── status/                   # Per-session summaries
    │   └── PROJECT_STATUS_DAY*_SHORT.md
    └── Research/                 # Research docs
        ├── Sector_Rotation_ETF_Module_Day11.md
        └── Sector_Bear_Market_Day19.md
```

---

## Testing

```bash
cd backend
./venv/bin/python -m pytest tests/ -v
```

27 tests covering:
- **Black-Scholes greeks** — delta ranges (ATM/ITM/OTM), theta/vega signs, invalid inputs
- **Spread math** — bear call + bull put: max_loss, max_profit, breakeven correctness
- **Direction routing** — normalization (bear_call_spread → sell_call), all 4 directions route correctly
- **Gate engine (ETF)** — IVR pass/fail thresholds, DTE ranges, verdict logic
- **ETF gate post-processing** — OI=0 promotion, max_loss spread recalc, regime non-blocking, DTE seller promotion

All tests run without IBKR — pure mock data, <1 second total.

---




---

## Version History

| Version | Day | Highlights |
|---------|-----|-----------|
| v0.16.1 | 24 | Structural cleanup: analyze_service.py extraction (app.py 965→320), 27 tests, ExecutionCard visual guide |
| v0.16.0 | 23 | First GO signals (XLF, XLV bear_call_spread). bull_put_spread built. 6 bugs fixed. |
| v0.15.1 | 22 | Live smoke test + 5 ETF gate fixes |
| v0.15.0 | 21 | ETF-Only Pivot. Signal Board UI. 16-ETF universe enforced. All 4 directions tested. |
| v0.14.1 | 20 | ETF liquidity gate BLOCK→WARN, narrow-chain fallback |
| v0.14.0 | 19 | Sector bear market strategies. Lagging→bear_call_spread. Broad selloff detection. |
| v0.13.1 | 17 | First full audit (8 categories). KI-060 SPY gate fix. |
| v0.13.0 | 16 | L2 live test passed (6/7 ETFs). SPY regime from STA. |
| v0.12.0 | 15 | Sector L2 pipeline fixed. Behavioral audit (21 claims). |
| v0.11.0 | 14 | Sector rotation frontend. Tab switcher. |
| v0.10.0 | 13 | Sector rotation backend. Multi-LLM research audit. |
| v0.9.2 | 12 | System hardening. gate_engine Rule 3. SQLite WAL. |
| v0.9 | 10 | Alpaca provider. OI fix. MarketData.app tested. |
| v0.8 | 9 | Live greeks confirmed. bear_call_spread working. |
| v0.7 | 7 | All 4 direction strategies. reqMktData fix. |
| v0.6 | 6 | Market hours detection. BS greeks when closed. |
| v0.5 | 5 | IBWorker heartbeat. STA mapping. Direction locking. |
| v0.3 | 3 | Data layer complete. Live IBKR confirmed. |
| v0.1 | 1 | Project scaffold. |

---

## License

Personal project — not open source.
