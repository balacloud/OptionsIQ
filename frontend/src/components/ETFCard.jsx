const QUADRANT_COLORS = {
  Leading:   'green',
  Improving: 'blue',
  Weakening: 'amber',
  Lagging:   'red',
};

const ACTION_LABELS = {
  ANALYZE: { text: 'Analyze', cls: 'etf-action-analyze' },
  WATCH:   { text: 'Watch',   cls: 'etf-action-watch' },
  SKIP:    { text: 'Skip',    cls: 'etf-action-skip' },
};

const DIR_LABELS = {
  buy_call:         'Buy Call',
  bull_call_spread: 'Bull Call Spread',
  sell_call:        'Sell Call',
  buy_put:          'Buy Put',
  sell_put:         'Sell Put',
};

function fmt(v, decimals = 1) {
  if (v == null) return '—';
  const n = Number(v);
  return isNaN(n) ? v : n.toFixed(decimals);
}

function pctClass(v) {
  if (v == null) return 'text-dim';
  return v >= 0 ? 'text-green' : 'text-red';
}

export default function ETFCard({ etf, onAnalyze, onDeepDive }) {
  const color = QUADRANT_COLORS[etf.quadrant] || 'text-dim';
  const action = ACTION_LABELS[etf.action] || ACTION_LABELS.SKIP;
  const dirLabel = etf.suggested_direction ? DIR_LABELS[etf.suggested_direction] || etf.suggested_direction : null;

  return (
    <div className={`etf-card etf-card-${color}`}>
      <div className="etf-card-top">
        <div className="etf-ticker">{etf.etf}</div>
        <span className={`etf-quadrant-badge badge-${color}`}>{etf.quadrant}</span>
      </div>

      <div className="etf-name">{etf.name}</div>

      <div className="etf-metrics">
        <div className="etf-metric">
          <span className="etf-metric-label">Price</span>
          <span className="etf-metric-value monospace">{etf.price != null ? `$${fmt(etf.price, 2)}` : '—'}</span>
        </div>
        <div className="etf-metric">
          <span className="etf-metric-label">RS Ratio</span>
          <span className={`etf-metric-value monospace ${etf.rs_ratio >= 100 ? 'text-green' : 'text-red'}`}>
            {fmt(etf.rs_ratio)}
          </span>
        </div>
        <div className="etf-metric">
          <span className="etf-metric-label">1W</span>
          <span className={`etf-metric-value monospace ${pctClass(etf.week_change)}`}>
            {etf.week_change != null ? `${etf.week_change >= 0 ? '+' : ''}${fmt(etf.week_change)}%` : '—'}
          </span>
        </div>
        <div className="etf-metric">
          <span className="etf-metric-label">1M</span>
          <span className={`etf-metric-value monospace ${pctClass(etf.month_change)}`}>
            {etf.month_change != null ? `${etf.month_change >= 0 ? '+' : ''}${fmt(etf.month_change)}%` : '—'}
          </span>
        </div>
      </div>

      {dirLabel && (
        <div className="etf-direction">
          <span className="etf-direction-label">Direction:</span>
          <span className={`etf-direction-value badge-${color}`}>{dirLabel}</span>
        </div>
      )}

      {etf.catalyst_warnings && etf.catalyst_warnings.length > 0 && (
        <div className="etf-warnings">
          {etf.catalyst_warnings.map((w, i) => (
            <div key={i} className="etf-warning">⚠ {w}</div>
          ))}
        </div>
      )}

      <div className="etf-card-actions">
        {etf.action === 'ANALYZE' ? (
          <>
            <button className="etf-btn etf-btn-analyze" onClick={() => onAnalyze && onAnalyze(etf)}>
              L2 Detail
            </button>
            <button className="etf-btn etf-btn-deep" onClick={() => onDeepDive && onDeepDive(etf)}>
              Deep Dive →
            </button>
          </>
        ) : (
          <span className={`etf-action-label ${action.cls}`}>{action.text}</span>
        )}
      </div>
    </div>
  );
}
