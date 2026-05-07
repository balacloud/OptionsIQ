# Project Status — Day 45 (May 6, 2026)
> **Version:** v0.30.0
> **Tests:** 36 (unchanged)

---

## What Shipped

### MASTER_AUDIT_FRAMEWORK v1.4 — Category 10: Trading Effectiveness Audit
**File:** `docs/stable/MASTER_AUDIT_FRAMEWORK.md`
**Why:** The existing 9 categories verify code correctness. Category 10 verifies that what we're building is actually useful — surfacing trades at a reasonable rate, with empirically grounded thresholds.

Five new checks:
- **10.1 Gate Pass Rate** — Run all 15 ETFs × scan; count non-BLOCKED setups. Target: 3-6/week = healthy. <2 = over-tuned. >10 = under-tuned. Identifies single biggest gate blocker.
- **10.2 "Always One Direction" claim** — At any given VIX regime, at least one ETF/direction should surface CAUTION or GO. If none do, it's a gate miscalibration not a market signal.
- **10.3 DTE Calibration** — Frames the tastylive 45 DTE vs 21 DTE empirical question with specific research queries before any threshold change.
- **10.4 Unbiased Evaluation** — Three methods: paper trade win rate (30-trade sample), adversarial LLM review ("reasons NOT to take this trade"), weekly gate pass rate log.
- **10.5 Expected Value Sanity** — Short strike must be outside the 1-sigma expected move (underlying × IV × sqrt(DTE/365)). If inside, stress_check should WARN.

Trigger: Monthly OR when user says "I can't find any setups."

### Phase 7c Research Scope — expanded in ROADMAP.md
Beyond cyclical/defensive split, added four research questions:
- Gate calibration target (3-5 ETFs/week)
- DTE empirical research (tastylive 45 DTE vs 21 DTE)
- "Always one direction" verification methodology
- Unbiased evaluation methods (paper trade, adversarial LLM, gate pass rate trending)

Research questions live in:
- `docs/stable/ROADMAP.md` — Phase 7c bullets (what to research)
- `docs/stable/MASTER_AUDIT_FRAMEWORK.md` — Category 10 (how to measure it)
- Research output doc will be created at session start when research is run: `docs/Research/Phase7c_Trading_Effectiveness_Day46.md`

### README staleness logged
Full rewrite deferred until all code issues closed. Tracked in memory. Issues: wrong provider hierarchy (IBKR shown as primary), SCHB listed but not in app, test count 27→36, missing new files (tradier_provider, batch_service, etc.), version history stops at v0.20.0.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (DEFERRED) | Single-stock bear tracks untested — ETF-only mode (400) |
| KI-086 | LOW (partial) | app.py `_run_one` closure still inline, ~449 lines, Rule 4 violation |

---

## Next Session Priorities (Day 46)

| Priority | Issue | Effort |
|----------|-------|--------|
| P0 | KI-086: app.py `_run_one` extraction to best_setups_service.py | 45 min |
| P1 | Phase 7c research: run Cat 10.1 gate pass rate live + start research doc | 60 min |
| P2 | MASTER_AUDIT_FRAMEWORK weekly sweep (skip until Day 49+ — last audit Day 42) | — |
| P3 | README full rewrite (after KI-086 closed) | 45 min |
