import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listActivityLogs, listOrganizationMembers } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PaginationBar from "../components/PaginationBar.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate, formatId } from "../utils/format.js";
import { getMemberOptionLabel, getPersonLabel } from "../utils/display.js";
import { canViewActivityLogs } from "../utils/roles.js";

export default function ActivityLogsPage() {
  const { accessToken, isAuthenticated, isSuperAdmin, organizationId, organizationRole } = useSession();
  const [items, setItems] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    actor_user_id: "",
    event_type: "",
    target_type: "",
    sort_by: "created_at",
    order: "desc",
    limit: "20",
    page: 1
  });
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });

  const canReadLogs = canViewActivityLogs(organizationRole, isSuperAdmin);

  useEffect(() => {
    async function loadLogs() {
      if (!isAuthenticated || !organizationId || !canReadLogs) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [response, membersResponse] = await Promise.all([
          listActivityLogs(accessToken, organizationId, {
            search: filters.search || undefined,
            actor_user_id: filters.actor_user_id || undefined,
            event_type: filters.event_type || undefined,
            target_type: filters.target_type || undefined,
            sort_by: filters.sort_by,
            order: filters.order,
            limit: Number(filters.limit),
            page: filters.page
          }),
          listOrganizationMembers(accessToken, organizationId, { limit: 100, page: 1, sort_by: "joined_at", order: "desc" })
        ]);
        const loaded = response?.data?.items || [];
        setItems(loaded);
        setMembers(membersResponse?.data?.items || []);
        setPagination(response?.data?.pagination || { page: 1, total_pages: 1, total_items: loaded.length });
      } catch (requestError) {
        setError(requestError.message || "Unable to load activity logs.");
      } finally {
        setLoading(false);
      }
    }

    loadLogs();
  }, [accessToken, canReadLogs, filters, isAuthenticated, organizationId]);

  function setFilterValue(name, value) {
    setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  }

  function applyPreset(name) {
    if (name === "all") {
      setFilters((current) => ({
        ...current,
        search: "",
        actor_user_id: "",
        event_type: "",
        target_type: "",
        page: 1
      }));
      return;
    }

    if (name === "tasks") {
      setFilters((current) => ({ ...current, target_type: "task", event_type: "", page: 1 }));
      return;
    }

    if (name === "members") {
      setFilters((current) => ({ ...current, target_type: "organization_membership", event_type: "", page: 1 }));
      return;
    }

    if (name === "invites") {
      setFilters((current) => ({ ...current, target_type: "organization_invite", event_type: "", page: 1 }));
      return;
    }

    if (name === "recent") {
      setFilters((current) => ({ ...current, search: "", actor_user_id: "", event_type: "", target_type: "", limit: "20", page: 1 }));
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to view activity"
          description="Track critical workspace events from a single audit timeline."
          action={
            <Link to="/login" className="btn btn-primary">
              Open sign in
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
          title="Select a workspace first"
          description="Choose an organization before opening the audit timeline."
          action={
            <Link to="/organizations" className="btn btn-primary">
              Choose workspace
            </Link>
          }
        />
      </section>
    );
  }

  if (!canReadLogs) {
    return (
      <section className="page">
        <EmptyState
          title="Activity logs are restricted"
          description="This timeline is available to project managers and organization admins."
          action={
            <Link to="/" className="btn btn-primary">
              Back to overview
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Activity"
        title="Organization timeline"
        description="Audit the most important events in your workspace with filters for actor, event, and target."
      />

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="panel list-toolbar">
        <div className="quick-links">
          <button type="button" className="btn btn-secondary" onClick={() => applyPreset("all")}>All events</button>
          <button type="button" className="btn btn-secondary" onClick={() => applyPreset("recent")}>Recent 20</button>
          <button type="button" className="btn btn-secondary" onClick={() => applyPreset("tasks")}>Task events</button>
          <button type="button" className="btn btn-secondary" onClick={() => applyPreset("members")}>Member events</button>
          <button type="button" className="btn btn-secondary" onClick={() => applyPreset("invites")}>Invite events</button>
        </div>
        <div className="filters-grid">
          <div className="field">
            <label htmlFor="log-search">Search</label>
            <input
              id="log-search"
              className="text-input"
              value={filters.search}
              onChange={(event) => setFilterValue("search", event.target.value)}
              placeholder="event or target"
            />
          </div>
          <div className="field">
            <label htmlFor="log-actor">Actor</label>
            <select
              id="log-actor"
              className="select-input"
              value={filters.actor_user_id}
              onChange={(event) => setFilterValue("actor_user_id", event.target.value)}
            >
              <option value="">All actors</option>
              {members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {getMemberOptionLabel({ id: member.user_id, name: member.user_name, email: member.user_email, roleName: member.role_name || member.role_code })}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="log-event">Event type</label>
            <input
              id="log-event"
              className="text-input"
              value={filters.event_type}
              onChange={(event) => setFilterValue("event_type", event.target.value)}
              placeholder="task.updated"
            />
          </div>
          <div className="field">
            <label htmlFor="log-target">Target type</label>
            <input
              id="log-target"
              className="text-input"
              value={filters.target_type}
              onChange={(event) => setFilterValue("target_type", event.target.value)}
              placeholder="task"
            />
          </div>
        </div>
      </section>

      <section className="panel">
        <h3 className="section-heading">Event stream</h3>
        {loading ? <LoadingGrid cards={3} /> : null}
        {!loading && !items.length ? <p className="muted">No activity events found for current filters.</p> : null}
        <div className="data-list">
          {items.map((log) => (
            <article key={log.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>{log.event_type}</h3>
                  <p>{log.target_type} - {formatId(log.target_id)}</p>
                </div>
                <StatusPill value="active" />
              </div>
              <div className="list-row">
                <div>
                  <p className="data-meta">Actor</p>
                  <strong>{getPersonLabel({ id: log.actor_user_id, name: members.find((member) => member.user_id === log.actor_user_id)?.user_name, email: members.find((member) => member.user_id === log.actor_user_id)?.user_email })}</strong>
                </div>
                <div>
                  <p className="data-meta">Request</p>
                  <strong>{formatId(log.request_id)}</strong>
                </div>
                <div>
                  <p className="data-meta">Created</p>
                  <strong>{formatDate(log.created_at)}</strong>
                </div>
              </div>
              <pre className="json-preview">{JSON.stringify(log.metadata_json, null, 2)}</pre>
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
