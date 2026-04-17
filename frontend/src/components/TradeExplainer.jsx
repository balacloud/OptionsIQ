function fmt2(v) {
  if (v == null) return '—';
  return Number(v).toFixed(2);
}

// Determine chart range with padding to prevent crowding
function getChartRange(values) {
  const clean = values.filter(v => v != null && !isNaN(v));
  if (clean.length === 0) return { chartMin: 0, chartMax: 100 };
  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const padding = Math.max((max - min) * 0.35, 0.75);
  return { chartMin: min - padding, chartMax: max + padding };
}

function toPct(value, chartMin, chartMax) {
  if (chartMax === chartMin) return 50;
  return Math.max(0, Math.min(100, ((value - chartMin) / (chartMax - chartMin)) * 100));
}

// Plain English summary by strategy type
function getTradeHeadline(strategy, ticker) {
  if (!strategy || !ticker) return null;
  const { strategy_type, breakeven, strike, dte } = strategy;
  const be = fmt2(breakeven);
  const st = fmt2(strike);
  const days = dte ?? '?';

  switch (strategy_type) {
    case 'bear_call_spread':
      return `You profit if ${ticker} stays below $${be} for the next ${days} days`;
    case 'bull_put_spread':
      return `You profit if ${ticker} stays above $${be} for the next ${days} days`;
    case 'itm_call':
    case 'atm_call':
      return `You profit if ${ticker} rises above $${be} within ${days} days`;
    case 'itm_put':
    case 'atm_put':
      return `You profit if ${ticker} drops below $${be} within ${days} days`;
    case 'sell_call':
      return `You profit if ${ticker} stays below $${st} for ${days} days — note: unlimited risk without spread`;
    case 'sell_put':
      return `You profit if ${ticker} stays above $${st} for ${days} days`;
    default:
      return null;
  }
}

// Whether this strategy collects credit (sellers)
function isCreditStrategy(strategy_type) {
  return ['bear_call_spread', 'bull_put_spread', 'sell_call', 'sell_put'].includes(strategy_type);
}

// Whether this is a bearish strategy (zones flip)
function isBearish(strategy_type) {
  return ['bear_call_spread', 'sell_call', 'buy_put', 'itm_put', 'atm_put'].includes(strategy_type);
}

// Which side is ITM for calls vs puts
function getMoneyness(underlyingPrice, strikes, strategy_type) {
  const isPut = ['buy_put', 'itm_put', 'atm_put', 'bull_put_spread'].includes(strategy_type);
  return { isPut };
}

export default function TradeExplainer({ strategy, underlyingPrice, ticker, direction }) {
  if (!strategy || underlyingPrice == null) {
    return (
      <div className="trade-explainer trade-explainer-empty">
        <div className="te-empty-msg">Run analysis to see what this trade means</div>
      </div>
    );
  }

  const {
    strategy_type,
    short_strike,
    long_strike,
    strike,
    breakeven,
    max_gain_per_lot,
    max_loss_per_lot,
    label,
  } = strategy;

  const headline = getTradeHeadline(strategy, ticker);
  const isCredit = isCreditStrategy(strategy_type);
  const bearish = isBearish(strategy_type);
  const { isPut } = getMoneyness(underlyingPrice, { short_strike, long_strike }, strategy_type);

  // Determine markers for number line
  const markers = [];
  const priceValues = [underlyingPrice];

  if (short_strike != null) priceValues.push(short_strike);
  if (long_strike != null)  priceValues.push(long_strike);
  if (breakeven != null)    priceValues.push(breakeven);
  if (strike != null && short_strike == null) priceValues.push(strike);

  const { chartMin, chartMax } = getChartRange(priceValues);
  const pct = (v) => toPct(v, chartMin, chartMax);

  // Current price marker
  markers.push({ value: underlyingPrice, pct: pct(underlyingPrice), type: 'current', label: `$${fmt2(underlyingPrice)}`, sublabel: 'Current' });

  // Short strike (the one you SELL)
  if (short_strike != null) {
    const label_text = isCredit ? `SELL $${fmt2(short_strike)}` : `$${fmt2(short_strike)}`;
    markers.push({ value: short_strike, pct: pct(short_strike), type: 'short', label: label_text, sublabel: isCredit ? 'Short leg' : 'Strike' });
  } else if (strike != null) {
    markers.push({ value: strike, pct: pct(strike), type: 'short', label: `$${fmt2(strike)}`, sublabel: 'Strike' });
  }

  // Long strike (the one you BUY for protection)
  if (long_strike != null) {
    markers.push({ value: long_strike, pct: pct(long_strike), type: 'long', label: `BUY $${fmt2(long_strike)}`, sublabel: 'Protection' });
  }

  // Breakeven
  if (breakeven != null) {
    markers.push({ value: breakeven, pct: pct(breakeven), type: 'breakeven', label: `BE $${fmt2(breakeven)}`, sublabel: 'Breakeven' });
  }

  // Detect label collisions — stagger if within 8% of chart width
  const sorted = [...markers].sort((a, b) => a.pct - b.pct);
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i].pct - sorted[i - 1].pct < 8) {
      sorted[i].stagger = true;
    }
  }
  // Apply stagger back
  const markerMap = {};
  sorted.forEach(m => { markerMap[m.type] = m; });

  // Profit/loss zone positions
  const profitZone = bearish
    ? { left: 0, width: breakeven != null ? pct(breakeven) : (short_strike != null ? pct(short_strike) : 50) }
    : { left: breakeven != null ? pct(breakeven) : (short_strike != null ? pct(short_strike) : 50), width: null };

  const lossZone = bearish
    ? { left: breakeven != null ? pct(breakeven) : (short_strike != null ? pct(short_strike) : 50), width: null }
    : { left: 0, width: breakeven != null ? pct(breakeven) : (short_strike != null ? pct(short_strike) : 50) };

  // Risk/reward bar
  const gain = max_gain_per_lot;
  const loss = max_loss_per_lot;
  const hasRR = gain != null || loss != null;
  const total = (gain ?? 0) + (loss ?? 0);
  const gainPct = total > 0 ? ((gain ?? 0) / total) * 100 : 50;
  const lossPct = total > 0 ? ((loss ?? 0) / total) * 100 : 50;

  // Margin of safety: distance from current price to short strike
  const shortSt = short_strike ?? strike;
  const marginOfSafety = shortSt != null ? Math.abs(shortSt - underlyingPrice) : null;
  const marginPct = (shortSt != null && underlyingPrice != null)
    ? ((Math.abs(shortSt - underlyingPrice) / underlyingPrice) * 100).toFixed(1)
    : null;

  // Credit framing
  const netCredit = gain != null ? (gain / 100).toFixed(2) : null;

  return (
    <div className="trade-explainer">
      <div className="te-header">
        <div className="te-title">What This Trade Is</div>
        <div className="te-subtitle">{label}</div>
      </div>

      {headline && (
        <div className="te-headline-box">
          {headline}
        </div>
      )}

      {/* ── Number Line ── */}
      <div className="te-section-label">Strike Zone</div>
      <div className="te-numberline-wrap">

        {/* Profit zone */}
        {bearish ? (
          <div
            className="te-zone te-zone-profit"
            style={{ left: 0, width: `${profitZone.width}%` }}
          />
        ) : (
          <div
            className="te-zone te-zone-profit"
            style={{ left: `${profitZone.left}%`, right: 0 }}
          />
        )}

        {/* Loss zone */}
        {bearish ? (
          <div
            className="te-zone te-zone-loss"
            style={{ left: `${lossZone.left}%`, right: 0 }}
          />
        ) : (
          <div
            className="te-zone te-zone-loss"
            style={{ left: 0, width: `${lossZone.width}%` }}
          />
        )}

        {/* Base axis line */}
        <div className="te-axis" />

        {/* Markers */}
        {markers.map((m) => {
          const staggered = markerMap[m.type]?.stagger;
          return (
            <div
              key={m.type}
              className={`te-marker te-marker-${m.type} ${staggered ? 'te-marker-stagger' : ''}`}
              style={{ left: `${m.pct}%` }}
            >
              <div className="te-marker-line" />
              <div className="te-marker-dot" />
              <div className={`te-marker-labels ${staggered ? 'te-labels-below' : ''}`}>
                <div className="te-marker-label">{m.label}</div>
                <div className="te-marker-sublabel">{m.sublabel}</div>
              </div>
            </div>
          );
        })}

        {/* Zone labels */}
        <div className="te-zone-labels">
          <span>{bearish ? '← Profit Zone' : '← Loss Zone'}</span>
          <span>{bearish ? 'Loss Zone →' : 'Profit Zone →'}</span>
        </div>

        {/* ITM / ATM / OTM education */}
        <div className="te-moneyness-row">
          {isPut ? (
            <>
              <span className="te-itm">ITM</span>
              <span className="te-atm">ATM</span>
              <span className="te-otm">OTM</span>
            </>
          ) : (
            <>
              <span className="te-otm">OTM</span>
              <span className="te-atm">ATM</span>
              <span className="te-itm">ITM</span>
            </>
          )}
        </div>
      </div>

      {/* Moneyness legend */}
      <div className="te-legend">
        <span><strong>OTM</strong> = Out of The Money (no value yet)</span>
        <span><strong>ATM</strong> = At The Money (right at price)</span>
        <span><strong>ITM</strong> = In The Money (has real value now)</span>
      </div>

      {/* Margin of safety */}
      {marginOfSafety != null && (
        <div className="te-margin-safety">
          <span className="te-mos-icon">↔</span>
          <span>
            <strong>Margin of Safety:</strong> ${marginOfSafety.toFixed(2)} ({marginPct}%) — the gap the ETF can move against you before this trade loses money
          </span>
        </div>
      )}

      {/* Expiry note */}
      <div className="te-expiry-note">
        This shows your trade at expiry. Before expiry, actual P&amp;L can vary due to volatility and time decay.
      </div>

      {/* ── Risk / Reward Bar ── */}
      {hasRR && (
        <div className="te-rr-section">
          <div className="te-section-label">Risk vs Reward (per contract)</div>

          {isCredit && netCredit && (
            <div className="te-credit-note">
              You collected ${netCredit}/share credit — this is not profit until expiry
            </div>
          )}

          <div className="te-rr-bar-wrap">
            <div className="te-rr-bar">
              {gain != null && (
                <div
                  className="te-rr-profit"
                  style={{ width: `${gainPct}%` }}
                >
                  {gainPct > 12 && `$${gain}`}
                </div>
              )}
              {loss != null ? (
                <div
                  className="te-rr-loss"
                  style={{ width: `${lossPct}%` }}
                >
                  {lossPct > 12 && `$${loss}`}
                </div>
              ) : (
                <div className="te-rr-unlimited">
                  Unlimited
                </div>
              )}
            </div>
          </div>

          <div className="te-rr-stats">
            {gain != null && (
              <div className="te-rr-stat te-rr-stat-profit">
                <div className="te-rr-stat-val">+${gain}</div>
                <div className="te-rr-stat-lbl">Max Profit per contract</div>
                <div className="te-rr-stat-ctx">
                  {bearish ? `if ${ticker} stays below $${fmt2(short_strike ?? breakeven)} at expiry` : `if ${ticker} rises past $${fmt2(breakeven)} at expiry`}
                </div>
              </div>
            )}
            {loss != null ? (
              <div className="te-rr-stat te-rr-stat-loss">
                <div className="te-rr-stat-val">−${loss}</div>
                <div className="te-rr-stat-lbl">Max Loss per contract</div>
                <div className="te-rr-stat-ctx">
                  {bearish ? `if ${ticker} rises above $${fmt2(long_strike)} at expiry` : `if ${ticker} drops below $${fmt2(long_strike ?? breakeven)} at expiry`}
                </div>
              </div>
            ) : (
              <div className="te-rr-stat te-rr-stat-loss">
                <div className="te-rr-stat-val te-unlimited">Unlimited</div>
                <div className="te-rr-stat-lbl">Max Loss</div>
                <div className="te-rr-stat-ctx">No protection — consider using a spread</div>
              </div>
            )}
          </div>

          {gain != null && loss != null && (
            <div className="te-rr-ratio">
              Risk:Reward = {(loss / gain).toFixed(1)}:1 — you risk ${loss} to make ${gain}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
