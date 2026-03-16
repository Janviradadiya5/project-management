function toClassName(value) {
  return String(value || "default")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-");
}

export default function StatusPill({ value }) {
  return <span className={`status-pill ${toClassName(value)}`}>{value || "unknown"}</span>;
}