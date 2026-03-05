# OptionsIQ — Golden Rules
> **Last Updated:** Day 1 (March 5, 2026)

---

## Rule 1: Live Data Is the Default. Always.

`reqMarketDataType(1)` is hardcoded as the startup call.
Paper trading uses the same live data path as production.
Mock data is for `pytest` and CI only — never for paper trades.
If IBKR is offline, show a banner. Never silently fall back to stale/fake data without telling the user.

## Rule 2: One IB() Instance. One Worker Thread.

The IB() instance lives in `IBWorker` — a single dedicated thread started at app startup.
Flask routes NEVER create IB() instances directly.
Flask routes NEVER call ib_insync methods directly.
All IBKR requests go through `data_service.request_chain(ticker)` which queues to IBWorker.

## Rule 3: No Magic Numbers.

Every threshold lives in `constants.py`. No raw numbers in gate_engine, ranker, or route handlers.
If you need a new threshold, add it to `constants.py` first, then import it.

## Rule 4: app.py Is Routes Only.

`app.py` max 150 lines. Routes only — validate input, call service, return JSON.
Business logic goes in `analyze_service.py`.
Data access goes in `data_service.py`.
If app.py grows past 150 lines, something is wrong.

## Rule 5: Gate Math Is Frozen.

`gate_engine.py` is verified correct. Do not touch the math.
Only allowed changes: import constants from `constants.py` instead of inline numbers.
New gates must be added as new functions — never modify existing gate functions.

## Rule 6: STA Integration Is Optional, Never Required.

OptionsIQ works standalone. If STA is offline: Manual mode.
Never crash or block if `localhost:5001` is unreachable.
`fetch_sta_data()` returns `None` on connection error — UI handles this gracefully.

## Rule 7: ACCOUNT_SIZE Must Be Explicit.

ACCOUNT_SIZE is a required `.env` variable. App raises at startup if not set.
No default value in code. User must be conscious of their account size for position sizing.

## Rule 8: Quality Banners Are Mandatory.

When data quality is below "live", the frontend MUST show a banner.
- Tier 2 (cached): "Using cached chain from X minutes ago"
- Tier 3 (yfinance): "Live data unavailable — using yfinance (greeks estimated)"
- Tier 4 (mock): "MOCK DATA — testing only. Do not paper trade."

## Rule 9: Session Close Protocol.

At every session close, update:
- `CLAUDE_CONTEXT.md`: Current State table + Session Log + Next Session Priorities
- `docs/versioned/KNOWN_ISSUES_DAY[N].md`: Mark resolved, add new
- `docs/stable/ROADMAP.md`: Mark completed phases
- `docs/stable/API_CONTRACTS.md`: If any endpoint added or changed
- `docs/status/PROJECT_STATUS_DAY[N]_SHORT.md`: New status doc

## Rule 10: Read CLAUDE_CONTEXT.md First.

At the start of every session: read `CLAUDE_CONTEXT.md` before writing a single line of code.
Check Current State table. Check Known Issues. Check Next Session Priorities.
Do not assume state from memory — verify from the doc.
