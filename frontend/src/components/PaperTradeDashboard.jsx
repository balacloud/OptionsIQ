import { useEffect, useState, useCallback } from 'react';

const DIR_LABELS = {
  buy_call: 'Buy Call', sell_call: 'Sell Call',
  buy_put:  'Buy Put',  sell_put:  'Sell Put',
};

const VERDICT_COLORS = {
  green:  { bg: 'rgba(0,200,150,0.1)',  border: 'rgba(0,200,150,0.3)',  text: '#00c896' },
  amber:  { bg: 'rgba(250,180,50,0.1)', border: 'rgba(250,180,50,0.3)', text: '#f5a623' },
  red:    { bg: 'rgba(220,60,60,0.1)',  border: 'rgba(220,60,60,0.3)',  text: '#e05252' },
  closed: { bg: 'rgba(120,120,120,0.1)',border: 'rgba(120,120,120,0.3)',text: '#888' },
};

function StatCard({ label, value, sub, color }) {
  return (
    <div className="pt-stat-card">
      <div className="pt-stat-label">{label}</div>
      <div className="pt-stat-value" style={color ? { color } : {}}>{value ?? '—'}</div>
      {sub && <div className="pt-stat-sub">{sub}</div>}
    </div>
  );
}

function BreakdownRow({ label, data }) {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="pt-breakdown">
      <div className="pt-breakdown-title">{label}</div>
      {Object.entries(data).map(([k, v]) => (
        <div key={k} className="pt-breakdown-row">
          <span className="pt-breakdown-key">{DIR_LABELS[k] || k}</span>
          <span className="pt-breakdown-count">{v.count} trades</span>
          <span className="pt-breakdown-winrate">
            {v.win_rate != null ? `${v.win_rate}% win` : '—'}
          </span>
          <span className={`pt-breakdown-pnl ${v.total_pnl >= 0 ? 'pos' : 'neg'}`}>
            {v.total_pnl >= 0 ? '+' : ''}${v.total_pnl.toFixed(0)}
          </span>
        </div>
      ))}
    </div>
  );
}

function EquityCurve({ points }) {
  if (!points || points.length < 2) return null;
  const values = points.map(p => p.pnl);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const range = max - min || 1;
  const W = 500, H = 80, PAD = 8;
  const pts = points.map((p, i) => {
    const x = PAD + (i / (points.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((p.pnl - min) / range) * (H - PAD * 2);
    return `${x},${y}`;
  }).join(' ');
  const zeroY = H - PAD - ((0 - min) / range) * (H - PAD * 2);
  const finalPnl = values[values.length - 1];
  return (
    <div className="pt-curve-wrap">
      <div className="pt-section-title">Equity Curve</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="pt-curve-svg">
        <line x1={PAD} y1={zeroY} x2={W - PAD} y2={zeroY}
          stroke="rgba(255,255,255,0.1)" strokeWidth="1" strokeDasharray="4,3" />
        <polyline points={pts} fill="none"
          stroke={finalPnl >= 0 ? '#00c896' : '#e05252'}
          strokeWidth="2" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

function TradeRow({ trade, onRefresh }) {
  const [markInput, setMarkInput] = useState('');
  const [busy, setBusy] = useState(false);

  const pnlColor = trade.pnl == null ? '' : trade.pnl >= 0 ? 'pos' : 'neg';
  const verdictStyle = VERDICT_COLORS[trade.verdict] || {};
  const isClosed = trade.verdict === 'closed';

  const patch = async (body) => {
    setBusy(true);
    await fetch(`http://localhost:5051/api/options/paper-trade/${trade.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    setBusy(false);
    onRefresh();
  };

  const del = async () => {
    if (!window.confirm(`Delete trade #${trade.id} (${trade.ticker} ${trade.direction})?`)) return;
    setBusy(true);
    await fetch(`http://localhost:5051/api/options/paper-trade/${trade.id}`, { method: 'DELETE' });
    setBusy(false);
    onRefresh();
  };

  return (
    <div className={`pt-trade-card ${isClosed ? 'pt-trade-closed' : ''}`}>
      <div className="pt-trade-main">
        <span className="pt-trade-ticker">{trade.ticker}</span>
        <span className="pt-trade-dir">{DIR_LABELS[trade.direction] || trade.direction}</span>
        <span className="pt-trade-strike">${trade.strike}</span>
        <span className="pt-trade-expiry">{trade.expiry}</span>
        <span className="pt-trade-premium">entry ${trade.premium}</span>
        {trade.verdict
          ? <span className="pt-trade-verdict" style={{ color: verdictStyle.text }}>{trade.verdict.toUpperCase()}</span>
          : <span className="pt-trade-verdict">—</span>}
        <span className={`pt-trade-pnl ${pnlColor}`}>
          {trade.pnl != null ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(0)}` : '—'}
        </span>
        <span className="pt-trade-date">{trade.created_at?.slice(0, 10)}</span>
      </div>

      {!isClosed && (
        <div className="pt-trade-actions">
          <input
            className="pt-mark-input"
            type="number"
            step="0.01"
            placeholder="current premium"
            value={markInput}
            onChange={e => setMarkInput(e.target.value)}
          />
          <button
            className="pt-action-btn"
            disabled={busy || !markInput}
            onClick={() => patch({ mark_price: parseFloat(markInput) })}
          >Update mark</button>
          <button
            className="pt-action-btn pt-close-btn"
            disabled={busy}
            onClick={() => patch({ mark_price: markInput ? parseFloat(markInput) : undefined, closed: true })}
          >Close trade</button>
          <button className="pt-action-btn pt-delete-btn" disabled={busy} onClick={del}>✕</button>
        </div>
      )}
      {isClosed && (
        <div className="pt-trade-actions">
          <span className="pt-closed-label">Closed · mark ${trade.mark_price ?? '—'}</span>
          <button className="pt-action-btn pt-delete-btn" disabled={busy} onClick={del}>✕</button>
        </div>
      )}
    </div>
  );
}

export default function PaperTradeDashboard({ refreshTick }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    fetch('http://localhost:5051/api/options/paper-trades/summary')
      .then(r => r.json())
      .then(d => { setSummary(d); setLoading(false); })
      .catch(() => { setError('Could not load paper trades'); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load, refreshTick]);

  if (loading) return <div className="pt-loading">Loading paper trades…</div>;
  if (error)   return <div className="pt-error">{error}</div>;

  if (!summary || summary.total_trades === 0) {
    return (
      <div className="pt-empty">
        <div className="pt-empty-icon">📋</div>
        <div className="pt-empty-title">No paper trades recorded yet</div>
        <div className="pt-empty-sub">
          Run an analysis → get a GO or CAUTION verdict → click <strong>Log Paper Trade</strong>.
          <br />Pick any of the 3 ranked strategies. Your P&amp;L and win rate will appear here.
        </div>
        <div className="pt-empty-tracked">
          <div className="pt-empty-tracked-title">What gets tracked</div>
          <div className="pt-empty-tracked-items">
            <span>Win rate by direction</span>
            <span>P&amp;L by ETF</span>
            <span>GO vs CAUTION verdict accuracy</span>
            <span>Equity curve over time</span>
          </div>
        </div>
      </div>
    );
  }

  const pnlColor = summary.total_pnl >= 0 ? '#00c896' : '#e05252';

  return (
    <div className="pt-dashboard">
      <div className="pt-header">
        <div>
          <div className="pt-header-title">Paper Trade Dashboard</div>
          <div className="pt-header-sub">{summary.total_trades} trades · <button className="pt-refresh-btn" onClick={load}>↺ Refresh</button></div>
        </div>
        <div className="pt-persist-badge" title="Trades stored in SQLite — survive restarts">
          ● SQLite — persists across restarts
        </div>
      </div>

      <div className="pt-stats-row">
        <StatCard label="Win Rate"
          value={summary.win_rate != null ? `${summary.win_rate}%` : '—'}
          sub={`${summary.wins}W / ${summary.losses}L`}
          color={summary.win_rate > 50 ? '#00c896' : '#e05252'} />
        <StatCard label="Total P&L"
          value={`${summary.total_pnl >= 0 ? '+' : ''}$${summary.total_pnl.toFixed(0)}`}
          color={pnlColor} />
        <StatCard label="Trades" value={summary.total_trades} />
      </div>

      <EquityCurve points={summary.equity_curve} />

      <div className="pt-breakdowns">
        <BreakdownRow label="By Direction" data={summary.by_direction} />
        <BreakdownRow label="By ETF" data={summary.by_ticker} />
        <BreakdownRow label="By Verdict" data={summary.by_verdict} />
      </div>

      <div className="pt-section-title" style={{ marginTop: 20 }}>
        Open &amp; Closed Trades
        <span className="pt-section-hint"> · Enter current premium → Update mark · or Close trade when done</span>
      </div>
      {summary.trades.map(t => (
        <TradeRow key={t.id} trade={t} onRefresh={load} />
      ))}
    </div>
  );
}
