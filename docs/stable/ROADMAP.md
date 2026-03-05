# OptionsIQ — Roadmap
> **Last Updated:** Day 1 (March 5, 2026)
> **Current Version:** v0.1 (scaffold)

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

## Phase 1 — Backend Foundation (Day 2)

Fix the critical scaffold issues before anything can run.

- [ ] `constants.py` — all thresholds, DTE limits, ports, defaults
- [ ] `bs_calculator.py` — Black-Scholes greeks + price (scipy.stats.norm)
- [ ] Fix `mock_provider.py` — dynamic pricing per ticker (not hardcoded AME)
- [ ] Fix `iv_store.py` — add `entry_price`, `mark_price` columns to paper_trades table
- [ ] Remove `QUICK_ANALYZE_MODE` from app.py

**Done when:** `python -c "from backend import constants, bs_calculator"` runs clean

---

## Phase 2 — Data Layer (Day 2-3)

- [ ] Wrap `ibkr_provider.py` in `IBWorker` dedicated thread
- [ ] `yfinance_provider.py` — middle tier (price, chain structure, IV, no live greeks)
- [ ] `data_service.py` — provider selection + persistent SQLite cache + circuit breaker

**Done when:** `curl localhost:5051/api/health` returns `{"ibkr": "connected"|"offline", "data_tier": "live"|"cached"|"yfinance"}`

---

## Phase 3 — Analysis Layer (Day 3)

- [ ] `analyze_service.py` — validate payload, run gates, rank strategies, build P&L, STA fetch
- [ ] `gate_engine.py` — import thresholds from constants (math unchanged)
- [ ] `strategy_ranker.py` — DTE window 14-120, seller ranking (3 strike distances)

**Done when:** `POST /api/options/analyze` returns valid response for AMD buy_call with manual swing fields

---

## Phase 4 — API Layer (Day 3)

- [ ] `app.py` refactor — routes only, ≤ 150 lines
- [ ] `/api/health` endpoint
- [ ] `/api/integrate/sta-fetch/{ticker}` endpoint
- [ ] Remove all business logic from app.py

**Done when:** app.py < 150 lines, all existing endpoints still respond

---

## Phase 5 — Frontend (Day 4)

- [ ] `SwingImportStrip.jsx` — "Connect to STA" button, STA Live / Manual badge, FOMC field visible
- [ ] `App.jsx` cleanup — remove hardcoded AME defaults
- [ ] `useOptionsData.js` — API_BASE from env, not hardcoded localhost:5051
- [ ] All other components — keep as-is (math and structure verified correct)

**Done when:** Full flow works in browser: enter AMD, click "Connect to STA", click Analyze, see gates + strategies + P&L table

---

## Phase 6 — Documentation Close (Day 4)

- [ ] Update CLAUDE_CONTEXT.md current state table
- [ ] Finalize API_CONTRACTS.md
- [ ] Update KNOWN_ISSUES to mark resolved issues
- [ ] All 13 original Codex issues resolved or tracked
- [ ] git tag v1.0 — paper trading begins

---

## Post-v1.0 (Backlog — do not build until paper trading running)

- [ ] Real-time chain refresh (background polling, configurable interval)
- [ ] Paper trade P&L history chart
- [ ] Multi-ticker watchlist
- [ ] Export paper trades to CSV

---

## Version Log

| Version | Day | Notes |
|---------|-----|-------|
| v0.1 | Day 1 | Scaffold — Codex files ported, Phase 0 docs complete |
