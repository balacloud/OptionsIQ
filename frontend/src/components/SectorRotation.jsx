import { useEffect, useState } from 'react';
import ETFCard from './ETFCard';

function fmt(v, d = 1) {
  if (v == null) return '—';
  const n = Number(v);
  return isNaN(n) ? v : n.toFixed(d);
}

function ETFDetailPanel({ detail, loading, onClose, onDeepDive }) {
  if (loading) {
    return (
      <div className="etf-detail-panel">
        <div className="etf-detail-header">
          <div className="etf-detail-title">Loading...</div>
          <button className="etf-detail-close" onClick={onClose}>✕</button>
        </div>
        <div style={{ padding: 20, color: 'var(--text-dim)' }}>Fetching L2 data...</div>
      </div>
    );
  }
  if (!detail) return null;

  return (
    <div className="etf-detail-panel">
      <div className="etf-detail-header">
        <div>
          <div className="etf-detail-title">{detail.etf} — Level 2 Analysis</div>
          <div className="etf-detail-sub">{detail.name} · {detail.quadrant}</div>
        </div>
        <button className="etf-detail-close" onClick={onClose}>✕</button>
      </div>

      <div className="etf-detail-grid">
        <div className="etf-detail-item">
          <span className="etf-detail-label">Price</span>
          <span className="etf-detail-value monospace">${fmt(detail.price, 2)}</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">RS Ratio</span>
          <span className="etf-detail-value monospace">{fmt(detail.rs_ratio)}</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">RS Momentum</span>
          <span className="etf-detail-value monospace">{fmt(detail.rs_momentum)}</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">IV Current</span>
          <span className="etf-detail-value monospace">{detail.iv_current != null ? `${detail.iv_current}%` : '—'}</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">IV Percentile</span>
          <span className="etf-detail-value monospace">{detail.iv_percentile != null ? `${detail.iv_percentile}%` : '—'}</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">HV 20</span>
          <span className="etf-detail-value monospace">{detail.hv_20 != null ? `${detail.hv_20}%` : '—'}</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">Suggested DTE</span>
          <span className="etf-detail-value monospace">{detail.suggested_dte ?? '—'}d</span>
        </div>
        <div className="etf-detail-item">
          <span className="etf-detail-label">Direction</span>
          <span className="etf-detail-value">{detail.suggested_direction || 'None'}</span>
        </div>
      </div>

      {detail.catalyst_warnings && detail.catalyst_warnings.length > 0 && (
        <div className="etf-detail-warnings">
          {detail.catalyst_warnings.map((w, i) => (
            <div key={i} className="etf-warning">⚠ {w}</div>
          ))}
        </div>
      )}

      {detail.action === 'ANALYZE' && (
        <button className="etf-btn etf-btn-deep etf-detail-deep-btn" onClick={() => onDeepDive(detail)}>
          Full Gate Analysis (L3) →
        </button>
      )}

      {detail.note && (
        <div className="etf-detail-note">{detail.note}</div>
      )}
    </div>
  );
}

export default function SectorRotation({ sectorData, loading, detailLoading, error, etfDetail, onScan, onAnalyzeETF, onClearDetail, onDeepDive }) {
  const [filter, setFilter] = useState('all'); // all, analyze, watch, skip

  useEffect(() => {
    if (!sectorData) onScan();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const sectors = sectorData?.sectors || [];
  const filtered = filter === 'all' ? sectors : sectors.filter(s => s.action === filter.toUpperCase());

  const counts = {
    all: sectors.length,
    analyze: sectors.filter(s => s.action === 'ANALYZE').length,
    watch: sectors.filter(s => s.action === 'WATCH').length,
    skip: sectors.filter(s => s.action === 'SKIP').length,
  };

  return (
    <div className="sector-view">
      {/* Size signal banner */}
      {sectorData?.size_bias && (
        <div className="sector-size-banner">
          <span className="sector-size-label">Cap-Size Signal:</span>
          <span className="sector-size-value">{sectorData.size_signal}</span>
          <span className="sector-size-bias">— {sectorData.size_bias}</span>
        </div>
      )}

      {/* Filter bar + refresh */}
      <div className="sector-toolbar">
        <div className="sector-filters">
          {['all', 'analyze', 'watch', 'skip'].map(f => (
            <button
              key={f}
              className={`sector-filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)} ({counts[f]})
            </button>
          ))}
        </div>
        <button className="sector-refresh-btn" onClick={onScan} disabled={loading}>
          {loading ? 'Scanning...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="error-bar">{error}</div>}

      {loading && !sectorData && (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>
          Scanning 15 ETFs...
        </div>
      )}

      {/* ETF detail panel (L2) */}
      {(etfDetail || detailLoading) && (
        <ETFDetailPanel
          detail={etfDetail}
          loading={detailLoading}
          onClose={onClearDetail}
          onDeepDive={onDeepDive}
        />
      )}

      {/* ETF grid */}
      <div className="etf-grid">
        {filtered.map(etf => (
          <ETFCard
            key={etf.etf}
            etf={etf}
            onAnalyze={(e) => onAnalyzeETF(e.etf)}
            onDeepDive={onDeepDive}
          />
        ))}
      </div>

      {!loading && sectorData && filtered.length === 0 && (
        <div style={{ padding: 30, textAlign: 'center', color: 'var(--text-dim)' }}>
          No ETFs match filter "{filter}"
        </div>
      )}

      {/* STA status footer */}
      {sectorData && (
        <div className="sector-footer">
          STA: {sectorData.sta_status === 'ok' ? '● Connected' : '○ Offline'}
          {sectorData.timestamp && (
            <span className="text-dim"> · {new Date(sectorData.timestamp + 'Z').toLocaleTimeString()}</span>
          )}
        </div>
      )}
    </div>
  );
}
