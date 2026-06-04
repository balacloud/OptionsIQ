import { useState } from 'react';

export default function MasterVerdict({ verdict, gates, compact = true }) {
  const [showAll, setShowAll] = useState(false);

  if (!verdict) {
    return (
      <div className="verdict-hero empty">
        <div className="verdict-label">—</div>
        <div className="verdict-headline">Run analysis to see verdict</div>
      </div>
    );
  }

  const colorMap  = { green: 'go', red: 'block', amber: 'pause' };
  const heroClass = colorMap[verdict.color] || 'pause';
  const labelMap  = { go: 'GO', block: 'BLOCK', pause: 'PAUSE' };
  const label     = labelMap[heroClass] || verdict.score_label;

  const pass  = gates.filter((g) => g.status === 'pass').length;
  const warn  = gates.filter((g) => g.status === 'warn').length;
  const fail  = gates.filter((g) => g.status === 'fail').length;
  const total = gates.length;

  const failGates   = gates.filter((g) => g.status === 'fail');
  const warnGates   = gates.filter((g) => g.status === 'warn');
  const passedGates = gates.filter((g) => g.status === 'pass');

  const subtitleMap = {
    go:    'All gates clear. Review the strategy below and log the trade.',
    pause: `${pass} gates clear${warn + fail > 0 ? ` · ${warn + fail} advisories below` : ''}. Read the warnings, then trade.`,
    block: 'A structural gate failed — downtrend or IV-cheap. Wait for conditions to change.',
  };

  const GateRow = ({ g, type }) => (
    <div className={`verdict-gate-row ${type}`}>
      <span className="vg-name">{g.name}</span>
      {g.computed_value && <span className="vg-value">{g.computed_value}</span>}
      {g.reason && <span className="vg-reason">{g.reason}</span>}
    </div>
  );

  return (
    <div className={`verdict-hero ${heroClass}`}>
      <div className="verdict-label">{label}</div>
      <div className="verdict-headline">{verdict.headline}</div>
      <div className="verdict-subtitle">{subtitleMap[heroClass]}</div>

      {total > 0 && (
        <div className="verdict-gate-summary">
          {compact ? (
            <>
              {/* Compact: count chip + warn/fail only */}
              <div className="verdict-gate-count">
                <span className="vg-pass-chip">{pass} pass</span>
                {warn > 0 && <span className="text-amber"> · {warn} warn</span>}
                {fail > 0 && <span className="text-red"> · {fail} fail</span>}
              </div>

              {(failGates.length > 0 || warnGates.length > 0) && (
                <div className="verdict-gate-detail">
                  {failGates.map((g)  => <GateRow key={g.id} g={g} type="fail" />)}
                  {warnGates.map((g)  => <GateRow key={g.id} g={g} type="warn" />)}
                </div>
              )}

              {!showAll ? (
                <button className="vg-toggle-btn" onClick={() => setShowAll(true)}>
                  ▸ show all {total} checks
                </button>
              ) : (
                <>
                  <div className="verdict-passed-row">
                    <span className="vp-label">✓ Passed:</span>
                    {passedGates.map((g) => (
                      <span key={g.id} className="vp-chip" title={g.computed_value || g.reason || ''}>
                        {g.name}
                      </span>
                    ))}
                  </div>
                  <button className="vg-toggle-btn" onClick={() => setShowAll(false)}>
                    ▴ collapse
                  </button>
                </>
              )}
            </>
          ) : (
            <>
              {/* Full view: all 14 dots + breakdown */}
              <div className="gate-dot-row">
                {gates.map((g) => (
                  <span
                    key={g.id}
                    className={`gdot ${g.status === 'pass' ? 'pass' : g.status === 'warn' ? 'warn' : g.status === 'fail' ? 'fail' : 'na'}`}
                    title={`${g.name}: ${g.status}${g.computed_value ? ' · ' + g.computed_value : ''}${g.reason ? ' — ' + g.reason : ''}`}
                  />
                ))}
              </div>
              <div className="verdict-gate-count">
                {pass}/{total} pass
                {warn > 0 && <span className="text-amber"> · {warn} warn</span>}
                {fail > 0 && <span className="text-red"> · {fail} fail</span>}
              </div>
              {(failGates.length > 0 || warnGates.length > 0) && (
                <div className="verdict-gate-detail">
                  {failGates.map((g)  => <GateRow key={g.id} g={g} type="fail" />)}
                  {warnGates.map((g)  => <GateRow key={g.id} g={g} type="warn" />)}
                </div>
              )}
              {passedGates.length > 0 && (
                <div className="verdict-passed-row">
                  <span className="vp-label">✓ Passed:</span>
                  {passedGates.map((g) => (
                    <span key={g.id} className="vp-chip" title={g.computed_value || g.reason || ''}>
                      {g.name}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
