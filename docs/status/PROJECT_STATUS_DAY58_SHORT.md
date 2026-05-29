# Project Status — Day 58 (May 29, 2026)
> **Version:** v0.35.1
> **Tests:** 37 (unchanged)

## What Shipped

### 1. Today's Trade Tab (BestSetups.jsx replacement)
**Root cause of previous issue:** BestSetups fetched from STA on mount → "STA offline" error.
**Fix:** Complete rewrite. Zero API calls. Shows 6-ETF quick-launcher grid (QQQ/IWM/XLF/GLD/TQQQ/SPY) → direction picker → Analyze button. Calls `onSelect(ticker, direction)` which wires to Signal Board.
**Verification:** Build clean. 3-step workflow instructions reference `/ibkr-scan`. TQQQ blue rules banner, GLD amber rules banner on selection.

### 2. TopThreeCards.jsx — expected_move + exit_plan display
**Added:**
- `expectedMove1sd` prop from App.jsx: `data?.expected_move_1sd`
- `em-context` banner: "±$X.XX expected move (1σ, Nd) — strikes outside this range have PoP ≥ 84%"
- `strike_vs_em_label` detail item in strategy grid (σ OTM classification)
- `ExitPlanBlock` sub-component: rule text + target credit chip + exit date chip (stop chip for buys)
- Gated-out state: exit plan + P&L chips hidden when GATED OUT overlay shown
**Verification:** Build clean. plainEnglishSummary handles both old (itm_call/atm_call) and new type names.

### 3. CSS additions (index.css)
- `.em-context` — purple left-border banner for expected move
- `.exit-plan-block` / `.exit-plan-chips` / `.exit-chip-*` — exit plan display
- `.tt-*` — Today's Trade full CSS suite (grid, buttons, banners, responsive)

### 4. MASTER_AUDIT_FRAMEWORK.md updated to v1.5 (Day 58)
Full Day 57-58 architecture reflected. Stale claims (spreads, 15 ETFs, old builder names) replaced with current single-leg, 6-ETF, expected_move/exit_plan system. All 4 HIGH bugs discovered in audit.

### 5. Audit Bug Fixes (4 HIGH findings, all fixed)

**pnl_calculator.py — otm_call/otm_put P&L was zero:**
`_scenario_pnl()` only handled `itm_call`/`atm_call`. R3 of buy_call (type `otm_call`) returned 0.
Fix: added `otm_call` to call set, `otm_put` to put set.

**TradeExplainer.jsx — profit zone wrong for buy_put R3:**
`isBearish()`, `getMoneyness()`, `getTradeHeadline()` all missing `otm_put` and `otm_call`.
Fix: added to all three helpers (4 lines).

**DirectionGuide.jsx — sell_call risk label stale:**
"Spread width (capped with spread)" — wrong since Day 57 single-leg pivot.
Fix: "Uncapped (naked call — unlimited upside exposure)"

**gate_engine.py — FOMC gate hard-blocked buy directions:**
`_run_etf_buy_call` and `_run_etf_buy_put` called `_etf_fomc_gate` which hard-blocks XLF/TQQQ within 14d FOMC regardless of direction. Buyers should only get WARN.
Fix: added `direction` param (default "sell_put"); Tier 1 hard block only for sellers.

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-107 | MEDIUM | TQQQ delta guard not enforced in gate_engine |
| KI-108 | MEDIUM | GLD IV/HV ≥ 1.10 gate not enforced in gate_engine |
| KI-109 | MEDIUM | sell_call uses legacy FOMC events check (not _etf_fomc_gate tier logic) |
| KI-110 | LOW | _rank_buy_call/_rank_buy_put return stale strategy_type names (itm_call/atm_call) |
| KI-059 | LOW | Single-stock bear untested (ETF-only, won't fix) |

## Next Session Priorities

| Priority | Task | Effort |
|----------|------|--------|
| P1 | KI-107: TQQQ delta guard in gate_engine (~10 lines) | 30 min |
| P2 | KI-108: GLD IV/HV gate in gate_engine (~3 lines) | 15 min |
| P3 | KI-109: sell_call FOMC gate consistency (replace legacy events block) | 30 min |
| P4 | End-to-end morning workflow test: ibkr-scan → analyze → paper trade | 60 min |
| P5 | `/chartreview` skill (`.claude/commands/chartreview.md`) | 60 min |
| P6 | `/catalyst-check` skill (`.claude/commands/catalyst-check.md`) | 60 min |
