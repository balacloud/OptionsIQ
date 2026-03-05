const cards = [
  { id: 'buy_call', label: 'Buy Call' },
  { id: 'sell_put', label: 'Sell Put' },
  { id: 'sell_call', label: 'Sell Call' },
  { id: 'buy_put', label: 'Buy Put' },
];

export default function DirectionSelector({ direction, setDirection, swingSignal, locked }) {
  const lockByBuy = swingSignal === 'BUY';
  return (
    <section className="card">
      <h3>Direction</h3>
      <div className="cards4">
        {cards.map((c) => {
          const disabled = lockByBuy && locked.includes(c.id);
          return (
            <button
              key={c.id}
              className={`dir-card ${direction === c.id ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
              onClick={() => !disabled && setDirection(c.id)}
              title={disabled ? 'Locked: contradicts BUY signal' : ''}
            >
              {c.label}
            </button>
          );
        })}
      </div>
    </section>
  );
}
