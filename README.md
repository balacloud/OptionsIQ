# OptionsIQ

**Personal ETF options analysis tool — analysis only, zero orders sent.**

OptionsIQ scans 15 sector ETFs using STA's relative-strength data, runs a multi-gate quality framework against live Tradier options chain data, and recommends the best strike/expiry for defined-risk vertical spreads. It covers all four directions (buy call, sell call, buy put, sell put) with empirically grounded gate thresholds and a step-by-step IBKR Client Portal execution guide.

> **v0.32.0** — Day 49 (May 8, 2026)

---

## What It Does

- **Best Setups Tab** (home screen) — parallel scan of all 15 ETFs, surfaces GO/CAUTION candidates ranked by gate pass rate
- **Sector ETF Scanner** — classifies ETFs into Leading/Improving/Weakening/Lagging quadrants via STA relative-strength data
- **4-Direction Analysis** — buy call, sell call (bear call spread), buy put, sell put (bull put spread) with direction-aware chain fetching and gate evaluation
- **Multi-Gate Quality Framework** — 10+ gates: IV Rank, Vol Risk Premium (Sinclair), VIX regime, DTE window, event calendar (FOMC/CPI/NFP/PCE), liquidity, market regime, McMillan stress check, position sizing, ETF holdings earnings risk
- **Defined-Risk Spreads** — builds bear call spreads and bull put spreads (delta 0.30/0.15) with exact max profit, max loss, and breakeven
- **IBKR Client Portal Guide** — on GO verdict: step-by-step instructions to place the exact trade
- **IV Rank Scoring** — percentile IVR from 252-day IV history (SQLite), seeded nightly via IBKR
- **Paper Trading** — records trades with live mark-to-market P&L, win rate tracking
- **Data Provenance Tab** — shows chain source quality (Tradier/BOD cache/stale/Alpaca/yfinance), batch run history, per-ETF IV coverage

### What It Doesn't Do

- Send orders to IBKR (analysis only — you place trades manually)
- Work with individual stocks (ETF-only since v0.15.0)
- Backtest (deferred — rationale in ROADMAP.md)
- Replace your own judgment — decision-support tool only

---

## ETF Universe (15 Tickers)

| Sector ETFs | Broad / Leveraged |
|-------------|-------------------|
| XLK (Tech), XLF (Financials), XLV (Healthcare), XLE (Energy), XLU (Utilities), XLI (Industrials), XLY (Consumer Disc.), XLP (Consumer Staples), XLB (Materials), XLRE (Real Estate), XLC (Communications) | MDY (Mid-Cap), IWM (Small-Cap), QQQ (Nasdaq 100), TQQQ (3× Nasdaq) |

Non-ETF tickers return HTTP 400 with the full ETF universe list.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (React, port 3050)                                 │
│                                                              │
│  Tabs: Best Setups (home) │ Signal Board │ Learn │ Provenance│
│                                                              │
│  Best Setups: auto-scan all 15 ETFs → GO/CAUTION cards       │
│  Signal Board: RegimeBar → ETF Scanner → Analysis Panel      │
│  Analysis Panel: Verdict → Gates → Strategies → Execution    │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼─────────────────────────────────────┐
│  Backend (Flask, port 5051)                                  │
│                                                              │
│  app.py (402 lines — thin route handlers only)               │
│  analyze_service.py (887 lines — main analysis orchestrator) │
│  sector_scan_service.py — STA consumer + quadrant logic      │
│  best_setups_service.py — single-ETF scan worker             │
│  sta_service.py — STA HTTP fetch + SPY regime computation    │
│  batch_service.py (238 lines) — BOD/EOD batch jobs           │
│  gate_engine.py (1217 lines — frozen, verified)              │
│  strategy_ranker.py — delta-targeted spread builder          │
│  pnl_calculator.py — price-relative P&L scenarios            │
│  iv_store.py — SQLite: IV history, OHLCV, paper trades       │
│  bs_calculator.py — Black-Scholes greeks (off-hours)         │
│                                                              │
│  Data Provider Cascade (DataService):                        │
│    [1] BOD Cache (SQLite, pre-warmed 9:31 AM ET)             │
│    [2] Tradier REST (real-time, free brokerage account) ←PRIMARY│
│    [3] Stale BOD Cache (last known-good)                     │
│    [4] Alpaca (15-min delayed REST, greeks via BS)           │
│    [5] yfinance (emergency fallback, BS greeks)              │
│    [6] Mock (dev/CI only — never for paper trades)           │
│                                                              │
│  IBKR used only by: EOD batch → reqHistoricalData for IV     │
│  MarketData.app: OI/volume supplement (Free tier, ~33/day)   │
└──────────────────────────────────────────────────────────────┘

Optional:
  STA (Swing Trade Analyzer, port 5001) — separate project
  Provides: sector rotation quadrants, RS ratios, SPY regime, VIX
  If offline: sector scan returns 503, analysis still works via Manual mode
  
  IB Gateway (port 4001) — needed only for:
    EOD batch (4:05 PM ET): reqHistoricalData OPTION_IMPLIED_VOLATILITY → iv_history.db
    NOT needed for live chain data (Tradier handles that)
```

### Threading Model

All IBKR calls are serialized through a single dedicated thread:

```
Flask thread → IBWorker.submit(fn, timeout=24s) → queue.Queue → "ib-worker" thread owns IB()
```

### Batch Infrastructure (APScheduler)

```
9:31 AM ET (Mon-Fri) — BOD batch: pre-warms all 15 ETF chains into SQLite
4:05 PM ET (Mon-Fri) — EOD batch: seeds IV history via IBKR reqHistoricalData
Startup:              run_startup_catchup() fires any missed BOD/EOD from prev session
```

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.9+ | Backend (tested on 3.9.6) |
| Node.js 18+ | Frontend |
| Tradier account | Free brokerage account — no paid subscription needed |
| STA (optional) | `localhost:5001` — sector scan + SPY regime. Falls back to Manual if offline |
| IB Gateway (optional) | Port 4001 — only needed for EOD IV seeding. Not required for live analysis |

---

## Setup

```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env — required fields:
#   ACCOUNT_SIZE=25000
#   TRADIER_KEY=<your_tradier_api_token>

# 2. Start OptionsIQ
./start.sh

# Frontend:  http://localhost:3050
# Backend:   http://localhost:5051/api/health

# 3. (Optional) Start IB Gateway for IV seeding
# Settings → API → Enable Socket Clients → port 4001

# 4. Stop
./stop.sh
```

### `.env` Variables

```bash
ACCOUNT_SIZE=25000        # Required — app raises at startup if missing
TRADIER_KEY=<token>       # Required — Tradier free brokerage API token
IBKR_HOST=127.0.0.1       # Optional — default: 127.0.0.1
IBKR_PORT=4001             # Optional — 4001 (IB Gateway) or 7497 (TWS)
IBKR_CLIENT_ID=10          # Optional — default: 10
RISK_PCT=0.01              # Optional — max risk per trade as decimal (1%)
MARKET_DATA_KEY=<token>    # Optional — MarketData.app (Free tier, OI/volume supplement)
```

---

## How to Use

### Best Setups (Home Tab)

1. Open `http://localhost:3050` — Best Setups auto-scan loads on startup
2. The scan runs all 15 ETFs sequentially and surfaces GO/CAUTION candidates
3. Click **Run Scan** to refresh manually
4. Each card shows: verdict, pass rate, IVR, IV/HV ratio, top strategy + credit
5. Click a card → jumps to Signal Board with that ETF pre-loaded

### Signal Board Workflow

1. **RegimeBar** at the top shows VIX level (color-coded) + SPY status
2. **ETF Scanner** on the left shows all 15 ETFs with quadrant badges:
   - **Leading** (green) → sell_put / buy_call direction
   - **Improving** (blue) → buy_call direction
   - **Weakening** (amber) → WAIT (no trade — defensive inflows risk)
   - **Lagging** (red) → bear_call_spread direction
3. Click any ETF card → **Analysis Panel** opens on the right
4. Select direction, click **Run Analysis**
5. Review results:
   - **Verdict**: GO (green) / CAUTION (amber) / BLOCKED (red)
   - **Gates**: 10+ quality checks — each with pass/warn/fail and reason text
   - **Top Strategies**: ranked spread recommendations with full greeks
   - **Execution Guide**: step-by-step IBKR Client Portal instructions (on GO verdict)
   - **P&L Table**: price-relative scenarios at expiry

### Pre-Trade Research

Before taking a GO or CAUTION trade, use the 7 research prompts in `docs/Research/Daily_Trade_Prompts.md` — paste them into Perplexity, ChatGPT, or Gemini for macro context, sector rotation confirmation, and adversarial review.

---

## The Four Directions

| Direction | Market View | Strategy Built | Strike Zone | DTE Entry |
|-----------|------------|----------------|-------------|-----------|
| buy_call | Strongly Bullish | Long ITM call | 8-20% ITM, delta ~0.68 | 45-90 |
| sell_call | Neutral/Bearish | Bear call spread | OTM, delta 0.30/0.15 | 30-45 |
| buy_put | Strongly Bearish | Long ITM put | 8-20% ITM, delta ~-0.68 | 45-90 |
| sell_put | Neutral/Bullish | Bull put spread | OTM, delta 0.30/0.15 | 30-45 |

**DTE note for sellers:** Entry floor is 30 DTE (raised from 21 in v0.30.1). Opening at 21 DTE enters the gamma acceleration zone — tastylive 200k+ trade research shows the 45→21 DTE window captures 46% of profit at 2× the Sharpe ratio. 21 DTE = management exit, not entry.

---

## Quality Gates

Each analysis runs 10+ gates. Every gate is PASS / WARN / FAIL with a reason string.

| Gate | What It Checks |
|------|----------------|
| **IV Rank (Seller)** | IVR ≥ 35% = pass (tastylive: 50% threshold sacrifices 60-70% of frequency) |
| **Vol Risk Premium** | IV > HV (Sinclair): only sell when implied vol exceeds realized vol |
| **VIX Regime** | VIX < 15 = warn (thin vol). VIX > 30 = warn. VIX > 40 = fail |
| **DTE Window** | Sellers: 30-45 DTE pass, <30 warn. Buyers: 45-90 DTE |
| **Event Calendar** | Earnings inside DTE = fail. FOMC/CPI/NFP/PCE within 10d = warn |
| **Liquidity Proxy** | Bid-ask spread >20% = blocking fail. OI=0 = non-blocking warn (platform limit) |
| **Market Regime** | Sellers: flat/weak SPY = pass. Strong bull = warn/fail |
| **McMillan Stress** | Short strike inside historical 21-day worst-drawdown (sell_put) or rally (sell_call) = warn |
| **Credit-to-Width** | Spread credit/width ≥ 33% (tastylive/Sinclair minimum) |
| **Key Holdings Earnings** | ETF holdings with earnings before expiry = warn |

**Verdict:**
- **GO** (green) — no blocking gate fails
- **CAUTION** (amber) — one or more non-blocking warns, no blocking fails
- **BLOCKED** (red) — any blocking gate fails

---

## Sector Rotation Logic

| Quadrant | Conditions | Direction |
|----------|-----------|-----------|
| **Leading** | RS > 100, rising | sell_put or buy_call (IVR-driven) |
| **Improving** | RS < 100, rising | buy_call |
| **Weakening** | RS > 100, falling | WAIT — defensive inflows risk call assignment |
| **Lagging** | RS < 98, momentum < −0.5 | bear_call_spread |

**Broad Selloff Detection**: >50% of sectors Weakening/Lagging AND SPY below 200 SMA → BROAD SELLOFF banner.

---

## Backend API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | System health — IBKR, Tradier, circuit breaker |
| POST | `/api/options/analyze` | Main analysis — gates + strategies + verdict |
| GET | `/api/best-setups` | Scan all 15 ETFs → ranked GO/CAUTION list |
| GET | `/api/sectors/scan` | L1: all ETFs with quadrant + suggested direction |
| GET | `/api/sectors/analyze/{ticker}` | L2: single ETF IV/OI overlay |
| GET | `/api/data-health` | Data provenance — source quality per ETF per field |
| GET | `/api/admin/batch-status` | Last 10 BOD/EOD batch runs + next scheduled times |
| POST | `/api/admin/warm-cache` | Trigger BOD cache warm manually |
| POST | `/api/admin/seed-iv/all` | Trigger EOD IV seed manually |
| POST | `/api/options/seed-iv/{ticker}` | Seed IV history for one ticker |
| POST | `/api/options/paper-trade` | Record a paper trade |
| PATCH | `/api/options/paper-trade/{id}` | Update mark price or close a trade |
| DELETE | `/api/options/paper-trade/{id}` | Delete a trade |
| GET | `/api/options/paper-trades` | List trades + live mark-to-market P&L |
| GET | `/api/options/paper-trades/summary` | Win rate + equity curve |
| GET | `/api/integrate/sta-fetch/{ticker}` | Fetch swing data from STA |
| GET | `/api/options/chain/{ticker}` | Debug — raw chain data |
| GET | `/api/options/ivr/{ticker}` | Debug — IV rank data |

Full contracts: `docs/stable/API_CONTRACTS.md`

---

## Project Structure

```
options-iq/
├── start.sh / stop.sh
├── CLAUDE_CONTEXT.md              # AI session guide
│
├── backend/
│   ├── app.py                     # Flask routes (402 lines — thin wrappers only)
│   ├── analyze_service.py         # Main analysis orchestrator (887 lines)
│   ├── sector_scan_service.py     # STA consumer + quadrant → direction logic
│   ├── best_setups_service.py     # Single-ETF scan worker (extracted Day 39)
│   ├── sta_service.py             # STA HTTP fetch + SPY metrics (extracted Day 46)
│   ├── batch_service.py           # BOD/EOD batch jobs + startup catch-up (238 lines)
│   ├── gate_engine.py             # Gate calculations (frozen, verified — 1217 lines)
│   ├── strategy_ranker.py         # Spread builder + ranking
│   ├── pnl_calculator.py          # P&L scenarios (frozen)
│   ├── bs_calculator.py           # Black-Scholes greeks
│   ├── iv_store.py                # SQLite: IV history, OHLCV, paper trades, batch log
│   ├── constants.py               # All thresholds (single source of truth)
│   ├── data_service.py            # Provider cascade + SQLite cache + circuit breaker
│   ├── data_health_service.py     # Per-ETF per-field data quality report
│   ├── tradier_provider.py        # Tradier REST — primary live chain (346 lines)
│   ├── ib_worker.py               # Single IBKR thread (queue + heartbeat)
│   ├── ibkr_provider.py           # IBKR options chain fetch (readonly — EOD only)
│   ├── marketdata_provider.py     # MarketData.app OI/volume + greeks supplement
│   ├── alpaca_provider.py         # Alpaca REST fallback (greeks, no OI)
│   ├── yfinance_provider.py       # Emergency fallback (BS-computed greeks)
│   ├── mock_provider.py           # Dev/CI only
│   └── tests/                     # 36 tests (pytest — no IBKR required)
│       ├── test_bs_calculator.py
│       ├── test_spread_math.py
│       ├── test_direction_routing.py
│       ├── test_gate_engine_etf.py
│       ├── test_etf_gate_postprocess.py
│       └── test_resolve_underlying_hint.py
│
├── frontend/src/
│   ├── App.jsx                    # Tab layout: Best Setups / Signal Board / Learn / Provenance
│   ├── index.css
│   ├── hooks/
│   │   ├── useOptionsData.js
│   │   └── useSectorData.js
│   └── components/
│       ├── BestSetups.jsx         # Home tab — parallel ETF scan, GO/CAUTION cards
│       ├── RegimeBar.jsx          # VIX badge + SPY regime status bar
│       ├── SectorRotation.jsx     # Sector rotation panel
│       ├── ETFCard.jsx            # Per-ETF scanner card
│       ├── DirectionGuide.jsx     # Educational 2×2 direction selector
│       ├── MasterVerdict.jsx      # GO/CAUTION/BLOCKED verdict hero
│       ├── GateExplainer.jsx      # Gate accordion with plain-English Q&A
│       ├── TopThreeCards.jsx      # Top 3 strategy recommendations
│       ├── TradeExplainer.jsx     # Number line + risk/reward bar
│       ├── ExecutionCard.jsx      # IBKR Client Portal step-by-step guide
│       ├── PnLTable.jsx           # P&L scenarios table
│       ├── LearnTab.jsx           # 5-panel interactive options education
│       ├── PaperTradeBanner.jsx   # Paper trade recording
│       ├── PaperTradeDashboard.jsx# Paper trade P&L + win rate
│       ├── DataProvenance.jsx     # Data source health + batch status
│       ├── PreAnalysisPrompts.jsx # Copyable pre-trade research prompts
│       ├── CopyForChatGPT.jsx     # One-click trade summary for ChatGPT
│       ├── BehavioralChecks.jsx   # Advisory warnings
│       ├── DirectionSelector.jsx
│       ├── GatesGrid.jsx
│       ├── Header.jsx
│       └── SwingImportStrip.jsx   # STA swing data import
│
└── docs/
    ├── stable/
    │   ├── GOLDEN_RULES.md
    │   ├── ROADMAP.md
    │   ├── API_CONTRACTS.md
    │   └── MASTER_AUDIT_FRAMEWORK.md  # 10-category audit (Category 10: Trading Effectiveness)
    ├── versioned/KNOWN_ISSUES_DAY*.md
    ├── status/PROJECT_STATUS_DAY*_SHORT.md
    └── Research/
        ├── Phase7c_Research.md                     # Phase 7c: scan findings, fixes, audit prompts, roadmap
        ├── Daily_Trade_Prompts.md                  # 7 pre-trade research prompts
        ├── data-providers/DATA_PROVIDERS_SYNTHESIS.md
        └── [sector-rotation/, ux-design/, ki-plans/, ...]
```

---

## Testing

```bash
cd backend
./venv/bin/python -m pytest tests/ -v
```

36 tests, no IBKR required, <1 second total:

| File | What It Covers |
|------|----------------|
| `test_bs_calculator.py` | Delta ranges (ATM/ITM/OTM), theta/vega signs, invalid inputs |
| `test_spread_math.py` | bear call + bull put: max_loss, max_profit, breakeven |
| `test_direction_routing.py` | Direction normalization, all 4 directions route correctly |
| `test_gate_engine_etf.py` | IVR pass/fail thresholds, DTE ranges (30-45 seller), verdict logic |
| `test_etf_gate_postprocess.py` | OI=0 promotion, max_loss spread recalc, regime non-blocking |
| `test_resolve_underlying_hint.py` | STA price fallback, underlying price cascade |

---

## Version History

| Version | Day | Highlights |
|---------|-----|-----------|
| v0.30.1 | 46 | KI-086 closed (sta_service.py extracted, app.py 402 lines). ETF sell_call DTE gate fixed (_run_etf_sell_call). ETF_DTE_SELLER_PASS_MIN 21→30 (tastylive 200k+ research). |
| v0.30.0 | 43-45 | Defect sweep + verification. KI-064/075/076/077/081 resolved. MASTER_AUDIT_FRAMEWORK v1.4: Category 10 (Trading Effectiveness). |
| v0.29.0 | 42 | compute_skew() (Tradier 30-delta put/call IV spread). Full audit: 0C/2H/3M all resolved. |
| v0.28.1 | 40 | Tradier production-ready. KI-090/091/092/093 resolved (delta coercion, OTM filter, bod_cache rename). |
| v0.28.0 | 39 | **Tradier primary.** IBKR removed from live chain path (EOD batch only). best_setups_service.py. QQQ sell_put ITM fix. |
| v0.27.0 | 37 | Startup catch-up (missed BOD/EOD). yfinance HV removed from IV seeding. Research folder reorganized. |
| v0.26.0 | 35 | APScheduler BOD/EOD batch. batch_service.py. Batch status dashboard. MarketData.app credit tracking. |
| v0.25.1 | 34 | KI-088: _resolve_underlying_hint() — STA canonical for underlying price. |
| v0.25.0 | 33 | Best Setups scan reliability overhaul (8 fixes). 6 CAUTION setups confirmed live. |
| v0.24.0 | 32 | VRP gate inversion fix. IV/HV column in Best Setups. |
| v0.23.0 | 31 | LearnTab redesign. Paper trade workflow rebuilt. Best Setups as home screen. VIX badge. |
| v0.22.0 | 30 | McMillan stress check. OHLCV cleanup (XLE/IWM corrupted rows deleted). 33 tests. |
| v0.21.0 | 29 | Gate hardening: credit-to-width 33%, VRP gate, VIX regime gate, IVR threshold 50%→35%. Data Health tab. Best Setups tab. Paper Trade Dashboard. |
| v0.20.0 | 28 | ETF holdings earnings gate (52 companies). Bid-ask >20% hard block. FOMC inside-window fix. |
| v0.19.0 | 27 | Full audit (0C/0H). bull_put_spread P&L fix. MarketData.app OI supplement. Daily_Trade_Prompts.md. |
| v0.18.0 | 26 | IV seeding (7,492 rows). FOMC gate fixed. MasterVerdict pass chips. |
| v0.17.0 | 25 | Phase 8 UX overhaul. DirectionGuide, TradeExplainer, GateExplainer, LearnTab. |
| v0.16.1 | 24 | analyze_service.py extraction. 27 tests. ExecutionCard visual guide. |
| v0.15.0 | 21 | **ETF-Only Pivot.** 15-ETF universe. Signal Board UI. All 4 directions tested. |
| v0.14.0 | 19 | Sector bear strategies. Lagging→bear_call_spread. Broad selloff detection. |
| v0.10.0 | 13 | Sector rotation backend. Multi-LLM research audit. sector_scan_service.py. |
| v0.9.2 | 12 | System hardening. gate_engine constants. SQLite WAL. sell_put naked warning. |
| v0.3 | 3 | Data layer complete. IBWorker. DataService cascade. Live IBKR confirmed. |
| v0.1 | 1 | Project scaffold. |

---

## License

Personal project — not open source.
