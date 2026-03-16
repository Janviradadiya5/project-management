import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listNotifications, markNotificationRead } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PaginationBar from "../components/PaginationBar.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate, formatId } from "../utils/format.js";

export default function NotificationsPage() {
  const { accessToken, isAuthenticated, organizationId } = useSession();
  const { pushToast } = useNotifications();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [markingId, setMarkingId] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    is_read: "",
    type: "",
    sort_by: "created_at",
    order: "desc",
    limit: "20",
    page: 1
  });
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });

  function extractTaskId(payload) {
    if (!payload || typeof payload !== "object") {
      return "";
    }

    return payload.task_id || payload.taskId || payload?.task?.id || "";
  }

  useEffect(() => {
    async function loadData() {
      if (!isAuthenticated || !organizationId) {
        return;
      }

      setLoading(true);
      setError("");
      try {
        const response = await listNotifications(accessToken, organizationId, {
          search: filters.search || undefined,
          is_read: filters.is_read || undefined,
          type: filters.type || undefined,
          sort_by: filters.sort_by,
          order: filters.order,
          limit: Number(filters.limit),
          page: filters.page
        });
        const loaded = response?.data?.items || [];
        setItems(loaded);
        setPagination(response?.data?.pagination || { page: 1, total_pages: 1, total_items: loaded.length });
      } catch (requestError) {
        setError(requestError.message || "Unable to load notifications.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [accessToken, filters, isAuthenticated, organizationId]);

  function setFilterValue(name, value) {
    setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  }

  async function handleMarkRead(notificationId) {
    setMarkingId(notificationId);
    setError("");

    try {
      const response = await markNotificationRead(accessToken, organizationId, notificationId);
      const updated = response?.data;
      setItems((current) =>
        current.map((item) => (item.id === notificationId ? { ...item, ...updated, is_read: true } : item))
      );
      pushToast("Notification marked as read.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to mark notification as read.");
      pushToast("Notification update failed.", "error");
    } finally {
      setMarkingId("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to load notifications"
          description="Notifications are per-user and require an authenticated session."
          action={
            <Link to="/login" className="btn btn-primary">
              Open login
            </Link>
          }
        />
      </section>
    );
  }

  if (!organizationId) {
    return (
      <section className="page">
        <EmptyState
          title="Select an organization first"
          description="Notification list requires the organization context header."
          action={
            <Link to="/organizations" className="btn btn-primary">
              Choose organization
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Notifications"
        title="Inbox"
        description="Review user notifications and mark unread items as read."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <LoadingGrid cards={3} /> : null}

      <section className="panel list-toolbar">
        <div className="filters-grid">
          <div className="field">
            <label htmlFor="notif-search">Search</label>
            <input id="notif-search" className="text-input" value={filters.search} onChange={(event) => setFilterValue("search", event.target.value)} placeholder="title or body" />
          </div>
          <div className="field">
            <label htmlFor="notif-read">Read status</label>
            <select id="notif-read" className="select-input" value={filters.is_read} onChange={(event) => setFilterValue("is_read", event.target.value)}>
              <option value="">all</option>
              <option value="false">unread</option>
              <option value="true">read</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="notif-type">Type</label>
            <input id="notif-type" className="text-input" value={filters.type} onChange={(event) => setFilterValue("type", event.target.value)} placeholder="task_due" />
          </div>
          <div className="field">
            <label htmlFor="notif-order">Order</label>
            <select id="notif-order" className="select-input" value={filters.order} onChange={(event) => setFilterValue("order", event.target.value)}>
              <option value="desc">desc</option>
              <option value="asc">asc</option>
            </select>
          </div>
        </div>
      </section>

      <section className="panel">
        <h3 className="section-heading">Recent notifications</h3>
        {!loading && !items.length ? <p className="muted">No notifications found.</p> : null}
        <div className="data-list">
          {items.map((item) => (
            <article key={item.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
                <StatusPill value={item.is_read ? "done" : "todo"} />
              </div>
              <div className="list-row">
                <div>
                  <p className="data-meta">Type</p>
                  <strong>{item.type}</strong>
                </div>
                <div>
                  <p className="data-meta">Created</p>
                  <strong>{formatDate(item.created_at)}</strong>
                </div>
                <div>
                  <p className="data-meta">ID</p>
                  <strong>{formatId(item.id)}</strong>
                </div>
              </div>
              <div className="toolbar-actions">
                {extractTaskId(item.payload_json) ? (
                  <Link to={`/tasks/${extractTaskId(item.payload_json)}`} className="btn btn-secondary">
                    Open task
                  </Link>
                ) : null}
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={item.is_read || markingId === item.id}
                  onClick={() => handleMarkRead(item.id)}
                >
                  {markingId === item.id ? "Updating..." : item.is_read ? "Read" : "Mark as read"}
                </button>
              </div>
            </article>
          ))}
        </div>
        <PaginationBar
          pagination={pagination}
          loading={loading}
          onPageChange={(nextPage) => {
            if (nextPage < 1 || nextPage > (pagination.total_pages || 1)) {
              return;
            }
            setFilters((current) => ({ ...current, page: nextPage }));
          }}
        />
      </section>
    </section>
  );
}
