export default function ListToolbar({
  search,
  onSearchChange,
  children,
  onApply,
  loading
}) {
  return (
    <form
      className="panel list-toolbar"
      onSubmit={(event) => {
        event.preventDefault();
        onApply();
      }}
    >
      <div className="filters-grid">
        <div className="field">
          <label htmlFor="list-search">Search</label>
          <input
            id="list-search"
            className="text-input"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Type to filter"
          />
        </div>
        {children}
      </div>
      <div className="toolbar-actions">
        <button type="submit" className="btn btn-secondary" disabled={loading}>
          {loading ? "Loading..." : "Apply filters"}
        </button>
      </div>
    </form>
  );
}
