
function fmt(v) {
  if (v == null) return '—';
  const n = Number(v);
  return isNaN(n) ? v : n.toFixed(2);
}

function plainEnglishSummary(strategy) {
  if (!strategy) return null;
  const { strategy_type, short_strike, long_strike, strike, breakeven, expiry_display, max_gain_per_lot } = strategy;
  const credit = max_gain_per_lot != null ? (max_gain_per_lot / 100).toFixed(2) : null;
  const be = breakeven != null ? Number(breakeven).toFixed(2) : null;
  const ss = short_strike ?? strike;
  const ls = long_strike;

  if (strategy_type === 'bear_call_spread' && ss != null && ls != null && credit) {
    return `SELL the $${fmt(ss)} call + BUY the $${fmt(ls)} call for $${credit}/share credit. You keep the credit if ETF stays below $${fmt(ss)}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if (strategy_type === 'bull_put_spread' && ss != null && ls != null && credit) {
    return `SELL the $${fmt(ss)} put + BUY the $${fmt(ls)} put for $${credit}/share credit. You keep the credit if ETF stays above $${fmt(ss)}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if (strategy_type === 'buy_call' && be) {
    return `Buy this call. You profit if ETF rises above $${be}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if (strategy_type === 'buy_put' && be) {
    return `Buy this put. You profit if ETF drops below $${be}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if ((strategy_type === 'itm_call' || strategy_type === 'atm_call') && be) {
    return `Buy this call. You profit if ETF rises above $${be}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if ((strategy_type === 'itm_put' || strategy_type === 'atm_put') && be) {
    return `Buy this put. You profit if ETF drops below $${be}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if (strategy_type === 'sell_call' && ss && credit) {
    return `Sell the $${fmt(ss)} call, collect $${credit}/share. You keep the credit if ETF stays below $${fmt(ss)}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  if (strategy_type === 'sell_put' && ss && credit) {
    return `Sell the $${fmt(ss)} put, collect $${credit}/share. You keep the credit if ETF stays above $${fmt(ss)}${expiry_display ? ' by ' + expiry_display : ''}.`;
  }
  return null;
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

function ExitPlanBlock({ exitPlan, strategyType }) {
  if (!exitPlan?.rule) return null;
  const isSeller = ['sell_put', 'sell_call', 'bull_put_spread', 'bear_call_spread'].includes(strategyType);
  return (
    <div className="exit-plan-block">
      <div className="exit-plan-header">Exit Plan</div>
      <div className="exit-plan-rule">{exitPlan.rule}</div>
      <div className="exit-plan-chips">
        {exitPlan.profit_target_credit != null && (
          <span className="exit-chip exit-chip-target">
            {isSeller ? 'Close below' : 'Sell at'} ${exitPlan.profit_target_credit.toFixed(2)}/sh
          </span>
        )}
        {!isSeller && exitPlan.stop_loss_credit != null && (
          <span className="exit-chip exit-chip-stop">
            Stop ${exitPlan.stop_loss_credit.toFixed(2)}/sh
          </span>
        )}
        {exitPlan.exit_date && (
          <span className="exit-chip exit-chip-date">
            Exit by {exitPlan.exit_date}
          </span>
        )}
      </div>
    </div>
  );
}

const SUPPORT_ZONE_COLOR = {
  above_s1:      '#e0b87e',  // amber — exposed
  between_s1_s2: '#c0c0c0',  // neutral
  below_s1:      '#7fe0a0',  // green
  below_s2:      '#7fe0a0',  // green
  above_r2:      '#7fe0a0',
  above_r1:      '#7fe0a0',
  between_r1_r2: '#c0c0c0',
  below_r1:      '#e0b87e',
  no_data:       null,
};

const CHART_VERDICT_STYLE = {
  go:    { color: '#7fe0a0', label: 'Chart GO ✅' },
  wait:  { color: '#e0b87e', label: 'Chart WAIT ⚠️' },
  block: { color: '#e05252', label: 'Chart BLOCK ❌' },
};

export default function TopThreeCards({ strategies, gates, pnlTable, expectedMove1sd, chartVerdict, selectedRank, onSelectRank }) {

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
        {/* Expected move context — top-level 1σ move */}
        {expectedMove1sd != null && (
          <div className="em-context">
            <span>±<strong>${Number(expectedMove1sd).toFixed(2)}</strong> expected move (1σ, {rank1.dte ?? '?'}d)</span>
            <span style={{ marginLeft: 10, color: 'var(--text-muted)' }}>— strikes outside this range have PoP ≥ 84%</span>
            {chartVerdict && CHART_VERDICT_STYLE[chartVerdict] && (
              <span style={{ marginLeft: 12, fontSize: 11, color: CHART_VERDICT_STYLE[chartVerdict].color, fontWeight: 600 }}>
                {CHART_VERDICT_STYLE[chartVerdict].label}
              </span>
            )}
          </div>
        )}

        {/* Rank 1 — dominant */}
        <div className="strategy-rank1" style={{ marginTop: expectedMove1sd != null ? 8 : 4 }}>
          {gatedOut && <div className="strategy-overlay">GATED OUT — Gate conditions not met</div>}

          <div className="strategy-rank1-badge"># 1 — Top Recommendation</div>
          <div className="strategy-rank1-title">{rank1.label}</div>

          {/* Plain English summary */}
          {plainEnglishSummary(rank1) && (
            <div className="strategy-plain-english">
              {plainEnglishSummary(rank1)}
            </div>
          )}

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
            {rank1.strike_vs_em_label != null && (
              <div className="strategy-detail-item">
                <label>σ OTM</label>
                <div className="val" style={{ fontSize: 13 }}>{rank1.strike_vs_em_label}</div>
              </div>
            )}
            {rank1.strike_vs_support?.label && rank1.strike_vs_support.zone !== 'no_data' && (
              <div className="strategy-detail-item" style={{ gridColumn: '1 / -1' }}>
                <label>vs Support</label>
                <div className="val" style={{ fontSize: 12, color: SUPPORT_ZONE_COLOR[rank1.strike_vs_support.zone] || 'inherit' }}>
                  {rank1.strike_vs_support.label}
                </div>
              </div>
            )}
            {rank1.credit_to_width_ratio != null && (
              <div className="strategy-detail-item">
                <label>Credit / Width</label>
                <div className="val" style={{
                  color: rank1.credit_to_width_ratio < 0.33 ? '#e05252' : '#00c896'
                }}>
                  {(rank1.credit_to_width_ratio * 100).toFixed(0)}%
                </div>
              </div>
            )}
          </div>

          {/* Exit plan */}
          {!gatedOut && rank1.exit_plan && (
            <ExitPlanBlock exitPlan={rank1.exit_plan} strategyType={rank1.strategy_type} />
          )}

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
          {rank1.catalyst_overlay?.clears_event === false && rank1.catalyst_overlay?.label && (
            <div className="strategy-warning" style={{ borderLeftColor: '#e0b87e', color: '#e0b87e' }}>
              <span>!</span>
              <span>{rank1.catalyst_overlay.label}</span>
            </div>
          )}
        </div>

        {/* Ranks 2 & 3 — always-visible compact rows */}
        {alts.length > 0 && (
          <div className="strategy-alts-compact">
            {alts.map((s) => {
              const pnl = extractPnl(pnlTable, s.rank);
              const isSelected = selectedRank === s.rank;
              return (
                <div
                  key={s.rank}
                  className={`strategy-alt-row ${isSelected ? 'selected' : ''}`}
                  style={{ opacity: gatedOut ? 0.5 : 1 }}
                >
                  <span className="sar-rank">#{s.rank}</span>
                  <span className="sar-label">{s.label}</span>
                  {s.strike_vs_em_label && (
                    <span className="sar-sigma">{s.strike_vs_em_label}</span>
                  )}
                  {pnl.target != null && (
                    <span className="sar-pnl text-green">+${Math.abs(pnl.target).toFixed(0)}</span>
                  )}
                  {pnl.stop != null && (
                    <span className="sar-pnl text-red">-${Math.abs(pnl.stop).toFixed(0)}</span>
                  )}
                  {s.catalyst_overlay?.clears_event === false && (
                    <span style={{ fontSize: 10, color: '#e0b87e' }}>⚠️ earnings</span>
                  )}
                  {s.strike_vs_support?.zone === 'above_s1' && (
                    <span style={{ fontSize: 10, color: '#e0b87e' }}>⚠️ above S1</span>
                  )}
                  {onSelectRank && (
                    <button
                      className="sar-select-btn"
                      onClick={() => onSelectRank(isSelected ? null : s.rank)}
                    >
                      {isSelected ? '✓ selected' : 'select'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
