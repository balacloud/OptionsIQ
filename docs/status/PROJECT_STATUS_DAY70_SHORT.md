# Project Status — Day 70 (Jun 16, 2026)
> **Version:** v0.36.2
> **Session type:** Frontend — Quick Reference card

---

## What Shipped

### Quick Reference tab in Learn panel
`frontend/src/components/LearnTab.jsx` + `frontend/src/index.css`:

New 6th panel "Quick Ref" added to the Learn tab. One click from any learn panel.

**Contents:**
1. **Strategy comparison table** — Buy Call / Buy Call Spread / Sell Put / Buy Stock / Sell Call (naked). Downside, upside, best when. Buy Call row highlighted in green.
2. **Call buying strike ranking** — R1 = ITM δ0.68 (best balance), R2 = ATM δ0.50, R3 = OTM δ0.30. Far OTM (delta < 0.15) marked as blocked/avoid.
3. **Key rules** — DTE 45-90 (buyers), 21-45 (sellers), IVR ≥ 40% for sellers, GLD IV/HV ≥ 1.10, TQQQ delta max 0.10, exit at 50% profit or 21 DTE.
4. **Warning box** — "Capped downside ≠ low risk. You can still lose 100% of premium paid."

Badge shows: `R1=δ0.68 · 45-90 DTE`
Build: clean (0 warnings, 0 errors).

---

## Test Count
**110 tests** — no backend changes.

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear — ETF-only, permanent deferral |
| KI-099 | LOW | buy_call Leading/Improving ETFs — deferred |

---

## Audit Health
**0 CRITICAL / 0 HIGH / 0 MEDIUM** — Safe to paper trade.

---

## Next Session Priorities (Day 71)

### P0 — GLD skew inversion flag
`gate_engine._skew_flow_gate()`: GLD skew inverts during gold rallies (calls bid above puts).
Add GLD-specific branch for sell_call skew check. ~10 lines.

### P1 — XLF post-FOMC re-entry check
FOMC Jun 16-17 (Warsh). Run `/ibkr-scan` Jun 17 — if IV/HV recovers > 1.10 and IVR climbs
toward 50%, XLF sell_put is the candidate. First real trade opportunity.

### P2 — Paper trade #1
When conditions are right (post-FOMC, XLF or QQQ with VRP restored), log the first paper trade.
30 trades = meaningful win rate data.
