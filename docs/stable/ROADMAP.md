# OptionsIQ — Roadmap
> **Last Updated:** Day 4 (March 7, 2026)
> **Current Version:** v0.4

---

## Phase 0 — Documentation (Day 1) ✅ COMPLETE
- [x] CLAUDE_CONTEXT.md, GOLDEN_RULES.md, ROADMAP.md, API_CONTRACTS.md
- [x] Codex source files ported, .gitignore, .env.example, requirements.txt, start.sh, stop.sh

## Phase 1 — Backend Foundation (Day 3) ✅ COMPLETE
- [x] `constants.py`, `bs_calculator.py`, `ibkr_provider.py` market_data_type=1

## Phase 2 — Data Layer (Day 3) ✅ COMPLETE
- [x] `ib_worker.py`, `yfinance_provider.py`, `data_service.py`
- [x] Direction-aware chain fetch + 4h structure cache + threading violation fixed

## Phase 3 — Fix Concurrency + Analyze Service (Day 4) ✅ P1 COMPLETE

### P1 ✅ ALL DONE
- [x] `expires_at` on IBWorker `_Request` — queue poisoning fix (KI-016)
- [x] `ib.RequestTimeout = 15` around reqTickers (KI-017)
- [x] Legacy circuit breaker removed from app.py (KI-018)
- [x] `right=None` in strategy_ranker fixed (KI-020)
- [x] Ticker override bug fixed — App.jsx spread order
- [x] STA offline detection fixed — `json?.status === 'ok'`

### P2 — Day 5
- [ ] Create `analyze_service.py` — extract `_merge_swing`, `_extract_iv_data`, `_behavioral_checks`
- [ ] Synthetic-default warning when swing fields null (KI-022)
- [ ] FOMC days auto-compute from constants.FOMC_DATES
- [ ] app.py to ≤150 lines (currently 527, KI-023)

### P3 — Day 5
- [ ] IBWorker background heartbeat (KI-019)

## Phase 4 — API Polish + Frontend (Day 5)
- [ ] Full market-hours test — AMD + NVDA + PLTR, all four directions
- [ ] Synthetic swing default warning banner (KI-022)

## Phase 5 — Paper Trading Ready (Day 5-6)
- [ ] Paper trade record + mark-to-market verified
- [ ] IV history seeded for AMD, NVDA, PLTR, RKLB, AMZN
- [ ] git tag v1.0 — paper trading begins

## Post-v1.0 (Backlog)
- [ ] Real-time chain refresh, P&L history chart, multi-ticker watchlist, CSV export
- [ ] Persistent structure cache in SQLite, market hours detection

---

## Version Log

| Version | Day | Notes |
|---------|-----|-------|
| v0.1 | Day 1 | Scaffold — Codex files ported, Phase 0 docs complete |
| v0.2 | Day 2 | Frontend redesigned — two-panel layout, verdict hero, collapsible sections |
| v0.3 | Day 3 | Data layer complete — IBWorker, DataService, direction-aware fetch, live IBKR confirmed |
| v0.4 | Day 4 | Concurrency P1 fixes (KI-016/017/018), ticker override + STA offline detection fixed |
