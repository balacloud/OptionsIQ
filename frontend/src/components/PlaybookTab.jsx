import { useState } from 'react';

// ─── Data ────────────────────────────────────────────────────────────────────

const TIER1 = [
  {
    id: 'yield-banks',
    name: 'Yield Curve → Banks',
    mechanism: 'Banks borrow short, lend long. Steeper curve = wider net interest margin = more earnings.',
    watch: '10Y minus 2Y spread (FRED)',
    trigger: 'Spread turns positive after inversion, or steepens > 50bps from trough',
    target: 'XLF · JPM · RY · TD',
    structure: 'BULL CALL SPREAD',
    dte: '45 DTE',
    caution: 'Do not sell puts while curve is inverted — bank NIM is compressed',
    instances: '1994–95 · 2004–06 · 2010–11 · 2022–23',
  },
  {
    id: 'fed-tech',
    name: 'Fed Pivot → Tech',
    mechanism: 'Tech stocks are long-duration assets. Lower discount rate mechanically increases present value of future earnings.',
    watch: 'Fed dot plot · FOMC statement language',
    trigger: '"Higher for longer" → "Data dependent" → first rate cut',
    target: 'QQQ · XLK',
    structure: 'BULL CALL SPREAD',
    dte: '60–90 DTE',
    caution: 'Requires SPY above 200 EMA — cuts during recession do not work',
    instances: '1998 · 2019 · 2020 · 2024',
  },
  {
    id: 'vix-premium',
    name: 'VIX Spike → Premium',
    mechanism: 'VIX above 40 has never sustained more than 90 days. Panic inflates IV well above realized vol. Sellers collect the edge.',
    watch: 'VIX index (RegimeBar shows live level)',
    trigger: 'VIX > 35 (elevated edge) · VIX > 40 (maximum edge)',
    target: 'QQQ · SPY — sell puts',
    structure: 'SELL PUTS',
    dte: '30–45 DTE',
    caution: 'OptionsIQ VIX gate hard-blocks above 40 — your edge window is 30–39',
    instances: '1998 · 2008–09 · 2011 · 2020 · 2022',
  },
  {
    id: 'real-rates-gold',
    name: 'Real Rates → Gold',
    mechanism: 'Real rate = 10Y yield minus CPI. When negative, gold beats bonds as a store of value. Capital rotates mechanically.',
    watch: 'Monthly CPI print vs 10-year Treasury yield',
    trigger: 'CPI exceeds 10Y yield for 2+ consecutive months (real rate < 0)',
    target: 'GLD',
    structure: 'BULL CALL SPREAD',
    dte: '45 DTE',
    caution: 'GLD IV/HV gate must pass (IV > HV × 1.10). GLD skew inverts on rallies.',
    instances: '2008–09 · 2011–12 · 2019–20 · 2022–24',
  },
];

const TIER2 = [
  {
    id: 'oil-energy',
    name: 'Oil > $75 → Energy',
    mechanism: 'Energy FCF = oil price minus $45–55/barrel production cost. Above $75 = strong margins, buybacks, dividends.',
    watch: 'WTI crude price',
    trigger: 'WTI holds above $75 for 2+ weeks OR OPEC announces production cut',
    target: 'XLE · XOM · CVX',
    structure: 'BULL CALL SPREAD',
    dte: '45–60 DTE',
    caution: 'Wait 2 weeks for hold confirmation — do not chase first breakout',
    instances: '2004–08 · 2010–14 · 2021–22',
  },
  {
    id: 'china-copper',
    name: 'China Stimulus → Copper',
    mechanism: 'China consumes 50–55% of global copper. Fiscal stimulus = infrastructure build = copper demand surge within days.',
    watch: 'PBOC rate decisions · State Council announcements',
    trigger: 'PBOC rate cut OR major infrastructure spending headline',
    target: 'XLB · FCX',
    structure: 'BULL CALL SPREAD',
    dte: '45 DTE',
    caution: 'Wait for second confirmation — Chinese headlines are frequently walked back',
    instances: '2008 · 2015–16 · 2022–23',
  },
  {
    id: 'mortgage-housing',
    name: 'Mortgage Rate Drop → Housing',
    mechanism: '50bps rate drop adds $50–80k in buyer purchasing power. New home orders surge 60–90 days after the drop.',
    watch: '30-year fixed mortgage rate (Freddie Mac weekly survey)',
    trigger: 'Rate falls below 6.5% AND holds for 2+ weeks',
    target: 'XHB · DHI · LEN',
    structure: 'BULL CALL SPREAD',
    dte: '60–90 DTE',
    caution: 'Longer DTE required — housing activity data lags the rate move by 60–90 days',
    instances: '2009 · 2012 · 2019–20 · 2023',
  },
];

const SEASONAL = [
  { name: 'September Weakness', rate: '~65%', window: 'Late Aug → Sep', play: 'Sell calls in late August', note: 'No mechanism — statistical only' },
  { name: 'Santa Claus Rally',  rate: '~75%', window: 'Dec 24 – Jan 2',  play: 'Bull Call Spread QQQ — short DTE', note: 'Most reliable of the seasonal patterns' },
  { name: 'January Small-Cap',  rate: '~60%', window: 'First 2 weeks Jan', play: 'Bull Call Spread IWM', note: 'Weaker in recent years' },
  { name: '"Sell in May"',      rate: '~55%', window: 'May – October',    play: 'Mild bearish bias only', note: 'Weakest signal — secondary confirmation only' },
];

const STACKS = [
  {
    strength: 'MAXIMUM',
    color: '#7fe0a0',
    signals: ['VIX > 35', 'SPY above 200 EMA'],
    result: 'Sell puts on QQQ/SPY — OptionsIQ core workflow at its highest edge',
  },
  {
    strength: 'STRONG',
    color: '#7ec8e0',
    signals: ['Fed pivot signaled', 'VIX declining from peak', 'QQQ above 200 EMA'],
    result: 'Bull Call Spread QQQ — rate cut cycle + uptrend = most powerful tech setup',
  },
  {
    strength: 'STRONG',
    color: '#7ec8e0',
    signals: ['Yield curve steepening', 'CPI falling', 'XLF above 200 EMA'],
    result: 'Bull Call Spread XLF — NIM expanding + macro tailwind + technical',
  },
  {
    strength: 'STRONG',
    color: '#7ec8e0',
    signals: ['Real rates negative', 'GLD above 200 EMA', 'IV/HV > 1.10'],
    result: 'Bull Call Spread GLD — fundamental + technical aligned, gate clears',
  },
];

const DECISION_MATRIX = [
  {
    trigger: 'Known calendar event (FOMC, CPI, earnings date)',
    structure: 'Calendar Spread',
    structureColor: '#b4a0e0',
    why: 'Sell near-term theta; hold long-term exposure through the catalyst',
  },
  {
    trigger: 'Directional macro regime (yield curve, Fed pivot, oil breakout)',
    structure: 'Bull Call Spread',
    structureColor: '#7ec8e0',
    why: 'Caps cost + reduces theta drag vs naked call — profits sideways or up',
  },
  {
    trigger: 'VIX spike / IV elevated well above realized volatility',
    structure: 'Sell Puts',
    structureColor: '#7fe0a0',
    why: 'Collect overpriced panic premium — OptionsIQ core short-premium workflow',
  },
  {
    trigger: 'Range-bound / mean-reversion expected, no catalyst',
    structure: 'Iron Condor / Straddle',
    structureColor: '#b4a0e0',
    why: 'Theta harvest on both sides — no directional commitment required',
  },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

const STRUCTURE_STYLE = {
  'SELL PUTS':        { bg: 'rgba(127,224,160,0.12)', color: '#7fe0a0', border: 'rgba(127,224,160,0.3)' },
  'BULL CALL SPREAD': { bg: 'rgba(126,200,224,0.12)', color: '#7ec8e0', border: 'rgba(126,200,224,0.3)' },
  'CALENDAR SPREAD':  { bg: 'rgba(180,160,224,0.12)', color: '#b4a0e0', border: 'rgba(180,160,224,0.3)' },
};

const STATUS_CYCLE = ['IDLE', 'WATCH', 'ACTIVE'];

function PatternCard({ p, status, onToggle, tierColor }) {
  const ss = STRUCTURE_STYLE[p.structure] || STRUCTURE_STYLE['BULL CALL SPREAD'];
  const statusColor = status === 'ACTIVE' ? '#7fe0a0' : status === 'WATCH' ? '#e0b87e' : '#374151';
  const statusTextColor = status === 'IDLE' ? '#6b7280' : statusColor;

  return (
    <div className={`pb-card ${status !== 'IDLE' ? 'pb-card-lit' : ''}`} style={{ borderLeftColor: tierColor }}>
      <div className="pb-card-header">
        <span className="pb-card-name">{p.name}</span>
        <button
          className="pb-status-btn"
          style={{ color: statusTextColor, borderColor: statusColor }}
          onClick={onToggle}
          title="Click to cycle: IDLE → WATCH → ACTIVE"
        >
          {status}
        </button>
      </div>

      <div className="pb-mechanism">"{p.mechanism}"</div>

      <div className="pb-info-block">
        <div className="pb-info-row">
          <span className="pb-info-key">Watch</span>
          <span className="pb-info-val">{p.watch}</span>
        </div>
        <div className="pb-info-row">
          <span className="pb-info-key">Trigger</span>
          <span className="pb-info-val">{p.trigger}</span>
        </div>
        <div className="pb-info-row">
          <span className="pb-info-key">Target</span>
          <span className="pb-info-val pb-target">{p.target}</span>
        </div>
      </div>

      <div className="pb-card-footer">
        <span
          className="pb-struct-badge"
          style={{ background: ss.bg, color: ss.color, border: `1px solid ${ss.border}` }}
        >
          {p.structure} · {p.dte}
        </span>
        <span className="pb-instances">{p.instances}</span>
      </div>

      <div className="pb-caution">⚠ {p.caution}</div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function PlaybookTab() {
  const allPatterns = [...TIER1, ...TIER2];
  const [statuses, setStatuses] = useState(
    Object.fromEntries(allPatterns.map(p => [p.id, 'IDLE']))
  );

  const toggle = (id) => setStatuses(prev => {
    const cur = STATUS_CYCLE.indexOf(prev[id]);
    return { ...prev, [id]: STATUS_CYCLE[(cur + 1) % STATUS_CYCLE.length] };
  });

  const activeOrWatch = allPatterns.filter(p => statuses[p.id] !== 'IDLE');

  return (
    <div className="playbook-wrap">

      {/* Hero */}
      <div className="playbook-hero">
        <div className="ph-title">Macro Regime Playbook</div>
        <div className="ph-sub">
          Cyclical patterns with mechanical fundamental links, ranked by reliability.
          Click any card to mark it <span style={{ color: '#e0b87e' }}>WATCH</span> or <span style={{ color: '#7fe0a0' }}>ACTIVE</span>.
        </div>
      </div>

      {/* Active strip — only shows when at least one pattern is marked */}
      {activeOrWatch.length > 0 && (
        <div className="pb-active-strip">
          <span className="pb-active-label">Currently tracking:</span>
          {activeOrWatch.map(p => (
            <span
              key={p.id}
              className="pb-active-chip"
              style={{ color: statuses[p.id] === 'ACTIVE' ? '#7fe0a0' : '#e0b87e',
                       borderColor: statuses[p.id] === 'ACTIVE' ? 'rgba(127,224,160,0.4)' : 'rgba(224,184,126,0.4)' }}
              onClick={() => toggle(p.id)}
            >
              {statuses[p.id] === 'ACTIVE' ? '●' : '◐'} {p.name}
            </span>
          ))}
        </div>
      )}

      {/* Tier 1 */}
      <div className="pb-section">
        <div className="pb-section-head">
          <span className="pb-tier-pill t1">Tier 1</span>
          <span className="pb-section-title">Mechanically Reliable — direct fundamental cause → effect</span>
        </div>
        <div className="pb-grid-2">
          {TIER1.map(p => (
            <PatternCard key={p.id} p={p} status={statuses[p.id]} onToggle={() => toggle(p.id)} tierColor="#e0b87e" />
          ))}
        </div>
      </div>

      {/* Tier 2 */}
      <div className="pb-section">
        <div className="pb-section-head">
          <span className="pb-tier-pill t2">Tier 2</span>
          <span className="pb-section-title">Reliable, Longer Cycles — mechanical link but messier timing</span>
        </div>
        <div className="pb-grid-3">
          {TIER2.map(p => (
            <PatternCard key={p.id} p={p} status={statuses[p.id]} onToggle={() => toggle(p.id)} tierColor="#7ec8e0" />
          ))}
        </div>
      </div>

      {/* Tier 3 — Seasonal */}
      <div className="pb-section">
        <div className="pb-section-head">
          <span className="pb-tier-pill t3">Tier 3</span>
          <span className="pb-section-title">Seasonal / Statistical — no fundamental mechanism, secondary signal only</span>
        </div>
        <table className="pb-table">
          <thead>
            <tr>
              <th>Pattern</th>
              <th>Hit Rate</th>
              <th>Window</th>
              <th>Options Play</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {SEASONAL.map(s => (
              <tr key={s.name}>
                <td style={{ color: '#e0e0e0', fontWeight: 600 }}>{s.name}</td>
                <td style={{ color: '#e0b87e' }}>{s.rate}</td>
                <td>{s.window}</td>
                <td style={{ color: '#7ec8e0' }}>{s.play}</td>
                <td style={{ color: '#6b7280', fontStyle: 'italic' }}>{s.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Regime Stacking */}
      <div className="pb-section">
        <div className="pb-section-head">
          <span className="pb-section-title">Regime Stacking — highest-conviction setups when 2+ signals align</span>
        </div>
        <div className="pb-stack-grid">
          {STACKS.map((s, i) => (
            <div key={i} className="pb-stack-card" style={{ borderLeftColor: s.color }}>
              <div className="pbs-strength" style={{ color: s.color }}>{s.strength}</div>
              <div className="pbs-signals">
                {s.signals.map(sig => (
                  <span key={sig} className="pbs-pill" style={{ borderColor: s.color, color: s.color }}>{sig}</span>
                ))}
              </div>
              <div className="pbs-result">→ {s.result}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Decision Matrix */}
      <div className="pb-section">
        <div className="pb-section-head">
          <span className="pb-section-title">Decision Matrix — which options structure fits which trigger type</span>
        </div>
        <table className="pb-table pb-dm">
          <thead>
            <tr>
              <th>Trigger Type</th>
              <th>Best Structure</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            {DECISION_MATRIX.map(row => (
              <tr key={row.trigger}>
                <td>{row.trigger}</td>
                <td>
                  <span className="pb-struct-pill" style={{ color: row.structureColor, borderColor: row.structureColor }}>
                    {row.structure}
                  </span>
                </td>
                <td style={{ color: '#9ca3af' }}>{row.why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}
