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
import useOptionsData from './hooks/useOptionsData';
import './index.css';

const defaults = {
  swing_signal: 'BUY',
  entry_pullback: 204.15,
  entry_momentum: 234.35,
  stop_loss: 192.93,
  target1: 254.62,
  target2: 278.36,
  risk_reward: 4.5,
  vcp_pivot: 242.05,
  vcp_confidence: 70,
  adx: 40.2,
  last_close: 234.35,
  s1_support: 225.8,
  spy_above_200sma: true,
  spy_5day_return: 0.008,
  earnings_days_away: 45,
  pattern: 'VCP',
};

export default function App() {
  const { data, loading, error, analyze } = useOptionsData();
  const [ticker, setTicker] = useState('AME');
  const [direction, setDirection] = useState('buy_call');
  const [swing, setSwing] = useState(defaults);

  const lockedBySignal = useMemo(() => (
    swing.swing_signal === 'BUY' ? ['sell_call', 'buy_put'] : []
  ), [swing.swing_signal]);

  useEffect(() => {
    if (swing.swing_signal === 'BUY') setDirection((d) => (d === 'sell_call' || d === 'buy_put' ? 'buy_call' : d));
  }, [swing.swing_signal]);

  const onAnalyze = async () => {
    try {
      await analyze({ ticker, direction, ...swing });
    } catch (_) {
      // Error text is already surfaced via useOptionsData `error` state.
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlTicker = params.get('ticker');
    const auto = params.get('auto') === 'true';
    const swingParam = params.get('swing_data');
    if (urlTicker) setTicker(urlTicker.toUpperCase());
    if (swingParam) {
      try {
        const parsed = JSON.parse(swingParam);
        setSwing((s) => ({ ...s, ...parsed }));
      } catch (_) {}
    }
    if (auto) {
      analyze({ ticker: (urlTicker || ticker).toUpperCase(), direction, ...swing }).catch(() => {});
    } else {
      onAnalyze();
    }
  }, []);

  return (
    <div className="page">
      <Header ticker={ticker} data={data} loading={loading} />
      <div className="toolbar">
        <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} maxLength={8} />
        <button onClick={onAnalyze} disabled={loading}>{loading ? 'Analyzing...' : 'Analyze'}</button>
      </div>
      <SwingImportStrip swing={swing} setSwing={setSwing} />
      <DirectionSelector
        direction={direction}
        setDirection={setDirection}
        swingSignal={swing.swing_signal}
        locked={lockedBySignal}
      />
      <MasterVerdict verdict={data?.verdict} />
      <GatesGrid gates={data?.gates || []} />
      <BehavioralChecks checks={data?.behavioral_checks || []} />
      <TopThreeCards strategies={data?.top_strategies || []} gates={data?.gates || []} />
      <PnLTable table={data?.pnl_table} gateFailed={(data?.gates || []).some((g) => g.id === 'pivot_confirm' && g.status === 'fail')} />
      <PaperTradeBanner ticker={ticker} direction={direction} data={data} />
      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}
