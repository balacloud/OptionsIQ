# OptionsIQ

**Personal options analysis tool — analysis only, zero orders sent.**

Takes a stock ticker, pulls the live options chain from IBKR, runs a multi-gate quality check, and recommends the top 3 strike/expiry combinations for your chosen direction (buy call, sell call, buy put, sell put). Records paper trades with live mark-to-market P&L.

---

## What It Is (and Isn't)

| ✅ What it does | ❌ What it doesn't do |
|---|---|
| Pulls live options chain from IBKR | Send orders to IBKR |
| Evaluates 9 quality gates per setup | Manage a portfolio |
| Recommends top 3 strike/expiry combos | Guarantee any outcome |
| Records paper trades + tracks P&L | Execute real trades |
| Integrates with STA for swing context | Replace your own judgment |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React, port 3050)                            │
│  Ticker input → Direction → Analyze → Results display   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST /api/options/analyze
┌────────────────────────▼────────────────────────────────┐
│  Backend (Flask, port 5051)                             │
│                                                         │
│  app.py (routes)                                        │
│    ↓                                                    │
│  DataService (provider cascade + SQLite cache)          │
│    ↓                                                    │
│  IBWorker (single queue → single IB() thread)           │
│    ↓                                                    │
│  IBKRProvider ←→ IB Gateway (port 4001)                 │
│                                                         │
│  Fallback: yfinance → mock (CI only)                    │
└─────────────────────────────────────────────────────────┘

Optional:
  STA (Swing Trade Analyzer, port 5001) — separate project
  Provides: swing signal, entry/stop/target, ADX, VCP pattern
  If offline: manual mode, user enters fields directly
```

### Threading Model

All IBKR calls are serialised through a single dedicated thread:

```
Flask thread → IBWorker.submit(fn, timeout=24s)
                    ↓
             queue.Queue (thread-safe)
                    ↓
            "ib-worker" thread owns IB()
            → IBKRProvider.get_options_chain()
```

**Why:** `ib_insync` uses asyncio internally. Multiple Flask threads calling it directly causes event-loop conflicts and silent hangs. One thread, one IB() instance — safe.

### Data Provider Hierarchy (live-first)

```
[1] IBKR Live    reqMarketDataType=1 — default
[2] IBKR Cache   SQLite, 2-min TTL — "Using cached chain" banner
[3] yfinance     Emergency fallback — "Live data unavailable" banner
[4] Mock         CI/dev testing ONLY — never for paper trades
```

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Backend |
| Node.js | 18+ | Frontend |
| IB Gateway or TWS | Latest | Must be running, port 4001 |
| IBKR account | Any | Paper or live — analysis only |
| IBKR market data subscription | US Options (OPRA) | Required for greeks |

**Optional:**
- STA (Swing Trade Analyzer) running at `localhost:5001` — auto-fills swing fields

---

## Setup

```bash
# 1. Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env: set ACCOUNT_SIZE=25000 (your account size in USD)

# 2. Start IB Gateway or TWS
# Settings → API → Enable ActiveX and Socket Clients
# Socket port: 4001, Allow connections from: 127.0.0.1

# 3. Start OptionsIQ
./start.sh

# Access:
#   Frontend:  http://localhost:3050
#   Backend:   http://localhost:5051
#   Health:    http://localhost:5051/api/health

# 4. Stop
./stop.sh
```

### `.env` Variables

```bash
ACCOUNT_SIZE=25000        # Required — your account size in USD
IBKR_HOST=127.0.0.1       # Optional — default: 127.0.0.1
IBKR_PORT=7497            # Optional — default: 7497 (TWS) or 4001 (IB Gateway)
IBKR_CLIENT_ID=10         # Optional — default: 10
```

> **ACCOUNT_SIZE is mandatory.** The app raises at startup if not set. No default — you must be conscious of your position sizing.

---

## How to Use

### Basic Workflow

1. Open `http://localhost:3050`
2. If STA is running — Swing Data section shows **STA Live** badge and auto-fills entry/stop/target
3. Type a ticker (e.g. `AMD`)
4. Select direction based on your market view:
   - **Buy Call** — you expect strong move up (delta ~0.68, 45-90 DTE)
   - **Sell Put** — neutral to bullish, want to collect premium (ATM ±6%, 21-45 DTE)
   - **Buy Put** — you expect strong move down (delta ~-0.68, 45-90 DTE)
   - **Sell Call** — neutral to bearish (ATM ±6%, 21-45 DTE)
5. Click **Analyze** — wait ~8-12s for live IBKR data
6. Review verdict (GO / PAUSE / BLOCK) and gates
7. If verdict is GO, record a paper trade

> **Direction locking:** If STA gives a BUY signal, `sell_call` and `buy_put` are locked (contradicts the signal). SELL signal locks `buy_call` and `sell_put`.

### Market Hours

| Session | Hours (ET) | Behavior |
|---------|-----------|---------|
| Regular | 9:30am – 4:00pm | Live greeks from IBKR — full analysis |
| Pre-market | 6:30am – 9:30am | Zero greeks (market closed) — liquidity gate fails |
| After-hours | 4:00pm – 8:00pm | BS greeks (HV proxy) — `data_source = ibkr_closed` |
| Weekend | All day | BS greeks (HV proxy) — use for setup review only |

> **During market hours:** `data_source = ibkr_live`, full live greeks + bid/ask/OI, all gates evaluated.
> **Outside market hours:** `data_source = ibkr_closed`. Greeks computed via Black-Scholes (20-day HV as IV proxy). No bid/ask/OI. Liquidity gate always FAILs (expected). Delta/theta/vega are meaningful — use for directional setup planning. Re-analyze during market hours before paper trading.

### AMD → NVDA Workflow (sequential tickers)

```
T=0s    Analyze AMD    → IBKR fetch ~10s → AMD cached 2 min
T=10s   Analyze NVDA   → IBKR fetch ~10s → NVDA cached 2 min (no wait)
T=60s   Analyze AMD again → SQLite cache hit → instant response
T=62s   Analyze NVDA again → SQLite cache hit → instant response
```

Each ticker has its own independent 2-minute cache. **No waiting between different tickers.**

---

## The 9 Gates

Analysis runs 9 quality gates. Each is PASS / WARN / FAIL.

| Gate | What it checks | Typical threshold |
|------|---------------|------------------|
| **IV Rank** | Is implied volatility cheap or expensive? | IVR < 50 for buyers |
| **HV/IV Ratio** | Are options fairly priced vs realized vol? | IV/HV ratio < 1.5 |
| **Theta Burn** | Will theta erode gains before target hits? | < 5% per 7 days |
| **DTE Selection** | Is expiry in the sweet-spot window? | 45-90 DTE buyers, 21-45 sellers |
| **Event Calendar** | Earnings or FOMC near expiry? | Earnings > 21d, FOMC > 7d |
| **Liquidity Proxy** | Enough open interest and volume? | OI > 100, bid/ask spread reasonable |
| **Market Regime** | Is SPY above 200 SMA? 5-day return? | SPY above 200 SMA = favorable |
| **Confirmed Close Above Pivot** | Has stock closed above VCP pivot? | Last close > pivot = confirmed |
| **Position Sizing** | Can you risk ≤1% of account on this? | lots_allowed ≥ 1 |

**Verdict logic:**
- **GO** (green) — 7+ pass, ≤1 fail
- **PAUSE** (amber) — some warns, ≤2 fails
- **BLOCK** (red) — any critical gate fails (theta, liquidity, sizing)

---

## Data Fields: Live from IBKR vs Computed by IQ Engine

Understanding which fields are real market data vs computed helps interpret results, especially off-hours.

### Fetched Live from IB Gateway (market data subscription required)

| Field | IB API Call | When Available |
|-------|-------------|----------------|
| **Underlying price** | `reqMktData` (snapshot) | Always when IBKR connected |
| **Bid / Ask** | `reqTickers` | Market hours only (9:30am–4pm ET) |
| **Last price** | `reqTickers` | Market hours only |
| **Delta, Gamma, Theta, Vega** | `reqTickers` → `modelGreeks` | Market hours only |
| **Implied Volatility (per contract)** | `reqTickers` → `modelGreeks.impliedVol` | Market hours only |
| **Open Interest** | `reqTickers` → `callOpenInterest` / `putOpenInterest` | Market hours only |
| **Volume** | `reqTickers` → `volume` | Market hours only |
| **Available strikes / expiries** | `reqSecDefOptParams` | Always — cached 4h in memory |
| **IV history (for IVR)** | `reqHistoricalData` (OPTION_IMPLIED_VOLATILITY) | Always |
| **OHLCV history** | `reqHistoricalData` (TRADES) | Always |

### Computed by IQ Engine (never from IBKR)

| Field | Computation | Source Data |
|-------|-------------|-------------|
| **IV Rank (IVR)** | `(current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) × 100` | IV history from IBKR or yfinance |
| **HV/IV Ratio** | 20-day realized vol ÷ current IV | OHLCV returns (IBKR or yfinance) |
| **Theta Burn %** | `abs(theta × hold_days) / premium × 100` | theta + premium from chain |
| **Position sizing** | `account_size × risk_pct ÷ (premium × 100)` | User's account size + premium |
| **Put/Call Ratio** | `put OI / call OI` | OI from chain |
| **Max Pain Strike** | Minimize aggregate loss for option writers | OI from chain |
| **P&L scenarios** | Black-Scholes at each price target | premium + greeks |
| **SPY above 200 SMA** | `SPY.close[-1] > mean(SPY.close[-200:])` | yfinance SPY history |
| **SPY 5-day return** | `(close[-1] - close[-6]) / close[-6] × 100` | yfinance SPY history |

### Off-Hours (market closed — 4pm–9:30am ET, weekends)

When market is closed, `reqTickers` returns empty. The engine switches to estimated mode:

| Field | Source when closed | Notes |
|-------|-------------------|-------|
| **Delta, Gamma, Theta, Vega** | Black-Scholes (bs_calculator.py) | Uses 20-day HV as IV proxy |
| **Theoretical price (mid)** | Black-Scholes | Not a tradeable quote |
| **Implied Vol** | 20-day HV from yfinance | Approximation only |
| **Bid / Ask** | `null` | No market data |
| **Open Interest** | `0` | Not available off-hours |
| **data_source** | `ibkr_closed` | Amber banner shown in UI |

> **Rule of thumb:** Off-hours analysis gives you real direction/theta estimates for setup planning.
> Always re-analyze during market hours before recording a paper trade — live greeks are required.

---

## Four Directions

| Direction | Market View | Gate Track | Strike Zone | DTE Sweet Spot |
|-----------|------------|------------|-------------|----------------|
| buy_call | Strongly Bullish | A | 8-20% ITM below underlying (delta ~0.68) | 45-90 days |
| sell_call | Neutral to Bearish | A | ATM ±6% | 21-45 days |
| buy_put | Strongly Bearish | B | 8-20% ITM above underlying (delta ~-0.68) | 45-90 days |
| sell_put | Neutral to Bullish | B | ATM ±6% (below price) | 21-45 days |

---

## STA Integration

OptionsIQ integrates with [STA (Swing Trade Analyzer)](http://localhost:5001) — a separate project.

**When STA is online:**
- Swing Data section shows **STA Live** badge
- Entry price, stop loss, target, ADX, VCP pattern, R:R auto-filled
- Direction locked to signal (BUY → only buy_call / sell_put available)

**When STA is offline:**
- Manual mode — enter stop, target, entry directly
- All analysis still works — just uses your manual inputs

**STA endpoints used (read-only):**

| Data | STA Endpoint |
|------|-------------|
| Entry, stop, target, R:R | `/api/sr/{ticker}` → `suggestedEntry/Stop/Target`, `riskReward` |
| ADX, last close | `/api/sr/{ticker}` → `meta.adx.adx`, `/api/stock/{ticker}` → `currentPrice` |
| VCP pattern | `/api/patterns/{ticker}` → `patterns.vcp` |
| Earnings | `/api/earnings/{ticker}` → `days_until` |
| FOMC days | `/api/context/SPY` → `cycles.cards[FOMC].raw_value` |
| SPY above 200 SMA | Computed from yfinance (not in STA) |

---

## Paper Trading

When gates pass and you want to record a paper trade:

1. From the results page, click **Record Paper Trade** on your preferred strategy
2. Trade is stored in `backend/data/iv_store.db`
3. Check all trades at `GET /api/options/paper-trades` — includes mark-to-market P&L
4. P&L updates with each analyze call for that ticker

> Paper trading uses the exact same live data path as analysis. No mock data, no delayed prices.

---

## Backend API (key endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | System health + IBKR connection status |
| POST | `/api/options/analyze` | Main analysis — returns gates + strategies |
| GET | `/api/options/chain/{ticker}` | Debug — raw chain data |
| GET | `/api/options/ivr/{ticker}` | Debug — IV rank data |
| GET | `/api/integrate/sta-fetch/{ticker}` | Fetch swing data from STA |
| POST | `/api/options/paper-trade` | Record a paper trade |
| GET | `/api/options/paper-trades` | List paper trades + P&L |
| POST | `/api/options/seed-iv/{ticker}` | Seed IV history from IBKR |

Full contracts: `docs/stable/API_CONTRACTS.md`

---

## Project Structure

```
options-iq/
├── start.sh                    # Start backend + frontend
├── stop.sh                     # Stop all processes
├── CLAUDE_CONTEXT.md           # Claude AI session guide (not for humans)
│
├── backend/
│   ├── app.py                  # Flask routes (558 lines, target ≤150)
│   ├── constants.py            # All thresholds and config
│   ├── ib_worker.py            # Single IBKR thread — owns IB() instance
│   ├── ibkr_provider.py        # IBKR options chain fetch
│   ├── data_service.py         # Provider cascade + SQLite cache + circuit breaker
│   ├── yfinance_provider.py    # Fallback data provider
│   ├── bs_calculator.py        # Black-Scholes greeks
│   ├── gate_engine.py          # Gate math (frozen — verified correct)
│   ├── strategy_ranker.py      # Top-3 strategy selection (frozen)
│   ├── pnl_calculator.py       # P&L scenarios (frozen)
│   ├── iv_store.py             # IV history storage (frozen)
│   ├── .env                    # Your config (gitignored)
│   ├── .env.example            # Template
│   └── data/                  # SQLite databases
│       ├── chain_cache.db      # 2-min options chain cache
│       └── iv_store.db         # IV history + paper trades
│
├── frontend/
│   └── src/
│       ├── App.jsx             # Main app, state management
│       ├── hooks/
│       │   └── useOptionsData.js  # API calls
│       └── components/
│           ├── MasterVerdict.jsx    # GO/PAUSE/BLOCK hero
│           ├── GatesGrid.jsx        # 9 gates display
│           ├── TopThreeCards.jsx    # Strategy recommendations
│           ├── SwingImportStrip.jsx # STA import + manual entry
│           ├── DirectionSelector.jsx
│           ├── PnLTable.jsx
│           ├── BehavioralChecks.jsx
│           └── Header.jsx
│
└── docs/
    ├── stable/
    │   ├── GOLDEN_RULES.md         # Code + process rules
    │   ├── ROADMAP.md              # Phase progress
    │   ├── API_CONTRACTS.md        # Endpoint specs
    │   └── CONCURRENCY_ARCHITECTURE.md  # Threading design
    ├── versioned/
    │   └── KNOWN_ISSUES_DAY*.md   # Issue tracking by session
    └── status/
        └── PROJECT_STATUS_DAY*_SHORT.md  # Session summaries
```

---

## Known Limitations

| Limitation | Impact | Status |
|-----------|--------|--------|
| Market closed → no bid/ask/OI | Liquidity gate fails (expected) — greeks estimated via BS | Fixed: delta/theta are real off-hours (v0.6) |
| Deep ITM large-cap options sparse | NVDA buy_call may get only 2 contracts | Broad retry mitigates; verify during market hours |
| app.py 558 lines | Business logic not independently testable | Refactor to analyze_service.py planned |
| No market hours screening for candidates | Manual ticker selection only | Use TradingView screener + STA signals |

---

## Development Notes

**Frozen files** — do not modify the math in these:
- `gate_engine.py` — gate calculations are verified correct
- `strategy_ranker.py` — ranking math verified correct
- `pnl_calculator.py` — P&L scenarios verified correct
- `iv_store.py` — IV storage logic verified correct

**Adding a new gate threshold:** Add to `constants.py` first, then import. Never hardcode numbers in gate_engine or app.py.

**Adding a new route:** Keep app.py as routes-only. Business logic goes in `analyze_service.py` (when created).

**Testing IBKR connectivity:**
```bash
curl http://localhost:5051/api/health
# "ibkr_connected": true = IB Gateway live
# "ibkr_connected": false = check IB Gateway is running on port 4001
```

---

## Version History

| Version | What Changed |
|---------|-------------|
| v0.5 | IBWorker heartbeat, STA field mapping fixed, market regime fix, direction locking SELL |
| v0.6 | Market hours detection — BS greeks when closed, `ibkr_closed` tier, amber banner |
| v0.4 | Queue poisoning fix, RequestTimeout, legacy CB removed, frontend bugs |
| v0.3 | IBWorker, DataService, direction-aware chain fetch, live IBKR confirmed |
| v0.2 | Frontend redesign — two-panel layout, verdict hero |
| v0.1 | Scaffold — project structure, docs, codex files |
