/**
 * RegimeBar — always-visible macro context strip at the top of the Signal Board.
 * Shows SPY regime, 5-day return, VIX level, broad selloff alert.
 * Data sourced from sector scan spy_regime + market_regime + vix fields.
 */
export default function RegimeBar({ sectorData }) {
  if (!sectorData) return null;

  const spy = sectorData.spy_regime || {};
  const marketRegime = sectorData.market_regime;
  const isSelloff = marketRegime === 'BROAD_SELLOFF';

  const above200 = spy.spy_above_200sma;
  const fiveDay = spy.spy_5day_return;

  const vixData = sectorData.vix || {};
  const vixValue = vixData.value;
  let vixCls = 'regime-neutral';
  let vixLabel = '—';
  if (vixValue != null) {
    vixLabel = vixValue.toFixed(1);
    if (vixValue > 40) vixCls = 'regime-bear';
    else if (vixValue > 30) vixCls = 'regime-warn';
    else if (vixValue >= 15) vixCls = 'regime-bull';
    else vixCls = 'regime-neutral'; // <15 = thin premiums, gray
  }

  let regimeLabel = '—';
  let regimeCls = '';
  if (above200 === true) {
    regimeLabel = 'BULL';
    regimeCls = 'regime-bull';
  } else if (above200 === false) {
    regimeLabel = 'BEAR';
    regimeCls = 'regime-bear';
  }

  let fiveDayCls = 'regime-neutral';
  if (fiveDay != null) {
    fiveDayCls = fiveDay >= 0 ? 'regime-bull' : fiveDay < -2 ? 'regime-bear' : 'regime-warn';
  }

  return (
    <div className={`regime-bar ${isSelloff ? 'regime-bar-selloff' : ''}`}>
      <div className="regime-item">
        <span className="regime-label">SPY Regime</span>
        <span className={`regime-value ${regimeCls}`}>{regimeLabel}</span>
        <span className="regime-sub">
          {above200 === true ? 'above 200 SMA' : above200 === false ? 'below 200 SMA' : '—'}
        </span>
      </div>

      <div className="regime-divider" />

      <div className="regime-item">
        <span className="regime-label">SPY 5d</span>
        <span className={`regime-value ${fiveDayCls}`}>
          {fiveDay != null ? `${fiveDay >= 0 ? '+' : ''}${fiveDay.toFixed(1)}%` : '—'}
        </span>
      </div>

      <div className="regime-divider" />

      <div className="regime-item">
        <span className="regime-label">VIX</span>
        <span className={`regime-value ${vixCls}`}>{vixLabel}</span>
        <span className="regime-sub">
          {vixValue == null ? '—'
            : vixValue > 40 ? 'crisis'
            : vixValue > 30 ? 'stress'
            : vixValue >= 15 ? 'normal'
            : 'low vol'}
        </span>
      </div>

      <div className="regime-divider" />

      <div className="regime-item">
        <span className="regime-label">Market</span>
        <span className={`regime-value ${isSelloff ? 'regime-bear' : 'regime-bull'}`}>
          {isSelloff ? 'BROAD SELLOFF' : 'NORMAL'}
        </span>
      </div>

      {sectorData.size_signal && sectorData.size_signal !== 'Neutral' && (
        <>
          <div className="regime-divider" />
          <div className="regime-item">
            <span className="regime-label">Cap-Size</span>
            <span className="regime-value">{sectorData.size_signal}</span>
            {sectorData.size_bias && (
              <span className="regime-sub">{sectorData.size_bias}</span>
            )}
          </div>
        </>
      )}

      {isSelloff && (
        <div className="regime-selloff-alert">
          ! Broad selloff — majority of sectors weakening/lagging, SPY below 200 SMA.
          Favor defined-risk bear spreads.
        </div>
      )}
    </div>
  );
}
