# OptionsIQ Three-Input Context Architecture
> **Created:** Day 63 (Jun 2, 2026)
> **Designed by:** Opus 4.8 — dual-persona (Architect + Quant Trader, Golden Rule 22)
> **Status:** PLANNED — ready to build

---

## Vision

Three Claude skills (browser, flat-rate) each emit a structured context block.
User pastes all three into OptionsIQ. Backend combines them with live chain data
to produce a final recommendation that knows about IV environment, chart structure,
AND event risk — all at once.

```
/ibkr-scan      → SCAN CONTEXT      (IVR/IV_HV/P/C/EMA)         ← already live
/chartreview    → CHART CONTEXT     (S1/S2/R1/R2/TREND/RSI/ATR)  ← to build
/catalyst-check → CATALYST CONTEXT  (FOMC/earnings/macro/verdict) ← to build
                     ↓ paste into OptionsIQ
Backend → 3 strikes + strike_vs_support + expiry_vs_events + combined verdict
```

---

## 1. New Structured Block Formats

### CHART CONTEXT (emitted at end of /chartreview output)
```
CHART CONTEXT  TICKER=QQQ  DIRECTION=sell_put  TREND=UPTREND  S1=710.00  S2=695.00  S3=675.00  R1=748.00  R2=760.00  RSI=58  ATR=8.40  CHART_VERDICT=go
```
- `TREND` ∈ {UPTREND, DOWNTREND, RANGE, RECOVERY}
- `S1/S2/S3/R1/R2` — dollar floats. **Omit entirely if level not visible** (never emit `S3=0` or `S3=N/A`)
- `RSI`, `ATR` — optional floats
- `CHART_VERDICT` ∈ {go, wait, block} — advisory only, never hard-blocks backend

### CATALYST CONTEXT (emitted at end of /catalyst-check output)
```
CATALYST CONTEXT  TICKER=QQQ  DIRECTION=sell_put  FOMC_DAYS=16  FOMC_TIER=warn  HOLDINGS_RISK=true  HOLDINGS_COMPANY=NVDA  HOLDINGS_DAYS=23  MACRO_COUNT=1  CATALYST_VERDICT=caution
```
- `FOMC_TIER` ∈ {block, warn, pass}
- `HOLDINGS_RISK` — bool (true/false)
- Omit `HOLDINGS_COMPANY`/`HOLDINGS_DAYS` when `HOLDINGS_RISK=false`
- `CATALYST_VERDICT` ∈ {proceed, caution, abort}

---

## 2. New Backend Files

### `backend/chart_context_parser.py`
Modeled exactly on `scan_context_parser.py`.

Key functions:
- `parse_chart_context(text) -> dict` — KEY=VALUE regex extraction
- `apply_chart_context_to_response(response, payload, underlying, direction) -> dict`
  - Adds `response["chart_verdict"]` and `response["chart_levels"]`
  - **Does NOT touch gate_payload** — chart is post-gate, advisory only
  - Persona A: zero gate blast radius. A malformed chart paste cannot flip a block to pass.
- `compute_strike_vs_support(strike, levels, direction) -> dict`
  - Returns `{zone, label, atr_distance}` per strategy
  - `zone` ∈ {above_s1, between_s1_s2, below_s2, no_data}
  - Example label: `"$695 short strike sits below S1 $710 — cushioned by prior breakout base ✅"`
  - Missing levels → `{zone: "no_data", label: None}` — explicit null, never a fake pass (Rule 11)

### `backend/catalyst_context_parser.py`
- `parse_catalyst_context(text) -> dict`
- `apply_catalyst_context_to_gate_payload(gate_payload, payload) -> (dict, dict)`
  - Returns `(updated_gate_payload, catalyst_overlay_dict)`
  - Merges `gate_payload["catalyst_override"]` = {tier, verdict, fomc_days, reconcile_status}
  - **Rule 23 reconciliation logic:**
    - Backend fomc_days_away stays authoritative for XLF/TQQQ hard blocks
    - Catalyst `FOMC_TIER=pass` CANNOT unblock a structural hard block
    - Catalyst can confirm warn reasons ("confirmed by /catalyst-check")
    - Catalyst `HOLDINGS_RISK=false` when backend found risk → surface `catalyst_reconcile_warn`
    - Disagreement = signal, never silent (Rule 11)

---

## 3. analyze_service.py Changes (3 insertion points)

### Insertion A — before gates (line ~967, after existing scan-context merge):
```python
gate_payload, catalyst_overlay = apply_catalyst_context_to_gate_payload(gate_payload, payload)
```
Catalyst feeds gate_payload BEFORE `engine.run()` to adjust event gate severity.

### Insertion B — after strategy enrichment (line ~990):
```python
chart_ctx = parse_chart_context(payload.get("chart_context", ""))
for s in strategies:
    s["strike_vs_support"] = compute_strike_vs_support(float(s["strike"]), chart_ctx, direction)
    s["catalyst_overlay"] = _strategy_catalyst_overlay(s, at_risk, catalyst_overlay)
```

New helper `_strategy_catalyst_overlay(strategy, at_risk, overlay)`:
- Checks if **this strategy's expiry** clears the at-risk earnings date
- Returns `{clears_event: bool, label}`
- Example: `"Jun 20 expiry exits before NVDA earnings Jun 25 ✅"` or `"Jul 18 holds THROUGH NVDA ⚠️"`
- **Persona B: highest-value feature in the whole plan — changes which expiry I pick**

### Insertion C — response assembly:
New top-level fields: `chart_verdict`, `chart_levels`, `catalyst_overlay`
New per-strategy fields: `strike_vs_support`, `catalyst_overlay`

---

## 4. Gate Engine Changes (minimal, surgical)

In `_etf_fomc_gate` and `_etf_holdings_earnings_gate`:
- Read optional `p.get("catalyst_override")`
- **Only two allowed effects:**
  1. Append "(confirmed by /catalyst-check)" to warn reason when tiers agree
  2. Append reconcile warning when they disagree
- Hard-block branches (`FOMC_BLOCK_TICKERS` + `fomc_days <= 14` + seller) **UNTOUCHED**
- Persona A: additive-only changes. No existing gate assertion can flip.

---

## 5. Frontend Changes

### App.jsx
- Two new `useState`: `chartContext`, `catalystContext` (alongside existing `scanContext`)
- **Two separate textareas** (not combined) — separate failure domains. Malformed CATALYST paste doesn't disable valid CHART paste.
- Placeholders show exact example CHART/CATALYST CONTEXT lines
- Payload extended: `...(chartCtx ? {chart_context: chartCtx} : {}), ...`
- All three optional — missing = omitted = backend no-ops = response lacks those fields gracefully

### TopThreeCards.jsx
- `strike_vs_support` — new detail item after `strike_vs_em_label` (already exists), guarded by null check
- `chart_verdict` — small banner above rank-1 card: `"Chart: UPTREND · GO ✅"` colored by verdict
- `catalyst_overlay` per strategy — warning block (loud) when `clears_event=false`
  - Intentionally loud: holding through earnings = P&L event
- New props: `chartVerdict`, `catalystOverlay`

---

## 6. Skill Additions (chartreview.md + catalyst-check.md)

Add machine block instructions to end of each skill's Output Format section:

**chartreview.md addition:**
> After the human-readable review, emit exactly one line:
> `CHART CONTEXT  TICKER=… DIRECTION=… TREND=… S1=… S2=… [S3=…] R1=… R2=… [RSI=…] [ATR=…] CHART_VERDICT=go|wait|block`
> Omit any level you cannot identify. Map: GO→go, WAIT→wait, HARD BLOCK→block.

**catalyst-check.md addition:**
> After the human-readable output, emit exactly one line:
> `CATALYST CONTEXT  TICKER=… DIRECTION=… FOMC_DAYS=… FOMC_TIER=block|warn|pass HOLDINGS_RISK=true|false [HOLDINGS_COMPANY=…] [HOLDINGS_DAYS=…] MACRO_COUNT=… CATALYST_VERDICT=proceed|caution|abort`
> Map: PROCEED→proceed, CAUTION→caution, ABORT→abort. Omit HOLDINGS_COMPANY/HOLDINGS_DAYS when HOLDINGS_RISK=false.

---

## 7. Test Plan

Two new test files mirroring `test_scan_context.py`:

**`test_chart_context.py`:**
- `test_parse_full_line`
- `test_parse_omits_missing_s3` — "S3" absent → `"s3" not in result`
- `test_parse_empty_returns_empty`
- `compute_strike_vs_support` — below_s1, between_s1_s2, above_s1, no_data, call-side vs R1/R2
- `test_apply_no_chart_context_is_noop`
- `test_chart_never_touches_gates` — gate_payload identical before/after (proves zero blast radius)

**`test_catalyst_context.py`:**
- Parse full line, bool/int parsing, omitted holdings, empty
- `test_apply_noop`
- **Rule 23 reconciliation tests (critical):**
  - `test_catalyst_pass_cannot_unblock_xlf_fomc` — XLF, backend 10 days, FOMC_TIER=pass → still blocks
  - `test_catalyst_confirms_warn` — tier agrees → reason gets "(confirmed by /catalyst-check)"
  - `test_holdings_disagreement_surfaces_warn` — backend has NVDA risk, HOLDINGS_RISK=false → reconcile warn
- `_strategy_catalyst_overlay` — expiry before earnings → clears_event=True; after → False + label

**Regression guarantee:** New parsers no-op when payload keys absent. All 52 existing tests pass unchanged (additive-only gate changes).

---

## 8. Build Order

| Step | What | Depends on |
|------|------|-----------|
| 1 | `chart_context_parser.py` + `catalyst_context_parser.py` (pure functions) | nothing |
| 2 | `test_chart_context.py` + `test_catalyst_context.py` | step 1 |
| 3 | Gate engine edits (`catalyst_override` reads) + gate-wiring test | step 1 |
| 4 | `analyze_service.py` wiring (3 insertion points) | steps 1, 3 |
| 5 | Skill machine-block additions (chartreview.md, catalyst-check.md) | parallel with 1-4 |
| 6 | Frontend (App.jsx textareas + payload, TopThreeCards display) | step 4 stable |
| 7 | Full `pytest` run — confirm 52 original + new specs green | step 6 |

---

## Key Persona Decisions

| Decision | Persona | Reasoning |
|----------|---------|-----------|
| CHART context never touches gate_payload | Architect ✅ | Minimal blast radius — malformed paste can't flip a block |
| CHART TREND advisory only, never blocks | Quant ✅ + Rule 23 | /ibkr-scan owns the EMA hard-block with real IBKR numbers |
| Catalyst cannot override structural hard blocks | Architect ✅ | Backend is the safety net |
| S3 omitted when not visible (not S3=0) | Architect ✅ | Rule 11 + Rule 3 — no silent fallbacks, no magic sentinels |
| Holdings disagreement surfaces warn | Both ✅ | Disagreement is a signal — if calendar disagrees with live check, that's the exact moment you lose money |
| `_strategy_catalyst_overlay` checks per-expiry | Quant ✅ | Highest-value feature: "does Jun 20 expiry clear NVDA Jun 25?" changes which strike I pick |
| Two separate textareas, not one | Architect ✅ | Separate failure domains |
