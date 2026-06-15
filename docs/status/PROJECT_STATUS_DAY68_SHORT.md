# Project Status — Day 68 (Jun 15, 2026)
> **Version:** v0.36.0
> **Session type:** Peer review calibration — P1–P4 gate tweaks

---

## What Shipped

### P1 — IVR Seller Threshold: 35→40 + Warn Band 35–40%
`constants.py`: `IVR_SELLER_PASS_PCT` raised 35→40. New `IVR_SELLER_WARN_MIN=35`.
`gate_engine.py`: All 4 IVR seller gates updated (ETF sell_put, ETF sell_call, stock sell_put, stock sell_call) — now 4-tier logic:
- IVR ≥ 40% → **PASS**
- IVR 35–40% → **WARN** "borderline, size down" (new band)
- IVR 25–35% → **WARN** "minimum viable, reduced edge"
- IVR < 25% → **FAIL** (non-blocking on ETF tracks)

**Rationale:** Peer review (Perplexity/Gemini/ChatGPT Day 67) consensus — 35% conflated "adequate" with "good edge." Practical effect: trades at IVR 35–40 now surface a warn instead of a clean pass, prompting the trader to size down.

### P2 — Expected Move Distance Ratio Labels
`constants.py`: Added `EM_WARN=0.75`, `EM_WARN_STRONG=0.50`.
`analyze_service.py`: `_enrich_strategies()` updated — `strike_vs_em_label` now uses:
- ≥ 0.75x EM → `0.82x EM ✅`
- 0.50–0.75x EM → `0.65x EM ⚠️ high gamma risk`
- < 0.50x EM → `0.40x EM ❌ inside expected move — very high gamma risk`

**Old labels used "σ OTM" language (sigma implies log-normal) with thresholds 1.0/0.8.** New labels say "x EM" (dimensionless distance ratio) with thresholds 0.75/0.50. Peer review corrected the framing: "POP < 50%" is statistically imprecise; "high gamma risk" is honest.

### P3 — TQQQ Satellite Gate: Separate Thresholds
`constants.py`: 5 new TQQQ-specific constants added:
  - `TQQQ_IVR_PASS_MIN=50`, `TQQQ_IVR_WARN_MIN=40`
  - `TQQQ_VRP_PASS_MIN=1.15`, `TQQQ_VRP_WARN_MIN=1.05`
  - `TQQQ_SKEW_WARN_PTS=8`

`gate_engine.py`: `_tqqq_satellite_gate()` rewritten — now checks 4 conditions separately:
1. VIX < 18 (≥18 → warn)
2. IVR ≥ 50 (40–50 → borderline warn; <40 → thin premium warn)
3. IV/HV ≥ 1.15 (1.05–1.15 → VRP borderline; <1.05 → no edge)
4. Put skew < 8 pts (≥8 → elevated hedging warn)

**Previously:** Always returned WARN with vague "verify via /ibkr-scan" message.
**Now:** Returns PASS when all 4 conditions met; WARN with specific issues listed otherwise.

Peer review flagged TQQQ as "CRITICAL" — the generic warn gave no actionable guidance. Now users see exactly which condition is failing.

### P4 — GLD IV/HV Tenor Audit (Read-Only)
Verified: `current_iv` = ATM contract IV from Tradier chain (the selected expiry's implied vol, typically 30–45 DTE). `hv_20` = 20-day close-to-close HV from OHLCV. Different tenors by design — standard Sinclair VRP methodology. No code change needed. 1.10 threshold for GLD confirmed correct.
Documented in `docs/stable/GATE_REFERENCE.md` under `hv_iv_vrp`.

---

## Test Count
**110 tests** — 10 new tests added this session (was 100):
- 4 IVR tier boundary tests (P1)
- 6 TQQQ gate condition tests (P3)

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | LOW | Single-stock bear untested — ETF-only going forward |
| KI-099 | LOW | buy_call for Leading/Improving ETFs — single-leg only, deferred |

---

## Audit Health
**0 CRITICAL / 0 HIGH / 0 MEDIUM** — Safe to paper trade.

---

## Next Session Priorities (Day 69)

### P0 — Live end-to-end test with blended /chartreview
Run morning workflow: /ibkr-scan → /chartreview (blended 3-in-1 skill, paste screenshot + SCAN CONTEXT) → paste both context blocks into OptionsIQ → verify direction verdict matches backend recommendation. Carried over from Day 68 (session focused on calibration instead).

### P1 — Verify IVR threshold change live
Run /ibkr-scan + analyze on QQQ or IWM. Confirm IVR 35–40 now shows WARN (not PASS) in gate output.

### P2 — Frontend Redesign (backlog)
Warnings-only gate display, one trade per screen, cleaner aesthetic. Low priority — gate logic is now fully peer-reviewed.

### P3 — GLD skew inversion flag
Peer review noted: GLD calls get bid above puts during gold rallies (inverted skew vs equity ETFs). Add flag to `skew_flow` gate for GLD to invert the signal direction check. ~10 lines.
