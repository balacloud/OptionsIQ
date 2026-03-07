import { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5051';

// Human-readable labels for every swing field
const FIELD_META = {
  entry_pullback:     { label: 'Entry Pullback',     type: 'number', section: 'Entry' },
  entry_momentum:     { label: 'Entry Momentum',     type: 'number', section: 'Entry' },
  last_close:         { label: 'Last Close',         type: 'number', section: 'Entry' },
  stop_loss:          { label: 'Stop Loss',          type: 'number', section: 'Risk' },
  target1:            { label: 'Target 1',           type: 'number', section: 'Risk' },
  target2:            { label: 'Target 2',           type: 'number', section: 'Risk' },
  risk_reward:        { label: 'Risk / Reward',      type: 'number', section: 'Risk' },
  s1_support:         { label: 'S1 Support',         type: 'number', section: 'Risk' },
  vcp_pivot:          { label: 'VCP Pivot',          type: 'number', section: 'Pattern' },
  vcp_confidence:     { label: 'VCP Confidence %',  type: 'number', section: 'Pattern' },
  adx:                { label: 'ADX',                type: 'number', section: 'Pattern' },
  earnings_days_away: { label: 'Earnings Days Away', type: 'number', section: 'Calendar' },
  fomc_days_away:     { label: 'FOMC Days Away',     type: 'number', section: 'Calendar' },
  spy_5day_return:    { label: 'SPY 5-Day Return %', type: 'number', section: 'Market' },
};

const SECTIONS = ['Entry', 'Risk', 'Pattern', 'Calendar', 'Market'];

export default function SwingImportStrip({ swing, setSwing, ticker }) {
  const [open, setOpen]       = useState(false);
  const [staLive, setStaLive] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [staError, setStaError]     = useState(null);

  const connectSta = async () => {
    if (!ticker?.trim()) { setStaError('Enter a ticker first.'); return; }
    setConnecting(true);
    setStaError(null);
    try {
      const res = await fetch(`${API_BASE}/api/integrate/sta-fetch/${ticker.trim().toUpperCase()}`);
      if (!res.ok) throw new Error(`STA returned ${res.status}`);
      const json = await res.json();
      if (json?.status === 'ok') {
        setSwing((s) => ({ ...s, ...json }));
        setStaLive(true);
      } else {
        throw new Error(json?.message || json?.error || 'STA returned no data');
      }
    } catch (e) {
      setStaError(`STA offline — use Manual mode. (${e.message})`);
      setStaLive(false);
    } finally {
      setConnecting(false);
    }
  };

  const updateField = (key, raw) => {
    const meta = FIELD_META[key];
    const value = meta?.type === 'number'
      ? (raw === '' ? '' : Number(raw))
      : raw;
    setSwing((s) => ({ ...s, [key]: value }));
  };

  return (
    <div className="collapsible">
      <div className="collapsible-header" onClick={() => setOpen((o) => !o)}>
        <div className="collapsible-title">
          Swing Data
        </div>
        <div className="collapsible-meta">
          <span className={`sta-badge ${staLive ? 'live' : 'manual'}`}>
            {staLive ? '● STA Live' : '✎ Manual'}
          </span>
          <span className={`collapsible-arrow ${open ? 'open' : ''}`}>▼</span>
        </div>
      </div>

      {open && (
        <div className="collapsible-body">
          {/* STA Connect */}
          <div className="sta-header" style={{ marginTop: 4 }}>
            <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              {staLive
                ? 'Fields imported from STA — read only.'
                : 'Enter fields manually or connect to STA.'}
            </div>
            <button className="sta-connect-btn" onClick={connectSta} disabled={connecting}>
              {connecting ? 'Connecting...' : staLive ? 'Refresh STA' : 'Connect to STA'}
            </button>
          </div>

          {staError && (
            <div style={{ fontSize: 12, color: 'var(--amber)', marginBottom: 8, lineHeight: 1.4 }}>
              {staError}
            </div>
          )}

          {/* Signal + Pattern — top row */}
          <div className="swing-fields-grid" style={{ marginBottom: 8 }}>
            <div className="field-item">
              <label>Signal</label>
              <select
                value={swing.swing_signal}
                disabled={staLive}
                onChange={(e) => setSwing((s) => ({ ...s, swing_signal: e.target.value }))}
              >
                <option value="BUY">BUY</option>
                <option value="HOLD">HOLD</option>
                <option value="AVOID">AVOID</option>
              </select>
            </div>
            <div className="field-item">
              <label>Pattern</label>
              <select
                value={swing.pattern}
                disabled={staLive}
                onChange={(e) => setSwing((s) => ({ ...s, pattern: e.target.value }))}
              >
                <option value="VCP">VCP</option>
                <option value="Cup&Handle">Cup &amp; Handle</option>
                <option value="FlatBase">Flat Base</option>
                <option value="None">None</option>
              </select>
            </div>
            <div className="field-item">
              <label>SPY Above 200 SMA</label>
              <select
                value={String(swing.spy_above_200sma)}
                disabled={staLive}
                onChange={(e) => setSwing((s) => ({ ...s, spy_above_200sma: e.target.value === 'true' }))}
              >
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
          </div>

          {/* Sectioned fields */}
          {SECTIONS.map((section) => {
            const sectionFields = Object.entries(FIELD_META).filter(([, m]) => m.section === section);
            if (!sectionFields.length) return null;
            return (
              <div key={section}>
                <div className="swing-section-title">{section}</div>
                <div className="swing-fields-grid">
                  {sectionFields.map(([key, meta]) => (
                    <div key={key} className="field-item">
                      <label>{meta.label}</label>
                      <input
                        type="number"
                        step="any"
                        value={swing[key] ?? ''}
                        disabled={staLive}
                        onChange={(e) => updateField(key, e.target.value)}
                        placeholder="—"
                      />
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
