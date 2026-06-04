import { useState } from 'react';

const ETF_UNIVERSE = [
  { ticker: 'QQQ',  desc: 'Nasdaq-100',    defaultDir: 'sell_put' },
  { ticker: 'IWM',  desc: 'Small Cap',     defaultDir: 'sell_put' },
  { ticker: 'XLF',  desc: 'Financials',    defaultDir: 'sell_put' },
  { ticker: 'GLD',  desc: 'Gold',          defaultDir: 'sell_put' },
  { ticker: 'TQQQ', desc: '3× Nasdaq',     defaultDir: 'sell_put', satellite: true },
  { ticker: 'SPY',  desc: 'Regime Anchor', regimeOnly: true },
];

const DIRECTIONS = [
  { value: 'sell_put',  label: 'Sell Put',  note: 'Neutral-bullish · collect premium' },
  { value: 'sell_call', label: 'Sell Call', note: 'Neutral-bearish · collect premium' },
  { value: 'buy_call',  label: 'Buy Call',  note: 'Directional bullish' },
  { value: 'buy_put',   label: 'Buy Put',   note: 'Directional bearish' },
];

export default function BestSetups({ onSelect }) {
  const [selectedETF, setSelectedETF] = useState(null);
  const [direction, setDirection]     = useState('sell_put');

  const handleETFClick = (etf) => {
    if (etf.regimeOnly) return;
    setSelectedETF(etf.ticker);
    setDirection(etf.defaultDir || 'sell_put');
  };

  const handleAnalyze = () => {
    if (selectedETF && onSelect) onSelect(selectedETF, direction);
  };

  const selectedMeta = ETF_UNIVERSE.find(e => e.ticker === selectedETF);
  const dirLabel = DIRECTIONS.find(d => d.value === direction)?.label;

  return (
    <div className="tt-wrap">
      {/* Header */}
      <div className="tt-header">
        <div className="tt-title">Today's Trade</div>
        <div className="tt-sub">
          Use <code className="tt-code">/ibkr-scan</code> to identify which ETF to trade, then select it below.
        </div>
      </div>

      {/* Workflow steps */}
      <div className="tt-steps">
        <div className="tt-step">
          <span className="tt-step-n">1</span>
          Run <code className="tt-code">/ibkr-scan</code> in browser (MCP auto-pulls all 6 ETFs + screenshot) → names top pick
        </div>
        <div className="tt-step">
          <span className="tt-step-n">2</span>
          Run <code className="tt-code">/chartreview</code> + <code className="tt-code">/catalyst-check</code> → copy all 3 context blocks
        </div>
        <div className="tt-step">
          <span className="tt-step-n">3</span>
          Select ETF below → paste 3 contexts → Run Analysis → log paper trade
        </div>
      </div>

      {/* ETF selector grid */}
      <div className="tt-section-label">Select ETF</div>
      <div className="tt-etf-grid">
        {ETF_UNIVERSE.map(etf => (
          <button
            key={etf.ticker}
            className={[
              'tt-etf-btn',
              selectedETF === etf.ticker ? 'tt-etf-selected' : '',
              etf.regimeOnly  ? 'tt-etf-regime'    : '',
              etf.satellite   ? 'tt-etf-satellite'  : '',
            ].filter(Boolean).join(' ')}
            onClick={() => handleETFClick(etf)}
            disabled={etf.regimeOnly}
            title={etf.regimeOnly ? 'SPY is regime anchor only — no trades' : etf.desc}
          >
            <div className="tt-etf-ticker">{etf.ticker}</div>
            <div className="tt-etf-desc">{etf.desc}</div>
            {etf.satellite  && <div className="tt-etf-tag">satellite</div>}
            {etf.regimeOnly && <div className="tt-etf-tag tt-etf-tag-dim">regime only</div>}
          </button>
        ))}
      </div>

      {/* Direction picker + Analyze — shown after ETF selected */}
      {selectedETF && !selectedMeta?.regimeOnly && (
        <>
          <div className="tt-section-label" style={{ marginTop: 20 }}>Direction</div>
          <div className="tt-dir-grid">
            {DIRECTIONS.map(d => (
              <button
                key={d.value}
                className={`tt-dir-btn ${direction === d.value ? 'tt-dir-selected' : ''}`}
                onClick={() => setDirection(d.value)}
              >
                <div className="tt-dir-label">{d.label}</div>
                <div className="tt-dir-note">{d.note}</div>
              </button>
            ))}
          </div>

          {/* TQQQ satellite rules */}
          {selectedETF === 'TQQQ' && (
            <div className="tt-rules tt-rules-blue">
              <span className="tt-rules-icon">⚡</span>
              <span>
                <strong>TQQQ satellite:</strong> delta ≤ 0.10 · VIX &lt; 18 · QQQ above 200+50 EMA ·
                exit 25% profit or 14 DTE · 1–2% account risk only
              </span>
            </div>
          )}

          {/* GLD rules */}
          {selectedETF === 'GLD' && (direction === 'sell_put' || direction === 'sell_call') && (
            <div className="tt-rules tt-rules-amber">
              <span className="tt-rules-icon">◈</span>
              <span>
                <strong>GLD rules:</strong> IVR ≥ 35 + IV/HV ≥ 1.10 required ·
                delta 0.15–0.20 · hard stop 2–3× premium · no rolling down
              </span>
            </div>
          )}

          {/* Analyze CTA */}
          <button className="tt-analyze-btn" onClick={handleAnalyze}>
            Analyze {selectedETF} · {dirLabel} →
          </button>
        </>
      )}

      {/* Hint when nothing selected */}
      {!selectedETF && (
        <div className="tt-hint">↑ Select an ETF from your /ibkr-scan result</div>
      )}
    </div>
  );
}
