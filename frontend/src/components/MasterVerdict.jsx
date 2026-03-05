export default function MasterVerdict({ verdict, gates }) {
  if (!verdict) {
    return (
      <div className="verdict-hero empty">
        <div className="verdict-label">—</div>
        <div className="verdict-headline">Run analysis to see verdict</div>
      </div>
    );
  }

  // Map backend color → CSS class
  const colorMap = { green: 'go', red: 'block', amber: 'pause' };
  const heroClass = colorMap[verdict.color] || 'pause';

  // Gate dot summary
  const pass  = gates.filter((g) => g.status === 'pass').length;
  const warn  = gates.filter((g) => g.status === 'warn').length;
  const fail  = gates.filter((g) => g.status === 'fail').length;
  const total = gates.length;

  const labelMap = { go: 'GO', block: 'BLOCK', pause: 'PAUSE' };
  const label = labelMap[heroClass] || verdict.score_label;

  return (
    <div className={`verdict-hero ${heroClass}`}>
      <div className="verdict-label">{label}</div>
      <div className="verdict-headline">{verdict.headline}</div>

      {total > 0 && (
        <div className="verdict-gate-summary">
          <div className="gate-dot-row">
            {gates.map((g) => (
              <span
                key={g.id}
                className={`gdot ${g.status === 'pass' ? 'pass' : g.status === 'warn' ? 'warn' : g.status === 'fail' ? 'fail' : 'na'}`}
                title={`${g.name}: ${g.status}`}
              />
            ))}
          </div>
          <div className="verdict-gate-count">
            {pass}/{total} pass
            {warn > 0 && <span className="text-amber"> · {warn} warn</span>}
            {fail > 0 && <span className="text-red"> · {fail} fail</span>}
          </div>
        </div>
      )}
    </div>
  );
}
