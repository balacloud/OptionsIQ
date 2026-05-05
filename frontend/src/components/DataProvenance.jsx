import { useState } from 'react';

const API = 'http://localhost:5051';

function StatusDot({ status }) {
  const color = {
    ok: '#00c896', connected: '#00c896', fresh: '#00c896',
    stale: '#f0b429', sparse: '#f0b429', disconnected: '#f0b429', null: '#f0b429',
    empty: '#e53e3e', missing: '#e53e3e', error: '#e53e3e', unavailable: '#888',
  }[status] || '#888';
  return <span style={{ color, fontSize: 14, marginRight: 6 }}>●</span>;
}

function SourceCard({ label, icon, children }) {
  return (
    <div className="dp-source-card">
      <div className="dp-source-label">{icon} {label}</div>
      <div className="dp-source-body">{children}</div>
    </div>
  );
}

function Row({ label, value, status }) {
  return (
    <div className="dp-row">
      <span className="dp-row-label">{label}</span>
      <span className="dp-row-value">
        {status && <StatusDot status={status} />}
        {value ?? <span className="dp-null">null</span>}
      </span>
    </div>
  );
}

function BatchStatusPanel({ batch }) {
  if (!batch) return null;
  const runs = batch.recent_runs || [];

  function fmtTime(iso) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short'
      });
    } catch { return iso; }
  }

  function statusColor(s) {
    if (s === 'ok') return '#00c896';
    if (s === 'partial') return '#f0b429';
    return '#e53e3e';
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <div className="dp-section-title">
        Batch Schedule
        <span className="dp-section-note"> — auto-runs Mon-Fri via APScheduler</span>
      </div>
      <div style={{ display: 'flex', gap: 24, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ background: '#1a1f2e', borderRadius: 8, padding: '10px 18px' }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>NEXT BOD (9:31 AM ET)</div>
          <div style={{ fontWeight: 600, color: '#00c896' }}>{fmtTime(batch.next_bod)}</div>
        </div>
        <div style={{ background: '#1a1f2e', borderRadius: 8, padding: '10px 18px' }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>NEXT EOD (4:05 PM ET)</div>
          <div style={{ fontWeight: 600, color: '#00c896' }}>{fmtTime(batch.next_eod)}</div>
        </div>
      </div>

      {runs.length === 0 ? (
        <div style={{ color: '#888', fontSize: 13, padding: '8px 0' }}>
          No batch runs logged yet — BOD/EOD will fire automatically on schedule.
        </div>
      ) : (
        <table className="dp-table">
          <thead>
            <tr>
              <th>Type</th><th>Ran At</th><th>Status</th>
              <th>OK</th><th>Failed</th><th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r, i) => (
              <tr key={i} className="dp-table-row">
                <td style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: 12 }}>{r.batch_type}</td>
                <td>{fmtTime(r.ran_at)}</td>
                <td>
                  <span style={{ color: statusColor(r.status), fontWeight: 600 }}>
                    {r.status === 'ok' ? '✓' : r.status === 'partial' ? '⚠' : '✗'} {r.status}
                  </span>
                </td>
                <td style={{ color: '#00c896' }}>{r.tickers_ok}</td>
                <td style={{ color: r.tickers_failed > 0 ? '#e53e3e' : '#888' }}>{r.tickers_failed}</td>
                <td style={{ color: '#888' }}>{r.duration_sec != null ? `${r.duration_sec}s` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function IVCoverageGrid({ ivh, cc }) {
  const tickers = Object.keys(ivh).sort();

  function coverageColor(pct) {
    if (pct >= 95) return '#00c896';
    if (pct >= 60) return '#f0b429';
    return '#e53e3e';
  }

  function coverageBar(pct) {
    const filled = Math.round(pct / 10);
    return '█'.repeat(filled) + '░'.repeat(10 - filled);
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <div className="dp-section-title">
        IV Store Coverage
        <span className="dp-section-note"> — 252 days needed for valid IVR gate</span>
      </div>
      <table className="dp-table">
        <thead>
          <tr>
            <th>ETF</th><th>Days</th><th>Coverage</th><th>IVR Valid</th>
            <th>Last Seed</th><th>OHLCV</th><th>HV-20</th><th>Chain Cache</th>
          </tr>
        </thead>
        <tbody>
          {tickers.map(t => {
            const h = ivh[t] || {};
            const c = cc[t] || {};
            const days = h.rows || 0;
            const pct = Math.min(Math.round(days / 252 * 100), 100);
            const ivrValid = days >= 30;
            return (
              <tr key={t} className="dp-table-row">
                <td className="dp-ticker">{t}</td>
                <td style={{ color: coverageColor(pct), fontWeight: 600 }}>{days}</td>
                <td style={{ fontFamily: 'monospace', fontSize: 11 }}>
                  <span style={{ color: coverageColor(pct) }}>{coverageBar(pct)}</span>
                  <span style={{ color: '#888', marginLeft: 6 }}>{pct}%</span>
                </td>
                <td>
                  {ivrValid
                    ? <span style={{ color: '#00c896', fontWeight: 600 }}>✓ valid</span>
                    : <span style={{ color: '#e53e3e', fontWeight: 600 }}>✗ need seed</span>}
                </td>
                <td style={{ color: '#888', fontSize: 12 }}>{h.last_date ?? '—'}</td>
                <td style={{ color: h.ohlcv_rows >= 21 ? '#00c896' : '#e53e3e' }}>
                  {h.ohlcv_rows ?? 0}
                </td>
                <td>
                  {h.hv_20 != null
                    ? <span style={{ color: '#00c896' }}>{h.hv_20}%</span>
                    : <span style={{ color: '#e53e3e' }}>—</span>}
                </td>
                <td>
                  <StatusDot status={c.status || 'missing'} />
                  <span style={{ color: '#888', fontSize: 12 }}>
                    {c.status === 'fresh' ? `${c.age_minutes}m ago` : c.status || 'missing'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DataFlowDiagram() {
  return (
    <div style={{ marginBottom: 28 }}>
      <div className="dp-section-title">
        Data Flow Architecture
        <span className="dp-section-note"> — how data moves from sources to verdict</span>
      </div>
      <div style={{ background: '#0d1117', borderRadius: 10, padding: '16px 8px', overflowX: 'auto' }}>
        <svg viewBox="0 0 860 430" style={{ width: '100%', minWidth: 580, display: 'block' }}>
          <defs>
            <marker id="dfa-a" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#64748b" />
            </marker>
            <marker id="dfa-g" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#10b981" />
            </marker>
            <marker id="dfa-o" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#f97316" />
            </marker>
            <marker id="dfa-b" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#38bdf8" />
            </marker>
          </defs>

          {/* ── section labels ── */}
          <text x="210" y="16" textAnchor="middle" fill="#475569" fontSize="10" fontWeight="700" letterSpacing="2">LIVE ANALYSIS FLOW</text>
          <text x="645" y="16" textAnchor="middle" fill="#475569" fontSize="10" fontWeight="700" letterSpacing="2">BATCH / NIGHTLY FLOW</text>
          <line x1="435" y1="22" x2="435" y2="410" stroke="#1e293b" strokeWidth="1" strokeDasharray="5,5" />

          {/* ══════════ LEFT: LIVE ANALYSIS ══════════ */}

          {/* 1. User trigger */}
          <rect x="80" y="24" width="260" height="30" rx="6" fill="#4c1d95" />
          <text x="210" y="44" textAnchor="middle" fill="#ede9fe" fontSize="12" fontWeight="600">User: Analyze ETF</text>

          <line x1="210" y1="54" x2="210" y2="72" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          {/* 2. Provider row */}
          <rect x="48" y="76" width="88" height="30" rx="4" fill="#1e40af" />
          <text x="92" y="87" textAnchor="middle" fill="#bfdbfe" fontSize="11" fontWeight="600">IBKR</text>
          <text x="92" y="100" textAnchor="middle" fill="#93c5fd" fontSize="9">primary</text>

          <rect x="144" y="76" width="80" height="30" rx="4" fill="#065f46" />
          <text x="184" y="87" textAnchor="middle" fill="#a7f3d0" fontSize="11" fontWeight="600">Alpaca</text>
          <text x="184" y="100" textAnchor="middle" fill="#6ee7b7" fontSize="9">fallback</text>

          <rect x="232" y="76" width="84" height="30" rx="4" fill="#374151" />
          <text x="274" y="87" textAnchor="middle" fill="#d1d5db" fontSize="11" fontWeight="600">yfinance</text>
          <text x="274" y="100" textAnchor="middle" fill="#9ca3af" fontSize="9">OHLCV only</text>

          {/* STA — side feed (dashed blue) */}
          <rect x="326" y="76" width="90" height="30" rx="4" fill="#0c4a6e" />
          <text x="371" y="87" textAnchor="middle" fill="#bae6fd" fontSize="11" fontWeight="600">STA</text>
          <text x="371" y="100" textAnchor="middle" fill="#7dd3fc" fontSize="9">Price / VIX / SPY</text>

          {/* converging arrows to DataService */}
          <line x1="92"  y1="106" x2="176" y2="148" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="184" y1="106" x2="202" y2="148" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="274" y1="106" x2="238" y2="148" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="348" y1="106" x2="275" y2="154" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="4,3" markerEnd="url(#dfa-b)" />

          {/* 3. DataService Cascade */}
          <rect x="110" y="152" width="200" height="28" rx="4" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="210" y="171" textAnchor="middle" fill="#e2e8f0" fontSize="11" fontWeight="600">DataService Cascade</text>

          {/* MD.app supplement — dashed orange */}
          <rect x="326" y="154" width="100" height="24" rx="4" fill="#7c2d12" />
          <text x="376" y="163" textAnchor="middle" fill="#fed7aa" fontSize="10" fontWeight="600">MD.app (free)</text>
          <text x="376" y="174" textAnchor="middle" fill="#fdba74" fontSize="9">OI / Vol / SpotIV</text>
          <line x1="326" y1="166" x2="311" y2="166" stroke="#f97316" strokeWidth="1.5" strokeDasharray="3,2" markerEnd="url(#dfa-o)" />

          <line x1="210" y1="180" x2="210" y2="200" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          {/* 4. iv_store.db — IVR */}
          <rect x="100" y="204" width="220" height="28" rx="4" fill="#78350f" />
          <text x="210" y="223" textAnchor="middle" fill="#fef3c7" fontSize="11" fontWeight="600">iv_store.db  ·  IVR (252 days)</text>

          <line x1="210" y1="232" x2="210" y2="252" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          {/* 5. gate_engine */}
          <rect x="100" y="256" width="220" height="28" rx="4" fill="#1e3a8a" />
          <text x="210" y="275" textAnchor="middle" fill="#bfdbfe" fontSize="11" fontWeight="600">gate_engine()</text>

          <line x1="210" y1="284" x2="210" y2="306" stroke="#10b981" strokeWidth="2" markerEnd="url(#dfa-g)" />

          {/* 6. MasterVerdict */}
          <rect x="88" y="310" width="244" height="38" rx="19" fill="#064e3b" stroke="#10b981" strokeWidth="1.5" />
          <text x="210" y="324" textAnchor="middle" fill="#6ee7b7" fontSize="12" fontWeight="700">MasterVerdict</text>
          <text x="210" y="340" textAnchor="middle" fill="#34d399" fontSize="10">GO  ·  CAUTION  ·  BLOCK</text>

          {/* ══════════ RIGHT: BATCH FLOW ══════════ */}

          {/* 1. APScheduler */}
          <rect x="535" y="24" width="220" height="30" rx="6" fill="#3b0764" />
          <text x="645" y="44" textAnchor="middle" fill="#e9d5ff" fontSize="12" fontWeight="600">APScheduler  Mon – Fri</text>

          {/* fork */}
          <line x1="645" y1="54" x2="645" y2="70" stroke="#64748b" strokeWidth="1.5" />
          <line x1="568" y1="70" x2="722" y2="70" stroke="#64748b" strokeWidth="1.5" />
          <line x1="568" y1="70" x2="568" y2="82" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="722" y1="70" x2="722" y2="82" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          {/* BOD */}
          <rect x="508" y="86" width="120" height="34" rx="5" fill="#1e3a5f" />
          <text x="568" y="99"  textAnchor="middle" fill="#bfdbfe" fontSize="12" fontWeight="700">BOD</text>
          <text x="568" y="113" textAnchor="middle" fill="#93c5fd" fontSize="10">9:31 AM ET</text>

          {/* EOD */}
          <rect x="662" y="86" width="120" height="34" rx="5" fill="#1e3a5f" />
          <text x="722" y="99"  textAnchor="middle" fill="#bfdbfe" fontSize="12" fontWeight="700">EOD</text>
          <text x="722" y="113" textAnchor="middle" fill="#93c5fd" fontSize="10">4:05 PM ET</text>

          <line x1="568" y1="120" x2="568" y2="148" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="722" y1="120" x2="722" y2="148" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          {/* actions */}
          <rect x="488" y="152" width="160" height="24" rx="4" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />
          <text x="568" y="168" textAnchor="middle" fill="#94a3b8" fontSize="10">Pre-warm 16 ETF chains</text>

          <rect x="642" y="152" width="160" height="24" rx="4" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />
          <text x="722" y="168" textAnchor="middle" fill="#94a3b8" fontSize="10">Seed IV history + OHLCV</text>

          <line x1="568" y1="176" x2="568" y2="200" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="722" y1="176" x2="722" y2="200" stroke="#64748b" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          {/* databases */}
          <rect x="488" y="204" width="160" height="28" rx="4" fill="#713f12" />
          <text x="568" y="223" textAnchor="middle" fill="#fef3c7" fontSize="11" fontWeight="600">chain_cache.db</text>

          <rect x="642" y="204" width="160" height="28" rx="4" fill="#78350f" />
          <text x="722" y="223" textAnchor="middle" fill="#fef3c7" fontSize="11" fontWeight="600">iv_store.db</text>

          {/* converge to startup_catchup */}
          <line x1="568" y1="232" x2="620" y2="276" stroke="#475569" strokeWidth="1.5" markerEnd="url(#dfa-a)" />
          <line x1="722" y1="232" x2="676" y2="276" stroke="#475569" strokeWidth="1.5" markerEnd="url(#dfa-a)" />

          <rect x="534" y="280" width="224" height="34" rx="5" fill="#1e293b" stroke="#334155" strokeWidth="1" />
          <text x="646" y="293" textAnchor="middle" fill="#94a3b8" fontSize="11" fontWeight="600">run_startup_catchup()</text>
          <text x="646" y="307" textAnchor="middle" fill="#64748b" fontSize="10">fills missed jobs on boot</text>

          {/* ── legend ── */}
          <g transform="translate(450, 372)">
            <text x="2" y="0" fill="#334155" fontSize="10" fontWeight="700" letterSpacing="1">LEGEND</text>
            {[
              { fill: '#4c1d95', label: 'Trigger' },
              { fill: '#1e40af', label: 'Data Source' },
              { fill: '#78350f', label: 'SQLite DB' },
              { fill: '#1e3a8a', label: 'Processing' },
              { fill: '#064e3b', label: 'Output' },
              { fill: '#7c2d12', label: 'Supplement' },
            ].map(({ fill, label }, i) => (
              <g key={i} transform={`translate(${i * 68}, 14)`}>
                <rect width="10" height="10" rx="2" fill={fill} />
                <text x="14" y="10" fill="#475569" fontSize="10">{label}</text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}

export default function DataProvenance() {
  const [data, setData] = useState(null);
  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [checkedAt, setCheckedAt] = useState(null);

  async function runCheck() {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, batchRes] = await Promise.all([
        fetch(`${API}/api/data-health`),
        fetch(`${API}/api/admin/batch-status`),
      ]);
      if (!healthRes.ok) throw new Error(`data-health HTTP ${healthRes.status}`);
      const json = await healthRes.json();
      setData(json);
      if (batchRes.ok) setBatch(await batchRes.json());
      setCheckedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const src = data?.sources || {};
  const ivh = data?.iv_history || {};
  const cc = data?.chain_cache || {};
  const tickers = Object.keys(ivh).sort();

  return (
    <div className="dp-wrap">
      <div className="dp-header">
        <div>
          <h2 className="dp-title">Data Provenance</h2>
          {checkedAt && <div className="dp-sub">Checked at {checkedAt}</div>}
        </div>
        <button className="dp-check-btn" onClick={runCheck} disabled={loading}>
          {loading ? 'Checking…' : '⟳ Check Health'}
        </button>
      </div>

      {error && <div className="dp-error">Error: {error}</div>}

      <DataFlowDiagram />

      {!data && !loading && (
        <div className="dp-idle">
          <div className="dp-idle-icon">🔍</div>
          <div className="dp-idle-text">Click Check Health to inspect all data sources</div>
          <div className="dp-idle-sub">No IBKR calls — reads cached state only</div>
        </div>
      )}

      {loading && <div className="dp-loading">Checking data sources…</div>}

      {data && (
        <>
          {/* ── Batch Schedule ───────────────────────────────────────── */}
          <BatchStatusPanel batch={batch} />

          {/* ── IV Coverage Grid ─────────────────────────────────────── */}
          <IVCoverageGrid ivh={data?.iv_history || {}} cc={data?.chain_cache || {}} />

          {/* ── Sources ──────────────────────────────────────────────── */}
          <div className="dp-section-title">Data Sources</div>
          <div className="dp-sources-grid">

            <SourceCard label="IBKR Gateway" icon="📡">
              <Row label="Status" value={src.ibkr?.status} status={src.ibkr?.status} />
              <Row label="Mode" value={src.ibkr?.mode} />
              {src.ibkr?.error && <Row label="Error" value={src.ibkr.error} status="error" />}
              <Row
                label="Circuit Breaker"
                value={src.ibkr?.circuit_breaker?.open
                  ? `OPEN — ${src.ibkr.circuit_breaker.seconds_remaining}s remaining`
                  : `closed (${src.ibkr?.circuit_breaker?.failures} failures)`}
                status={src.ibkr?.circuit_breaker?.open ? 'error' : 'ok'}
              />
            </SourceCard>

            <SourceCard label="VIX" icon="📊">
              <Row label="Status" value={src.vix?.status} status={src.vix?.status} />
              <Row label="Value" value={src.vix?.value != null ? src.vix.value.toFixed(2) : null} />
              <Row label="Source" value={src.vix?.source} />
              <Row label="Age" value={src.vix?.age_seconds != null ? `${src.vix.age_seconds}s` : null} />
            </SourceCard>

            <SourceCard label="SPY Regime" icon="📈">
              <Row label="Status" value={src.spy_regime?.status} status={src.spy_regime?.status} />
              <Row
                label="Above 200 SMA"
                value={src.spy_regime?.above_200sma != null ? String(src.spy_regime.above_200sma) : null}
                status={src.spy_regime?.above_200sma ? 'ok' : src.spy_regime?.above_200sma === false ? 'stale' : null}
              />
              <Row
                label="5-Day Return"
                value={src.spy_regime?.five_day_return != null ? `${src.spy_regime.five_day_return}%` : null}
              />
              <Row label="Source" value={src.spy_regime?.source} />
            </SourceCard>

            <SourceCard label="FOMC" icon="🏛️">
              <Row label="Status" value={src.fomc?.status} status={src.fomc?.status} />
              <Row label="Next Date" value={src.fomc?.next_date} />
              <Row
                label="Days Away"
                value={src.fomc?.days_away}
                status={src.fomc?.days_away <= 5 ? 'error' : src.fomc?.days_away <= 14 ? 'stale' : 'ok'}
              />
              <Row label="Source" value={src.fomc?.source} />
            </SourceCard>

            <SourceCard label="Alpaca" icon="🦙">
              <Row label="Status" value={src.alpaca?.status} status={src.alpaca?.status} />
            </SourceCard>

            <SourceCard label="MarketData.app" icon="📦">
              <Row label="Status" value={src.marketdata_app?.status} status={src.marketdata_app?.status} />
            </SourceCard>

          </div>

          {/* ── IV History ───────────────────────────────────────────── */}
          <div className="dp-section-title">IV History Database <span className="dp-section-note">(iv_history.db)</span></div>
          <table className="dp-table">
            <thead>
              <tr>
                <th>ETF</th><th>Status</th><th>IV Rows</th><th>First Date</th><th>Last Date</th>
                <th>HV-20</th><th>HV Status</th><th>OHLCV Rows</th>
              </tr>
            </thead>
            <tbody>
              {tickers.map(t => {
                const h = ivh[t] || {};
                return (
                  <tr key={t} className="dp-table-row">
                    <td className="dp-ticker">{t}</td>
                    <td><StatusDot status={h.status} />{h.status}</td>
                    <td>{h.rows ?? <span className="dp-null">—</span>}</td>
                    <td>{h.first_date ?? <span className="dp-null">—</span>}</td>
                    <td>{h.last_date ?? <span className="dp-null">—</span>}</td>
                    <td>{h.hv_20 != null ? `${h.hv_20}%` : <span className="dp-null">—</span>}</td>
                    <td><StatusDot status={h.hv_status === 'ok' ? 'ok' : 'stale'} />{h.hv_status}</td>
                    <td>{h.ohlcv_rows ?? <span className="dp-null">—</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* ── Field-Level Resolution ───────────────────────────── */}
          <div className="dp-section-title">
            Field-Level Data Source
            <span className="dp-section-note"> — where each analysis field comes from, right now</span>
          </div>
          <div className="dp-field-note">
            Fields below are resolved in the order shown. First available source wins.
            "stale" means data exists but may be outdated. "null" means no data — gate will fail or skip.
          </div>
          {tickers.map(t => {
            const fr = (data?.field_resolution || {})[t] || {};
            const FIELDS = [
              { key: 'underlying_price',  label: 'Underlying Price' },
              { key: 'chain_implied_vol', label: 'Chain / Implied Vol' },
              { key: 'oi_volume',         label: 'OI / Volume' },
              { key: 'hv_20',             label: 'HV-20 (Hist. Vol)' },
              { key: 'ivr',               label: 'IVR (IV Rank)' },
              { key: 'vix',               label: 'VIX' },
              { key: 'spy_regime',        label: 'SPY Regime' },
              { key: 'fomc',              label: 'FOMC Event' },
            ];
            return (
              <div key={t} className="dp-fr-block">
                <div className="dp-fr-ticker">{t}</div>
                <table className="dp-table dp-fr-table">
                  <thead>
                    <tr><th>Field</th><th>Source</th><th>Status</th><th>Note</th></tr>
                  </thead>
                  <tbody>
                    {FIELDS.map(({ key, label }) => {
                      const f = fr[key] || {};
                      return (
                        <tr key={key} className="dp-table-row">
                          <td className="dp-fr-field">{label}</td>
                          <td className="dp-fr-source">{f.source ?? <span className="dp-null">—</span>}</td>
                          <td><StatusDot status={f.status} />{f.status ?? '—'}</td>
                          <td className="dp-fr-note">{f.note ?? ''}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            );
          })}

          {/* ── Chain Cache ──────────────────────────────────────────── */}
          <div className="dp-section-title">Chain Cache <span className="dp-section-note">(chain_cache.db)</span></div>
          <table className="dp-table">
            <thead>
              <tr>
                <th>ETF</th><th>Status</th><th>Saved At (UTC)</th><th>Age (min)</th><th>Expires In (min)</th><th>Entries</th>
              </tr>
            </thead>
            <tbody>
              {tickers.map(t => {
                const c = cc[t] || {};
                return (
                  <tr key={t} className="dp-table-row">
                    <td className="dp-ticker">{t}</td>
                    <td><StatusDot status={c.status || 'missing'} />{c.status || 'missing'}</td>
                    <td>{c.saved_at ?? <span className="dp-null">—</span>}</td>
                    <td>{c.age_minutes ?? <span className="dp-null">—</span>}</td>
                    <td>{c.expires_in_minutes ?? <span className="dp-null">—</span>}</td>
                    <td>{c.entries ?? <span className="dp-null">—</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
