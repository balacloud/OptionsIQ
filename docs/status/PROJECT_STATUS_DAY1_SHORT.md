# OptionsIQ — Project Status Day 1
> March 5, 2026 | v0.1 scaffold

## What Was Done Today
- New standalone repo created at `/Users/balajik/projects/options-iq/`
- Codex source files ported (9 backend + 13 frontend files)
- Full Phase 0 documentation created
- Build plan finalized (live-first, all 4 directions, 5 open questions resolved)
- 13 known issues catalogued from Codex audit

## Current State
- Backend: scaffold only — files copied, not refactored
- Frontend: scaffold only — files copied, not refactored
- IBKR connection: not working (app.py still God Object)
- Gate logic: verified correct, keep as-is
- P&L math: verified correct, keep as-is

## Blockers
- Nothing blocked — Phase 1 is ready to start

## Next Session: Phase 1 — Backend Foundation
1. Create `constants.py`
2. Create `bs_calculator.py`
3. Fix `mock_provider.py` (dynamic pricing)
4. Fix `iv_store.py` (add entry_price, mark_price columns)
5. Remove QUICK_ANALYZE_MODE from app.py
