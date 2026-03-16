export default function PaginationBar({ pagination, onPageChange, loading }) {
  const page = pagination?.page || 1;
  const totalPages = pagination?.total_pages || 1;
  const totalItems = pagination?.total_items || 0;

  return (
    <div className="pagination-bar">
      <p className="muted">Page {page} of {totalPages} · {totalItems} items</p>
      <div className="toolbar-actions">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={loading || page <= 1}
        >
          Previous
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={loading || page >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}
