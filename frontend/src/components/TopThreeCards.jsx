import { useState } from 'react';

function fmt(v) {
  if (v == null) return '—';
  const n = Number(v);
  return isNaN(n) ? v : n.toFixed(2);
}

function fmtPnl(v) {
  if (v == null || v === '--') return null;
  const n = Number(v);
  if (isNaN(n)) return null;
  return n;
}

// Extract the target/stop P&L for rank from the pnl_table
function extractPnl(pnlTable, rank) {
  if (!pnlTable?.scenarios) return { target: null, stop: null };
  const key = `pnl_c${rank}`;
  const targetRow = pnlTable.scenarios.find((r) =>
    r.scenario_label?.toLowerCase().includes('target'));
  const stopRow = pnlTable.scenarios.find((r) =>
    r.scenario_label?.toLowerCase().includes('stop'));
  return {
    target: targetRow ? fmtPnl(targetRow[key]) : null,
    stop:   stopRow   ? fmtPnl(stopRow[key])   : null,
  };
}

function PnlChip({ label, value, type }) {
  if (value == null) return null;
  const cls = type === 'target' ? 'target' : 'stop';
  const sign = value >= 0 ? '+' : '';
  return (
    <div className={`pnl-scenario ${cls}`}>
      <label>{label}</label>
      <div className="pnl-val">{sign}${Math.abs(value).toFixed(0)}</div>
    </div>
  );
}

export default function TopThreeCards({ strategies, gates, pnlTable }) {
  const [altsOpen, setAltsOpen] = useState(false);

  const pivotFail       = gates.some((g) => g.id === 'pivot_confirm' && g.status === 'fail');
  const anyBlockingFail = gates.some((g) => g.blocking && g.status === 'fail');
  const gatedOut        = pivotFail || anyBlockingFail;

  const [rank1, ...alts] = strategies;

  if (!rank1) {
    return (
      <div className="collapsible">
        <div className="collapsible-header" style={{ cursor: 'default' }}>
          <div className="collapsible-title">Recommended Strategy</div>
        </div>
        <div className="collapsible-body">
          <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '8px 0' }}>
            No strategies — run analysis first.
          </div>
        </div>
      </div>
    );
  }

  const r1Pnl = extractPnl(pnlTable, 1);

  return (
    <div className="collapsible" style={{ overflow: 'visible' }}>
      <div className="collapsible-header" style={{ cursor: 'default', borderBottom: '1px solid var(--border-dim)' }}>
        <div className="collapsible-title">Recommended Strategy</div>
        {gatedOut && (
          <span style={{ fontSize: 11, color: 'var(--red)', fontWeight: 600 }}>GATED OUT</span>
        )}
      </div>

      <div className="collapsible-body">
        {/* Rank 1 — dominant */}
        <div className="strategy-rank1" style={{ marginTop: 4 }}>
          {gatedOut && <div className="strategy-overlay">GATED OUT — Gate conditions not met</div>}

          <div className="strategy-rank1-badge"># 1 — Top Recommendation</div>
          <div className="strategy-rank1-title">{rank1.label}</div>

          <div className="strategy-details">
            <div className="strategy-detail-item">
              <label>Strike</label>
              <div className="val">{rank1.strike_display ?? '—'}</div>
            </div>
            <div className="strategy-detail-item">
              <label>Expiry</label>
              <div className="val">{rank1.expiry_display ?? '—'}</div>
            </div>
            <div className="strategy-detail-item">
              <label>Premium / Lot</label>
              <div className="val">${fmt(rank1.premium_per_lot)}</div>
            </div>
            <div className="strategy-detail-item">
              <label>Breakeven</label>
              <div className="val">${fmt(rank1.breakeven)}</div>
            </div>
            {rank1.delta != null && (
              <div className="strategy-detail-item">
                <label>Delta</label>
                <div className="val">{fmt(rank1.delta)}</div>
              </div>
            )}
            {rank1.theta_per_day != null && (
              <div className="strategy-detail-item">
                <label>Theta / Day</label>
                <div className="val">{fmt(rank1.theta_per_day)}</div>
              </div>
            )}
            {rank1.dte != null && (
              <div className="strategy-detail-item">
                <label>DTE</label>
                <div className="val">{rank1.dte}d</div>
              </div>
            )}
          </div>

          {/* P&L at target / stop */}
          {(r1Pnl.target != null || r1Pnl.stop != null) && !gatedOut && (
            <div className="strategy-pnl-row">
              <PnlChip label="At Target" value={r1Pnl.target} type="target" />
              <PnlChip label="At Stop"   value={r1Pnl.stop}   type="stop" />
            </div>
          )}

          {rank1.why && <div className="strategy-why">{rank1.why}</div>}
          {rank1.warning && (
            <div className="strategy-warning">
              <span>!</span>
              <span>{rank1.warning}</span>
            </div>
          )}
        </div>

        {/* Ranks 2 & 3 — collapsible */}
        {alts.length > 0 && (
          <div className="collapsible" style={{ marginTop: 10 }}>
            <div className="collapsible-header" onClick={() => setAltsOpen((o) => !o)}>
              <div className="collapsible-title" style={{ fontSize: 12 }}>
                Alternative Strategies
              </div>
              <span className={`collapsible-arrow ${altsOpen ? 'open' : ''}`}>▼</span>
            </div>
            {altsOpen && (
              <div className="collapsible-body">
                <div className="strategy-alts">
                  {alts.map((s) => {
                    const pnl = extractPnl(pnlTable, s.rank);
                    return (
                      <div key={s.rank} className="strategy-alt" style={{ position: 'relative' }}>
                        {gatedOut && <div className="strategy-overlay">GATED OUT</div>}
                        <div className="strategy-alt-rank">#{s.rank}</div>
                        <div className="strategy-alt-title">{s.label}</div>
                        <div className="strategy-alt-meta">
                          {s.strike_display && <div>Strike: {s.strike_display}</div>}
                          {s.expiry_display && <div>Expiry: {s.expiry_display}</div>}
                          {s.premium_per_lot != null && <div>Premium: ${fmt(s.premium_per_lot)}/lot</div>}
                          {s.breakeven      != null && <div>Breakeven: ${fmt(s.breakeven)}</div>}
                        </div>
                        {!gatedOut && pnl.target != null && (
                          <div style={{ marginTop: 8, fontSize: 12 }}>
                            <span className="text-green">Target: +${Math.abs(pnl.target).toFixed(0)}</span>
                            {pnl.stop != null && (
                              <span className="text-red" style={{ marginLeft: 10 }}>
                                Stop: -${Math.abs(pnl.stop).toFixed(0)}
                              </span>
                            )}
                          </div>
                        )}
                        {s.why && (
                          <div className="strategy-alt-meta" style={{ marginTop: 6 }}>{s.why}</div>
                        )}
                        {s.warning && (
                          <div className="strategy-warning" style={{ marginTop: 6, fontSize: 11 }}>
                            <span>!</span><span>{s.warning}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
