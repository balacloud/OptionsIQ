# OptionsIQ — Roadmap
> **Last Updated:** Day 5 (March 10, 2026)
> **Current Version:** v0.5

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

### P2 — Day 6
- [ ] Create `analyze_service.py` — extract `_merge_swing`, `_extract_iv_data`, `_behavioral_checks`
- [ ] Synthetic-default warning when swing fields null (KI-022)
- [ ] FOMC days auto-compute from constants.FOMC_DATES in manual mode
- [ ] app.py to ≤150 lines (currently 558, KI-023)

### P3 ✅ DONE (Day 5)
- [x] IBWorker background heartbeat (KI-019) — `reqCurrentTime()` every 30s, staleness check

## Phase 3 Additional Fixes (Day 5) ✅ COMPLETE
- [x] STA field mapping fixed — `suggestedEntry/Stop/Target/riskReward` (was `levels.*`)
- [x] `spy_above_200sma` computed from yfinance — no more false Market Regime FAILs
- [x] Direction locking fixed for SELL signal
- [x] Struct cache drift invalidation (>15% price move clears cache)
- [x] `SMART_MAX_STRIKES` 4→6, `SMART_MAX_EXPIRIES` 1→2, broad-window retry when <3 qualify
- [x] `start.sh` `.env` path fix + venv creation fix

## Phase 4 — Market Hours + Analyze Service (Day 6)
- [ ] Market hours detection — use BS greeks when market closed (KI-024)
- [ ] Full weekday test — AMD + NVDA + PLTR, all four directions, market open
- [ ] Synthetic swing default warning banner (KI-022)

## Phase 5 — Paper Trading Ready (Day 6-7)
- [ ] Paper trade record + mark-to-market verified end-to-end
- [ ] IV history seeded for AMD, NVDA, PLTR, RKLB, AMZN
- [ ] git tag v1.0 — paper trading begins

## Post-v1.0 (Backlog)
- [ ] Real-time chain refresh, P&L history chart, multi-ticker watchlist, CSV export
- [ ] Persistent structure cache in SQLite
- [ ] Request deduplication for simultaneous analyze calls (P4 from concurrency arch)

---

## Version Log

| Version | Day | Notes |
|---------|-----|-------|
| v0.1 | Day 1 | Scaffold — Codex files ported, Phase 0 docs complete |
| v0.2 | Day 2 | Frontend redesigned — two-panel layout, verdict hero, collapsible sections |
| v0.3 | Day 3 | Data layer complete — IBWorker, DataService, direction-aware fetch, live IBKR confirmed |
| v0.4 | Day 4 | Concurrency P1 fixes (KI-016/017/018), ticker override + STA offline detection fixed |
| v0.5 | Day 5 | KI-019 heartbeat done, STA field mapping fixed, SPY/200SMA from yfinance, direction lock SELL, struct cache drift, broader strike qualification |
