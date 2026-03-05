function cls(name) {
  if (name.includes('Target') || name.includes('Pivot')) return 'row-target';
  if (name.includes('Stop Loss')) return 'row-stop';
  return '';
}

function val(v) {
  if (v === '--') return '--';
  const n = Number(v);
  const c = n >= 0 ? 'profit' : 'loss';
  return <span className={c}>{n.toFixed(2)}</span>;
}

export default function PnLTable({ table, gateFailed }) {
  if (!table) return null;
  return (
    <section className="card">
      <h3>P&L Table</h3>
      <table>
        <thead>
          <tr><th>Scenario</th><th>Stock</th><th>C1</th><th>C2</th><th>C3 ⚠️ HIGH THETA</th></tr>
        </thead>
        <tbody>
          {table.scenarios.map((r) => (
            <tr key={r.scenario_label} className={cls(r.scenario_label)}>
              <td>{r.scenario_label}</td>
              <td>${r.stock_price}</td>
              <td>{gateFailed ? '--' : val(r.pnl_c1)}</td>
              <td>{gateFailed ? '--' : val(r.pnl_c2)}</td>
              <td>{gateFailed ? '--' : val(r.pnl_c3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
