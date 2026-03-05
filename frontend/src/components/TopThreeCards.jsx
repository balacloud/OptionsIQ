export default function TopThreeCards({ strategies, gates }) {
  const pivotFail = gates.some((g) => g.id === 'pivot_confirm' && g.status === 'fail');
  const anyBlockingFail = gates.some((g) => g.blocking && g.status === 'fail');

  return (
    <section className="card">
      <h3>Top Three</h3>
      <div className="cards3">
        {strategies.map((s) => (
          <div key={s.rank} className="strategy-card">
            {(pivotFail || anyBlockingFail) ? <div className="overlay">🔒 GATED OUT</div> : null}
            <strong>#{s.rank} {s.label}</strong>
            <div>Strike: {s.strike_display}</div>
            <div>Expiry: {s.expiry_display}</div>
            <div>Premium/Lot: ${s.premium_per_lot}</div>
            <div>Breakeven: ${s.breakeven}</div>
            <small>{s.why}</small>
            {s.warning ? <div className="warn">⚠️ {s.warning}</div> : null}
          </div>
        ))}
      </div>
    </section>
  );
}
