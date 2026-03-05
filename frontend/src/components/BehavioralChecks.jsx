import { useState } from 'react';

export default function BehavioralChecks({ checks }) {
  const [open, setOpen] = useState(false);

  const hardBlocks = checks.filter((c) => c.type === 'hard_block').length;
  const warnings   = checks.filter((c) => c.type === 'warning').length;

  return (
    <div className="collapsible">
      <div className="collapsible-header" onClick={() => setOpen((o) => !o)}>
        <div className="collapsible-title">Behavioral Notes</div>
        <div className="collapsible-meta">
          {hardBlocks > 0 && <span style={{ fontSize: 11, color: 'var(--red)',   fontWeight: 600 }}>{hardBlocks} block</span>}
          {warnings   > 0 && <span style={{ fontSize: 11, color: 'var(--amber)', fontWeight: 600 }}>{warnings} warn</span>}
          <span className={`collapsible-arrow ${open ? 'open' : ''}`}>▼</span>
        </div>
      </div>

      {open && (
        <div className="collapsible-body">
          {checks.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '8px 0' }}>
              No behavioral data — run analysis first.
            </div>
          ) : (
            <div className="checks-list">
              {checks.map((c) => (
                <div key={c.id} className={`check ${c.type}`}>
                  <div className="check-label">{c.label}</div>
                  <div className="check-message">{c.message}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
