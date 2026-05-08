# OptionsIQ — Known Issues Day 48
> **Last Updated:** Day 48 (May 8, 2026)
> **Previous:** KNOWN_ISSUES_DAY47.md

---

## Resolved This Session (Day 48)

No code changes this session — research/documentation only.

---

## New Issues Found This Session (Day 48)

Design gaps identified by ChatGPT external audit (all pending external audit consolidation before implementing):

### KI-096: IVR null coerced to 0.0 — missing data treated as low volatility (MEDIUM)

**Description:** When IVR history is unavailable (most Tier 2 ETFs), `ivr_data` is coerced to `0.0` before being passed to `gate_engine`. The IVR gate then sees 0% IVR and fails the seller threshold (IVR_SELLER_PASS_PCT=35%), routing to buyer direction instead. This means "no data" behaves identically to "IV is very cheap" — both result in buyer direction.

**Root cause:** `analyze_service.py` coerces None IVR to 0.0 before gate_payload to satisfy gate_engine's float requirement.

**Impact:** IWM was showing `bull_call_spread` in the May 7 scan not because conditions favor buying, but because IVR data was missing and coerced to 0.0.

**Fix needed:** Separate the null path — treat `ivr=None` as "unknown confidence" in gate logic rather than "low IVR". Gate should warn on null IVR rather than silently routing to buyer direction.

**Awaiting:** External audit consolidation (Gemini/Perplexity responses pending).

---

### KI-097: Event density gate missing — single-next-event logic misses clustered macro risk (MEDIUM)

**Description:** `_days_until_next_macro()` finds only the nearest upcoming event. For a 22 DTE trade, 4 macro events (NFP May 8, CPI May 12, FOMC minutes May 20, PCE May 28) are treated identically to 1 event. Event density is a path-risk problem, not a point-in-time problem.

**Root cause:** `gate_engine.py` `_etf_fomc_gate()` checks single-event proximity only.

**Fix needed:** Count events in DTE window. Escalate WARN→BLOCK at 3+ events for rate-sensitive ETFs (XLF, XLRE, XLU, XLE, IWM, QQQ); 4+ for any ETF.

**Awaiting:** External audit consolidation before implementing.

---

### KI-098: Absolute trend gate missing for bear_call_spread (MEDIUM)

**Description:** `quadrant_to_direction()` maps Lagging quadrant → `bear_call_spread` based on relative RS only (`rs_ratio < 98 AND rs_momentum < -0.5`). A sector can be Lagging vs SPY while rising in absolute terms (e.g., sector +2% while SPY +5%). Bear call spread on a rising sector fights the tape. `weekChange` is already in the STA response but unused.

**Root cause:** `sector_scan_service.py` `quadrant_to_direction()` does not accept `week_change` parameter. Confirmed by reading STA `backend.py` — STA computes `weekChange` as `(price[-1]/price[-5] - 1) * 100` and returns it; OptionsIQ passes it through but never uses it for direction decisions.

**Fix needed:** Add `week_change` parameter to `quadrant_to_direction()`. Require `week_change <= 0` for `bear_call_spread`. Call sites: `scan_sectors()` line 257, `analyze_sector_etf()` line 446.

**Awaiting:** External audit consolidation before implementing.

---

### KI-099: bull_call_spread missing as direction option (LOW)

**Description:** For Leading/Improving sectors with IVR 30–50%, the system currently returns `sell_put` (IVR≥50%) or `buy_call` (IVR<30%). There is no `bull_call_spread` option for the mid-IVR range. A debit spread reduces theta and vega exposure vs naked long call and is often the better structure at mid-IV.

**Fix needed:** Add `bull_call_spread` case to `quadrant_to_direction()` for Leading/Improving + IVR 30–50%.

**Awaiting:** External audit consolidation.

---

### KI-100: Tier 1 GO rate not tracked separately (LOW)

**Description:** The weekly gate pass rate log tracks all 15 ETFs. Tier 2 ETFs (XLV, XLI, XLC, XLB, XLP, MDY) are structurally blocked by liquidity in most market conditions. The aggregate "0 GO out of 15" number misrepresents system performance — the true tradable universe is ~5 Tier 1 ETFs (QQQ, IWM, XLF, XLK, XLY).

**Fix needed:** Add Tier 1 GO rate column to weekly gate pass rate log in Phase7c_Research.md. Track separately in Best Setups scan output.

---

## Still Open (Carried Forward)

### KI-059: Single-stock bear untested (HIGH — DEFERRED)
Stocks still return HTTP 400 (ETF-only mode). Bear directions for stocks untested since ETF pivot Day 21. Deferred by design — ETF-only is the current product scope.

---

## Resolved History (recent)
- KI-086: app.py `_run_one` extraction ✅ Day 46
- KI-076: TradeExplainer isBearish() live test ✅ Day 44
- KI-081: CPI/NFP/PCE macro events calendar ✅ Day 43
- KI-077: DirectionGuide sell_put label ✅ Day 43
- KI-075: GateExplainer GATE_KB drift ✅ Day 43
- KI-064: IVR mismatch L2 vs L3 ✅ Day 43
- KI-094: QualityBanner dead ibkr_cache key ✅ Day 42
- KI-095: BatchStatusPanel timestamp UTC offset ✅ Day 42
