/**
 * OptionsIQ — ETF Signal Board
 * Layout: RegimeBar (top) | ETF Scanner (left) | Analysis Panel (right)
 * No tab switching. Click ETF → analysis panel opens inline.
 */
import { useEffect, useState, useCallback } from 'react';
import RegimeBar from './components/RegimeBar';
import DirectionGuide from './components/DirectionGuide';
import MasterVerdict from './components/MasterVerdict';
import GateExplainer from './components/GateExplainer';
import TradeExplainer from './components/TradeExplainer';
import TopThreeCards from './components/TopThreeCards';
import ExecutionCard from './components/ExecutionCard';
import PnLTable from './components/PnLTable';
import PaperTradeBanner from './components/PaperTradeBanner';
import CopyForChatGPT from './components/CopyForChatGPT';
import PreAnalysisPrompts from './components/PreAnalysisPrompts';
import LearnTab from './components/LearnTab';
import PaperTradeDashboard from './components/PaperTradeDashboard';
import BestSetups from './components/BestSetups';
import DataProvenance from './components/DataProvenance';
import useOptionsData from './hooks/useOptionsData';
import './index.css';

// Display labels for directions
const DIR_LABELS = {
  buy_call: 'Buy Call',
  bull_call_spread: 'Bull Call Spread',
  sell_call: 'Sell Call',
  bear_call_spread: 'Bear Call Spread',
  buy_put: 'Buy Put',
  sell_put: 'Sell Put',
};

// Map sector display hints → core 4 directions for gate engine
const SECTOR_DIR_TO_CORE = {
  buy_call: 'buy_call',
  bull_call_spread: 'buy_call',
  bear_call_spread: 'sell_call',
  sell_call: 'sell_call',
  buy_put: 'buy_put',
  sell_put: 'sell_put',
};


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

function AnalysisPanel({ ticker, direction, setDirection, data, loading, error, onAnalyze, onClose, onTradeLogged, scanContext, onScanContextChange }) {
  return (
    <div className="analysis-panel">
      <div className="analysis-panel-header">
        <div>
          <div className="analysis-panel-title">{ticker}</div>
          <div className="analysis-panel-sub">Gate Analysis · L3</div>
        </div>
        <button className="analysis-panel-close" onClick={onClose}>✕</button>
      </div>

      <QualityBanner data={data} />

      {data?.underlying_price && (
        <div className="analysis-price-row">
          <span className="underlying-label">Underlying</span>
          <span className="underlying-price">${data.underlying_price.toFixed(2)}</span>
          {data.ivr_data?.ivr_pct != null && (
            <span className={`ivr-badge ${data.ivr_data.ivr_pct > 50 ? 'ivr-high' : data.ivr_data.ivr_pct < 25 ? 'ivr-low' : 'ivr-mid'}`}>
              IVR {data.ivr_data.ivr_pct.toFixed(0)}%
            </span>
          )}
        </div>
      )}

      {/* Direction Guide — replaces bare DirectionSelector */}
      <div className="card card-sm">
        <DirectionGuide
          direction={direction}
          setDirection={setDirection}
          locked={[]}
        />
        <PreAnalysisPrompts ticker={ticker} direction={direction} />

        {/* Scan Context — paste /ibkr-scan SCAN CONTEXT block here */}
        <div style={{ marginTop: 10 }}>
          <textarea
            placeholder="Optional: paste SCAN CONTEXT from /ibkr-scan to activate live IVR, P/C ratio, and trend gate&#10;Example: TICKER=XLF  IVR=47  IV_HV=1.21  PEMA200=+3.1  PEMA50=+1.2  PC=0.85  DIRECTION=sell_put"
            value={scanContext}
            onChange={e => onScanContextChange(e.target.value)}
            style={{
              width: '100%', boxSizing: 'border-box', minHeight: 52,
              padding: '6px 8px', borderRadius: 6, border: '1px solid #334',
              background: scanContext.trim() ? '#0d2a1a' : '#151520',
              color: scanContext.trim() ? '#7fe0a0' : '#6b7280',
              fontSize: 11, fontFamily: 'monospace', resize: 'vertical',
              outline: 'none',
            }}
          />
          {scanContext.trim() && (
            <div style={{ fontSize: 10, color: '#7fe0a0', marginTop: 2 }}>
              Scan context active — IVR, P/C, and trend gates will use live IBKR data
            </div>
          )}
        </div>

        <button
          className="analyze-btn"
          style={{ marginTop: 10, width: '100%' }}
          onClick={onAnalyze}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {error && <div className="error-bar">{error}</div>}

      <MasterVerdict verdict={data?.verdict} gates={data?.gates || []} />

      <CopyForChatGPT ticker={ticker} direction={direction} data={data} />

      {/* Trade Explainer — visual "what is this trade" */}
      {data?.top_strategies?.[0] && (
        <TradeExplainer
          strategy={data.top_strategies[0]}
          underlyingPrice={data.underlying_price}
          ticker={ticker}
          direction={direction}
        />
      )}

      {/* Gate Explainer — replaces GatesGrid */}
      <GateExplainer gates={data?.gates || []} direction={direction} />

      <TopThreeCards
        strategies={data?.top_strategies || []}
        gates={data?.gates || []}
        pnlTable={data?.pnl_table}
        expectedMove1sd={data?.expected_move_1sd}
      />
      <ExecutionCard
        ticker={ticker}
        strategy={data?.top_strategies?.[0]}
        verdict={data?.verdict}
      />
      <PnLTable
        table={data?.pnl_table}
        gateFailed={false}
      />

      {/* ETF behavioral checks — regime/IV context advisories */}
      {data?.behavioral_checks?.length > 0 && (
        <div className="card">
          <div className="section-title">Advisories</div>
          {data.behavioral_checks.map(c => (
            <div key={c.id} className={`behavioral-check behavioral-check-${c.type}`}>
              <span className="bc-label">{c.label}</span>
              <span className="bc-msg">{c.message}</span>
            </div>
          ))}
        </div>
      )}

      <PaperTradeBanner ticker={ticker} direction={direction} data={data} onLogged={onTradeLogged} />
    </div>
  );
}

export default function App() {
  const { data, loading, error, analyze } = useOptionsData();

  const [selectedETF, setSelectedETF]     = useState(null);
  const [direction, setDirection]         = useState('buy_call');
  const [activeTab, setActiveTab]         = useState('setups');
  const [dashRefreshTick, setDashRefreshTick] = useState(0);
  const [scanContext, setScanContext]     = useState('');

  const handleTradeLogged = () => {
    setDashRefreshTick(t => t + 1);
    setActiveTab('dashboard');
  };



  const runAnalysis = useCallback((etfTicker, dir) => {
    const ctx = scanContext.trim();
    analyze({ ticker: etfTicker, direction: dir, ...(ctx ? { scan_context: ctx } : {}) }).catch(() => {});
  }, [analyze, scanContext]);

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

      {/* Top-level tab nav */}
      <div className="app-tab-nav">
        <button
          className={`app-tab-btn ${activeTab === 'signals' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('signals')}
        >
          Signal Board
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'learn' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('learn')}
        >
          Learn Options
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'dashboard' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'setups' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('setups')}
        >
          Today's Trade
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'data' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('data')}
        >
          Data Health
        </button>
      </div>

      {/* Always-mounted tabs — display:none preserves state across switches */}
      <div style={{ display: activeTab === 'learn' ? 'block' : 'none' }}>
        <LearnTab ticker={selectedETF?.etf} direction={direction} data={data} />
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

