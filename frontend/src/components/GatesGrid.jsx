export default function GatesGrid({ gates }) {
  return (
    <section className="card">
      <h3>Gates</h3>
      <div className="grid3">
        {gates.map((g) => (
          <div key={g.id} className={`gate ${g.status}`}>
            <div className="row-between"><strong>{g.name}</strong><span>{g.status}</span></div>
            <div>{g.computed_value}</div>
            <small>{g.reason}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
