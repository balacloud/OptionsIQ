export default function Header({ ticker, data, onIbClick }) {
  const connected = !!data?.ibkr_connected;
  const source    = data?.data_source || 'mock';

  const sourceLabel = {
    ibkr_live:    'IB Live',
    ibkr_closed:  'IB Closed',
    ibkr_cache:   'IB Cache',
    ibkr_stale:   'IB Stale',
    ibkr_partial: 'IB Partial',
    alpaca:       'Alpaca',
    yfinance:     'yfinance',
    mock:         'Mock',
  }[source] || source;

  return (
    <div className="card card-sm">
      <div className="row-between">
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            OptionsIQ
          </div>
          {ticker && (
            <div style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 1 }}>
              {ticker}
              {data?.underlying_price && (
                <span className="monospace" style={{ marginLeft: 6, color: 'var(--text)' }}>
                  ${data.underlying_price.toFixed(2)}
                </span>
              )}
            </div>
          )}
        </div>
        <button className="ib-status-dot" onClick={onIbClick}>
          <span className={`dot ${connected ? 'live' : 'offline'}`}>●</span>
          <span>{connected ? sourceLabel : 'Offline'}</span>
        </button>
      </div>
    </div>
  );
}
