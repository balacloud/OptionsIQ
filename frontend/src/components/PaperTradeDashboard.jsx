import { useEffect, useState } from 'react';

const DIR_LABELS = {
  buy_call:  'Buy Call',
  sell_call: 'Sell Call',
  buy_put:   'Buy Put',
  sell_put:  'Sell Put',
};

const VERDICT_COLORS = {
  green:  { bg: 'rgba(0,200,150,0.1)',  border: 'rgba(0,200,150,0.3)',  text: '#00c896' },
  yellow: { bg: 'rgba(250,180,50,0.1)', border: 'rgba(250,180,50,0.3)', text: '#f5a623' },
  red:    { bg: 'rgba(220,60,60,0.1)',  border: 'rgba(220,60,60,0.3)',  text: '#e05252' },
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

function TradeRow({ trade }) {
  const pnlColor = trade.pnl == null ? '' : trade.pnl >= 0 ? 'pos' : 'neg';
  const verdictStyle = VERDICT_COLORS[trade.verdict] || {};
  return (
    <div className="pt-trade-row">
      <span className="pt-trade-ticker">{trade.ticker}</span>
      <span className="pt-trade-dir">{DIR_LABELS[trade.direction] || trade.direction}</span>
      <span className="pt-trade-strike">${trade.strike}</span>
      <span className="pt-trade-expiry">{trade.expiry}</span>
      {trade.verdict
        ? <span className="pt-trade-verdict" style={{ color: verdictStyle.text }}>{trade.verdict.toUpperCase()}</span>
        : <span className="pt-trade-verdict">—</span>
      }
      <span className={`pt-trade-pnl ${pnlColor}`}>
        {trade.pnl != null ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(0)}` : '—'}
      </span>
      <span className="pt-trade-date">{trade.created_at?.slice(0, 10)}</span>
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
        <polyline points={pts}
          fill="none"
          stroke={finalPnl >= 0 ? '#00c896' : '#e05252'}
          strokeWidth="2"
          strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export default function PaperTradeDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => {
    fetch('http://localhost:5051/api/options/paper-trades/summary')
      .then(r => r.json())
      .then(d => { setSummary(d); setLoading(false); })
      .catch(() => { setError('Could not load paper trades'); setLoading(false); });
  }, []);

  if (loading) return <div className="pt-loading">Loading paper trades…</div>;
  if (error)   return <div className="pt-error">{error}</div>;

  if (!summary || summary.total_trades === 0) {
    return (
      <div className="pt-empty">
        <div className="pt-empty-icon">📋</div>
        <div className="pt-empty-title">No paper trades recorded yet</div>
        <div className="pt-empty-sub">
          Run an analysis → get a GO verdict → click <strong>Record Paper Trade</strong>.
          <br />Your win rate, P&L, and equity curve will appear here.
        </div>
        <div className="pt-empty-tracked">
          <div className="pt-empty-tracked-title">What gets tracked</div>
          <div className="pt-empty-tracked-items">
            <span>Win rate by direction</span>
            <span>P&L by ETF</span>
            <span>GO vs WAIT verdict accuracy</span>
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
          <div className="pt-header-sub">{summary.total_trades} trades recorded</div>
        </div>
        <div className="pt-persist-badge" title="Trades are stored in SQLite (iv_history.db) and survive restarts">
          ● SQLite — persists across restarts
        </div>
      </div>

      {/* Top stats */}
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

      {/* Equity curve */}
      <EquityCurve points={summary.equity_curve} />

      {/* Breakdown tables */}
      <div className="pt-breakdowns">
        <BreakdownRow label="By Direction" data={summary.by_direction} />
        <BreakdownRow label="By ETF" data={summary.by_ticker} />
        <BreakdownRow label="By Verdict" data={summary.by_verdict} />
      </div>

      {/* Trade list */}
      <div className="pt-section-title" style={{ marginTop: 20 }}>All Trades</div>
      <div className="pt-trade-header">
        <span>Ticker</span><span>Direction</span><span>Strike</span>
        <span>Expiry</span><span>Verdict</span><span>P&L</span><span>Date</span>
      </div>
      {summary.trades.map(t => <TradeRow key={t.id} trade={t} />)}
    </div>
  );
}
