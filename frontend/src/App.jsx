/**
 * OptionsIQ — ETF Signal Board
 * Layout: RegimeBar (top) | ETF Scanner (left) | Analysis Panel (right)
 * No tab switching. Click ETF → analysis panel opens inline.
 */
import { useState, useCallback } from 'react';
import RegimeBar from './components/RegimeBar';
import PlaybookTab from './components/PlaybookTab';
import MasterVerdict from './components/MasterVerdict';
import GateExplainer from './components/GateExplainer';
import TradeExplainer from './components/TradeExplainer';
import TopThreeCards from './components/TopThreeCards';
import ExecutionCard from './components/ExecutionCard';
import PnLTable from './components/PnLTable';
import PaperTradeBanner from './components/PaperTradeBanner';
import CopyForChatGPT from './components/CopyForChatGPT';
import LearnTab from './components/LearnTab';
import PaperTradeDashboard from './components/PaperTradeDashboard';
import BestSetups from './components/BestSetups';
import DataProvenance from './components/DataProvenance';
import useOptionsData from './hooks/useOptionsData';
import './index.css';




function QualityBanner({ data }) {
  const source = data?.data_source;
  // tradier = real-time live (same tier as ibkr_live) — no banner needed
  if (!source || source === 'ibkr_live' || source === 'tradier') return null;

  const BANNERS = {
    bod_cache:    { cls: 'banner-cached',  icon: 'i', text: () => 'BOD cache — pre-warmed this morning via Tradier. Chain is from ~9:31 AM ET.' },
    ibkr_stale:   { cls: 'banner-delayed', icon: '!', text: () => 'Stale cache — Tradier unavailable, using last known-good chain.' },
    ibkr_closed:  { cls: 'banner-delayed', icon: '!', text: () => 'Market closed — estimated greeks (BS + HV). No bid/ask/OI.' },
    alpaca:       { cls: 'banner-delayed', icon: '!', text: () => 'Alpaca fallback — 15-min delayed. No OI/volume.' },
    yfinance:     { cls: 'banner-delayed', icon: '!', text: () => 'yfinance fallback — greeks estimated via Black-Scholes.' },
    mock:         { cls: 'banner-mock',    icon: '!', text: () => 'MOCK DATA — do not paper trade.' },
  };
  const b = BANNERS[source];
  if (!b) return null;
  return (
    <div className={`quality-banner ${b.cls}`}>
      <span className="banner-icon">{b.icon}</span>
      <span className="banner-text">{b.text(data)}</span>
    </div>
  );
}

function ContextChips({ scanContext, chartVerdict, catalystVerdict }) {
  if (!scanContext?.trim() && !chartVerdict && !catalystVerdict) return null;
  const chartStyle = { go: { color: '#7fe0a0', label: '📈 Chart GO ✅' }, wait: { color: '#e0b87e', label: '📈 Chart WAIT ⚠️' }, block: { color: '#e05252', label: '📈 Chart BLOCK ❌' } };
  const catStyle   = { proceed: { color: '#7fe0a0', label: '📅 Events ✅' }, caution: { color: '#e0b87e', label: '📅 Events ⚠️' }, abort: { color: '#e05252', label: '📅 Events ❌' } };
  return (
    <div className="context-chips">
      {scanContext?.trim()  && <span className="context-chip scan">📊 SCAN ✅</span>}
      {chartVerdict && chartStyle[chartVerdict]    && <span className="context-chip" style={{ color: chartStyle[chartVerdict].color }}>{chartStyle[chartVerdict].label}</span>}
      {catalystVerdict && catStyle[catalystVerdict] && <span className="context-chip" style={{ color: catStyle[catalystVerdict].color }}>{catStyle[catalystVerdict].label}</span>}
    </div>
  );
}

function AnalysisPanel({ ticker, direction, setDirection, data, loading, error, onAnalyze, onClose, onTradeLogged, scanContext, onScanContextChange, chartCatalystContext, onChartCatalystContextChange }) {
  const [selectedRank, setSelectedRank] = useState(null);
  const hasData = !!data?.top_strategies?.[0];
  const strategyForLog = selectedRank
    ? data?.top_strategies?.find(s => s.rank === selectedRank)
    : data?.top_strategies?.[0];

  return (
    <div className="analysis-panel">
      {/* ── Header ── */}
      <div className="analysis-panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div>
            <div className="analysis-panel-title">{ticker}</div>
            <div className="analysis-panel-sub">Options Analysis</div>
          </div>
          {data?.underlying_price && (
            <span className="underlying-price" style={{ fontSize: 18, marginLeft: 8 }}>
              ${data.underlying_price.toFixed(2)}
            </span>
          )}
          {data?.ivr_data?.ivr_pct != null && (
            <span className={`ivr-badge ${data.ivr_data.ivr_pct > 50 ? 'ivr-high' : data.ivr_data.ivr_pct < 25 ? 'ivr-low' : 'ivr-mid'}`}>
              IVR {data.ivr_data.ivr_pct.toFixed(0)}%
            </span>
          )}
        </div>
        <button className="analysis-panel-close" onClick={onClose}>✕</button>
      </div>

      <QualityBanner data={data} />

      {/* ── Setup zone — direction + 3-column context inputs ── */}
      <div className="card card-sm">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', flexShrink: 0 }}>Direction:</span>
          <select
            value={direction}
            onChange={e => setDirection(e.target.value)}
            style={{ background: '#1a1a2e', color: '#e0e0e0', border: '1px solid #334', borderRadius: 4, padding: '3px 6px', fontSize: 12 }}
          >
            <option value="sell_put">Sell Put</option>
            <option value="sell_call">Sell Call</option>
            <option value="buy_call">Buy Call</option>
            <option value="buy_put">Buy Put</option>
          </select>
        </div>

        {/* 2-column context grid — box 2 accepts full /chartreview output (CHART CONTEXT + CATALYST CONTEXT lines together) */}
        <div className="context-grid">
          <div className="context-input-col">
            <div className="context-input-label">1 — SCAN CONTEXT <span style={{ color: '#7fe0a0' }}>/ibkr-scan</span></div>
            <textarea
              placeholder="TICKER=QQQ  IVR=75  IV_HV=1.299  PC=1.008  PEMA200=+20.49  PEMA50=+10.04  DIRECTION=sell_put"
              value={scanContext}
              onChange={e => onScanContextChange(e.target.value)}
              className={`context-textarea scan${scanContext.trim() ? ' active' : ''}`}
            />
            {scanContext.trim() && <div className="context-active-msg scan">✓ IVR · P/C · trend gates active</div>}
          </div>
          <div className="context-input-col">
            <div className="context-input-label">2 — CHART + CATALYST CONTEXT <span style={{ color: '#7ec8e0' }}>/chartreview</span></div>
            <textarea
              placeholder={"CHART CONTEXT  TICKER=QQQ  TREND=UPTREND  S1=710.00  S2=695.00  R1=748.00  CHART_VERDICT=go\nCATALYST CONTEXT  TICKER=QQQ  FOMC_DAYS=16  FOMC_TIER=warn  HOLDINGS_RISK=true  CATALYST_VERDICT=caution"}
              value={chartCatalystContext}
              onChange={e => onChartCatalystContextChange(e.target.value)}
              className={`context-textarea chartcatalyst${chartCatalystContext.trim() ? ' active' : ''}`}
            />
            {chartCatalystContext.trim() && <div className="context-active-msg chartcatalyst">✓ Strike vs support · Event risk active</div>}
          </div>
        </div>

        <button className="analyze-btn" style={{ marginTop: 10, width: '100%' }} onClick={onAnalyze} disabled={loading}>
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {error && <div className="error-bar">{error}</div>}

      {/* ── Decision zone — only when data exists ── */}
      {hasData && (
        <>
          {/* Context status chips */}
          <ContextChips
            scanContext={scanContext}
            chartVerdict={data?.chart_verdict}
            catalystVerdict={data?.catalyst_summary?.catalyst_verdict}
          />

          {/* Two-column layout: verdict left, trade right */}
          <div className="decision-layout">
            <div className="verdict-col">
              <MasterVerdict verdict={data?.verdict} gates={data?.gates || []} compact={true} />
            </div>
            <div className="trade-col">
              <TopThreeCards
                strategies={data?.top_strategies || []}
                gates={data?.gates || []}
                pnlTable={data?.pnl_table}
                expectedMove1sd={data?.expected_move_1sd}
                chartVerdict={data?.chart_verdict}
                selectedRank={selectedRank}
                onSelectRank={setSelectedRank}
              />
              {/* Log Paper Trade — inline under the trade cards */}
              <PaperTradeBanner
                ticker={ticker}
                direction={direction}
                data={selectedRank ? { ...data, top_strategies: [strategyForLog, ...(data?.top_strategies?.filter(s => s.rank !== selectedRank) || [])] } : data}
                onLogged={onTradeLogged}
              />
            </div>
          </div>

          {/* Below-fold collapsibles — educational/detail */}
          <details className="below-fold-section">
            <summary>Understand this trade</summary>
            <TradeExplainer strategy={data.top_strategies[0]} underlyingPrice={data.underlying_price} ticker={ticker} direction={direction} />
          </details>

          <details className="below-fold-section">
            <summary>All {data?.gates?.length ?? 0} gate checks</summary>
            <GateExplainer gates={data?.gates || []} direction={direction} />
          </details>

          <details className="below-fold-section">
            <summary>Place in IBKR</summary>
            <ExecutionCard ticker={ticker} strategy={data?.top_strategies?.[0]} verdict={data?.verdict} />
          </details>

          <details className="below-fold-section">
            <summary>P&amp;L table</summary>
            <PnLTable table={data?.pnl_table} gateFailed={false} />
          </details>

          {data?.behavioral_checks?.length > 0 && (
            <details className="below-fold-section">
              <summary>Advisories ({data.behavioral_checks.length})</summary>
              <div className="card" style={{ marginTop: 0 }}>
                {data.behavioral_checks.map(c => (
                  <div key={c.id} className={`behavioral-check behavioral-check-${c.type}`}>
                    <span className="bc-label">{c.label}</span>
                    <span className="bc-msg">{c.message}</span>
                  </div>
                ))}
              </div>
            </details>
          )}

          <div style={{ textAlign: 'right', marginTop: 8 }}>
            <CopyForChatGPT ticker={ticker} direction={direction} data={data} />
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const { data, loading, error, analyze } = useOptionsData();

  const [selectedETF, setSelectedETF]     = useState(null);
  const [direction, setDirection]         = useState('buy_call');
  const [activeTab, setActiveTab]         = useState('setups');
  const [dashRefreshTick, setDashRefreshTick] = useState(0);
  const [scanContext, setScanContext]               = useState('');
  const [chartCatalystContext, setChartCatalystContext] = useState('');

  const handleTradeLogged = () => {
    setDashRefreshTick(t => t + 1);
    setActiveTab('dashboard');
  };



  const runAnalysis = useCallback((etfTicker, dir) => {
    const ctx      = scanContext.trim();
    const chartCat = chartCatalystContext.trim();
    analyze({
      ticker: etfTicker, direction: dir,
      ...(ctx      ? { scan_context: ctx } : {}),
      ...(chartCat ? { chart_context: chartCat, catalyst_context: chartCat } : {}),
    }).catch(() => {});
  }, [analyze, scanContext, chartCatalystContext]);

  // Select from Today's Trade → switch to signal board with ETF pre-analyzed
  const handleSelectFromSetups = useCallback((ticker, direction) => {
    setSelectedETF({ etf: ticker, suggested_direction: direction });
    setDirection(direction);
    runAnalysis(ticker, direction);
    setActiveTab('signals');
  }, [runAnalysis]);

  // Direction override in analysis panel → re-run
  const handleDirectionChange = useCallback((newDir) => {
    setDirection(newDir);
    if (selectedETF) runAnalysis(selectedETF.etf, newDir);
  }, [selectedETF, runAnalysis]);

  // Explicit "Run Analysis" button in panel
  const handleReanalyze = useCallback(() => {
    if (selectedETF) runAnalysis(selectedETF.etf, direction);
  }, [selectedETF, direction, runAnalysis]);

  const hasAnalysisPanel = !!selectedETF;

  return (
    <div className="app-shell">
      {/* Regime bar — always visible */}
      <RegimeBar />

      {/* Top-level tab nav — 4 primary tabs + ⚙ overflow */}
      <div className="app-tab-nav">
        <button
          className={`app-tab-btn ${activeTab === 'setups' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('setups')}
        >
          Today's Trade
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'signals' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('signals')}
        >
          Signal Board
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'dashboard' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Paper Trades
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'learn' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('learn')}
        >
          Learn
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'playbook' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('playbook')}
        >
          Playbook
        </button>
        {/* ⚙ overflow — maintenance/debug tools */}
        <button
          className={`app-tab-btn ${activeTab === 'data' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('data')}
          title="Data Health — infrastructure monitoring"
          style={{ marginLeft: 'auto', opacity: 0.6, fontSize: 14 }}
        >
          ⚙
        </button>
      </div>

      {/* Always-mounted tabs — display:none preserves state across switches */}
      <div style={{ display: activeTab === 'learn' ? 'block' : 'none' }}>
        <LearnTab ticker={selectedETF?.etf} direction={direction} data={data} />
      </div>
      <div style={{ display: activeTab === 'playbook' ? 'block' : 'none' }}>
        <PlaybookTab />
      </div>
      <div style={{ display: activeTab === 'dashboard' ? 'block' : 'none' }}><PaperTradeDashboard refreshTick={dashRefreshTick} /></div>
      <div style={{ display: activeTab === 'setups' ? 'block' : 'none' }}><BestSetups onSelect={handleSelectFromSetups} /></div>
      <div style={{ display: activeTab === 'data' ? 'block' : 'none' }}><DataProvenance /></div>

      <div style={{ display: activeTab === 'signals' ? undefined : 'none' }}>
        {hasAnalysisPanel ? (
          <AnalysisPanel
            ticker={selectedETF.etf}
            direction={direction}
            setDirection={handleDirectionChange}
            data={data}
            loading={loading}
            error={error}
            onAnalyze={handleReanalyze}
            onClose={() => setSelectedETF(null)}
            onTradeLogged={handleTradeLogged}
            scanContext={scanContext}
            onScanContextChange={setScanContext}
            chartCatalystContext={chartCatalystContext}
            onChartCatalystContextChange={setChartCatalystContext}
          />
        ) : (
          <div className="analysis-empty">
            <div className="analysis-empty-icon">↑</div>
            <div className="analysis-empty-msg">Select an ETF from Today's Trade</div>
          </div>
        )}
      </div>
    </div>
  );
}

