# OptionsIQ — Project Status Day 29
> **Date:** April 27, 2026
> **Version:** v0.21.0
> **Session:** Day 29

---

## What Shipped Today

### Data Infrastructure
- **IVR "—" bug fixed** — key mismatch `iv_data` → `ivr_data` in best-setups endpoint. IVR now shows correctly in watchlist (QQQ 69%, IWM 67%, XLK 85%, etc.)
- **SQLite WAL fix** — `iv_store.py` `_conn()` now uses `timeout=10, check_same_thread=False`, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000`. Prevents parallel read contention during best-setups scan.

### Gate Logic
- **KI-082 resolved** — credit-to-width ratio gate. `MIN_CREDIT_WIDTH_RATIO = 0.33` in constants (empirical: 33% per tastylive/Sinclair, not 20%). `_credit_width()` helper in strategy_ranker. Bear_call + bull_put R1/R2 now carry `credit_to_width_ratio` and warning. 4 tests added.
- **HV/IV VRP seller gate** — `_etf_hv_iv_seller_gate()` in gate_engine.py. Sells only when IV > HV (positive VRP). `HV_IV_SELL_PASS_RATIO=1.05`, `HV_IV_SELL_WARN_RATIO=1.15`. Wired into `_run_etf_sell_put` and `_run_sell_call`.
- **FOMC imminent bug fixed** — all 4 inline event gates now check `fomc_days < 5` warn BEFORE `fomc_days <= 10`. Imminent FOMC (<5 days) was falling through to PASS.
- **VIX gate** — `_vix_regime_gate()`: <15 WARN (thin), >30 WARN (stress), >40 FAIL (crisis). Wired into seller tracks.
- **IVR seller threshold lowered** — `IVR_SELLER_PASS_PCT`: 50→35, `IVR_SELLER_MIN_PCT`: 30→25. Perplexity/tastylive: IVR>50 sacrifices 60-70% trade frequency with negligible benefit.

### New Features
- **Best Setups tab** — parallel scan of all ETFs using sector-suggested direction. Manual "Run Scan" button (no auto-load). GO/CAUTION grid + Watchlist table sorted by gate pass rate. Shows ETF, direction, gates (X/Y), IVR, quadrant, failed gates.
- **Data Health tab** — `GET /api/data-health` endpoint + `DataProvenance.jsx`. Shows:
  - Source health: IBKR status + CB, VIX (value/source/age), SPY regime, FOMC (days away), Alpaca, MarketData.app
  - IV History per ETF: rows, date range, HV-20, OHLCV rows
  - Chain cache per ETF: age, freshness, entries
  - **Field-level resolution per ETF**: for each analysis field (chain/IV, OI/volume, HV-20, IVR, VIX, SPY regime, FOMC) — exact source, status, and explanatory note
- **Pre-analysis prompts (P0)** — `PreAnalysisPrompts.jsx` wired into analyze tab
- **Paper Trade Dashboard (P1)** — `PaperTradeDashboard.jsx`, SQLite-backed via `/api/options/paper-trades/summary`. SQLite persistence badge added.
- **Tab state retention** — all tabs now always-mounted with `display: none/undefined`. Best Setups scan results and Data Health results survive tab switches.

### Bugs Fixed
- Signal board `display: grid` being overridden by `display: 'block'` — fixed with `undefined`
- IVR key mismatch `iv_data` → `ivr_data`
- Run Scan button invisible — `var(--accent)` undefined, hardcoded `#00c896`
- Best setups `KeyError: 'ticker'` — sector scan returns `s["etf"]` not `s["ticker"]`

### Data Quality Issues Found (via Data Health tab)
- **XLE OHLCV corrupted** — stray rows at ~$100 in $57-63 range → HV-20 = 413% (KI-083, HIGH)
- **XLC + XLRE no OHLCV** — 0 bars stored, HV-20 null, VRP gate cannot run (KI-084, MEDIUM)
- **FOMC 2 days away (Apr 29)** — confirmed via data health tab, explains all-blocked Best Setups

---

## Test Count
29 (unchanged — gate changes tested manually via live ChatGPT stress tests)

## Endpoints Added
- `GET /api/data-health` — full data provenance report (sources + iv_history + chain_cache + field_resolution)
- `GET /api/best-setups` — parallel ETF scan

## Files Changed
```
backend/
  app.py                  +/api/data-health route, ivr key fix, import data_health_service
  analyze_service.py      +get_vix_status(), _etf_hv_iv_seller_gate(), _vix_regime_gate(), VIX fetch/cache
  gate_engine.py          +_etf_hv_iv_seller_gate(), _vix_regime_gate(), FOMC imminent fix (all 4 tracks)
  constants.py            +MIN_CREDIT_WIDTH_RATIO=0.33, IVR_SELLER_PASS_PCT=35, HV_IV_SELL_* ratios, VIX buckets
  strategy_ranker.py      +_credit_width(), credit_to_width_ratio on bear_call/bull_put R1/R2
  iv_store.py             +get_iv_stats(), get_ohlcv_stats(), WAL+busy_timeout in _conn()
  data_service.py         +get_cache_stats()
  data_health_service.py  NEW — build_data_health() orchestrator
  tests/test_spread_math.py  +4 credit-to-width tests

frontend/
  src/App.jsx             +DataProvenance tab, always-mount pattern, signal-board display fix
  src/components/BestSetups.jsx          NEW
  src/components/DataProvenance.jsx      NEW
  src/components/PreAnalysisPrompts.jsx  NEW
  src/components/PaperTradeDashboard.jsx NEW + SQLite badge
  src/components/TopThreeCards.jsx       +credit/width stat
  src/index.css           +Best Setups CSS, Data Provenance CSS, paper trade badge CSS
```

---

## Current Blockers
- **IBKR disconnected** (market closed) — best setups scan runs in mock mode, slow
- **FOMC April 29** — 2 days away, all seller gates blocked (expected behavior)
- **XLE HV corrupted** (KI-083) — needs OHLCV cleanup before XLE VRP gate is reliable
