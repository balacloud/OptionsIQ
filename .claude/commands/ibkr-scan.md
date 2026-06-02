# /ibkr-scan — IBKR Watchlist Morning Scan (MCP-Powered)

Pull live market data for all 6 ETFs via IBKR MCP, score them through the 4-layer sieve,
and output a ranked table + SCAN CONTEXT ready to paste into the OptionsIQ analyze tool.

No screenshot needed. All data comes from live IBKR API calls.

---

## Contract IDs (hardcoded — stable, do not need to search)

| ETF  | Contract ID | Exchange |
|------|-------------|----------|
| SPY  | 756733      | ARCA     |
| QQQ  | 320227571   | NASDAQ   |
| IWM  | 9579970     | ARCA     |
| XLF  | 4215220     | ARCA     |
| TQQQ | 72539702    | NASDAQ   |
| GLD  | 51529211    | ARCA     |

---

## Step 0 — Pull Live Data (do this for all 6 ETFs before scoring)

For each ETF, make **two MCP calls**:

### Call A — Price Snapshot
`get_price_snapshot(contract_id, exchange="SMART", market_data_names=[...])`

Request all of these fields in one call:
```
"implied-vol-underlying"          → annual_iv (fraction → ×100 = IV%)
"historical-vol"                   → annual_pct (fraction → ×100 = HV%)
"implied-volatility-percentile"    → high_13w, high_26w, high_52w (fractions → ×100)
"underlying-today-option-volume"   → callVolume, putVolume
"underlying-avg-option-volume"     → avgCallVolume, avgPutVolume
"misc-statistics"                  → high_52w (price), low_52w (price)
"year-to-date-change"              → change_pct
"last"                             → current price
```

### Call B — Price History (for EMA computation)
`get_price_history(contract_id, exchange=[see table above], security_type="STK", step="ONE_DAY", period="TWO_YEARS", outside_rth=false)`

### Compute from history bars (close prices, oldest-first):
```
EMA(n) algorithm:
  ema = close[0]
  k   = 2 / (n + 1)
  for each price in close[1:]:
      ema = price * k + ema * (1 - k)

EMA200 = EMA(200) applied to all ~502 close bars
EMA50  = EMA(50)  applied to all ~502 close bars

P/EMA200 = (current_price - EMA200) / EMA200 × 100   [sign matters: negative = below 200 EMA]
P/EMA50  = (current_price - EMA50)  / EMA50  × 100

If -1% < P/EMA200 < +1%: flag as "(near 200 EMA — borderline)"
```

### Derived values per ETF:
```
IV_pct     = implied-vol-underlying.annual_iv × 100
HV_pct     = historical-vol.annual_pct × 100
IV_HV      = IV_pct / HV_pct              [e.g. 1.254 = IV 25% above HV]
IV_edge    = IV_pct - HV_pct              [e.g. +4.1% = seller's edge]
IVR_13w    = implied-volatility-percentile.high_13w × 100
IVR_26w    = implied-volatility-percentile.high_26w × 100
IVR_52w    = implied-volatility-percentile.high_52w × 100
call_vol   = underlying-today-option-volume.callVolume
put_vol    = underlying-today-option-volume.putVolume
avg_call   = underlying-avg-option-volume.avgCallVolume
avg_put    = underlying-avg-option-volume.avgPutVolume
PC_ratio   = put_vol / call_vol            [e.g. 1.15 = put-leaning]
call_pct   = call_vol / avg_call × 100    [e.g. 72% of 90d avg]
put_pct    = put_vol  / avg_put  × 100
hi_52w     = misc-statistics.high_52w     [52-week price high]
lo_52w     = misc-statistics.low_52w      [52-week price low]
range_pos  = (current_price - lo_52w) / (hi_52w - lo_52w) × 100  [0–100+ %ile]
```

**Market closed / pre-market detection:**
If `call_vol = 0` AND `put_vol = 0` → market is closed or pre-market.
In that case: skip Layer 4 (sentiment). Note "pre-market — volume signals unavailable."

---

## Step 1 — Regime Check (read SPY row first)

| SPY P/EMA200 | Regime | Impact |
|--------------|--------|--------|
| > +1%        | BULL — clear | Sell puts OK on all ETFs |
| 0% to +1%    | BULL — marginal | Proceed with caution, lower delta |
| < 0%         | BEAR | Hard block on ALL sell_put. Sell_call only. |

If regime is BEAR, output the block and stop. Do not score individual ETFs.

---

## Step 2 — Score Each ETF (5 tradeable: QQQ, IWM, XLF, TQQQ, GLD)

Apply layers in order. Stop at any hard block.

### Layer 1 — IV Gate (primary: IVR_52w + IV/HV)

| Condition | Points | Label |
|-----------|--------|-------|
| IVR_52w ≥ 75% AND IV_HV ≥ 1.20 | +3 | BEST |
| IVR_52w ≥ 60% AND IV_HV ≥ 1.10 | +2 | TRADABLE |
| IVR_52w 50–59% AND IV_HV ≥ 1.10 | +1 | MARGINAL |
| IVR_52w < 50% OR IV_HV < 1.05 | 0 | SKIP |
| IV_HV < 1.00 | -1 | IV CHEAP — do not sell |

**Multi-window context (no scoring impact — informational):**
- If IVR_13w < 35% while IVR_52w ≥ 60%: add note "IV recently compressed — may be deflating"
- If IVR_13w ≥ 60%: add note "IV elevated on both short and long windows — strong seller's environment"

### Layer 2 — Trend Gate

| Condition | Points | Label |
|-----------|--------|-------|
| P/EMA200 > 0 AND P/EMA50 > 0 | +2 | UPTREND |
| P/EMA200 > 0 AND P/EMA50 < 0 | +1 | PULLBACK — use delta 0.15 max |
| P/EMA200 < 0 | HARD BLOCK | Output ❌, score = 0, stop scoring this ETF |

### Layer 3 — Volume Conviction

Replaces the old "IV Change" layer (not available via MCP without yesterday's snapshot).

| Condition | Points | Note |
|-----------|--------|------|
| call_pct ≥ 80% AND put_pct ≥ 80% | +1 | Normal-to-elevated activity — confirms flow |
| call_pct 50–79% OR put_pct 50–79% | 0 | Below-avg volume — muted conviction |
| call_pct < 50% AND put_pct < 50% | -1 | Very low volume — treat as pre-market |
| Skip entirely if market closed | — | Note "pre-market — skip Layer 3" |

### Layer 4 — Put/Call Sentiment

Skip entirely if market closed (call_vol = 0).

| Condition | Points | Note |
|-----------|--------|------|
| PC_ratio < 1.0 | +1 | Call-dominant — bullish flow, confirms sell_put |
| PC_ratio 1.0–1.5 | 0 | Neutral |
| PC_ratio > 1.5 | -1 | Fear — institutional put buying. Wait even if IVR elevated. |
| PC_ratio < 0.5 | 0 | Complacency — note it |

**Volume split context (informational, no scoring):**
Output `calls: [call_pct]% of avg · puts: [put_pct]% of avg` alongside PC ratio.

### Layer 5 — Price Extension (advisory only, no scoring impact)

| Condition | Advisory |
|-----------|---------|
| range_pos > 99% (above 52w high) | "Above 52w ATH — breakout extension. Support is below; pullback risk elevated." |
| range_pos 95–99% | "Near 52w high — extended rally. Valid for sell_put (lots of distance to strike); adds risk for sell_call." |
| range_pos < 20% | "Near 52w low. Oversold zone — confirm SPY regime before sell_put." |

**Max score: 7 (BEST IV + UPTREND + normal volume + bullish sentiment)**
**Tradable threshold: ≥ 4**

---

## Step 3 — TQQQ Special Rules

TQQQ is a SATELLITE position. Even if it scores high:

| Gate | Requirement |
|------|-------------|
| Regime | SPY P/EMA200 > +1% (comfortably bull — not marginal) |
| TQQQ trend | TQQQ P/EMA50 must be > 0 |
| Max delta | 0.10 (not the standard 0.15–0.20) |
| Max size | 1–2% account risk only |
| Label | Always output as "SATELLITE" in verdict |

If TQQQ passes all gates: label "SELL PUT (SATELLITE) — delta 0.10 max"

---

## Step 4 — GLD Special Rules

| Gate | Requirement |
|------|-------------|
| IV/HV minimum | IV_HV must be ≥ 1.10 (GLD has no structural upward bias — needs clear VRP) |
| IVR_52w minimum | ≥ 35% (GLD IV mutes for long stretches) |
| Hard stop reminder | 2–3× premium collected. Never roll down. |

If GLD IV_HV < 1.00: output "IV CHEAP — realized vol exceeds implied. Never sell cheap vol."
If GLD IV_HV 1.00–1.09: output "HARD BLOCK — IV/HV below 1.10 threshold. GLD rule."

---

## Step 5 — System-Level Warnings

Check after scoring all ETFs:

**Macro fear flag:** If 4 or more of the 5 tradeable ETFs show IVR_52w ≥ 35% simultaneously:
`⚠️ MACRO FEAR SIGNAL: 4+ ETFs with elevated IVR. Reduce to 1 position max or wait for peak.`

**Broad low volume:** If 4+ ETFs show call_pct < 60% AND put_pct < 60%:
`⚠️ Below-avg volume across watchlist. Low conviction day — treat all signals as pre-market quality.`

**XLF below 200 EMA:** Always call out explicitly — rate regime concern for financials.

**Breakout extension:** If 3+ ETFs show range_pos > 95%:
`⚠️ Broad ATH extension across watchlist. Market extended — prefer further OTM strikes, smaller size.`

---

## Output Format

```
IBKR SCAN — [Date] [Pre-market / Market hours] [MCP live]

REGIME: [BULL/BEAR] — SPY P/EMA(200) = [value]

| ETF  | IVR 52w | IV/HV | Edge  | P/EMA200 | P/EMA50 | P/C  | Score | Verdict                         |
|------|---------|-------|-------|----------|---------|------|-------|---------------------------------|
| SPY  |   27%   | 1.23x | +3.8% | +12.15%  |  +5.76% |  —   |   —   | Regime anchor                   |
| QQQ  |   72%   | 1.25x | +4.1% | +19.92%  | +10.35% | 1.20 |  5/7  | SELL PUT ✅                     |
| IWM  |   40%   | 1.16x | +2.5% | +14.03%  |  +5.56% | 1.61 |  2/7  | SKIP — P/C fear + IVR marginal  |
| XLF  |   51%   | 1.18x | +2.9% |  -0.25%  |  +0.08% | 1.58 |  0/7  | HARD BLOCK ❌ (below 200 EMA)   |
| TQQQ |   71%   | 1.24x | +4.5% | +59.58%  | +29.99% | 1.15 |  5/7  | SELL PUT (SATELLITE) delta 0.10 |
| GLD  |   53%   | 0.94x | -1.4% |  +2.70%  |  -3.46% | 0.67 |  0/7  | HARD BLOCK ❌ (IV/HV < 1.10)   |

IVR multi-window context:
  QQQ: 13w=33% (compressed) / 26w=55% / 52w=72% ← IV elevated yearly but recently deflating
  IWM: 13w=xx% / 26w=xx% / 52w=40%

Volume conviction (market hours):
  QQQ: calls 84% of avg · puts 95% of avg
  IWM: calls 77% · puts 78%

Price extension:
  QQQ: range_pos=101% — above 52w ATH. Support is present; watch for mean reversion.

TOP PICK: QQQ sell_put
Rationale: IVR_52w 72%, IV/HV 1.25x (+4.1% seller edge), clean uptrend both EMAs. Top pick.
Runner-up: TQQQ — satellite only, delta 0.10 max, 1 lot.

[System warnings if any]

━━━ SCAN CONTEXT — copy and paste into OptionsIQ analyze tool ━━━
TICKER=QQQ  IVR=72  IV_HV=1.254  PC=1.20  PEMA200=+19.92  PEMA50=+10.35  DIRECTION=sell_put
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**SCAN CONTEXT field notes (MCP sources):**
- `IVR=` → use `IVR_52w` as integer (e.g., 0.716 → 72). Backend field is `ivr_pct` — expects percentile 0-100.
- `IV_HV=` → ratio as decimal (e.g., 1.254). Computed as `annual_iv / annual_pct`.
- `PC=` → put/call ratio (e.g., 1.20). Computed as `put_vol / call_vol`. Omit if market closed.
- `PEMA200=` / `PEMA50=` → computed from price history EMA, with sign (e.g., +19.92, -0.25).
- `DIRECTION=` → one of: `sell_put` / `sell_call` / `buy_call` / `buy_put`

---

## Verdict Labels

| Score | Label |
|-------|-------|
| 6–7 | **SELL PUT ✅** (or SELL CALL if downtrend regime) |
| 4–5 | **SELL PUT** (check advisory notes) |
| 3 | **MARGINAL** — lower delta only (0.15 max) |
| 1–2 | **SKIP** |
| 0 or HARD BLOCK | **HARD BLOCK ❌** or **NO TRADE** |
| TQQQ passing | **SELL PUT (SATELLITE) — delta 0.10 max** |

---

## Market Closed / Pre-Market Behavior

**Detected by:** `call_vol = 0` AND `put_vol = 0` in `underlying-today-option-volume`.

When market is closed:
- Skip Layer 3 (volume conviction) and Layer 4 (put/call sentiment)
- All other layers use prior-close IV/HV values — valid for gate checks
- EMA data (P/EMA200, P/EMA50) is always computed from history — unaffected by market hours
- Note in output: "Market closed / pre-market — volume signals unavailable, recheck at 9:35 AM"
- SCAN CONTEXT: omit `PC=` field when market is closed

---

## Fallback — Screenshot Mode

If the user pastes a screenshot instead of typing `/ibkr-scan` without arguments:
- Read the screenshot columns using the original watchlist layout (see git history for the old skill)
- Apply the same 4-layer scoring (use IV Pctl column for IVR_52w, IV/HV column for IV_HV)
- Layer 5 (price extension) unavailable from screenshot — skip
- Note "screenshot mode — EMA computed from watchlist values, not MCP"

---

## Example — Full Market Hours Output

```
IBKR SCAN — Jun 2, 2026 Market hours [MCP live]

REGIME: BULL — SPY P/EMA(200) = +12.15% ✅

| ETF  | IVR 52w | IV/HV | Edge  | P/EMA200 | P/EMA50 | P/C  | Score | Verdict                          |
|------|---------|-------|-------|----------|---------|------|-------|----------------------------------|
| SPY  |   27%   | 1.23x | +3.8% | +12.15%  |  +5.76% |  —   |   —   | Regime anchor                    |
| QQQ  |   72%   | 1.25x | +4.1% | +19.92%  | +10.35% | 1.20 |  5/7  | SELL PUT ✅                      |
| IWM  |   40%   | 1.16x | +2.5% | +14.03%  |  +5.56% | 1.61 |  2/7  | SKIP — P/C fear (>1.5)           |
| XLF  |   51%   | 1.18x | +2.9% |  -0.25%  |  +0.08% | 1.58 |  0/7  | HARD BLOCK ❌ (below 200 EMA)    |
| TQQQ |   71%   | 1.24x | +4.5% | +59.58%  | +29.99% | 1.15 |  5/7  | SELL PUT (SATELLITE) delta 0.10  |
| GLD  |   53%   | 0.94x | -1.4% |  +2.70%  |  -3.46% | 0.67 |  0/7  | HARD BLOCK ❌ (GLD IV/HV < 1.10) |

IVR multi-window:
  QQQ: 13w=33% (recently compressed) / 26w=55% / 52w=72% ← note IV deflating short-term
  IWM: 13w=28% / 26w=38% / 52w=40% — all windows marginal

Volume conviction:
  QQQ: calls 84% of avg · puts 95% of avg — normal activity
  IWM: calls 72% · puts 78% — slightly below avg

Price extension:
  QQQ: 101% of 52w range — +0.34% above prior ATH. Extended but support-rich for sell_put.
  TQQQ: 99th pct — near ATH, confirm SPY holds before opening satellite.

TOP PICK: QQQ sell_put
Rationale: IVR_52w 72%, IV/HV 1.25x (seller has +4.1% edge), both EMAs positive, P/C neutral.

SATELLITE CANDIDATE: TQQQ — delta 0.10 max, 1 lot only, only if SPY stays > +1% EMA200.

⚠️ NOTE: QQQ 13w IVR only 33% — IV has compressed recently vs the 52w window.
   Use delta 0.20 (not 0.28) and pick the 30-35 DTE expiry to stay away from near-term events.

━━━ SCAN CONTEXT — copy and paste into OptionsIQ analyze tool ━━━
TICKER=QQQ  IVR=72  IV_HV=1.254  PC=1.20  PEMA200=+19.92  PEMA50=+10.35  DIRECTION=sell_put
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
