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
import useSectorData from './hooks/useSectorData';
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

const FILTER_OPTIONS = ['all', 'analyze', 'watch', 'skip'];

function QualityBanner({ data }) {
  const source = data?.data_source;
  if (!source || source === 'ibkr_live') return null;

  const BANNERS = {
    ibkr_cache:   { cls: 'banner-cached',  icon: 'i', text: (d) => `Cached chain — ${Math.round((Date.now() - new Date(d.timestamp + 'Z').getTime()) / 60000)} min old.` },
    ibkr_stale:   { cls: 'banner-delayed', icon: '!', text: (d) => `Stale IBKR cache — IBKR unavailable.` },
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

function AnalysisPanel({ ticker, direction, setDirection, data, loading, error, onAnalyze, onClose, onTradeLogged }) {
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
  const sectorHook = useSectorData();

  const [selectedETF, setSelectedETF]     = useState(null);    // { etf, suggested_direction, ... }
  const [direction, setDirection]         = useState('buy_call');
  const [filter, setFilter]               = useState('all');
  const [l2ETF, setL2ETF]                 = useState(null);    // ETF being shown in L2 detail
  const [activeTab, setActiveTab]         = useState('setups'); // 'setups' is the home screen
  const [seedIVState, setSeedIVState]     = useState({ loading: false, result: null, error: null });
  const [dashRefreshTick, setDashRefreshTick] = useState(0);

  const handleTradeLogged = () => {
    setDashRefreshTick(t => t + 1);
    setActiveTab('dashboard');
  };

  const handleSeedIV = async () => {
    setSeedIVState({ loading: true, result: null, error: null });
    try {
      const res = await fetch('/api/admin/seed-iv/all', { method: 'POST' });
      if (!res.ok) {
        const text = await res.text();
        setSeedIVState({ loading: false, result: null, error: `Seed failed (HTTP ${res.status}) — ${text.slice(0, 120)}` });
        setTimeout(() => setSeedIVState(s => ({ ...s, error: null })), 8000);
        return;
      }
      const data = await res.json();
      setSeedIVState({ loading: false, result: data, error: null });
      setTimeout(() => setSeedIVState(s => ({ ...s, result: null })), 10000);
    } catch (e) {
      setSeedIVState({ loading: false, result: null, error: 'Seed failed — backend not reachable. Is it running?' });
      setTimeout(() => setSeedIVState(s => ({ ...s, error: null })), 8000);
    }
  };

  const seedIVMessage = (result) => {
    if (!result) return null;
    if (result.pacing_warning) {
      return { type: 'warn', text: 'IBKR pacing limit hit — nothing new pulled. Wait ~10 min and retry. Your existing data is intact.' };
    }
    const sources = result.sources_used?.length ? result.sources_used.join(' + ') : 'unknown';
    const sourceLabel = sources.includes('ibkr') ? 'IBKR' : sources.includes('yfinance') ? 'yfinance (HV proxy)' : sources;
    const errNote = result.errors?.length ? ` · ${result.errors.length} ticker${result.errors.length > 1 ? 's' : ''} failed` : '';
    return {
      type: result.errors?.length ? 'warn' : 'ok',
      text: `✓ Seeded ${result.total_iv_rows} rows from ${sourceLabel} across ${result.tickers_seeded} ETFs${errNote}`,
    };
  };

  // Auto-trigger sector scan on mount — swallow error, hook stores it in sectorHook.error
  useEffect(() => {
    if (!sectorHook.sectors) sectorHook.scanSectors().catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const sectors = sectorHook.sectors?.sectors || [];

  const counts = {
    all:     sectors.length,
    analyze: sectors.filter(s => s.action === 'ANALYZE').length,
    watch:   sectors.filter(s => s.action === 'WATCH').length,
    skip:    sectors.filter(s => s.action === 'SKIP').length,
  };

  const filtered = filter === 'all'
    ? sectors
    : sectors.filter(s => s.action === filter.toUpperCase());

  const runAnalysis = useCallback((etfTicker, dir) => {
    analyze({ ticker: etfTicker, direction: dir }).catch(() => {});
  }, [analyze]);

  // Click ETF card: set active ETF, auto-direction from regime, trigger L3 analysis
  const handleSelectETF = useCallback((etf) => {
    const coreDir = SECTOR_DIR_TO_CORE[etf.suggested_direction] || 'buy_call';
    setSelectedETF(etf);
    setDirection(coreDir);
    setL2ETF(null);
    runAnalysis(etf.etf, coreDir);
  }, [runAnalysis]);

  // Select from Best Setups → switch to signal board with ETF pre-analyzed
  const handleSelectFromSetups = useCallback((ticker, direction) => {
    const fakeEtf = { etf: ticker, suggested_direction: direction };
    setSelectedETF(fakeEtf);
    setDirection(direction);
    setL2ETF(null);
    runAnalysis(ticker, direction);
    setActiveTab('signals');
  }, [runAnalysis]);

  // L2 detail expand
  const handleL2 = useCallback((etf) => {
    if (etf.etf === l2ETF) { setL2ETF(null); sectorHook.clearDetail(); return; }
    setL2ETF(etf.etf);
    sectorHook.analyzeETF(etf.etf).catch(() => {});
  }, [l2ETF, sectorHook]);

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
      <RegimeBar sectorData={sectorHook.sectors} />

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
          Best Setups
        </button>
        <button
          className={`app-tab-btn ${activeTab === 'data' ? 'app-tab-active' : ''}`}
          onClick={() => setActiveTab('data')}
        >
          Data Health
        </button>
      </div>

      {/* Always-mounted tabs — display:none preserves state across switches */}
      <div style={{ display: activeTab === 'learn' ? 'block' : 'none' }}><LearnTab /></div>
      <div style={{ display: activeTab === 'dashboard' ? 'block' : 'none' }}><PaperTradeDashboard refreshTick={dashRefreshTick} /></div>
      <div style={{ display: activeTab === 'setups' ? 'block' : 'none' }}><BestSetups onSelect={handleSelectFromSetups} /></div>
      <div style={{ display: activeTab === 'data' ? 'block' : 'none' }}><DataProvenance /></div>

      <div style={{ display: activeTab === 'signals' ? undefined : 'none' }} className={`signal-board ${hasAnalysisPanel ? 'signal-board-split' : ''}`}>
        {/* ── Left: ETF Scanner ── */}
        <div className="scanner-panel">
          <div className="scanner-header">
            <div className="scanner-title">ETF Signal Scanner</div>
            <div className="scanner-header-actions">
              <button
                className="sector-refresh-btn"
                onClick={sectorHook.scanSectors}
                disabled={sectorHook.loading}
              >
                {sectorHook.loading ? 'Scanning...' : '↻ Scan'}
              </button>
              <button
                className="seed-iv-btn"
                onClick={handleSeedIV}
                disabled={seedIVState.loading}
                title="Pull 1 year of IV history from IBKR for all ETFs — seeds the IVR gate. Takes ~30s."
              >
                {seedIVState.loading ? 'Seeding IVR… (~30s)' : '↓ Seed IV'}
              </button>
            </div>
          </div>
          {seedIVState.result && (() => {
            const msg = seedIVMessage(seedIVState.result);
            if (!msg) return null;
            const cls = msg.type === 'ok' ? 'seed-iv-success' : 'seed-iv-warn';
            return <div className={`seed-iv-toast ${cls}`}>{msg.text}</div>;
          })()}
          {seedIVState.error && (
            <div className="seed-iv-toast seed-iv-error">⚠ {seedIVState.error}</div>
          )}

          {/* Filter bar */}
          <div className="scanner-filters">
            {FILTER_OPTIONS.map(f => (
              <button
                key={f}
                className={`sector-filter-btn ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)} ({counts[f]})
              </button>
            ))}
          </div>

          {sectorHook.error && (
            <div className="scanner-sta-offline">
              <div className="sta-offline-icon">⚡</div>
              <div className="sta-offline-msg">STA offline</div>
              <div className="sta-offline-sub">Start STA at localhost:5001 to load sector signals</div>
              <button className="sector-refresh-btn" style={{ marginTop: 8 }} onClick={() => sectorHook.scanSectors().catch(() => {})}>
                Retry
              </button>
            </div>
          )}

          {/* L2 detail inline panel */}
          {(sectorHook.etfDetail || sectorHook.detailLoading) && (
            <div className="l2-inline-panel">
              {sectorHook.detailLoading && <div className="l2-loading">Loading L2 data...</div>}
              {sectorHook.etfDetail && !sectorHook.detailLoading && (
                <L2InlineDetail
                  detail={sectorHook.etfDetail}
                  onClose={sectorHook.clearDetail}
                  onDeepDive={handleSelectETF}
                />
              )}
            </div>
          )}

          {/* ETF list — scanner rows */}
          <div className="scanner-list">
            {filtered.map(etf => (
              <ScannerRow
                key={etf.etf}
                etf={etf}
                isSelected={selectedETF?.etf === etf.etf}
                onSelect={handleSelectETF}
                onL2={handleL2}
              />
            ))}
            {!sectorHook.loading && sectorHook.sectors && filtered.length === 0 && (
              <div className="scanner-empty">No ETFs match filter "{filter}"</div>
            )}
            {sectorHook.loading && !sectorHook.sectors && (
              <div className="scanner-empty">Scanning sector ETFs...</div>
            )}
          </div>

          {sectorHook.sectors && (
            <div className="sector-footer">
              STA: {sectorHook.sectors.sta_status === 'ok' ? '● Connected' : '○ Offline'}
              {sectorHook.sectors.timestamp && (
                <span className="text-dim"> · {new Date(sectorHook.sectors.timestamp).toLocaleTimeString()}</span>
              )}
            </div>
          )}
        </div>

        {/* ── Right: Analysis Panel (opens when ETF selected) ── */}
        {hasAnalysisPanel && (
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
          />
        )}

        {/* Empty state when no ETF selected */}
        {!hasAnalysisPanel && sectorHook.sectors && (
          <div className="analysis-empty">
            <div className="analysis-empty-icon">↑</div>
            <div className="analysis-empty-msg">Select an ETF to run gate analysis</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Scanner Row: compact ETF row with key signals ──
function ScannerRow({ etf, isSelected, onSelect, onL2 }) {
  const QUADRANT_CLS = {
    Leading: 'q-leading', Improving: 'q-improving',
    Weakening: 'q-weakening', Lagging: 'q-lagging',
  };
  const qCls = QUADRANT_CLS[etf.quadrant] || '';
  const dirLabel = etf.suggested_direction ? (DIR_LABELS[etf.suggested_direction] || etf.suggested_direction) : null;
  const isBear = etf.suggested_direction && ['bear_call_spread', 'sell_call', 'buy_put'].includes(etf.suggested_direction);

  return (
    <div
      className={`scanner-row ${isSelected ? 'scanner-row-selected' : ''} ${etf.action === 'SKIP' ? 'scanner-row-skip' : ''}`}
      onClick={() => etf.action === 'ANALYZE' && onSelect(etf)}
      title={etf.action !== 'ANALYZE' ? `${etf.action} — ${etf.quadrant}` : undefined}
    >
      <div className="sr-ticker">{etf.etf}</div>
      <div className={`sr-quadrant ${qCls}`}>{etf.quadrant}</div>
      <div className={`sr-direction ${isBear ? 'sr-bear' : 'sr-bull'}`}>
        {dirLabel || <span className="text-dim">{etf.action}</span>}
      </div>
      <div className="sr-changes">
        <span className={`sr-chg ${etf.week_change >= 0 ? 'text-green' : 'text-red'}`}>
          {etf.week_change != null ? `${etf.week_change >= 0 ? '+' : ''}${etf.week_change.toFixed(1)}%` : '—'}
        </span>
      </div>
      {etf.action === 'ANALYZE' && (
        <button
          className="sr-l2-btn"
          onClick={(e) => { e.stopPropagation(); onL2(etf); }}
          title="L2 IV Detail"
        >
          IV
        </button>
      )}
    </div>
  );
}

// ── L2 inline detail panel (inside scanner) ──
function L2InlineDetail({ detail, onClose, onDeepDive }) {
  return (
    <div className="l2-detail">
      <div className="l2-detail-header">
        <span className="l2-detail-title">{detail.etf} — IV / Liquidity</span>
        <button className="etf-detail-close" onClick={onClose}>✕</button>
      </div>
      <div className="etf-detail-grid">
        <div className="etf-detail-item"><span className="etf-detail-label">IV</span><span className="etf-detail-value monospace">{detail.iv_current != null ? `${detail.iv_current}%` : '—'}</span></div>
        <div className="etf-detail-item"><span className="etf-detail-label">IVR</span><span className={`etf-detail-value monospace ${detail.iv_percentile > 50 ? 'text-red' : detail.iv_percentile < 25 ? 'text-green' : ''}`}>{detail.iv_percentile != null ? `${detail.iv_percentile}%` : '—'}</span></div>
        <div className="etf-detail-item"><span className="etf-detail-label">HV20</span><span className="etf-detail-value monospace">{detail.hv_20 != null ? `${detail.hv_20}%` : '—'}</span></div>
        <div className="etf-detail-item"><span className="etf-detail-label">Sug. DTE</span><span className="etf-detail-value monospace">{detail.suggested_dte ?? '—'}d</span></div>
        <div className="etf-detail-item"><span className="etf-detail-label">Spread</span><span className={`etf-detail-value monospace ${detail.atm_spread_pct > 5 ? 'text-red' : detail.atm_spread_pct > 2 ? 'text-amber' : 'text-green'}`}>{detail.atm_spread_pct != null ? `${detail.atm_spread_pct}%` : '—'}</span></div>
        <div className="etf-detail-item"><span className="etf-detail-label">OI</span><span className="etf-detail-value monospace">{detail.atm_oi != null ? detail.atm_oi.toLocaleString() : '—'}</span></div>
      </div>
      {detail.ivr_bear_warning && <div className="etf-warning etf-warning-bear">⚠ {detail.ivr_bear_warning}</div>}
      {detail.catalyst_warnings?.map((w, i) => <div key={i} className="etf-warning">⚠ {w}</div>)}
      <button className="etf-btn etf-btn-deep" style={{ marginTop: 10, width: '100%' }} onClick={() => { onClose(); onDeepDive(detail); }}>
        Full Gate Analysis →
      </button>
    </div>
  );
}
