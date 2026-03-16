export default function EmptyState({ title, description, action }) {
  return (
    <section className="panel empty-state">
      <h3 className="section-heading">{title}</h3>
      <p>{description}</p>
      {action}
    </section>
  );
}