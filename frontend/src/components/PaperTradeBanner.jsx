export default function PaperTradeBanner({ ticker, direction, data }) {
  const save = async () => {
    if (!data?.top_strategies?.length) return;
    const s = data.top_strategies[0];
    await fetch('http://localhost:5051/api/options/paper-trade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker,
        direction,
        strategy_rank: s.rank,
        strike: s.strike,
        expiry: s.expiry_display,
        premium: s.premium,
        lots: 1,
        account_size: 50000,
        verdict: data.verdict?.color || null,
      }),
    });
  };

  return (
    <section className="card cta">
      <strong>Paper Trade Before Live</strong>
      <button onClick={save}>Record Paper Trade</button>
    </section>
  );
}
