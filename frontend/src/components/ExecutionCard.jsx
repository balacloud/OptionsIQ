import { useState } from 'react';

const SUPPORTED_SPREADS = ['bear_call_spread', 'bull_put_spread'];

function fmtExpiry(isoDate) {
  if (!isoDate) return '—';
  try {
    const d = new Date(isoDate + 'T12:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
  } catch { return isoDate; }
}

function fmtDollar(n) {
  if (n == null || isNaN(n)) return '—';
  return `$${Number(n).toFixed(2)}`;
}

export default function ExecutionCard({ ticker, strategy, verdict }) {
  const [copied, setCopied] = useState(false);

  if (!strategy || !SUPPORTED_SPREADS.includes(strategy.strategy_type)) return null;
  if (!verdict || verdict.color !== 'green') return null;

  const isBearCall = strategy.strategy_type === 'bear_call_spread';
  const rightLabel = strategy.right === 'C' ? 'Call' : 'Put';
  const spreadLabel = isBearCall ? 'Bear Call Spread' : 'Bull Put Spread';
  const viewLabel = isBearCall ? 'Vertical Spread' : 'Vertical Spread';

  const sellStrike = strategy.short_strike;
  const buyStrike  = strategy.long_strike;
  const netCredit  = strategy.net_premium ?? strategy.premium ?? 0;
  const maxProfit  = strategy.max_gain_per_lot ?? (netCredit * 100);
  const maxLoss    = strategy.max_loss_per_lot;
  const breakeven  = strategy.breakeven;
  const expiry     = strategy.expiry;
  const dte        = strategy.dte;

  const steps = [
    { text: `Log into IBKR Client Portal → Trade → Option Chains` },
    { text: `Search for ${ticker}` },
    { text: `Click View dropdown → select "${viewLabel}"` },
    { text: `Select expiration: ${fmtExpiry(expiry)} (${dte} DTE)` },
    isBearCall
      ? { text: `Click Ask on ${sellStrike}${rightLabel[0]} to SELL, then Bid on ${buyStrike}${rightLabel[0]} to BUY` }
      : { text: `Click Ask on ${sellStrike}${rightLabel[0]} to SELL, then Bid on ${buyStrike}${rightLabel[0]} to BUY` },
    { text: `Set quantity (start with 1 contract)` },
    { text: `Set order type: Limit at net credit ${fmtDollar(netCredit)}` },
    { text: `Click Preview → verify legs match → Submit` },
  ];

  function handleCopy() {
    const summary = [
      `${ticker} ${spreadLabel}`,
      `Expiry: ${fmtExpiry(expiry)} (${dte} DTE)`,
      `SELL ${sellStrike}${rightLabel[0]} + BUY ${buyStrike}${rightLabel[0]}`,
      `Net Credit: ${fmtDollar(netCredit)}/sh`,
      `Max Profit: ${fmtDollar(maxProfit)} | Max Loss: ${maxLoss != null ? fmtDollar(maxLoss) : '—'}`,
      `Breakeven: ${breakeven != null ? fmtDollar(breakeven) : '—'}`,
    ].join('\n');
    navigator.clipboard.writeText(summary).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="card execution-card">
      <div className="section-title execution-title">
        How to Place This Trade
        <span className="execution-badge">{spreadLabel}</span>
      </div>

      {/* Strategy summary */}
      <div className="execution-header">
        <span className="execution-ticker">{ticker}</span>
        <span className="execution-expiry">{fmtExpiry(expiry)} · {dte}d</span>
      </div>

      {/* Legs */}
      <div className="execution-legs">
        <div className="exec-leg exec-leg-sell">
          <span className="exec-leg-action">SELL</span>
          <span className="exec-leg-strike">{sellStrike}{rightLabel[0]}</span>
        </div>
        <span className="exec-leg-plus">+</span>
        <div className="exec-leg exec-leg-buy">
          <span className="exec-leg-action">BUY</span>
          <span className="exec-leg-strike">{buyStrike}{rightLabel[0]}</span>
        </div>
        <div className="exec-credit">
          Net Credit&nbsp;<strong>{fmtDollar(netCredit)}/sh</strong>
        </div>
      </div>

      {/* Risk metrics */}
      <div className="execution-metrics">
        <div className="exec-metric">
          <span className="exec-metric-label">Max Profit</span>
          <span className="exec-metric-value text-green">{fmtDollar(maxProfit)}</span>
        </div>
        <div className="exec-metric">
          <span className="exec-metric-label">Max Loss</span>
          <span className="exec-metric-value text-red">{maxLoss != null ? fmtDollar(maxLoss) : '—'}</span>
        </div>
        <div className="exec-metric">
          <span className="exec-metric-label">Breakeven</span>
          <span className="exec-metric-value">{breakeven != null ? fmtDollar(breakeven) : '—'}</span>
        </div>
      </div>

      {/* Step-by-step IBKR Client Portal guide */}
      <div className="execution-steps">
        <div className="exec-steps-title">IBKR Client Portal Steps</div>
        <ol className="exec-steps-list">
          {steps.map((s, i) => (
            <li key={i} className="exec-step">{s.text}</li>
          ))}
        </ol>
      </div>

      {/* Copy + note */}
      <div className="execution-footer">
        <button className="exec-copy-btn" onClick={handleCopy}>
          {copied ? 'Copied!' : 'Copy Trade Details'}
        </button>
        <div className="exec-footer-note">
          If "riskless combination" error appears in Client Portal, place via TWS desktop or use market order type.
        </div>
      </div>
    </div>
  );
}
