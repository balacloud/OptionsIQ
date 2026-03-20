import { useEffect, useMemo, useState } from 'react';
import Header from './components/Header';
import SwingImportStrip from './components/SwingImportStrip';
import DirectionSelector from './components/DirectionSelector';
import MasterVerdict from './components/MasterVerdict';
import GatesGrid from './components/GatesGrid';
import BehavioralChecks from './components/BehavioralChecks';
import TopThreeCards from './components/TopThreeCards';
import PnLTable from './components/PnLTable';
import PaperTradeBanner from './components/PaperTradeBanner';
import SectorRotation from './components/SectorRotation';
import useOptionsData from './hooks/useOptionsData';
import useSectorData from './hooks/useSectorData';
import './index.css';

const emptySwing = {
  swing_signal: 'BUY',
  entry_pullback: '',
  entry_momentum: '',
  stop_loss: '',
  target1: '',
  target2: '',
  risk_reward: '',
  vcp_pivot: '',
  vcp_confidence: '',
  adx: '',
  last_close: '',
  s1_support: '',
  spy_above_200sma: true,
  spy_5day_return: '',
  earnings_days_away: '',
  fomc_days_away: '',
  pattern: 'VCP',
};

function QualityBanner({ data }) {
  const source  = data?.data_source;
  const quality = data?.quality;
  const asof    = data?.timestamp;

  if (!source || source === 'ibkr_live') return null;

  let cls = 'banner-cached', icon = 'i', text = '';
  if (source === 'ibkr_cache') {
    const mins = asof ? Math.round((Date.now() - new Date(asof + 'Z').getTime()) / 60000) : '?';
    text = `Using cached chain — data from ${mins} min ago. Refreshing in background.`;
    cls = 'banner-cached';
    icon = 'i';
  } else if (source === 'ibkr_stale') {
    const mins = asof ? Math.round((Date.now() - new Date(asof + 'Z').getTime()) / 60000) : '?';
    text = `Stale IBKR cache (${mins} min old) — IBKR currently unavailable. Refreshing in background.`;
    cls = 'banner-delayed';
    icon = '!';
  } else if (source === 'ibkr_closed') {
    text = 'Market closed — using estimated greeks (Black-Scholes + 20-day HV). No bid/ask/OI data. Use for directional setup review only.';
    cls = 'banner-delayed';
    icon = '!';
  } else if (source === 'alpaca') {
    text = 'Using Alpaca fallback — 15-min delayed data. No OI or volume data available. Verify liquidity before trading.';
    cls = 'banner-delayed';
    icon = '!';
  } else if (source === 'yfinance') {
    text = 'Live data unavailable — using yfinance. Greeks are estimated via Black-Scholes.';
    cls = 'banner-delayed';
    icon = '!';
  } else if (source === 'mock') {
    text = 'MOCK DATA — for development only. Do not paper trade.';
    cls = 'banner-mock';
    icon = '!';
  } else if (quality === 'partial') {
    text = 'Partial chain — some greeks may be missing. Verify strikes manually.';
    cls = 'banner-delayed';
    icon = '!';
  } else {
    return null;
  }

  return (
    <div className={`quality-banner ${cls}`}>
      <span className="banner-icon">{icon}</span>
      <span className="banner-text">{text}</span>
    </div>
  );
}

export default function App() {
  const { data, loading, error, analyze } = useOptionsData();
  const sectorHook = useSectorData();
  const [activeTab, setActiveTab] = useState('analyze'); // 'analyze' | 'sectors'
  const [ticker, setTicker]     = useState('');
  const [direction, setDirection] = useState('buy_call');
  const [swing, setSwing]       = useState(emptySwing);
  const [ibModal, setIbModal]   = useState(false);

  // Deep dive from sector tab → switch to analyze tab with ETF pre-filled
  // Map bull_call_spread → buy_call for L3 gate_engine (only knows 4 core directions)
  const SECTOR_DIR_TO_CORE = {
    buy_call: 'buy_call',
    bull_call_spread: 'buy_call',
    sell_call: 'sell_call',
    buy_put: 'buy_put',
    sell_put: 'sell_put',
  };
  const handleSectorDeepDive = (etf) => {
    const deepTicker = etf.etf;
    const coreDir = SECTOR_DIR_TO_CORE[etf.suggested_direction] || 'buy_call';
    setTicker(deepTicker);
    setDirection(coreDir);
    setActiveTab('analyze');
    // Auto-trigger L3 analysis — use values directly (React state is async)
    analyze({ direction: coreDir, ...swing, ticker: deepTicker }).catch(() => {});
  };

  const lockedBySignal = useMemo(() => {
    if (swing.swing_signal === 'BUY')  return ['sell_call', 'buy_put'];
    if (swing.swing_signal === 'SELL') return ['buy_call', 'sell_put'];
    return [];
  }, [swing.swing_signal]);

  useEffect(() => {
    if (swing.swing_signal === 'BUY') {
      setDirection((d) => (d === 'sell_call' || d === 'buy_put' ? 'buy_call' : d));
    }
  }, [swing.swing_signal]);

  const onAnalyze = async () => {
    if (!ticker.trim()) return;
    try {
      await analyze({ direction, ...swing, ticker: ticker.trim().toUpperCase() });
    } catch (_) {}
  };

  // Support deep-link from STA: ?ticker=AMD&auto=true&swing_data={...}
  useEffect(() => {
    const params     = new URLSearchParams(window.location.search);
    const urlTicker  = params.get('ticker');
    const auto       = params.get('auto') === 'true';
    const swingParam = params.get('swing_data');
    if (urlTicker) setTicker(urlTicker.toUpperCase());
    if (swingParam) {
      try {
        const parsed = JSON.parse(swingParam);
        setSwing((s) => ({ ...s, ...parsed }));
      } catch (_) {}
    }
    if (auto && urlTicker) {
      analyze({ direction, ...swing, ticker: urlTicker.toUpperCase() }).catch(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="app-shell">
      <QualityBanner data={data} />

      {/* ── Tab Bar ── */}
      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Analyze
        </button>
        <button
          className={`tab-btn ${activeTab === 'sectors' ? 'active' : ''}`}
          onClick={() => setActiveTab('sectors')}
        >
          Sectors
        </button>
      </div>

      {/* ── Analyze Tab ── */}
      {activeTab === 'analyze' && (
        <div className="app-layout">
          {/* ── Left Panel: controls + verdict ── */}
          <aside className="left-panel">
            <Header
              ticker={ticker}
              data={data}
              onIbClick={() => setIbModal(true)}
            />

            {/* Ticker + Analyze */}
            <div className="card card-sm">
              <div className="ticker-bar">
                <input
                  className="ticker-input"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="AMD"
                  maxLength={8}
                />
                <button className="analyze-btn" onClick={onAnalyze} disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
              {data?.underlying_price && (
                <div style={{ marginTop: 10 }}>
                  <div className="underlying-label">{data.ticker} underlying</div>
                  <div className="underlying-price">${data.underlying_price.toFixed(2)}</div>
                </div>
              )}
            </div>

            {/* Direction */}
            <div className="card card-sm">
              <div className="section-title">Direction</div>
              <DirectionSelector
                direction={direction}
                setDirection={setDirection}
                swingSignal={swing.swing_signal}
                locked={lockedBySignal}
              />
            </div>

            {/* Master Verdict */}
            <MasterVerdict verdict={data?.verdict} gates={data?.gates || []} />

            {/* Swing Import — collapsible */}
            <SwingImportStrip swing={swing} setSwing={setSwing} ticker={ticker} />
          </aside>

          {/* ── Right Panel: results ── */}
          <main className="right-panel">
            {error && <div className="error-bar">{error}</div>}

            <GatesGrid gates={data?.gates || []} />
            <TopThreeCards
              strategies={data?.top_strategies || []}
              gates={data?.gates || []}
              pnlTable={data?.pnl_table}
            />
            <PnLTable
              table={data?.pnl_table}
              gateFailed={(data?.gates || []).some((g) => g.id === 'pivot_confirm' && g.status === 'fail')}
            />
            <BehavioralChecks checks={data?.behavioral_checks || []} />
            <PaperTradeBanner ticker={ticker} direction={direction} data={data} />
          </main>
        </div>
      )}

      {/* ── Sectors Tab ── */}
      {activeTab === 'sectors' && (
        <SectorRotation
          sectorData={sectorHook.sectors}
          loading={sectorHook.loading}
          detailLoading={sectorHook.detailLoading}
          error={sectorHook.error}
          etfDetail={sectorHook.etfDetail}
          onScan={sectorHook.scanSectors}
          onAnalyzeETF={(ticker) => sectorHook.analyzeETF(ticker).catch(() => {})}
          onClearDetail={sectorHook.clearDetail}
          onDeepDive={handleSectorDeepDive}
        />
      )}

      {/* IB Gateway modal */}
      {ibModal && (
        <div className="modal" onClick={() => setIbModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">IB Gateway Connection</div>
            <div className="modal-body">
              Start IB Gateway or TWS and enable API connections.<br /><br />
              <strong>Default ports:</strong><br />
              7497 — TWS Paper Trading<br />
              7496 — TWS Live Trading<br />
              4001 — IB Gateway Live<br />
              4002 — IB Gateway Paper
            </div>
            <div className="modal-footer">
              <button className="btn-primary" onClick={() => setIbModal(false)}>Got it</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
