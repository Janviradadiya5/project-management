export default function LoadingGrid({ cards = 3 }) {
  return (
    <div className="data-list" aria-live="polite" aria-label="Loading content">
      {Array.from({ length: cards }).map((_, index) => (
        <article key={`loading-${index}`} className="data-card skeleton-card" aria-hidden="true">
          <div className="skeleton-line skeleton-line-lg" />
          <div className="skeleton-line" />
          <div className="skeleton-line" />
        </article>
      ))}
    </div>
  );
}