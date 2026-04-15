import { useState } from 'react';

const SUPPORTED_SPREADS = ['bear_call_spread', 'bull_put_spread'];

function fmtExpiry(isoDate) {
  // "2026-05-15" → "May 15 '26"
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
  const [qty, setQty]     = useState(1);
  const [status, setStatus] = useState('idle'); // idle | loading | staged | error
  const [result, setResult] = useState(null);
  const [errMsg, setErrMsg] = useState('');

  // Only render for spread types on GO verdict
  if (!strategy || !SUPPORTED_SPREADS.includes(strategy.strategy_type)) return null;
  if (!verdict || verdict.color !== 'green') return null;

  const isBearCall = strategy.strategy_type === 'bear_call_spread';
  const rightLabel = strategy.right === 'C' ? 'Call' : 'Put';
  const spreadLabel = isBearCall ? 'Bear Call Spread' : 'Bull Put Spread';

  // Bear call: SELL short_strike C, BUY long_strike C (long > short)
  // Bull put:  SELL short_strike P, BUY long_strike P (long < short)
  const sellStrike = strategy.short_strike;
  const buyStrike  = strategy.long_strike;
  const netCredit  = strategy.net_premium ?? strategy.premium ?? 0;
  const maxProfit  = strategy.max_gain_per_lot ?? (netCredit * 100);
  const maxLoss    = strategy.max_loss_per_lot;
  const breakeven  = strategy.breakeven;
  const expiry     = strategy.expiry;
  const dte        = strategy.dte;

  async function handleStage() {
    setStatus('loading');
    setErrMsg('');
    try {
      const res = await fetch('/api/orders/stage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          strategy_type: strategy.strategy_type,
          right:         strategy.right,
          expiry,
          short_strike:  sellStrike,
          long_strike:   buyStrike,
          net_credit:    netCredit,
          qty,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setResult(data);
        setStatus('staged');
      } else {
        setErrMsg(data.error || 'Staging failed');
        setStatus('error');
      }
    } catch (e) {
      setErrMsg('Network error — is the backend running?');
      setStatus('error');
    }
  }

  return (
    <div className="card execution-card">
      <div className="section-title execution-title">
        Execution
        <span className="execution-badge">{spreadLabel}</span>
      </div>

      {/* Strategy header */}
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

      {/* Action row */}
      {status !== 'staged' && (
        <div className="execution-action">
          <div className="exec-qty-row">
            <span className="exec-qty-label">Contracts</span>
            <button className="exec-qty-btn" onClick={() => setQty(q => Math.max(1, q - 1))} disabled={status === 'loading'}>−</button>
            <span className="exec-qty-val">{qty}</span>
            <button className="exec-qty-btn" onClick={() => setQty(q => Math.min(50, q + 1))} disabled={status === 'loading'}>+</button>
          </div>
          <button
            className={`exec-stage-btn ${status === 'loading' ? 'exec-stage-loading' : ''}`}
            onClick={handleStage}
            disabled={status === 'loading'}
          >
            {status === 'loading' ? 'Staging…' : 'Stage in TWS'}
          </button>
        </div>
      )}

      {/* Success state */}
      {status === 'staged' && result && (
        <div className="exec-staged">
          <div className="exec-staged-icon">✓</div>
          <div className="exec-staged-text">
            <strong>Order #{result.order_id} staged in TWS</strong>
            <span>Open TWS → Order Management → review and click Transmit</span>
          </div>
          <button className="exec-reset-btn" onClick={() => { setStatus('idle'); setResult(null); }}>
            Reset
          </button>
        </div>
      )}

      {/* Error state */}
      {status === 'error' && (
        <div className="exec-error">
          <span className="exec-error-icon">✕</span>
          <span className="exec-error-msg">{errMsg}</span>
          <button className="exec-reset-btn" onClick={() => setStatus('idle')}>Retry</button>
        </div>
      )}

      {/* Footer note */}
      {status !== 'staged' && (
        <div className="exec-footer-note">
          transmit=False — order sits in TWS blotter until you click Transmit
        </div>
      )}
    </div>
  );
}
