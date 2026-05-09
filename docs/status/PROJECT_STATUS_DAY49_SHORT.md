# OptionsIQ — Project Status Day 49
> **Date:** May 8, 2026 | **Version:** v0.32.0 | **Tests:** 44

## What Shipped

KI-098, KI-096, KI-097, KI-100 all implemented and tested. 8 new tests (36 → 44).

**KI-098 (Absolute Trend Gate):** `quadrant_to_direction()` now takes `week_change`. If `weekChange > 0` in Lagging branch, returns `None` — no tape-fighting bear spreads when sector is actually rising.

**KI-096 (IVR Null Handling):** `ivr_confidence = "known"/"unknown"` added to gate_payload. All 4 seller IVR gates now WARN (non-blocking) instead of FAIL when no IV history exists. Removes false blocks on new ETFs.

**KI-097 (Event Density Gate):** New `_etf_event_density_gate()` method counts all events (FOMC+CPI+NFP+PCE) in the DTE window with weighted scores. Rate-sensitive ETFs (XLF/XLRE/XLU/XLE/IWM/QQQ) escalate one tier earlier. Existing `_etf_fomc_gate()` unchanged (Rule 5).

**KI-100 (Tier 1 GO Rate):** `/api/best-setups` now returns `tier1_summary` for the 5 tradeable ETFs (IWM, QQQ, XLF, XLK, XLY). `BestSetups.jsx` shows GO/CAUTION/BLOCKED pills bar to distinguish structural Tier 2 liquidity blocks from real market conditions.

**Audit consolidation (Phase 7c):** Perplexity + Gemini results consolidated into Phase7c_Research.md. 3/3 LLM consensus on all 5 KIs confirmed before implementing.

## Test Count
44 (from 36): +4 direction routing (KI-098), +2 gate engine (KI-096), +2 gate engine (KI-097)

**`/ki` slash command:** `.claude/commands/ki.md` created. Type `/ki "description"` during any session to instantly log a numbered KI entry to the active KNOWN_ISSUES file. Auto-detects day, finds next KI number, inserts formatted entry with severity.

## Open Issues
- KI-101: Best Setups watchlist IV/HV shows `—` when chain IV missing (MEDIUM)
- KI-099: bull_call_spread direction for Leading/Improving (LOW, deferred)
- KI-059: single-stock bear (HIGH, deferred by design)

## Next Session Priorities
1. **P0:** Paper trade logging — log next XLF or QQQ setup. Need 30 trades for win rate data. Still 0.
2. **P1:** KI-099 assessment — bull_call_spread for Leading/Improving + IVR 30–50%. Decide scope.
3. **P2:** MASTER_AUDIT_FRAMEWORK sweep — overdue since Day 42.
4. **P3:** KI-101 fix — IV/HV ratio in watchlist when chain IV null.
