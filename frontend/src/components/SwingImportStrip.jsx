import { useState } from 'react';

const fields = ['entry_pullback', 'entry_momentum', 'stop_loss', 'target1', 'target2', 'risk_reward', 'vcp_pivot', 'vcp_confidence', 'adx', 'last_close', 's1_support', 'spy_5day_return', 'earnings_days_away'];

export default function SwingImportStrip({ swing, setSwing }) {
  const [live, setLive] = useState(false);

  const connect = async () => {
    const res = await fetch('http://localhost:5051/api/integrate/status', { method: 'POST' });
    setLive(res.ok);
  };

  return (
    <section className="card strip">
      <div className="row-between">
        <strong>Swing Import</strong>
        <span className={`badge ${live ? 'green-b' : 'amber-b'}`}>{live ? '● LIVE' : '✎ MANUAL'}</span>
      </div>
      <div className="grid2">
        <label>Signal<select value={swing.swing_signal} disabled={live} onChange={(e) => setSwing({ ...swing, swing_signal: e.target.value })}><option>BUY</option><option>HOLD</option><option>AVOID</option></select></label>
        <label>Pattern<select value={swing.pattern} disabled={live} onChange={(e) => setSwing({ ...swing, pattern: e.target.value })}><option>VCP</option><option>Cup&Handle</option><option>FlatBase</option><option>None</option></select></label>
      </div>
      <div className="grid4">
        {fields.map((f) => (
          <label key={f}>{f}
            <input
              value={swing[f]}
              disabled={live}
              onChange={(e) => setSwing({ ...swing, [f]: ['earnings_days_away'].includes(f) ? Number(e.target.value) : Number(e.target.value) })}
            />
          </label>
        ))}
        <label>spy_above_200sma
          <select value={String(swing.spy_above_200sma)} disabled={live} onChange={(e) => setSwing({ ...swing, spy_above_200sma: e.target.value === 'true' })}>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </label>
      </div>
      <button onClick={connect}>Connect to Swing Analyzer</button>
    </section>
  );
}
