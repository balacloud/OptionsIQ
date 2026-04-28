import { useEffect, useState } from 'react';

const DIR_LABELS = {
  buy_call:  'Buy Call',
  sell_call: 'Sell Call',
  buy_put:   'Buy Put',
  sell_put:  'Sell Put',
};

const VERDICT_STYLE = {
  green:  { bg: 'rgba(0,200,150,0.12)',  border: 'rgba(0,200,150,0.35)',  badge: '#00c896', label: 'GO' },
  yellow: { bg: 'rgba(250,180,50,0.10)', border: 'rgba(250,180,50,0.35)', badge: '#f5a623', label: 'CAUTION' },
  red:    { bg: 'rgba(220,60,60,0.10)',  border: 'rgba(220,60,60,0.35)',  badge: '#e05252', label: 'BLOCKED' },
};

function SetupCard({ s, onSelect }) {
  const vs = VERDICT_STYLE[s.verdict_color] || VERDICT_STYLE.yellow;
  const cwOk = s.credit_to_width_ratio != null && s.credit_to_width_ratio >= 0.33;
  const clickable = !!onSelect;

  return (
    <div
      className={`bs-card ${clickable ? 'bs-card-clickable' : ''}`}
      style={{ background: vs.bg, borderColor: vs.border }}
      onClick={clickable ? () => onSelect(s.ticker, s.direction) : undefined}
      title={clickable ? `Analyze ${s.ticker} ${DIR_LABELS[s.direction]}` : undefined}
    >
      <div className="bs-card-top">
        <div className="bs-ticker">{s.ticker}</div>
        <div className="bs-dir">{DIR_LABELS[s.direction] || s.direction}</div>
        <div className="bs-badge" style={{ background: vs.badge }}>{vs.label}</div>
      </div>

      <div className="bs-meta">
        {s.quadrant && <span className="bs-quad">{s.quadrant}</span>}
        {s.strike_display && <span>Strike: <strong>{s.strike_display}</strong></span>}
        {s.expiry_display && <span>Exp: {s.expiry_display?.slice(0, 10)}</span>}
        {s.premium_per_lot != null && <span>Premium: <strong>${s.premium_per_lot}/lot</strong></span>}
      </div>

      <div className="bs-stats">
        <div className="bs-stat">
          <span className="bs-stat-label">Gates</span>
          <span className="bs-stat-val">{s.gates_passed}/{s.gates_total}</span>
        </div>
        <div className="bs-stat">
          <span className="bs-stat-label">IVR</span>
          <span className="bs-stat-val">{s.ivr != null ? `${Number(s.ivr).toFixed(0)}%` : '—'}</span>
        </div>
        {s.credit_to_width_ratio != null && (
          <div className="bs-stat">
            <span className="bs-stat-label">Cr/Width</span>
            <span className="bs-stat-val" style={{ color: cwOk ? '#00c896' : '#e05252' }}>
              {(s.credit_to_width_ratio * 100).toFixed(0)}%
            </span>
          </div>
        )}
        <div className="bs-stat">
          <span className="bs-stat-label">Pass</span>
          <span className="bs-stat-val">{s.pass_rate}%</span>
        </div>
      </div>

      {clickable && (
        <div className="bs-card-cta">Analyze → Paper Trade</div>
      )}
    </div>
  );
}

export default function BestSetups({ onSelect }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [ts, setTs]           = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetch('http://localhost:5051/api/best-setups')
      .then(r => r.json())
      .then(d => {
        setData(d);
        setTs(new Date().toLocaleTimeString());
        setLoading(false);
      })
      .catch(() => {
        setError('Could not load setups — is the backend running?');
        setLoading(false);
      });
  };

  // Auto-scan on first mount — this is the home screen
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return (
    <div className="bs-loading">
      <div className="bs-spinner" />
      <div>Scanning ETFs across suggested directions…<br />
        <span style={{ fontSize: 12, opacity: 0.6 }}>Usually 20–40 seconds with IBKR live</span>
      </div>
    </div>
  );

  const setups = data?.setups || [];
  const allResults = (data?.all_results || []).filter(r => !r.error);
  const go = setups.filter(s => s.verdict_color === 'green');
  const caution = setups.filter(s => s.verdict_color === 'yellow');
  const blocked = allResults
    .filter(r => r.verdict_color === 'red' || (!r.verdict_color && r.gates_total > 0))
    .sort((a, b) => (b.pass_rate ?? 0) - (a.pass_rate ?? 0));

  // Pre-scan idle state
  if (!data && !error) return (
    <div className="bs-wrap">
      <div className="bs-idle">
        <div className="bs-idle-title">Best Setups Scanner</div>
        <div className="bs-idle-sub">
          Scans all ETFs using their sector-suggested direction and runs full gate analysis.
          Hits IBKR live — takes 20–40 seconds.
        </div>
        <button className="bs-run-btn" onClick={load}>Run Scan</button>
        <div className="bs-idle-note">Only run when markets are open and IB Gateway is connected.</div>
      </div>
    </div>
  );

  if (error) return (
    <div className="bs-wrap">
      <div className="bs-error">{error}</div>
      <div style={{ textAlign: 'center', marginTop: 12 }}>
        <button className="bs-run-btn" onClick={load}>Retry</button>
      </div>
    </div>
  );

  return (
    <div className="bs-wrap">
      <div className="bs-header">
        <div>
          <div className="bs-title">Best Setups</div>
          <div className="bs-sub">
            {data?.candidates_scanned ?? 0} ETFs scanned · {ts && `as of ${ts}`}
          </div>
        </div>
        <button className="bs-refresh" onClick={load}>↻ Refresh</button>
      </div>

      {setups.length === 0 && (
        <div className="bs-empty">
          <div className="bs-empty-icon">⏸</div>
          <div className="bs-empty-title">No GO or CAUTION setups right now</div>
          <div className="bs-empty-sub">
            All {data?.candidates_scanned ?? 0} scanned ETFs are currently blocked.
            This is normal before FOMC or earnings clusters.
          </div>
        </div>
      )}

      {go.length > 0 && (
        <div className="bs-section">
          <div className="bs-section-title" style={{ color: '#00c896' }}>GO — Ready to Trade</div>
          <div className="bs-grid">
            {go.map(s => <SetupCard key={`${s.ticker}-${s.direction}`} s={s} onSelect={onSelect} />)}
          </div>
        </div>
      )}

      {caution.length > 0 && (
        <div className="bs-section">
          <div className="bs-section-title" style={{ color: '#f5a623' }}>CAUTION — Review Before Trading</div>
          <div className="bs-grid">
            {caution.map(s => <SetupCard key={`${s.ticker}-${s.direction}`} s={s} onSelect={onSelect} />)}
          </div>
        </div>
      )}

      {/* Watchlist — nearest to GO even when blocked */}
      {blocked.length > 0 && (
        <div className="bs-section">
          <div className="bs-section-title" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Watchlist — Closest to GO When Event Clears
          </div>
          <div className="bs-watch-table">
            <div className="bs-watch-header">
              <span>ETF</span><span>Direction</span><span>Gates</span><span>IVR</span><span>Quadrant</span><span>Why Blocked</span>
            </div>
            {blocked.slice(0, 8).map(s => {
              const failedGates = (s.failed_gates || []).join(', ');
              return (
                <div key={`${s.ticker}-${s.direction}`} className="bs-watch-row">
                  <span className="bs-watch-ticker">{s.ticker}</span>
                  <span className="bs-watch-dir">{DIR_LABELS[s.direction] || s.direction}</span>
                  <span className="bs-watch-gates">
                    <span style={{ color: s.pass_rate >= 70 ? '#f5a623' : '#e05252' }}>
                      {s.gates_passed}/{s.gates_total}
                    </span>
                  </span>
                  <span className="bs-watch-ivr">{s.ivr != null ? `${Number(s.ivr).toFixed(0)}%` : '—'}</span>
                  <span className="bs-watch-quad">{s.quadrant || '—'}</span>
                  <span className="bs-watch-reason">
                    {(s.failed_gates || []).length > 0 ? (s.failed_gates || []).join(', ') : (s.verdict_label || 'BLOCKED')}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
