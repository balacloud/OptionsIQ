# OptionsIQ — Behavioral Audit (Day 11)

> **Date:** March 13, 2026
> **Method:** 4 parallel code-reading streams, structured verdict labels
> **Status:** Complete. Findings inform fix priority for Day 12 (during market hours).

---

## Audit Prompt Used

```
AUDIT MODE: Rigorous auditor. NOT helpful or agreeable — accurate.
VERDICTS: [VERIFIED], [MISLEADING], [FALSE], [PARTIAL]
METHOD: Read actual code, line numbers, compare to documented claims.
```

---

## Results: 17 Claims Audited

### Gate Logic (Claims 1-5)

#### Claim 1: "Track A gates are for calls, Track B for puts"
> **Verdict: [VERIFIED — with nuance]**
> **Source:** `gate_engine.py` lines 31-43
>
> **Reasoning:** There are actually **4 separate gate tracks**, not 2:
> - `buy_call` → `_run_track_a()` (9 gates)
> - `sell_call` → `_run_sell_call()` (7 gates, different thresholds)
> - `buy_put` → `_run_buy_put()` (9 gates, different confirmations)
> - `sell_put` → `_run_track_b()` (8 gates)
>
> Each direction runs **completely different** gate logic. They do NOT share gates.
> The "Track A / Track B" naming in docs oversimplifies — it's 4 tracks.

#### Claim 2: "Liquidity gate requires OI ≥ 1000"
> **Verdict: [VERIFIED — but permanently broken in practice]**
> **Source:** `gate_engine.py` lines 491-539, `constants.py` line 34
>
> **Reasoning:** Threshold is correct (`MIN_OPEN_INTEREST = 1000`). But when OI=0:
> - OI check fails (+1)
> - vol/OI ratio check fails (+1, division by zero → 0.0)
> - Total fails ≥ 2 → status = `"fail"`, `blocking=True`
>
> **Impact:** Liquidity gate is a **hard blocker on every analysis** because OI=0 for
> ALL current providers (IBKR KI-035 unverified, Alpaca has no OI field).
> This is the single biggest functional issue in the system.

#### Claim 3: "DTE gate enforces sweet spot per direction — seller 21-45, buyer 45-90"
> **Verdict: [MISLEADING — CORRECTION: buyers use signal confidence, not 45-90 range]**
> **Source:** `gate_engine.py` lines 140-155 (buy_call), 308-317 (sell_call), 227-236 (sell_put)
>
> **Reasoning:**
> - **Buyers:** DTE is VCP confidence + ADX dependent. High confidence → rec 21 DTE,
>   moderate → rec 45 DTE, low → `rec_dte=None` which allows any DTE ≥ 14.
>   The claimed 45-90 range is NOT enforced.
> - **Sellers:** sell_call pass=14-21, warn=21-45, fail=>60. sell_put pass=14-21, warn=21-35, fail=>45.
>   Partially matches claim but optimal range is 14-21, not 21-45.
>
> | Direction | Claimed Sweet Spot | Actual Pass Range |
> |-----------|-------------------|-------------------|
> | buy_call | 45-90 DTE | ≥14 (signal-dependent) |
> | sell_call | 21-45 DTE | 14-21 (pass), 21-45 (warn) |
> | buy_put | 45-90 DTE | ≥14 (signal-dependent) |
> | sell_put | 21-45 DTE | 14-21 (pass), 21-35 (warn) |

#### Claim 4: "IV Rank gate uses 252-day percentile"
> **Verdict: [VERIFIED]**
> **Source:** `iv_store.py` lines 104-112
>
> **Reasoning:** Formula is `(count of historical IVs ≤ current_iv / total_count) × 100`.
> This is a percentile calculation. Requires ≥30 days history (returns None if <30).
> When None: falls back to absolute IV thresholds (20/35% hardcoded in gate_engine).
> Graceful handling confirmed.

#### Claim 5: "Verdict color maps to GO/PAUSE/BLOCK with specific thresholds"
> **Verdict: [VERIFIED]**
> **Source:** `gate_engine.py` lines 45-74, `build_verdict()`
>
> **Reasoning:** Not a points/score system — it's a blocking hierarchy:
> 1. Any gate with `status="fail"` AND `blocking=True` → RED (BLOCKED)
> 2. No blocking fails but ≥1 warn → AMBER (CAUTION)
> 3. All pass → GREEN (GO)
>
> Thresholds are per-gate, not global. Each gate decides its own pass/warn/fail.

---

### Strategy Builders (Claims 6-8)

#### Claim 6: "sell_call builds bear_call_spread — works for all tickers"
> **Verdict: [VERIFIED]**
> **Source:** `strategy_ranker.py` lines 79-224, `_rank_sell_call()`
>
> **Reasoning:** Builds 3 ranked strategies:
> 1. Bear call spread (delta 0.30 short / 0.15 protection)
> 2. Higher PoP bear call spread (delta 0.20 short)
> 3. Naked short call (delta 0.15, far OTM) — fallback with "UNLIMITED RISK" warning
>
> Zero ticker-specific code. All leg selection is delta-based and generic.
> `_closest_delta()` finds nearest contract to target delta.
>
> **Caveat:** If chain has < 3 OTM contracts, `_closest_delta()` can crash
> with `ValueError` (calls `min()` on empty list). No pre-flight validation.

#### Claim 7: "buy_put builds ITM put + bear put spread + ATM put"
> **Verdict: [VERIFIED]**
> **Source:** `strategy_ranker.py` lines 226-257, `_rank_buy_put()`
>
> **Reasoning:** Returns exactly 3 strategies:
> 1. ITM put (delta ~-0.68) → `strategy_type = "itm_put"`
> 2. Bear put spread (long ATM ~-0.52, short near support) → `strategy_type = "spread"`
>    Falls back to single long put if strikes equal
> 3. ATM put (delta ~-0.52) → `strategy_type = "atm_put"`, warning "HIGH THETA"

#### Claim 8: "sell_put is still naked — no spread logic"
> **Verdict: [VERIFIED — with risk concern]**
> **Source:** `strategy_ranker.py` lines 422-475, `_rank_track_b()`
>
> **Reasoning:** All 3 ranked positions are naked short puts. No protection leg.
> - `strategy_type` always "sell_put"
> - `max_loss_per_lot = (strike - premium) × 100`
> - For $25k account: a 250-strike put = ~$25,000 max loss = **entire account**
> - **No warning label exists** (unlike sell_call which has "UNLIMITED RISK")
>
> **Recommendation:** Add warning: `"NAKED PUT — max loss = strike × 100. Margin required."`
> Or better: disable sell_put until bull_put_spread builder is implemented.

---

### Data Flow (Claims 9-11)

#### Claim 9: "Provider cascade: IBKR → Cache → Alpaca → yfinance → Mock"
> **Verdict: [MISLEADING — CORRECTION: Cache is checked BEFORE IBKR live]**
> **Source:** `data_service.py` lines 258-337
>
> **Actual order:**
> 1. Fresh cache (TTL valid) → return immediately + background refresh
> 2. IBKR live via IBWorker (circuit breaker gated)
> 3. Stale cache (expired but better than nothing)
> 4. Alpaca REST (15-min delayed)
> 5. yfinance (BS-computed greeks)
> 6. Mock (dev only)
>
> **Why this matters:** The cache-first design means if a valid cache entry exists,
> IBKR is never called synchronously. This is a performance optimization (returns in
> ~1ms vs 8-15s for IBKR), but the docs should say Cache → IBKR, not IBKR → Cache.

#### Claim 10: "Quality banner shows for every non-live source"
> **Verdict: [FALSE]**
> **Source:** `frontend/src/App.jsx` lines 34-73, QualityBanner component
>
> **Missing banner cases:**
> | data_source | Backend sends? | Frontend banner? | Gap? |
> |-------------|---------------|-----------------|------|
> | `ibkr_live` | ✅ | No banner (correct) | — |
> | `ibkr_cache` | ✅ | ✅ Info banner | — |
> | `ibkr_closed` | ✅ | ✅ Warning banner | — |
> | `ibkr_stale` | ✅ | ❌ **No banner** | **GAP** |
> | `alpaca` | ✅ | ❌ **No banner** | **GAP** |
> | `yfinance` | ✅ | ✅ Warning banner | — |
> | `mock` | ✅ | ✅ Error banner | — |
>
> Also: line 39 checks `source === 'ibkr'` but backend sends `'ibkr_live'` (A3 bug).
> **Violates Golden Rule 8.**

#### Claim 11: "None values coerced to 0.0 before gate_engine"
> **Verdict: [VERIFIED — with safe fallthrough]**
> **Source:** `app.py` line 328, `gate_engine.py` float patterns
>
> **Reasoning:**
> - `ivr_data`: Fully coerced via `{k: (0.0 if v is None else v)}` (line 328)
> - `swing_data`: NOT pre-coerced (vcp_confidence, adx passed as None)
> - `gate_engine`: Catches remaining None via `float(p.get(key, 0.0) or 0.0)` pattern
> - `bid/ask`: Explicitly checked with `if bid is not None and ask is not None`
>
> Net: safe in practice. Gate_engine is defensively coded.

---

### Frontend Behavior (Claims 12-13)

#### Claim 12: "Direction locking prevents wrong-direction analysis"
> **Verdict: [PARTIAL — frontend only, backend accepts anything]**
> **Source:** `App.jsx` lines 82-92, `app.py` line 386
>
> **Reasoning:**
> - Frontend: Disables locked direction buttons, auto-corrects selection. Works.
> - Backend: Returns `direction_locked` array but does NOT validate. Accepts any direction.
> - If someone calls the API directly, backend will analyze contradictory directions.

#### Claim 13: "Paper trade records with mark-to-market P&L"
> **Verdict: [VERIFIED]**
> **Source:** `app.py` lines 428-450
>
> **Reasoning:** Fully implemented:
> - `save_paper_trade()` persists to SQLite via iv_store
> - `list_paper_trades()` fetches live underlying price
> - MTM P&L computed dynamically on each read
> - Direction-aware formula (sell_put vs others)

---

### Golden Rules Enforcement (Claims 14-17)

#### Claim 14: "Rule 3: No magic numbers — gate_engine imports from constants.py"
> **Verdict: [FALSE — gate_engine has ZERO imports from constants.py]**
> **Source:** `gate_engine.py` lines 1-4 (imports), entire file
>
> **Reasoning:** gate_engine.py imports only `__future__`, `math`, `dataclasses`.
> **60+ numeric thresholds are hardcoded directly in the file.**
> Many have counterparts in constants.py (MIN_OPEN_INTEREST, HV_IV_PASS_RATIO, etc.)
> but gate_engine doesn't use them.
>
> Key duplicates:
> - `1000` in gate_engine vs `MIN_OPEN_INTEREST = 1000` in constants
> - `0.10` in gate_engine vs `MIN_VOLUME_OI_RATIO = 0.10` in constants
> - `2.00` in gate_engine vs `MIN_PREMIUM_DOLLAR = 2.00` in constants
>
> **This means changing a threshold in constants.py has ZERO effect on gate behavior.**

#### Claim 15: "Rule 4: app.py ≤ 150 lines, routes only"
> **Verdict: [FALSE — 581 lines, 200+ business logic]**
> **Source:** `app.py` full file
>
> **Breakdown:**
> - 23 lines: imports
> - 22 lines: module init
> - **200+ lines: business logic helpers** (should be in analyze_service.py)
>   - `_merge_swing()` (34 lines)
>   - `_extract_iv_data()` (41 lines)
>   - `_behavioral_checks()` (35 lines)
>   - `_chain_field_stats()` (24 lines)
>   - `_put_call_ratio()`, `_max_pain()`, `_get_live_price()`, `_f()`, `_i()` etc.
> - 131 lines: `/api/options/analyze` route (should be ~50)
> - 77 lines: `/api/integrate/sta-fetch` route (too large)
> - ~70 lines: other routes (OK)

#### Claim 16: "Rule 7: ACCOUNT_SIZE raises at startup if not in .env"
> **Verdict: [FALSE — silent default 25000]**
> **Source:** `app.py` line 279
>
> **Reasoning:**
> ```python
> account_size = float(payload.get("account_size", os.getenv("ACCOUNT_SIZE", 25000)))
> ```
> No startup validation exists. Default 25000 used silently.
> `constants.py` has `DEFAULT_ACCOUNT_SIZE = 25_000` but app.py doesn't reference it.

#### Claim 17: "Rule 8: Quality banners mandatory for non-live data"
> **Verdict: [FALSE — 2 gaps]**
> **Source:** `App.jsx` QualityBanner, same as Claim 10
>
> `ibkr_stale` and `alpaca` data sources show NO banner. Silent pass-through.

---

## Priority Matrix (Revised by Behavioral Audit)

Fixes should happen **during market hours** so OI/liquidity can be tested live.

### Tier 1 — Functional Blockers (fix first)
| # | Issue | Why it matters | Fix complexity |
|---|-------|---------------|----------------|
| 2 | Liquidity gate always fails (OI=0) | Every analysis hits blocking FAIL | Verify KI-035 fix live. If OI still 0, add OI-unavailable handling. |
| 14 | gate_engine 60+ hardcoded thresholds | Changing constants.py has zero effect | Add `from constants import ...`, replace all hardcoded values |
| A1 | logger undefined | App crashes on startup | 1-line fix |

### Tier 2 — Data Integrity (fix during same session)
| # | Issue | Fix |
|---|-------|-----|
| 10/17 | Missing quality banners (alpaca, ibkr_stale) | Add cases to QualityBanner |
| A3 | QualityBanner checks "ibkr" not "ibkr_live" | Fix comparison |
| 8 | sell_put naked with no warning | Add "NAKED PUT" warning label |
| 9 | Cascade order documented wrong | Update docs (code is correct — cache-first is a valid design) |

### Tier 3 — Hardening (next session if time)
| # | Issue | Fix |
|---|-------|-----|
| 3 | DTE buyer sweet spot not enforced | Design decision: enforce 45-90 or accept signal-based? |
| 12 | Direction lock frontend-only | Add backend validation |
| 16 | ACCOUNT_SIZE silent default | Add startup validation |
| A4 | SQLite WAL mode | Add PRAGMA |
| 15 | app.py 581 lines | Create analyze_service.py |

---

## Key Insight

The behavioral audit revealed that the **documentation is more aspirational than descriptive**.
5 of 17 claims are FALSE, 3 are MISLEADING. The system works (strategies build, verdicts render,
paper trades persist) but several documented constraints (sweet spots, magic numbers, account size
enforcement, quality banners) are not actually enforced in code.

**Next session must be during market hours** to:
1. Verify KI-035 OI fix (can only test when market is open)
2. Fix liquidity gate handling for OI=0 scenarios
3. Test all fixes with live data
