# Project Status — Day 47 (May 7, 2026)
> **Version:** v0.31.0
> **Tests:** 36 (unchanged)

---

## What Shipped

### README Full Rewrite (P0 from Day 46/47)
**Root cause:** README had 9+ stale sections since v0.20.0 — IBKR shown as primary data source (should be Tradier), SCHB listed as ETF (not in app), test count 27 (now 36), IVR threshold 50% (now 35%), DTE seller floor 21 (now 30), 6 missing backend files, 13 missing frontend components, version history stopped at v0.20.0, API table had only 10 of 21 endpoints.
**Fix:** Complete rewrite. Data provider cascade now shows Tradier as [2] PRIMARY LIVE; IBKR EOD-only. ETF universe: 15 tickers (SCHB removed). All 21 backend files listed with accurate descriptions. All 22 frontend components listed. All 6 test files listed with descriptions. API table complete (21 endpoints). Version history through v0.30.1. DTE/IVR thresholds corrected.
**Verification:** README now matches code state as of Day 47.

### Phase 7c Trading Effectiveness — Code Improvements
**Root cause (from Day 46 research):** 9/11 ETFs blocked by Liquidity Proxy (bid-ask >20%). System correctly identifies genuine illiquidity but provides no actionable guidance — same generic message for Tier 1 (liquid: QQQ/XLF) vs Tier 2 (sector ETFs with structurally wide OTM spreads). Time-of-day factor also not surfaced (early-session OTM spreads 2-3x wider).

**Fix 1 — ETF liquidity tiers (constants.py):**
- Added `ETF_OPTIONS_LIQUID_TIER1 = frozenset({"QQQ", "IWM", "XLF", "XLK", "XLY"})` with research-backed comment (Market Chameleon daily options volume data).

**Fix 2 — Time-of-day helper (analyze_service.py):**
- Added `_is_early_market_session()` — returns True if 9:30-10:00 AM ET on a weekday. Uses UTC + DST-aware offset approximation.

**Fix 3 — Actionable liquidity gate messages (analyze_service.py):**
- `"ticker"` added to gate_payload dict so `apply_etf_gate_adjustments` can access it.
- When blocked by >20% spread AND ticker is NOT Tier 1: message now includes "QQQ/XLF/IWM offer tighter OTM spreads for the same directional exposure".
- When blocked in early session: message adds "Early session: OTM spreads typically narrow after 10:00 AM ET — rescan later".

**Before:** `"Bid-ask spread 39.2% — data unreliable at this width; do not trade until spread narrows"`
**After:** `"Bid-ask spread 39.2% — too wide for efficient execution. XLV options have moderate liquidity; QQQ/XLF/IWM offer tighter OTM spreads for the same directional exposure"`

**Verification:** 36 tests pass. One test updated (message text assertion for new wording; blocking=True and status=fail behavior unchanged).

### Phase 7c Analysis Document
**Created:** `docs/Research/Phase7c_Actionable_Day47.md`
- Root cause analysis of liquidity tier problem
- Impact assessment table (before/after Day 47 messages)
- Adversarial LLM prompt for Check 10.4 method b (user action needed)
- Weekly gate pass rate log (first data point: 2/11 CAUTION, May 7)
- Long-term Phase 7c roadmap

---

## Open Issues

| ID | Severity | Description |
|----|----------|-------------|
| KI-059 | HIGH (DEFERRED) | Single-stock bear tracks untested — ETF-only mode (400) |

---

## Next Session Priorities (Day 48)

| Priority | Issue | Effort |
|----------|-------|--------|
| P0 | Adversarial LLM review: paste XLF/QQQ setup to ChatGPT with Check 10.4 prompt (Phase7c_Actionable_Day47.md) | 15 min |
| P1 | Start paper trade logging — log next XLF or QQQ CAUTION setup to Paper Trade Dashboard | ongoing |
| P2 | MASTER_AUDIT_FRAMEWORK weekly sweep (last audit Day 42, trigger at Day 49) | skip |
| P3 | Phase 7c cyclical vs defensive split (needs Weakening cyclicals in ANALYZE — deferred) | deferred |
| P4 | Weekly gate pass rate log maintenance (Check 10.1 — track second data point) | 5 min |
