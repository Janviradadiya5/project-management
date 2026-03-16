export default function MetricCard({ label, value, trend }) {
  return (
    <article className="metric-card">
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-trend">{trend}</p>
    </article>
  );
}
