import { useState } from 'react';

export default function GatesGrid({ gates }) {
  const [open, setOpen] = useState(false);

  const pass = gates.filter((g) => g.status === 'pass').length;
  const warn = gates.filter((g) => g.status === 'warn').length;
  const fail = gates.filter((g) => g.status === 'fail').length;

  return (
    <div className="collapsible">
      <div className="collapsible-header" onClick={() => setOpen((o) => !o)}>
        <div className="collapsible-title">
          Gates
          {gates.length > 0 && (
            <div className="gate-dot-row">
              {gates.map((g) => (
                <span
                  key={g.id}
                  className={`gdot ${g.status === 'pass' ? 'pass' : g.status === 'warn' ? 'warn' : 'fail'}`}
                  title={`${g.name}: ${g.status}`}
                />
              ))}
            </div>
          )}
        </div>
        <div className="collapsible-meta">
          {gates.length > 0 && (
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              {pass}/{gates.length}
              {warn > 0 && <span className="text-amber"> · {warn}w</span>}
              {fail > 0 && <span className="text-red"> · {fail}f</span>}
            </span>
          )}
          <span className={`collapsible-arrow ${open ? 'open' : ''}`}>▼</span>
        </div>
      </div>

      {open && (
        <div className="collapsible-body">
          {gates.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '8px 0' }}>
              No gate data — run analysis first.
            </div>
          ) : (
            <div className="gates-grid">
              {gates.map((g) => (
                <div key={g.id} className={`gate ${g.status}`}>
                  <div className="row-between">
                    <div className="gate-name">{g.name}</div>
                    <span className={`gate-status-badge ${g.status}`}>{g.status}</span>
                  </div>
                  <div className="gate-value">{g.computed_value ?? '—'}</div>
                  {g.reason && <div className="gate-reason">{g.reason}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
