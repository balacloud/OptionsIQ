import { useState } from 'react';

const DIR_LABELS = {
  buy_call: 'Buy Call', sell_call: 'Sell Call',
  buy_put:  'Buy Put',  sell_put:  'Sell Put',
};

export default function PaperTradeBanner({ ticker, direction, data, onLogged }) {
  const [selected, setSelected] = useState(0);
  const [status, setStatus]     = useState('idle'); // idle | saving | saved | error
  const [saved, setSaved]       = useState(null);

  const strategies = data?.top_strategies || [];
  if (!strategies.length || !ticker || !direction) return null;

  const s = strategies[selected];
  if (!s) return null;

  const verdictColor = data?.verdict?.color;
  const verdictLabel = { green: 'GO', amber: 'CAUTION', red: 'BLOCKED' }[verdictColor] || '—';
  const verdictCls   = { green: 'ptb-verdict-go', amber: 'ptb-verdict-caution', red: 'ptb-verdict-blocked' }[verdictColor] || '';

  const log = async () => {
    setStatus('saving');
    try {
      const resp = await fetch('http://localhost:5051/api/options/paper-trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          direction,
          strategy_rank: s.rank ?? selected + 1,
          strike: s.strike,
          expiry: s.expiry_display,
          premium: s.premium,
          lots: 1,
          account_size: data?.account_size || 25000,
          verdict: verdictColor || null,
        }),
      });
      const result = await resp.json();
      if (result.success) {
        setSaved({ ticker, direction: DIR_LABELS[direction] || direction, strike: s.strike, expiry: s.expiry_display, premium: s.premium });
        setStatus('saved');
        if (onLogged) onLogged();
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  };

  if (status === 'saved' && saved) {
    return (
      <div className="ptb-wrap ptb-confirmed">
        <div className="ptb-confirm-title">Trade logged</div>
        <div className="ptb-confirm-row">
          <span className="ptb-confirm-ticker">{saved.ticker}</span>
          <span className="ptb-confirm-dir">{saved.direction}</span>
          <span className="ptb-confirm-detail">${saved.strike} strike · {saved.expiry} · ${saved.premium} premium</span>
        </div>
        <div className="ptb-confirm-sub">Check the Paper Trades tab to track P&L.</div>
        <button className="ptb-btn-ghost" onClick={() => { setStatus('idle'); setSaved(null); }}>Log another</button>
      </div>
    );
  }

  return (
    <div className="ptb-wrap">
      <div className="ptb-header">
        <span className="ptb-title">Record Paper Trade</span>
        <span className={`ptb-verdict ${verdictCls}`}>{verdictLabel}</span>
      </div>

      {strategies.length > 1 && (
        <div className="ptb-strategy-tabs">
          {strategies.map((st, i) => (
            <button
              key={i}
              className={`ptb-strat-btn ${i === selected ? 'ptb-strat-active' : ''}`}
              onClick={() => setSelected(i)}
            >
              R{i + 1} · ${st.strike} · {st.expiry_display}
            </button>
          ))}
        </div>
      )}

      <div className="ptb-trade-detail">
        <div className="ptb-detail-row">
          <span className="ptb-detail-label">Ticker</span>
          <span className="ptb-detail-val">{ticker}</span>
        </div>
        <div className="ptb-detail-row">
          <span className="ptb-detail-label">Direction</span>
          <span className="ptb-detail-val">{DIR_LABELS[direction] || direction}</span>
        </div>
        <div className="ptb-detail-row">
          <span className="ptb-detail-label">Strike</span>
          <span className="ptb-detail-val">${s.strike}</span>
        </div>
        <div className="ptb-detail-row">
          <span className="ptb-detail-label">Expiry</span>
          <span className="ptb-detail-val">{s.expiry_display}</span>
        </div>
        <div className="ptb-detail-row">
          <span className="ptb-detail-label">Entry Premium</span>
          <span className="ptb-detail-val ptb-premium">${s.premium}</span>
        </div>
        <div className="ptb-detail-row">
          <span className="ptb-detail-label">Lots</span>
          <span className="ptb-detail-val">1</span>
        </div>
      </div>

      <button
        className="ptb-log-btn"
        onClick={log}
        disabled={status === 'saving'}
      >
        {status === 'saving' ? 'Saving…' : 'Log Paper Trade'}
      </button>
      {status === 'error' && <div className="ptb-error">Failed to save — check backend</div>}
    </div>
  );
}
