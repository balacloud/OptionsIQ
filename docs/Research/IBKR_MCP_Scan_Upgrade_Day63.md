# /ibkr-scan Upgrade — MCP-Powered (Option A)
> **Created:** Day 63 (Jun 2, 2026)
> **Decision:** Replace screenshot dependency with IBKR MCP API calls
> **Status:** IMPLEMENTED — Day 63 (Jun 2, 2026)

---

## Context

As of Day 63, the IBKR account is connected via **Claude Connectors** and MCP tools are available
**inside Claude Code CLI sessions** (prefixed `mcp__claude_ai_Interactive_Brokers_IBKR__*`).
Previous memory said "not available in CLI" — this is now superseded.

Live test on Day 63:
- QQQ contract ID: `320227571` confirmed
- `get_price_snapshot` returns: IV=20.4%, HV=16.3%, IV/HV=1.25x, IVR (52w percentile=70%, 13w=30%)
- EMA data NOT in price_snapshot — requires `get_price_history` computation

---

## Data Gap Analysis

### What MCP Covers (✅ = direct, 🔧 = computed)

| Watchlist Column | MCP Field | Status | Notes |
|-----------------|-----------|--------|-------|
| Price (LAST) | `get_price_snapshot` → `last` | ✅ | |
| IV/HV ratio | `implied-vol` / `historical-vol` | ✅ | Convert % to decimal |
| 52w IV Percentile | `implied-volatility-percentile` (52w) | ✅ | This is PERC, not RANK |
| 13w IV Percentile | `implied-volatility-percentile` (13w) | ✅ | Multi-window view |
| P/EMA(200) | `get_price_history` (260d) → compute EMA(200) | 🔧 | Must compute |
| P/EMA(50) | `get_price_history` (60d) → compute EMA(50) | 🔧 | Must compute |
| Opt Volume | `underlying-today-option-volume` | ✅ | Total (not per contract) |
| Opt Avg Volume | `underlying-avg-option-volume` | ✅ | 90-day baseline |
| YTD Change | `year-to-date-change` | ✅ | Directional bias |

### What MCP Cannot Provide (⚠️ = gap)

| Watchlist Column | Gap | Mitigation |
|-----------------|-----|-----------|
| **IV Rank (52w)** | MCP gives Percentile, not Rank | Use Percentile as proxy — actually stronger signal (see below) |
| **Opt. Imp. Vol. Change** | No delta vs yesterday | Drop Layer 3, replace with volume-vs-avg anomaly check |

### CONFIRMED: P/C Split IS Available (Day 63 live test)

Screenshot from Claude.ai MCP test on QQQ (Jun 2, 2026) confirms `get_price_snapshot` returns:
- Today call volume: 2,263,632
- Today put volume: 2,614,315
- **P/C volume ratio today: 1.15** ← computed from split
- Volume vs avg (calls): 72% of 90d avg
- Volume vs avg (puts): 78% of 90d avg

Decision 2 (P/C gap) is **RESOLVED**. MCP provides full P/C split. Layer 4 fully preserved.

### NEW Signals Available (not in watchlist)

| New Signal | Value (QQQ today) | Use in sieve |
|-----------|------------------|-------------|
| IVR 26-week | 53.2% | Multi-window IVR context |
| IV edge (IV - HV in %) | +4.1% | Explicit seller's edge |
| Price vs 52w high | +0.34% above | **ATH flag — extended rally** |
| Range position | 99th pct of 52w range | Price extension advisory |
| Call vol vs 90d avg | 72% | Low conviction signal |
| Put vol vs 90d avg | 78% | Low conviction signal |

### IV Rank vs IV Percentile — Why Percentile Wins

From today's live data: QQQ IVR=40 (rank) but 52w Percentile=70%.

- **IV Rank** = (current IV − 52w low) / (52w high − 52w low) × 100. Compressed by outliers.
- **IV Percentile** = % of trading days in last 52w where IV was below current level.

Percentile is spike-resistant and more stable for sell decisions. Our existing scoring already uses
Percentile as the primary gate (Layer 1 thresholds: ≥75%, ≥60%). **Switching fully to Percentile
removes no signal quality — it removes the IV Rank column entirely from the output.**

---

## Architecture Design

### New /ibkr-scan Flow (MCP mode)

```
/ibkr-scan [optional: ticker to focus on]

For each ETF in [SPY, QQQ, IWM, XLF, TQQQ, GLD]:
  1. contract_id = CACHED_IDS[ticker]  ← use stored IDs (see table below)
  2. snapshot = get_price_snapshot(contract_id, fields=[
       "implied-vol", "historical-vol",
       "implied-volatility-percentile",  # returns 13w/26w/52w
       "underlying-today-option-volume",
       "underlying-avg-option-volume",
       "year-to-date-change",
       "misc-statistics",
       "change"
     ])
  3. history = get_price_history(contract_id, period="1y", barSize="1d")
     → compute EMA(200): ema = close[0]; for c in close[1:]: ema = c*(2/201) + ema*(199/201)
     → compute EMA(50):  ema = close[0]; for c in close[1:]: ema = c*(2/51)  + ema*(49/51)
     → P/EMA200 = (last - EMA200) / EMA200 * 100
     → P/EMA50  = (last - EMA50)  / EMA50  * 100
  4. Apply 4-layer scoring (same thresholds, Percentile replaces Rank)
  5. Output scored table + SCAN CONTEXT for top pick
```

### Cached Contract IDs (confirmed or to be confirmed)

| ETF | Contract ID | Status |
|-----|-------------|--------|
| QQQ | 320227571 | ✅ Confirmed Day 63 |
| SPY | TBD | Pull once, cache here |
| IWM | TBD | Pull once, cache here |
| XLF | TBD | Pull once, cache here |
| TQQQ | TBD | Pull once, cache here |
| GLD | TBD | Pull once, cache here |

> **Note:** Contract IDs are stable for ETFs — they don't change. Confirm once and hardcode in skill.
> Fallback: `search_contracts(ticker, secType=STK)` if ID not in cache.

### EMA Computation (in-skill pseudocode)

```
Given: bars = [close_day_0, close_day_1, ..., close_day_N] (oldest first)
EMA(n) computation:
  ema = bars[0]
  k = 2 / (n + 1)
  for price in bars[1:]:
      ema = price * k + ema * (1 - k)
  return ema

P/EMA(200) = (current_price - EMA200) / EMA200 * 100
P/EMA(50)  = (current_price - EMA50)  / EMA50  * 100
```

Claude executes this within the skill using the returned price history array.

---

## Open Design Decisions

### Decision 1 — IVR Window: 52w only, or show both 13w + 52w?

Today's data shows the split: QQQ 13w=30% vs 52w=70%. These tell different stories.

| Option | Pros | Cons |
|--------|------|------|
| **52w only** (current) | Clean, single signal, consistent with existing gates | Misses near-term IV compression (13w=30% = recent IV contraction) |
| **Both windows, flag divergence** | Catches "IV was high YoY but compressed recently" | More complex output |
| **Use 52w as gate, 13w as advisory** | Best of both: gate stays clean, context preserved | Slight complexity |

**Recommendation:** Show both in output. Gate on 52w (≥60% tradable). If 13w < 40% while 52w ≥ 60%, add advisory: "IV recently compressed — may be deflating." No scoring change.

### Decision 2 — Put/Call Volume ✅ RESOLVED

**MCP provides full P/C split.** Confirmed from live test: today call vol + put vol returned separately.
`P/C = today_put_vol / today_call_vol` — computable directly from MCP data.

Layer 4 is **fully preserved** with same thresholds. Volume vs avg available for both calls and puts separately — adds precision over the single combined column we had before.

New Layer 4 output:
```
P/C ratio: 1.15 (put-leaning, neutral range)
Volume conviction: calls 72% / puts 78% of 90d avg — below-avg activity
```

### Decision 3 — Market Closed Behavior

When market is closed, `get_price_snapshot` returns prior close values (not live IV).

| Behavior | Handling |
|----------|---------|
| IV from prior close | Valid for all gate checks — IV doesn't change much overnight |
| P/EMA data | Computed from price history → always available |
| Volume | Shows prior day's volume — meaningless for sentiment |

**Decision:** When market is closed, skip Layer 4 (same as current pre-market behavior). Output note: "Market closed — using prior close IV. Volume signal unavailable."

---

## What Changes in ibkr-scan.md

### Remove
- `## Watchlist Layout` section (no more screenshot reading)
- Screenshot-based pre-market detection logic
- References to "UNDERLYING PRICE shows —" behavior

### Add
- `## MCP Data Pull` section — for each ETF, what calls to make
- Cached contract ID table
- EMA computation algorithm
- Market-closed detection via `change` field behavior

### Update
- Layer 1 scoring: "52 IV PERC" → "IV Percentile (52w from MCP)" — same thresholds. Add 13w/26w as context.
- Layer 1 addition: Show explicit IV edge % ("seller's edge: +4.1%")
- Layer 3: Drop Opt Imp Vol Change. Replace with: if call_vol < 60% avg AND put_vol < 60% avg → "low conviction — treat as pre-market"
- Layer 4: PRESERVED — P/C from MCP split. PLUS add volume conviction % for both calls and puts.
- NEW Layer 5 — Price Extension: if range_position > 95th pct → advisory "Price at ATH/multi-month high — extended rally, support is present but pullback risk elevated"
- Output format: drop IVR column, add IV Perc (52w). Add range position field.
- SCAN CONTEXT: PC field PRESERVED (MCP provides it directly)

### Backward Compatibility
Keep current screenshot mode as fallback:
```
/ibkr-scan          ← MCP mode (automatic, no screenshot needed)
/ibkr-scan [image]  ← Screenshot mode (current behavior, kept for fallback)
```

---

## Workflow After Upgrade

**Before (current):**
```
1. Open IBKR → screenshot watchlist
2. Paste screenshot → /ibkr-scan → scored table + SCAN CONTEXT
3. Paste SCAN CONTEXT → OptionsIQ analyze
```

**After (upgraded):**
```
1. Type /ibkr-scan
2. Claude calls MCP for all 6 ETFs automatically
3. Scored table + SCAN CONTEXT output
4. Paste SCAN CONTEXT → OptionsIQ analyze
```

**Savings:** ~2-3 minutes per morning session. No screenshot dependency. EMA data available even pre-market.

---

## Implementation Steps (ordered)

1. **Confirm remaining 5 contract IDs** — run `search_contracts` for SPY, IWM, XLF, TQQQ, GLD in this session
2. **Prototype EMA computation** — test `get_price_history` for QQQ, verify 260 bars returned, compute EMA(200) manually, validate against IBKR watchlist value
3. **Update ibkr-scan.md** — replace screenshot section with MCP section, update all layers
4. **Test full scan** — run upgraded skill against all 6 ETFs, compare output to today's screenshot data for validation
5. **Update IBKR_DATA_SOURCES.md + memory** — document final contract ID table

**Estimated effort:** 2-3 hours

---

## Live Test Results (Day 63 — all 3 questions answered)

### Q1 — Bar count: ONE_YEAR returns 251 daily bars ✅

`get_price_history(period=ONE_YEAR, step=ONE_DAY)` → **251 bars** (Jun 2025 – Jun 2026, excluding holidays).

**EMA accuracy validation** (Python computed vs IBKR watchlist):
| Metric | Computed | Watchlist | Delta |
|--------|----------|-----------|-------|
| EMA(50) | 674.34 | ~674.35 | **0.01 pp** ✅ near-perfect |
| EMA(200) | 620.52 | ~616.93 | **0.65 pp** bias |
| P/EMA50 | +10.35% | +10.34% | **0.01 pp** ✅ |
| P/EMA200 | +19.92% | +20.57% | **0.65 pp** underestimate |

**Root cause of EMA(200) bias:** 251 bars uses first bar (523.21) as seed — not long enough warmup.
EMA(50) converges in ~150 bars (3× period). EMA(200) needs ~600 bars (3× period) to fully converge.

**Fix:** Use `period=TWO_YEARS` (~502 bars). Same number of API calls, warmup bias drops to <0.1%.
P/EMA200 edge case: if computed value is between -1% and +1%, add advisory "Near 200 EMA — verify in IBKR."

### Q2 — implied-volatility-percentile: single object, all 3 windows ✅

One field request returns all three windows as a single JSON object:
```json
{"high_13w": 0.3333, "high_26w": 0.5484, "high_52w": 0.7160}
```
Values are fractions → multiply × 100 for percentage.
`implied-vol-underlying` and `historical-vol` also return objects with daily + annual values.

All 7 fields can be fetched in **one `get_price_snapshot` call** per ETF — confirmed in live test.

### Q3 — Batching: one contract at a time, 12 calls total per scan ✅

`contract_id` is a single int64 — no multi-contract batch. But ALL fields for one ETF fit in one call.

**Final call count per scan:** 6 ETFs × 2 calls = **12 MCP calls**
- 1× `get_price_snapshot` per ETF (all 7 fields in one shot)
- 1× `get_price_history` per ETF (TWO_YEARS for EMA warmup)

Acceptable for a morning scan — 12 sequential calls, ~15-20 seconds total estimated.

## Confirmed Contract IDs (all 6 ETFs)

| ETF | Contract ID | Exchange | Confirmed |
|-----|-------------|----------|-----------|
| QQQ | 320227571 | NASDAQ | ✅ Day 63 |
| SPY | 756733 | ARCA | ✅ Day 63 |
| IWM | 9579970 | ARCA | ✅ Day 63 |
| XLF | 4215220 | ARCA | ✅ Day 63 |
| TQQQ | 72539702 | NASDAQ | ✅ Day 63 |
| GLD | 51529211 | ARCA | ✅ Day 63 |
