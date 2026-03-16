export default function FeatureItem({ title, description }) {
  return (
    <article className="feature-item">
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}
