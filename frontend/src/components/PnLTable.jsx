import { useState } from 'react';

function rowClass(label) {
  const l = label?.toLowerCase() || '';
  if (l.includes('target')) return 'row-target';
  if (l.includes('stop'))   return 'row-stop';
  return '';
}

function PnlCell({ value, gated }) {
  if (gated || value === '--') return <td className="text-dim">—</td>;
  const n = Number(value);
  if (isNaN(n)) return <td className="text-dim">—</td>;
  return <td><span className={n >= 0 ? 'profit' : 'loss'}>{n >= 0 ? '+' : ''}{n.toFixed(2)}</span></td>;
}

export default function PnLTable({ table, gateFailed }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="collapsible">
      <div className="collapsible-header" onClick={() => setOpen((o) => !o)}>
        <div className="collapsible-title">P&amp;L Scenarios</div>
        <div className="collapsible-meta">
          {gateFailed && <span style={{ fontSize: 11, color: 'var(--red)' }}>GATED</span>}
          <span className={`collapsible-arrow ${open ? 'open' : ''}`}>▼</span>
        </div>
      </div>

      {open && (
        <div className="collapsible-body">
          {!table ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '8px 0' }}>
              No P&L data — run analysis first.
            </div>
          ) : (
            <div className="pnl-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Scenario</th>
                    <th>Stock</th>
                    <th>#1</th>
                    <th>#2</th>
                    <th>#3 <span style={{ color: 'var(--amber)', fontWeight: 400 }}>high theta</span></th>
                  </tr>
                </thead>
                <tbody>
                  {table.scenarios.map((r) => (
                    <tr key={r.scenario_label} className={rowClass(r.scenario_label)}>
                      <td style={{ fontWeight: 500 }}>{r.scenario_label}</td>
                      <td className="monospace">${r.stock_price}</td>
                      <PnlCell value={r.pnl_c1} gated={gateFailed} />
                      <PnlCell value={r.pnl_c2} gated={gateFailed} />
                      <PnlCell value={r.pnl_c3} gated={gateFailed} />
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
