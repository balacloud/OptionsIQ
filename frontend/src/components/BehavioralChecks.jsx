export default function BehavioralChecks({ checks }) {
  return (
    <section className="card">
      <h3>Behavioral Checks</h3>
      <div className="checks">
        {checks.map((c) => (
          <div key={c.id} className="check">
            <strong>{c.label}</strong>
            <div>{c.message}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
