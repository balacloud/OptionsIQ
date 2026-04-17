const DIRECTIONS = [
  {
    id: 'buy_call',
    label: 'Buy Call',
    icon: '▲',
    group: 'bullish',
    view: 'I think price will RISE significantly',
    howItWorks: 'You PAY a premium upfront. Profit if the ETF climbs above your breakeven.',
    risk: 'Risk: Premium paid (fully capped)',
    reward: 'Reward: Unlimited upside',
    color: 'green',
  },
  {
    id: 'sell_put',
    label: 'Sell Put',
    icon: '►',
    group: 'bullish',
    view: 'I think price will STAY or rise slowly',
    howItWorks: 'You COLLECT a credit upfront. Profit if the ETF stays flat or rises.',
    risk: 'Risk: Spread width (capped with spread)',
    reward: 'Reward: Keep the credit collected',
    color: 'green',
  },
  {
    id: 'sell_call',
    label: 'Sell Call',
    icon: '◄',
    group: 'bearish',
    view: 'I think price will STAY or drop slowly',
    howItWorks: 'You COLLECT a credit upfront. Profit if the ETF stays flat or drops.',
    risk: 'Risk: Spread width (capped with spread)',
    reward: 'Reward: Keep the credit collected',
    color: 'red',
  },
  {
    id: 'buy_put',
    label: 'Buy Put',
    icon: '▼',
    group: 'bearish',
    view: 'I think price will DROP significantly',
    howItWorks: 'You PAY a premium upfront. Profit if the ETF falls below your breakeven.',
    risk: 'Risk: Premium paid (fully capped)',
    reward: 'Reward: Large downside capture',
    color: 'red',
  },
];

export default function DirectionGuide({ direction, setDirection, locked = [] }) {
  const bullish = DIRECTIONS.filter(d => d.group === 'bullish');
  const bearish = DIRECTIONS.filter(d => d.group === 'bearish');

  function renderCard(d) {
    const isActive = direction === d.id;
    const isLocked = locked.includes(d.id);

    return (
      <button
        key={d.id}
        className={`dg-card dg-card-${d.color} ${isActive ? 'dg-card-active' : ''} ${isLocked ? 'dg-card-locked' : ''}`}
        onClick={() => !isLocked && setDirection(d.id)}
        disabled={isLocked}
        title={isLocked ? 'Locked — contradicts market signal' : ''}
      >
        <div className="dg-card-top">
          <span className="dg-icon">{d.icon}</span>
          <span className="dg-label">{d.label}</span>
          {isActive && <span className="dg-active-dot" />}
        </div>
        <div className="dg-view">{d.view}</div>
        <div className="dg-works">{d.howItWorks}</div>
        <div className="dg-meta">
          <span className="dg-risk">{d.risk}</span>
          <span className="dg-reward">{d.reward}</span>
        </div>
      </button>
    );
  }

  return (
    <div className="direction-guide">
      <div className="dg-header">
        <span className="dg-title">What&apos;s your market view?</span>
        <span className="dg-hint">Click to select, then run analysis</span>
      </div>
      <div className="dg-groups">
        <div className="dg-group">
          <div className="dg-group-label dg-group-bull">BULLISH</div>
          <div className="dg-group-cards">
            {bullish.map(renderCard)}
          </div>
        </div>
        <div className="dg-group">
          <div className="dg-group-label dg-group-bear">BEARISH</div>
          <div className="dg-group-cards">
            {bearish.map(renderCard)}
          </div>
        </div>
      </div>
    </div>
  );
}
