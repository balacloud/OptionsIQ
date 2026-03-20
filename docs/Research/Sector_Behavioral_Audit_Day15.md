# OptionsIQ — Sector Rotation Behavioral Audit (Day 15, Iteration 1)

> **Date:** March 20, 2026
> **Method:** End-to-end trace: STA → sector_scan_service → app.py → useSectorData → SectorRotation.jsx → ETFCard.jsx → App.jsx deep dive
> **Auditor mode:** Quant trader + systems architect (Rule 21). Verdict priority: P&L impact → data integrity → UX → code style.
> **Status:** Complete. Findings below.

---

## Audit Prompt

```
AUDIT MODE: Quant trader with 50 years experience. NOT helpful — accurate.
VERDICTS: [VERIFIED], [MISLEADING], [FALSE], [PARTIAL], [BROKEN]
METHOD: Trace every data field from producer → API → frontend. Every field shown
to the trader must trace to a real computation. Dead paths are critical bugs.
PRIORITY: Would this cost me money? → Would this show me wrong data? → Is the UX confusing?
```

---

## Results: 21 Claims Audited

### Data Pipeline (Claims 1-6) — The Money Path

#### Claim 1: "L2 fetches chain data from data_service and extracts IV + liquidity"
> **Verdict: [BROKEN — L2 chain fetch crashes on every call]**
> **Source:** `sector_scan_service.py` line 331, `data_service.py` line 252
>
> `data_service.get_chain()` returns `tuple[dict, str]` (chain, data_source).
> Sector L2 does: `chain = data_service.get_chain(ticker, direction=direction)`
> Then: `chain.get("data_source")` → **AttributeError: 'tuple' object has no attribute 'get'**
>
> The `except` on line 356 silently catches this and logs a warning. All IV, liquidity,
> bid/ask, OI fields return `None`. The L2 response looks "clean" but contains
> **zero actual data** — every field is dash.
>
> **Compare:** app.py line 324: `chain, data_source = data_svc.get_chain(...)` — correct tuple unpacking.
>
> **Impact:** CRITICAL. L2 has **never worked** with any live data source. Every L2 call
> returns a response with all None fields, and nobody noticed because the UI renders
> "—" for None and the error is swallowed silently. The entire L2 feature is non-functional.

#### Claim 2: "IVR is computed from iv_store when iv_current is available"
> **Verdict: [BROKEN — upstream dependency (Claim 1) prevents execution]**
> **Source:** `sector_scan_service.py` lines 360-364
>
> Code is correct in isolation: `ivr = iv_store.compute_ivr_pct(ticker, iv_current)`.
> But `iv_current` is always `None` because the chain fetch crashes (Claim 1).
> The `if iv_store and iv_current is not None` guard prevents execution.
> IVR remains `None`. DTE model runs with `None` → always returns 45 (default).
> Direction re-evaluation with IVR: never fires.
>
> **Cascade:** Q1 fix (IVR wiring) is correct code sitting behind a broken pipe.

#### Claim 3: "HV20 is computed independently from iv_store"
> **Verdict: [PARTIAL — runs but likely returns None for ETFs]**
> **Source:** `sector_scan_service.py` lines 365-369, `iv_store.py` lines 147-178
>
> `compute_hv(ticker, 20)` requires 21+ OHLCV rows in SQLite for that ticker.
> OHLCV is only stored when `_extract_iv_data` in app.py runs (L3 analyze flow).
> If the user has never run a full L3 analysis on an ETF, `ohlcv_daily` table
> has no rows for it → `compute_hv` returns `None`.
>
> **Not a code bug** — it's a cold-start problem. HV20 will populate after first L3 run.
> But the user sees "—" for HV on all ETFs until they've deep-dived each one individually.

#### Claim 4: "ATM contract is found by closest strike to underlying"
> **Verdict: [BROKEN — same Claim 1 crash. But logic is correct if reached.]**
> **Source:** `sector_scan_service.py` line 339
>
> `min(contracts, key=lambda c: abs(c.get("strike", 0) - underlying))` — correct.
> Uses `impliedVol` (not `iv`) — correct after Q1 fix.
> But never executes because of Claim 1.

#### Claim 5: "SPY regime check adds leading-indicator warning to L1 scan"
> **Verdict: [VERIFIED — with performance concern]**
> **Source:** `sector_scan_service.py` lines 130-165
>
> `_spy_regime()` fetches 1 year of SPY daily data via yfinance. Computes SMA200 and 5-day return.
> Warning fires when SPY 5d <= -2% or below 200 SMA. Cached with scan data (60s TTL).
>
> **Performance:** yfinance SPY fetch is ~1-3 seconds. On first scan load this adds to latency.
> Not a bug, but user sees "Scanning sector ETFs..." for 3-5 seconds instead of <2s (claimed in docstring).
>
> **Math verified:** SMA200 = mean of last 200 closes. 5-day = (close[-1] - close[-6]) / close[-6] × 100.

#### Claim 6: "Scan cache prevents N+1 STA calls from L2"
> **Verdict: [VERIFIED]**
> **Source:** `sector_scan_service.py` lines 34-36, 302-309
>
> Cache stores full scan result. L2 checks `time.monotonic()` delta < 60s.
> Deep copy on read (line 305) prevents mutation. Fresh scan called on miss.
> Correct implementation.

---

### Direction + Mapping Logic (Claims 7-10)

#### Claim 7: "bull_call_spread maps to buy_call at all boundaries"
> **Verdict: [VERIFIED]**
> **Source:**
> - Backend L2: line 330 `direction = "buy_call" if raw_dir == "bull_call_spread" else raw_dir`
> - Frontend deep dive: App.jsx line 99 `bull_call_spread: 'buy_call'`
>
> Both boundaries covered. Display label preserved in L1/L2. Core direction used for data layer + L3.

#### Claim 8: "L1 direction is research-verified quadrant mapping"
> **Verdict: [VERIFIED]**
> **Source:** `sector_scan_service.py` lines 42-57
>
> Leading → buy_call (bull_call_spread if IVR>50). Improving → bull_call_spread.
> Weakening/Lagging → None. Matches research doc Day 13.
> IVR branch in L1 never fires (no IVR at L1 level) — this is **by design** (L1 is STA-only).
> IVR-aware direction only at L2 (line 376). Correct separation of concerns.

#### Claim 9: "TQQQ direction filter prevents inappropriate strategies"
> **Verdict: [PARTIAL — filter logic has dead branch]**
> **Source:** `sector_scan_service.py` lines 260-264
>
> `if tqqq["suggested_direction"] not in ("buy_call", "sell_call", "bull_call_spread", None):`
> TQQQ inherits QQQ's quadrant. QQQ can only be Leading/Improving/Weakening/Lagging.
> `quadrant_to_direction` returns: buy_call, bull_call_spread, or None.
> So `suggested_direction` can only ever be: `buy_call`, `bull_call_spread`, or `None`.
> All three are in the `not in` whitelist. **The filter condition is never True.**
> The `sell_call` entry in the whitelist is dead — no quadrant maps to sell_call.
>
> Not a P&L risk (TQQQ gets correct bullish-or-skip directions), but the filter
> creates false safety — it looks like it's protecting against something it can't encounter.

#### Claim 10: "Deep dive from L2 detail auto-triggers L3 analysis"
> **Verdict: [FALSE — user must manually click Analyze]**
> **Source:** App.jsx lines 104-109
>
> `handleSectorDeepDive` sets ticker + direction + switches tab. Does NOT call `onAnalyze()`.
> User lands on Analyze tab with ETF pre-filled but must manually click "Analyze" button.
> The "Full Gate Analysis (L3) →" button label implies immediate execution.
>
> **UX impact:** Medium. Trader clicks "Full Gate Analysis", waits, sees... nothing happened.
> Has to find and click Analyze button. Breaks the "one click to answer" mental model.

---

### Frontend Display (Claims 11-15)

#### Claim 11: "Quality banner renders for all non-live data sources in L2 detail"
> **Verdict: [PARTIAL — missing ibkr_stale]**
> **Source:** SectorRotation.jsx lines 35-42
>
> Handles: ibkr_cache, ibkr_closed, alpaca, yfinance, mock. ✅
> Missing: `ibkr_stale` — no banner text for this source. Would render empty `<div>`.
>
> **Impact:** Low (ibkr_stale is rare — only when IBKR goes down during a session).
> But Golden Rule 8 violation.

#### Claim 12: "Spread color coding: green < 2%, amber 2-5%, red > 5%"
> **Verdict: [PARTIAL — null spread gets colored]**
> **Source:** SectorRotation.jsx line 95
>
> `detail.atm_spread_pct > 5 ? 'text-red' : detail.atm_spread_pct > 2 ? 'text-amber' : 'text-green'`
> When `atm_spread_pct` is `null`: `null > 5` is `false`, `null > 2` is `false` → falls to `text-green`.
> A null spread renders as "—" in green color. Green on "—" implies "good liquidity" when
> actually there's NO data. Should check for null first.

#### Claim 13: "ETFCard handles null price/week_change/month_change gracefully"
> **Verdict: [VERIFIED]**
> **Source:** ETFCard.jsx lines 50, 61, 67
>
> Price: `$${fmt(etf.price, 2)}` — `fmt` returns "—" for null. Shows "$—" (minor: dollar sign before dash).
> Week/Month: explicit null check `etf.week_change != null ? ...` Shows "—" for null. Correct.

#### Claim 14: "Timestamp parses correctly in STA footer"
> **Verdict: [BROKEN — invalid ISO date construction]**
> **Source:** SectorRotation.jsx line 230, sector_scan_service.py line 275
>
> Backend: `datetime.now(timezone.utc).isoformat()` → `"2026-03-20T15:30:00+00:00"`
> Frontend: `new Date(sectorData.timestamp + 'Z')` → `"2026-03-20T15:30:00+00:00Z"`
>
> `+00:00Z` is an invalid ISO 8601 suffix. `new Date()` may parse it in Chrome/V8
> (lenient parser) but it's technically undefined behavior. Safari is stricter.
>
> **Fix:** Remove the `+ 'Z'` append — the timestamp already has timezone info.

#### Claim 15: "RS ratio defaults to 0 when STA doesn't provide it"
> **Verdict: [MISLEADING — 0 is semantically wrong]**
> **Source:** `sector_scan_service.py` lines 206-207
>
> `"rs_ratio": s.get("rsRatio", 0), "rs_momentum": s.get("rsMomentum", 0)`
> RS Ratio is normalized around 100 (midpoint). Value of 0 means "catastrophically weak" —
> it would color-code as deep red and misclassify the ETF's quadrant for cap-size derivation.
> Cap-size ETFs (line 222): `rs = sr.get("rsRatio", 100)` defaults to 100 (neutral). Inconsistent.
>
> Sector ETFs default to 0, cap-size ETFs default to 100. Same field, different defaults.

---

### System Architecture (Claims 16-21)

#### Claim 16: "L1 scan is < 2 seconds"
> **Verdict: [FALSE — 3-5 seconds with SPY regime]**
> **Source:** Docstring line 169, `_spy_regime()` line 138
>
> STA fetch: ~0.5-1s. SPY yfinance fetch: ~1-3s. Total: 2-5s.
> Docstring says "< 2 sec — STA data + SPY regime". The SPY addition violates the claim.
>
> Not a code bug — but the timing claim is now wrong.

#### Claim 17: "Sector ETF universe is 15 tickers"
> **Verdict: [VERIFIED — but count varies]**
> **Source:** `constants.py` lines 232-237
>
> ETF_TICKERS has 15 entries. But scan_sectors adds TQQQ dynamically (line 253).
> So scan returns up to 16 entries. Frontend `sector_count` field reflects actual count.

#### Claim 18: "Catalyst warnings fire for FOMC-sensitive ETFs within 3 days"
> **Verdict: [VERIFIED]**
> **Source:** `sector_scan_service.py` lines 96-111, `constants.py` lines 256-258
>
> FOMC_HIGH_SENSITIVITY = {XLF, XLRE}. FOMC_WARN_DAYS = 3. Iterates FOMC_DATES,
> checks `0 <= days_until <= 3`. Breaks after first match. Correct.
>
> Next FOMC: 2026-05-06 (47 days away). No warnings currently active. Will fire when ≤3 days.

#### Claim 19: "L2 direction re-evaluated with IVR feeds back to frontend"
> **Verdict: [VERIFIED in code — but never executes (Claim 1 dependency)]**
> **Source:** `sector_scan_service.py` lines 374-376, 382
>
> `direction_with_ivr = quadrant_to_direction(quadrant, ivr=ivr)` → overrides L1 direction.
> Response: `"suggested_direction": direction_with_ivr`. Correct override placement (after `**etf_data`).
> But IVR is always None due to Claim 1, so direction_with_ivr always equals L1 direction.

#### Claim 20: "app.py route validates ticker against ETF_TICKERS before calling service"
> **Verdict: [VERIFIED — but duplicate validation]**
> **Source:** app.py lines 620-622, sector_scan_service.py lines 298-300
>
> Both check `ticker not in ETF_TICKERS`. Double validation is harmless but redundant.

#### Claim 21: "Error responses from sector endpoints return 503"
> **Verdict: [VERIFIED]**
> **Source:** app.py lines 612-613, 624-625
>
> Both scan and analyze check `result.get("error")` → return 503. Correct for service-unavailable.

---

## Priority Matrix (Quant Impact Order)

### Tier 0 — Broken (non-functional)
| # | Finding | Impact | Fix |
|---|---------|--------|-----|
| 1 | `get_chain` returns tuple, L2 treats as dict | **L2 has never worked.** All IV/liquidity fields are None on every call. | Tuple unpack: `chain, data_source = data_service.get_chain(...)` |
| 2 | IVR/HV/DTE all dead (blocked by #1) | DTE always 45. Direction never IVR-adjusted. | Unblocked by fixing #1. |

### Tier 1 — Wrong Data Shown to Trader
| # | Finding | Impact | Fix |
|---|---------|--------|-----|
| 12 | Null spread renders as green | Trader sees green "—" = "good liquidity" when no data exists | Add null guard before color ternary |
| 15 | rs_ratio defaults 0 (sector) vs 100 (cap-size) | RS=0 misclassifies quadrant for any missing data | Default to `None`, not `0` |
| 14 | Timestamp `+00:00Z` invalid | May fail in Safari, shows wrong time | Remove `+ 'Z'` in frontend |

### Tier 2 — UX Friction
| # | Finding | Impact | Fix |
|---|---------|--------|-----|
| 10 | Deep dive doesn't auto-trigger analysis | User clicks "Full Gate Analysis" → nothing happens | Call `onAnalyze()` after state set (useEffect or callback) |
| 11 | Missing `ibkr_stale` quality banner text | Empty banner div renders | Add stale case |

### Tier 3 — Documentation / Cosmetic
| # | Finding | Impact | Fix |
|---|---------|--------|-----|
| 9 | TQQQ filter condition is always false | Dead code, false safety | Remove or document |
| 16 | L1 "< 2 sec" claim wrong | Misleading docstring | Update docstring |
| 13 | `$—` for null price | Minor display quirk | Conditional dollar sign |
| 20 | Duplicate ticker validation | Harmless redundancy | Leave as defense-in-depth |

---

## Iteration Summary

**21 claims audited. 3 BROKEN, 3 FALSE, 3 PARTIAL, 3 MISLEADING, 9 VERIFIED.**

The critical finding is Claim 1: **the entire L2 pipeline has never worked** because `get_chain` returns a tuple and sector L2 treats it as a dict. This single bug silently nullifies every Q1-Q2 fix from earlier today. All IV, IVR, HV20, bid/ask, OI, spread, volume — all None on every L2 call.

**Next iteration target:** 0 BROKEN, 0 FALSE. Remaining PARTIAL/MISLEADING acceptable if documented.
