"""
OptionsIQ — Constants
All thresholds, defaults, and configuration values.
No magic numbers anywhere else in the codebase — import from here.

Source of truth: docs/Research/Options_Research_Plan Section 4F
Last updated: Day 3 (March 5, 2026)
"""

# ---------------------------------------------------------------------------
# Gate thresholds — IV / Vol
# ---------------------------------------------------------------------------
IVR_BUYER_PASS_PCT      = 30.0   # IVR < 30 = cheap IV, good time to buy
IVR_BUYER_WARN_PCT      = 50.0   # IVR 30–50 = moderate (warn buyers)
IVR_SELLER_PASS_PCT     = 50.0   # IVR >= 50 = rich premium, good time to sell
IVR_SELLER_MIN_PCT      = 30.0   # IVR 30–50 = minimum viable for selling
HV_LOW_REGIME_PCT       = 15.0   # HV < 15% = special low-vol exception
HV_IV_PASS_RATIO        = 1.20   # HV/IV < 1.20 = not overpaying for IV
HV_IV_WARN_RATIO        = 1.30   # HV/IV 1.20–1.30 = borderline

# Absolute IV fallback thresholds (used when IVR history < 30 days)
IV_ABS_BUYER_PASS_PCT   = 20.0   # Absolute IV < 20% = cheap, good for buyers
IV_ABS_BUYER_WARN_PCT   = 35.0   # Absolute IV 20–35% = moderate for buyers
IV_ABS_LOW_HV_PASS_PCT  = 25.0   # In low-HV regime: IV < 25% still acceptable for buyers

# ---------------------------------------------------------------------------
# Gate thresholds — Theta / Time decay
# ---------------------------------------------------------------------------
THETA_BURN_PASS_PCT     = 8.0    # Theta burn over hold period <= 8% = acceptable
THETA_BURN_WARN_PCT     = 12.0   # 8–12% = borderline
THETA_BURN_FAIL_PCT     = 12.0   # > 12% = too much decay

# ---------------------------------------------------------------------------
# Gate thresholds — Liquidity
# ---------------------------------------------------------------------------
SPREAD_WARN_PCT         = 5.0    # Bid-ask spread > 5% of mid = warn
SPREAD_FAIL_PCT         = 10.0   # > 10% = fail (too wide, slippage risk)
SPREAD_BLOCK_PCT        = 15.0   # > 15% = hard block
MIN_OPEN_INTEREST       = 1000   # OI < 1000 = illiquid, fail
MIN_VOLUME_OI_RATIO     = 0.10   # Volume/OI < 10% = low activity, warn
MIN_PREMIUM_DOLLAR      = 2.00   # Premium < $2.00 = not worth the spread risk

# ---------------------------------------------------------------------------
# Gate thresholds — Strike / Position
# ---------------------------------------------------------------------------
STRIKE_NEARNESS_PCT     = 0.05   # ATM = within 5% of underlying price
STRIKE_SAFETY_RATIO     = 0.995  # sell_put strike must be <= 0.995 × S1 support
SELL_CALL_OTM_PASS_PCT  = 2.0    # sell_call: strike ≥ 2% OTM for pass
MAX_LOSS_WARN_PCT       = 0.10   # Max loss > 10% of account = warn
MAX_LOSS_FAIL_PCT       = 0.20   # Max loss > 20% of account = hard fail

# ---------------------------------------------------------------------------
# Gate thresholds — DTE / Signal quality
# ---------------------------------------------------------------------------
VCP_HIGH_CONF_PCT       = 80.0   # VCP confidence + ADX high → aggressive DTE
VCP_MED_CONF_PCT        = 60.0   # VCP confidence medium → standard DTE
ADX_HIGH_THRESH         = 40.0   # ADX >= 40 = strong trend confirmation
DTE_REC_HIGH_SIGNAL     = 21     # Recommended DTE when VCP+ADX both high
DTE_REC_MED_SIGNAL      = 45     # Recommended DTE when VCP medium confidence
DTE_GATE_TOLERANCE      = 5      # DTE gate: pass if within ±5d of recommended

# ---------------------------------------------------------------------------
# Gate thresholds — Market regime (SPY)
# ---------------------------------------------------------------------------
SPY_BULL_5D_WARN        = -0.02  # SPY 5-day < -2% = softening (buy_call warn)
SPY_BULL_5D_FAIL        = -0.04  # SPY 5-day < -4% = unsupportive (buy_call fail)
SPY_SELLPUT_5D_WARN     = -0.01  # SPY 5-day < -1% = weakening (sell_put warn)
SPY_SELLPUT_5D_FAIL     = -0.02  # SPY 5-day < -2% = too risky for put selling
SPY_SELLCALL_5D_PASS    = -0.01  # SPY 5-day < -1% = favorable for call selling
SPY_SELLCALL_5D_WARN    = 0.02   # SPY 5-day >= 2% = strong bull, elevated call risk
SPY_BUYPUT_5D_PASS      = -0.02  # SPY 5-day < -2% = bearish regime (buy_put pass)
SPY_BUYPUT_5D_WARN      = -0.01  # SPY 5-day < -1% = weakening (buy_put warn)

# ---------------------------------------------------------------------------
# Gate thresholds — Delta targeting
# ---------------------------------------------------------------------------
BUYER_TARGET_DELTA      = 0.68   # ITM call/put: delta closest to 0.68 / -0.68
BUYER_ATM_DELTA         = 0.52   # ATM fallback delta
SELLER_ATM_DELTA        = 0.50   # Sellers: ATM strike preference
DELTA_MATCH_TOLERANCE   = 0.10   # Within ±0.10 of target delta = match

# ---------------------------------------------------------------------------
# DTE windows
# ---------------------------------------------------------------------------
DEFAULT_MIN_DTE         = 14     # Never recommend < 14 DTE (theta too chaotic)
DEFAULT_MAX_DTE         = 120    # Full DTE window upper bound
BUYER_SWEET_MIN_DTE     = 45     # Buyer sweet spot lower bound
BUYER_SWEET_MAX_DTE     = 90     # Buyer sweet spot upper bound
SELLER_SWEET_MIN_DTE    = 21     # Seller sweet spot lower bound
SELLER_SWEET_MAX_DTE    = 45     # Seller sweet spot upper bound

# ---------------------------------------------------------------------------
# Chain fetch profiles
# ---------------------------------------------------------------------------
SMART_MAX_EXPIRIES      = 2      # Smart: 2 expiries — backup if first expiry has no valid strikes
SMART_MAX_STRIKES       = 12     # Smart: 12 strikes — ascending/descending sort for sell dirs, buffer for $2.5 increments
SMART_MAX_CONTRACTS     = 26     # Smart: 12 strikes × 2 expiries + ATM anchors
SMART_STRIKE_WINDOW     = 0.10   # Smart: fallback ±10% when no direction hint

FULL_MAX_EXPIRIES       = 3      # Full: up to 3 expiries in DTE window
FULL_MAX_STRIKES        = 8      # Full: 8 strikes per expiry
FULL_MAX_CONTRACTS      = 60     # Full: up to 60 contracts (reqTickers cap)
FULL_STRIKE_WINDOW      = 0.15   # Full: ±15% of underlying

IBKR_BATCH_SIZE         = 20     # reqTickers batch size per call

# ---------------------------------------------------------------------------
# Direction-aware strike windows (fraction of underlying)
# Based on research: buyers want delta ~0.68 (ITM), sellers want ATM
# ---------------------------------------------------------------------------
# buy_call: want ITM calls — strike ≈ 8-20% below underlying (delta ~0.68)
BUY_CALL_STRIKE_LOW_PCT  = 0.20  # deepest bound (20% below) — low strike bound
BUY_CALL_STRIKE_HIGH_PCT = 0.08  # shallowest bound (8% below) — high strike bound

# buy_put: want ITM puts — strike ≈ 8-20% above underlying (delta ~-0.68)
BUY_PUT_STRIKE_LOW_PCT   = 0.08  # 8% above underlying — low strike bound
BUY_PUT_STRIKE_HIGH_PCT  = 0.20  # 20% above underlying — high strike bound

# sell_call: ATM to OTM — extended to 15% above ATM
# Short leg needs delta ~0.30 (~5% OTM), protection leg needs delta ~0.15 (~12% OTM)
SELL_CALL_STRIKE_LOW_PCT = 0.02  # 2% below ATM (include slight ITM for short leg)
SELL_CALL_STRIKE_HIGH_PCT= 0.15  # 15% above ATM (wide enough for protection leg)

# sell_put: ATM to OTM — extended to 15% below ATM (symmetric with sell_call)
# Short leg needs delta ~-0.30 (~5% OTM), protection leg needs delta ~-0.15 (~12% OTM)
SELL_PUT_STRIKE_LOW_PCT  = 0.15  # 15% below ATM (wide enough for protection leg)
SELL_PUT_STRIKE_HIGH_PCT = 0.02  # 2% above ATM

# Structure cache: reqSecDefOptParams result (strikes/expiries) cached 4h
STRUCT_CACHE_TTL_SEC_4H  = 14_400  # 4 hours — chain structure is stable intraday

# ---------------------------------------------------------------------------
# Account / position sizing defaults
# ---------------------------------------------------------------------------
DEFAULT_ACCOUNT_SIZE    = 25_000  # User's actual account size ($25k)
DEFAULT_RISK_PCT        = 0.01    # 1% max risk per trade
DEFAULT_HOLD_DAYS       = 7       # Default planned hold period (days)
MAX_POSITION_PCT        = 0.05    # Never allocate > 5% of account to one option

# ---------------------------------------------------------------------------
# Black-Scholes
# ---------------------------------------------------------------------------
RISK_FREE_RATE          = 0.053   # Current T-bill rate (~5.3%) — update manually

# ---------------------------------------------------------------------------
# Cache TTLs (seconds unless noted)
# ---------------------------------------------------------------------------
CHAIN_CACHE_TTL_SEC     = 120     # Live chain: 2-minute freshness window
CHAIN_CACHE_STALE_SEC   = 600     # Stale chain: serve up to 10 min if IBKR down
OI_CACHE_TTL_SEC        = 28800   # Open Interest: 8h (only updates daily)
STRUCT_CACHE_TTL_SEC    = 14400   # Strike/expiry structure: 4h
IV_HISTORY_CACHE_DAYS   = 365     # Keep 1 year of IV history in SQLite
PAPER_TRADE_MTM_TTL     = 300     # Mark-to-market refresh: 5 minutes

# ---------------------------------------------------------------------------
# IB Worker / timeouts
# ---------------------------------------------------------------------------
IB_WORKER_TIMEOUT_SMART = 40      # Timeout for smart profile chain fetch (sec); 40s covers usopt warm-up retry (15+3+15=33s)
IB_WORKER_TIMEOUT_FULL  = 50      # Timeout for full profile chain fetch (sec)
IB_CHAIN_RETRY_ATTEMPTS = 2       # Retry attempts on timeout
IB_CHAIN_RETRY_BACKOFF  = 0.6     # Backoff between retries (sec)
IB_CB_FAILURE_THRESHOLD = 2       # Circuit breaker: open after N failures
IB_CB_COOLDOWN_SEC      = 45      # Circuit breaker cooldown (sec)

# ---------------------------------------------------------------------------
# Service ports
# ---------------------------------------------------------------------------
BACKEND_PORT            = 5051
FRONTEND_PORT           = 3050
IB_GATEWAY_HOST         = "127.0.0.1"
IB_GATEWAY_PORT         = 4001    # IB Gateway live
STA_BASE_URL            = "http://localhost:5001"
STA_TIMEOUT_SEC         = 3       # STA fetch timeout — never block main thread

# ---------------------------------------------------------------------------
# FOMC calendar 2026–2027 (hardcoded for standalone operation)
# Dates: scheduled FOMC meeting announcement days
# Update this list in early 2027 for the following year.
# ---------------------------------------------------------------------------
FOMC_DATES_2026 = [
    "2026-01-28",
    "2026-03-18",
    "2026-05-06",
    "2026-06-17",
    "2026-07-29",
    "2026-09-16",
    "2026-11-04",
    "2026-12-16",
]

FOMC_DATES_2027 = [
    "2027-01-27",
    "2027-03-17",
    "2027-05-05",
    "2027-06-16",
    "2027-07-28",
    "2027-09-15",
    "2027-11-03",
    "2027-12-15",
]

FOMC_DATES = FOMC_DATES_2026 + FOMC_DATES_2027

# ---------------------------------------------------------------------------
# Quality tier labels (used by frontend banners)
# ---------------------------------------------------------------------------
QUALITY_LIVE    = "live"
QUALITY_CACHED  = "cached"
QUALITY_DELAYED = "delayed"
QUALITY_PARTIAL = "partial"
QUALITY_MOCK    = "mock"

# ---------------------------------------------------------------------------
# Directions
# ---------------------------------------------------------------------------
DIRECTION_BUY_CALL  = "buy_call"
DIRECTION_SELL_CALL = "sell_call"
DIRECTION_BUY_PUT   = "buy_put"
DIRECTION_SELL_PUT  = "sell_put"

BUYER_DIRECTIONS    = {DIRECTION_BUY_CALL, DIRECTION_BUY_PUT}
SELLER_DIRECTIONS   = {DIRECTION_SELL_CALL, DIRECTION_SELL_PUT}
CALL_DIRECTIONS     = {DIRECTION_BUY_CALL, DIRECTION_SELL_CALL}
PUT_DIRECTIONS      = {DIRECTION_BUY_PUT, DIRECTION_SELL_PUT}
TRACK_A_DIRECTIONS  = {DIRECTION_BUY_CALL, DIRECTION_SELL_CALL}
TRACK_B_DIRECTIONS  = {DIRECTION_BUY_PUT, DIRECTION_SELL_PUT}

# ---------------------------------------------------------------------------
# Sector Rotation ETF Module (Day 13 — research-verified)
# Source: docs/Research/Sector_ETF_Options_Research_Prompt_Day13.md
# ---------------------------------------------------------------------------
ETF_TICKERS = {
    "XLK", "XLF", "XLV", "XLY", "XLP", "XLE", "XLI", "XLB",
    "XLU", "XLRE", "XLC",   # 11 SPDR sector ETFs
    "QQQ", "IWM", "MDY",    # Cap-size ETFs
    "TQQQ",                  # 3x leveraged (special rules)
}

# ETF-specific gate overrides (research: ETFs 10-100x more liquid than stocks)
ETF_MIN_PREMIUM_DOLLAR  = 0.50   # (stock = 2.00). XLU/XLP ATM < $2 at 45 DTE.
ETF_SPREAD_BLOCK_PCT    = 0.10   # (stock = 15%). ETF ATM spreads $0.01-0.05.
ETF_MIN_OPEN_INTEREST   = 500    # (stock = 1000). ETFs always exceed this.

# TQQQ special rules (VERIFIED: Seeking Alpha, Market Chameleon)
TQQQ_MAX_DTE            = 45     # Volatility decay accelerates beyond 45 days
# TQQQ decay formula: 3 × σ² per day (VERIFIED)
# No covered calls (VERIFIED: caps gains during 50%+ rallies)
# Bear call spreads at 7-14 DTE OK (VERIFIED: Market Chameleon)

# DTE by IVR (VERIFIED: tastylive "How IV Impacts the Selection of DTE", Aug 2024)
ETF_DTE_LOW_IVR         = 60     # IVR < 30 → 60 DTE
ETF_DTE_HIGH_IVR        = 30     # IVR >= 30 → 30 DTE
ETF_DTE_DEFAULT         = 45     # Fallback when IVR unavailable
ETF_DTE_SELLER_PASS_MIN = 21     # ETF seller sweet spot start (vs stock 14)
ETF_DTE_SELLER_PASS_MAX = 45     # ETF seller sweet spot end (vs stock 21)

# FOMC sensitivity (VERIFIED: QuantSeeker "Which Sectors Move on Fed Days")
FOMC_HIGH_SENSITIVITY   = {"XLF", "XLRE"}    # Biggest movers on Fed days
FOMC_LOW_SENSITIVITY    = {"XLU", "XLP"}      # Barely move on Fed days
FOMC_WARN_DAYS          = 3                    # WARN (not BLOCK) within 3 days

# Dividend risk (VERIFIED: Webull, Schwab, Fidelity, CBOE)
HIGH_DIVIDEND_ETFS      = {"XLU", "XLRE", "XLF"}  # Yield > 1.4%
DIVIDEND_WARN_DAYS      = 3                         # Short calls: WARN 3 days before ex-date

# Sector classifications (VERIFIED: ryanoconnellfinance.com)
CYCLICAL_SECTORS        = {"XLI", "XLY", "XLB", "XLF"}   # Risk-On favored
DEFENSIVE_SECTORS       = {"XLU", "XLV", "XLP"}           # Risk-Off favored

# Quadrant → action mapping (research-corrected Day 13)
# Leading/Improving = ANALYZE, Weakening = WATCH, Lagging = SKIP
QUADRANT_ANALYZE        = {"Leading", "Improving"}
QUADRANT_WATCH          = {"Weakening"}
QUADRANT_SKIP           = {"Lagging"}

# ---------------------------------------------------------------------------
# Phase 7b — Sector Bear Market Thresholds (Day 19)
# Source: docs/Research/Sector_Bear_Market_Day19.md
# ---------------------------------------------------------------------------
# Lagging ETF → bear_call_spread when RS meaningfully below SPY + declining momentum
RS_LAGGING_BEAR_RS              = 98.0    # RS below 98 = underperforming SPY by 2+ points
RS_LAGGING_BEAR_MOM             = -0.5    # Momentum still declining (not bottoming)
# Broad market regime detection
BROAD_SELLOFF_SECTOR_PCT        = 0.50    # >50% sectors Weakening+Lagging = broad selloff
# IVR soft warning threshold for bear spreads (L2 only — advisory, not a gate)
IVR_BEAR_SPREAD_WARN            = 40      # IVR below 40% = premium may be thin for credit spreads
# Display hint → core direction mapping for chain fetches
DIRECTION_TO_CHAIN_DIR = {
    "buy_call": "buy_call",
    "sell_call": "sell_call",
    "buy_put": "buy_put",
    "sell_put": "sell_put",
    "bull_call_spread": "buy_call",     # bull spread uses call buyer chain window
    "bear_call_spread": "sell_call",    # bear spread uses call seller chain window
}
