# OptionsIQ — Roadmap
> **Last Updated:** Day 3 (March 6, 2026)
> **Current Version:** v0.3

---

## Phase 0 — Documentation (Day 1) ✅ COMPLETE

- [x] CLAUDE_CONTEXT.md
- [x] GOLDEN_RULES.md
- [x] ROADMAP.md
- [x] API_CONTRACTS.md
- [x] KNOWN_ISSUES_DAY1.md
- [x] PROJECT_STATUS_DAY1_SHORT.md
- [x] Codex source files ported to new structure
- [x] .gitignore, .env.example, requirements.txt, start.sh, stop.sh

---

## Phase 1 — Backend Foundation (Day 3) ✅ COMPLETE

- [x] `constants.py` — all thresholds, DTE limits, ports, defaults, direction-aware strike windows
- [x] `bs_calculator.py` — Black-Scholes greeks + price (scipy.stats.norm)
- [x] Fix `ibkr_provider.py` — `market_data_type = 1` (live data, Golden Rule #1)
- [x] Remove `QUICK_ANALYZE_MODE` from app.py (KI-007)
- [ ] Fix `mock_provider.py` — dynamic pricing (LOW PRIORITY — yfinance covers fallback)
- [ ] Fix `iv_store.py` — add `entry_price`, `mark_price` columns to paper_trades (deferred)

**Done when:** Python imports clean, `constants.py` is source of truth ✓

---

## Phase 2 — Data Layer (Day 3) ✅ COMPLETE

- [x] `ib_worker.py` — single IB() thread, submit() queue, asyncio event loop per thread
- [x] `yfinance_provider.py` — middle tier (price, chain structure, IV, BS greeks)
- [x] `data_service.py` — provider cascade + persistent SQLite cache + circuit breaker
- [x] Direction-aware chain fetch — DTE sweet spot + ITM/ATM strike targeting
- [x] 4h in-memory structure cache — avoids repeated reqSecDefOptParams
- [x] Threading violation fixed — all IBKRProvider calls via IBWorker.submit()
- [x] gate_engine None crash fixed — ivr_for_gates coercion layer

**Done when:** `curl localhost:5051/api/health` returns `ibkr_connected: true` ✓
**Live test:** AAPL chain fetched in ~8s, AMD at $198.53, IVR 60.6% ✓

---

## Phase 3 — Fix Concurrency + Analyze Service (Day 4 — NEXT)

### P1 — Must fix before paper trading
- [ ] Add `expires_at` to IBWorker `_Request` — discard expired requests (KI-016)
- [ ] Set `ib.RequestTimeout` around reqTickers in IBKRProvider (KI-017)
- [ ] Remove legacy circuit breaker from app.py (KI-018)

### P2 — Analyze service extraction
- [ ] `analyze_service.py` — extract business logic from app.py
  - [ ] `_merge_swing()` with validation warnings
  - [ ] `_extract_iv_data()` with proper provider routing
  - [ ] `_behavioral_checks()`
  - [ ] FOMC days auto-compute from constants.FOMC_DATES
- [ ] app.py becomes routes-only ≤150 lines (Rule 4)

### P3 — Debug
- [ ] Investigate `right=None` in strategy_ranker output (KI-020)
- [ ] Add background heartbeat to IBWorker (KI-019)

**Done when:** `POST /api/options/analyze` returns valid response, app.py ≤150 lines, no queue poisoning

---

## Phase 4 — API Polish + Frontend Wire-up (Day 5)

- [ ] Full market-hours test (9:30am-4pm ET) — live bid/ask/greeks
- [ ] Add "Market closed" banner to frontend quality system
- [ ] `useOptionsData.js` — API_BASE from `REACT_APP_API_URL` env var (KI-013)
- [ ] `SwingImportStrip.jsx` — verify STA connect works end-to-end
- [ ] Request deduplication in DataService (KI-016 enhancement)

**Done when:** Full browser flow working — AMD → analyze → gates + strategies + P&L

---

## Phase 5 — Paper Trading Ready (Day 5-6)

- [ ] Paper trade record + mark-to-market verified working
- [ ] Quality banners display correctly for all data tiers
- [ ] IV history seeded for target tickers (AMD, NVDA, PLTR, RKLB, AMZN)
- [ ] git tag v1.0 — paper trading begins

---

## Post-v1.0 (Backlog — do not build until paper trading running)

- [ ] Real-time chain refresh (background polling)
- [ ] Paper trade P&L history chart
- [ ] Multi-ticker watchlist
- [ ] Export paper trades to CSV
- [ ] Persistent structure cache in SQLite (currently in-memory, lost on restart)
- [ ] Market hours detection → skip live pricing pre/post market
- [ ] Request deduplication in IBWorker (N simultaneous requests = 1 IBKR call)

---

## Version Log

| Version | Day | Notes |
|---------|-----|-------|
| v0.1 | Day 1 | Scaffold — Codex files ported, Phase 0 docs complete |
| v0.2 | Day 2 | Frontend redesigned — two-panel layout, verdict hero, collapsible sections |
| v0.3 | Day 3 | Data layer complete — IBWorker, DataService, direction-aware fetch, live IBKR confirmed |
