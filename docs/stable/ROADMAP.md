# OptionsIQ — Roadmap
> **Last Updated:** Day 12 (March 17, 2026)
> **Current Version:** v0.9.2

---

## Phase 0 — Documentation (Day 1) ✅ COMPLETE
- [x] CLAUDE_CONTEXT.md, GOLDEN_RULES.md, ROADMAP.md, API_CONTRACTS.md
- [x] Codex source files ported, .gitignore, .env.example, requirements.txt, start.sh, stop.sh
- [x] CLAUDE.md created + session startup/close checklists added to CLAUDE_CONTEXT.md (Day 8)

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

## Phase 4 — Market Hours + Analyze Service (Day 6–8)
- [x] Market hours detection — BS greeks when market closed (KI-024) ✅ Day 6
- [x] ibkr_closed data source tier — no stale-quote caching ✅ Day 6
- [x] Frontend: amber banner + "IB Closed" header label ✅ Day 6
- [x] Strategy ranker: explicit builders for all 4 directions (KI-021) ✅ Day 7
- [x] reqMktData(snapshot=False) replaces reqTickers — modelGreeks fix (KI-027) ✅ Day 7
- [x] KI-026 VERIFIED Day 9 — live greeks 100% during market hours, usopt lazy connect confirmed ✅
- [x] pnl_calculator: None guard + itm_put/atm_put/bear_call_spread/sell_call handlers ✅ Day 9
- [x] sell_call direction-aware sort + SMART_MAX_STRIKES 6→12 → bear_call_spread building ✅ Day 9
- [x] KI-035: OI always 0 — genericTickList="101" fix applied (verify market hours Day 11) ✅ Day 10
- [x] Create alpaca_provider.py — REST fallback with greeks (NO OI/volume) ✅ Day 10
- [ ] Synthetic swing default warning banner (KI-022)
- [ ] Create marketdata_provider.py — MarketData.app REST provider ($12/mo, pending support ticket)
- [ ] Create analyze_service.py — extract from app.py (KI-001/023, Day 11 P2)

## Phase 4b — System Audit + Hardening (Day 11-12) ✅ PHASE A+D COMPLETE
- [x] Behavioral audit: 17 claims verified against code ✅ Day 11
- [x] Phase A critical fixes (logger, QualityBanner, WAL, bare excepts, missing banners) ✅ Day 12
- [x] Phase D error handling (subscription cleanup, ticker validation, outer try-except) ✅ Day 12
- [x] gate_engine Rule 3 fix: 60+ hardcoded literals → constants.py imports ✅ Day 12
- [x] KI-035 OI: confirmed platform limitation, graceful degradation shipped ✅ Day 12
- [x] sell_put naked warning, ACCOUNT_SIZE startup guard ✅ Day 12
- [ ] Phase B API contract sync (update API_CONTRACTS.md to match code) — Day 13 P0
- [ ] Phase C provider consistency (None vs 0, bs_greeks flag)
- [ ] Phase E performance (deepcopy, struct_cache LRU, startup health check)
- [ ] Phase F documentation sync

## Phase 5 — Paper Trading Ready
- [ ] Paper trade record + mark-to-market verified end-to-end
- [ ] IV history seeded for AMD, NVDA, PLTR, RKLB, AMZN
- [ ] git tag v1.0 — paper trading begins

## Phase 6 — Sector Rotation ETF Module (STA-powered)
STA already provides: RS Ratio, quadrants, cap-size rotation, sector→ETF mapping.
OptionsIQ consumes `GET localhost:5001/api/sectors/rotation` — zero RS computation needed.
- [x] Research: RS methodology, strategy-per-quadrant, ETF liquidity ✅ Day 11
- [x] RS formula verified against STA source ✅ Day 11 (6-mo closes, midpoint normalize, 10-day delta)
- [ ] ~~`sector_rotation.py`~~ NOT NEEDED — STA provides all rotation data
- [ ] `sector_scan_service.py` — STA consumer + quadrant→direction mapping + IV overlay (~150 lines)
- [ ] Backend: `GET /api/sectors/scan` (L1) + `GET /api/sectors/analyze/{ticker}` (L2)
- [ ] Level 3 reuses existing `POST /api/options/analyze` (zero new code)
- [ ] TQQQ rules: max 45 DTE, no covered calls, bear call spreads only
- [ ] Frontend: SectorRotation.jsx + ETFCard.jsx + CapSizeStrip.jsx
See: `docs/Research/Sector_Rotation_ETF_Module_Day11.md`

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
| v0.6 | Day 6 | KI-024 market hours detection — BS greeks when closed, ibkr_closed tier, frontend banner |
| v0.7 | Day 7 | KI-021 strategy routing all 4 directions, KI-027 reqMktData fix for modelGreeks, Phase 4e BS fallback |
| v0.7 | Day 8 | Process session — CLAUDE.md created, session startup/close checklists formalized in CLAUDE_CONTEXT.md |
| v0.8 | Day 9 | KI-026 verified live. KI-030 hv_20 fix. KI-031 pnl_calculator fixed. KI-033 sell_call spread fixed (sort + SMART_MAX). Alpaca researched as REST fallback. |
| v0.9 | Day 10 | KI-035 OI fix applied. alpaca_provider.py created + wired. MarketData.app tested (hist IV=None). Provider research doc. Golden Rule 19. |
| v0.9.1 | Day 11 | KI-037 confirmed (MarketData.app no historical IV — platform limitation). System coherence audit: 47 findings (6 critical, 8 high). Audit doc created. |
| v0.9.2 | Day 12 | All Phase A+D audit fixes shipped. gate_engine Rule 3 fixed (60+ literals → constants.py). KI-035 OI platform limitation confirmed + graceful degradation. SQLite WAL. reqMktData try-finally. ACCOUNT_SIZE guard. sell_put naked warning. System usable for live analysis. |
