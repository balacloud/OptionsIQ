# OptionsIQ — Project Status Day 20
> **Date:** March 28, 2026
> **Version:** v0.14.1
> **Session type:** Market closed (weekend) — infrastructure fixes + sector options pipeline

---

## What Was Done

### Fixed: Sector Options Pipeline (end-to-end)
The main goal: clicking Sectors → getting real options strategies for bear ETFs. Three blocking issues cleared:

1. **503 sector scan error** — STA was offline. Once STA started, sector scan returned all 15 ETFs correctly.

2. **ETF liquidity gate blocking all strategies** — OTM legs (e.g. XLK 136C) have naturally wider bid-ask spreads than individual stocks. `SPREAD_BLOCK_PCT=15%` was too strict, blocking every ETF sell_call analysis. Fixed with ETF post-processing in `app.py` (Rule 5 pattern — same as events/pivot/DTE). Gate now warns instead of blocks.

3. **Bear call spread not building** — For ETFs with narrow option chains (XLK max strike 136 at $130.25), all delta targets (0.30, 0.20, 0.15) resolved to the same strike (136). Strategy ranker had no fallback. Fixed: now uses 2nd-highest OTM as short leg and highest OTM as protection leg → 135/136 Bear Call, net_credit=$0.52.

### Fixed: Session Protocol Documentation
`memory/MEMORY.md` had a 3-step session startup (missing ROADMAP, PROJECT_STATUS, KNOWN_ISSUES). GOLDEN_RULES.md startup checklist and Rule 9 (close) also had gaps vs CLAUDE_CONTEXT.md authoritative list. All three aligned.

---

## Live Test Results (weekend — market closed, cached IBKR data)

| ETF | Direction | Verdict | Top Strategy | net_credit |
|-----|-----------|---------|--------------|------------|
| XLK | sell_call | WARN | 135/136 Bear Call · Apr 2026 | $0.52 |
| XLY | sell_call | WARN | 110/111 Bear Call · Apr 2026 | live |
| XLF | sell_call | WARN | 50/51 Bear Call · Apr 2026 | live |
| QQQ | sell_call | BLOCKED | strike_otm: all calls ITM | KI-067 |

**Frontend:** Not smoke-tested end-to-end in UI this session (market closed). Monday re-test.

---

## Audit Health

| Category | Count |
|----------|-------|
| Critical | 0 |
| High | 1 (KI-059 single-stock bear) |
| Medium | 6 |
| Low | 5 |
| **Total** | **12** |

---

## Files Changed This Session

| File | Change |
|------|--------|
| `backend/app.py` | ETF liquidity gate post-processing (BLOCK→WARN for wide OTM spread) |
| `backend/strategy_ranker.py` | Narrow-chain fallback for bear_call_spread protection leg |
| `docs/stable/GOLDEN_RULES.md` | SESSION STARTUP CHECKLIST explicit file list; Rule 9 full 8-item close list |
| `memory/MEMORY.md` | Session Protocol expanded to full 6-step list |

---

## Day 21 Priorities

1. **P0:** Frontend smoke test — Sectors UI end-to-end (market open Monday)
2. **P0:** KI-059 — Single-stock bear live test (buy_put + sell_call on bearish stock)
3. **P1:** KI-067 — QQQ chain too narrow (struct_cache drift vs current price)
4. **P1:** KI-064 — IVR mismatch (L2 percentile 97% vs L3 average 21%)
5. **P2:** API_CONTRACTS.md sync (KI-044)
