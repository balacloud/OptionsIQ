export default function MasterVerdict({ verdict }) {
  if (!verdict) return null;
  return (
    <section className="card">
      <h3>Master Verdict</h3>
      <div className={`verdict ${verdict.color}`}>{verdict.score_label} · {verdict.headline}</div>
    </section>
  );
}
