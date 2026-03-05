import { useState } from 'react';

export default function Header({ ticker, data }) {
  const [show, setShow] = useState(false);
  const connected = !!data?.ibkr_connected;
  const source = data?.data_source || 'mock';
  const quality = data?.quality || (source === 'ibkr' ? 'full' : source === 'ibkr_cache' ? 'cached' : source === 'ibkr_partial' ? 'partial' : 'mock');
  const sourceMap = {
    ibkr: { label: 'IB Live', cls: 'src-live' },
    ibkr_cache: { label: 'IB Cache', cls: 'src-cache' },
    ibkr_partial: { label: 'IB Partial', cls: 'src-partial' },
    mock: { label: 'Mock Fallback', cls: 'src-mock' },
  };
  const qualityMap = {
    full: { label: 'Quality: Full', cls: 'q-full' },
    cached: { label: 'Quality: Cached', cls: 'q-cached' },
    partial: { label: 'Quality: Partial', cls: 'q-partial' },
    mock: { label: 'Quality: Mock', cls: 'q-mock' },
  };
  const sourceUi = sourceMap[source] || { label: source, cls: 'src-mock' };
  const qualityUi = qualityMap[quality] || qualityMap.mock;
  const showWarning = quality !== 'full';
  return (
    <header className="header card">
      <div>
        <h1>OptionsIQ 2.0</h1>
        <div className="sub">{ticker} · ${data?.underlying_price ?? '--'}</div>
        <div className={`source-pill ${sourceUi.cls}`}>{sourceUi.label}</div>
        <div className={`quality-pill ${qualityUi.cls}`}>{qualityUi.label}</div>
        {showWarning ? <div className="quality-note">Live options fields are degraded; verify execution manually.</div> : null}
      </div>
      <button className="ib-status" onClick={() => setShow(true)}>
        <span className={connected ? 'dot green' : 'dot red'}>{connected ? '● IB Gateway' : '○ Mock Mode'}</span>
      </button>
      {show ? (
        <div className="modal" onClick={() => setShow(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            Start IB Gateway/TWS on your configured API port (current setup uses 4001; common defaults are 7497 paper, 7496 live).
            <button onClick={() => setShow(false)}>Close</button>
          </div>
        </div>
      ) : null}
    </header>
  );
}
