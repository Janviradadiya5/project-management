import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createOrganization, deleteOrganization, listOrganizations, updateOrganization } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import ListToolbar from "../components/ListToolbar.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PaginationBar from "../components/PaginationBar.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate, formatId, toSlug } from "../utils/format.js";
import { canManageOrganization } from "../utils/roles.js";
import { isNonEmpty } from "../utils/validation.js";

const initialForm = {
  name: "",
  slug: ""
};

export default function OrganizationsPage() {
  const { accessToken, isAuthenticated, isSuperAdmin, organizationId, organizationRole, selectOrganization } = useSession();
  const [organizations, setOrganizations] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [manageForm, setManageForm] = useState({ name: "", slug: "" });
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [managing, setManaging] = useState(false);
  const [deletingOrgId, setDeletingOrgId] = useState("");
  const [activeSection, setActiveSection] = useState("create");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    status: "",
    sort_by: "created_at",
    order: "desc",
    limit: "20",
    page: 1
  });
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });
  const canManage = canManageOrganization(organizationRole, isSuperAdmin);

  const selectedOrganization = organizations.find((org) => org.id === organizationId) || null;

  useEffect(() => {
    async function loadOrganizationsData() {
      if (!isAuthenticated) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const response = await listOrganizations(accessToken, {
          search: filters.search || undefined,
          status: filters.status || undefined,
          sort_by: filters.sort_by,
          order: filters.order,
          limit: Number(filters.limit),
          page: filters.page
        });
        const items = response?.data?.items || [];
        setOrganizations(items);
        setPagination(response?.data?.pagination || { page: 1, total_pages: 1, total_items: items.length });

        const selected = items.find((org) => org.id === organizationId) || items[0] || null;
        if (selected) {
          setManageForm({ name: selected.name || "", slug: selected.slug || "" });
        }

        if (!organizationId && items[0]?.id) {
          selectOrganization(items[0].id);
        }
      } catch (requestError) {
        setError(requestError.message || "Unable to load organizations.");
      } finally {
        setLoading(false);
      }
    }

    loadOrganizationsData();
  }, [accessToken, filters, isAuthenticated, organizationId, selectOrganization]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => {
      if (name === "name") {
        return {
          ...current,
          name: value,
          slug: current.slug ? current.slug : toSlug(value)
        };
      }

      return { ...current, [name]: value };
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setCreating(true);
    setError("");
    setSuccess("");

    const normalizedName = form.name.trim();
    const normalizedSlug = form.slug.trim();

    if (!isNonEmpty(normalizedName, 3)) {
      setCreating(false);
      setError("Organization name must be at least 3 characters.");
      return;
    }

    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(normalizedSlug)) {
      setCreating(false);
      setError("Slug must be lowercase kebab-case.");
      return;
    }

    try {
      const response = await createOrganization(accessToken, {
        name: normalizedName,
        slug: normalizedSlug
      });
      const created = response?.data;

      setOrganizations((current) => [created, ...current]);
      selectOrganization(created?.id || "", created || null);
      setForm(initialForm);
      setSuccess("Organization created and selected.");
    } catch (requestError) {
      setError(requestError.message || "Unable to create organization.");
    } finally {
      setCreating(false);
    }
  }

  function setFilterValue(name, value) {
    setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  }

  function applyFilters() {
    setFilters((current) => ({ ...current, page: 1 }));
  }

  async function handleOrganizationUpdate(event) {
    event.preventDefault();
    if (!selectedOrganization) {
      setError("Select an organization first.");
      return;
    }

    setManaging(true);
    setError("");

    try {
      const response = await updateOrganization(accessToken, selectedOrganization.id, {
        name: manageForm.name.trim(),
        slug: manageForm.slug.trim()
      });
      const updated = response?.data;
      setOrganizations((current) => current.map((org) => (org.id === selectedOrganization.id ? { ...org, ...updated } : org)));
      setSuccess("Organization updated.");
    } catch (requestError) {
      setError(requestError.message || "Unable to update organization.");
    } finally {
      setManaging(false);
    }
  }

  async function handleOrganizationArchive() {
    if (!selectedOrganization) {
      setError("Select an organization first.");
      return;
    }

    setManaging(true);
    setError("");

    try {
      await deleteOrganization(accessToken, selectedOrganization.id);
      setOrganizations((current) => current.filter((org) => org.id !== selectedOrganization.id));
      selectOrganization("");
      setSuccess("Organization archived.");
    } catch (requestError) {
      setError(requestError.message || "Unable to archive organization.");
    } finally {
      setManaging(false);
    }
  }

  async function handleDeleteFromList(orgId) {
    setDeletingOrgId(orgId);
    setError("");

    try {
      await deleteOrganization(accessToken, orgId);
      setOrganizations((current) => current.filter((org) => org.id !== orgId));
      if (organizationId === orgId) {
        selectOrganization("");
      }
      setSuccess("Organization archived.");
    } catch (requestError) {
      setError(requestError.message || "Unable to archive organization.");
    } finally {
      setDeletingOrgId("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to open workspaces"
          description="Switch organizations, manage context, and continue work exactly where your team left off."
          action={
            <Link to="/login" className="btn btn-primary">
              Open sign in
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Organizations"
        title="Workspace switchboard"
        description="Choose and manage your workspace."
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Workspace mode</p>
          <h3 className="section-heading">Organization controls</h3>
          <p className="helper-text">Open one section and continue.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Organization sections">
            <button
              type="button"
              className={`tasks-view-button${activeSection === "create" ? " active" : ""}`}
              onClick={() => setActiveSection("create")}
            >
              Create
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "manage" ? " active" : ""}`}
              onClick={() => setActiveSection("manage")}
            >
              Manage
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "list" ? " active" : ""}`}
              onClick={() => setActiveSection("list")}
            >
              List
            </button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Organizations</p>
            <strong>{pagination.total_items || organizations.length}</strong>
          </div>
          <div>
            <p className="data-meta">Selected</p>
            <strong>{selectedOrganization?.name || "None"}</strong>
          </div>
          <div>
            <p className="data-meta">Mode</p>
            <strong>{canManage ? "Manager" : "Viewer"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection}</strong>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}

      {activeSection === "create" ? (
      <section className="split-grid">
        <form className="panel form-shell" onSubmit={handleSubmit}>
          <h3 className="section-heading">Create organization</h3>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" name="name" className="text-input" value={form.name} onChange={handleChange} required />
            </div>
            <div className="field">
              <label htmlFor="slug">Slug</label>
              <input id="slug" name="slug" className="text-input" value={form.slug} onChange={handleChange} required />
            </div>
          </div>
          <div className="toolbar-actions">
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? "Creating..." : "Create organization"}
            </button>
          </div>
        </form>

        <section className="panel">
          <h3 className="section-heading">Current workspace</h3>
          <p className="helper-text">
            Active workspace: <strong>{selectedOrganization?.name || "Not selected"}</strong>
          </p>
          <p className="helper-text">This selection controls what portfolio, tasks, and team data you see across the app.</p>
        </section>
      </section>
      ) : null}

      {activeSection === "manage" ? (!canManage ? (
        <section className="panel"><p className="muted">Admin role required to manage organizations.</p></section>
      ) : (
        <section className="split-grid">
          <form className="panel form-shell" onSubmit={handleOrganizationUpdate}>
            <h3 className="section-heading">Update selected organization</h3>
            <div className="field">
              <label htmlFor="manage-org-name">Name</label>
              <input
                id="manage-org-name"
                className="text-input"
                value={manageForm.name}
                onChange={(event) => setManageForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="manage-org-slug">Slug</label>
              <input
                id="manage-org-slug"
                className="text-input"
                value={manageForm.slug}
                onChange={(event) => setManageForm((current) => ({ ...current, slug: event.target.value }))}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={managing || !selectedOrganization}>
              {managing ? "Saving..." : "Save changes"}
            </button>
          </form>

          <section className="panel form-shell">
            <h3 className="section-heading">Archive selected organization</h3>
            <p className="helper-text">Archiving removes the organization from active workspace lists while preserving historical records.</p>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleOrganizationArchive}
              disabled={managing || !selectedOrganization}
            >
              {managing ? "Archiving..." : "Archive organization"}
            </button>
          </section>
        </section>
      )) : null}

      {activeSection === "list" ? (
      <>
      <ListToolbar
        search={filters.search}
        onSearchChange={(value) => setFilterValue("search", value)}
        onApply={applyFilters}
        loading={loading}
      >
        <div className="field">
          <label htmlFor="org-status">Status</label>
          <select id="org-status" className="select-input" value={filters.status} onChange={(event) => setFilterValue("status", event.target.value)}>
            <option value="">all</option>
            <option value="active">active</option>
            <option value="archived">archived</option>
            <option value="deleted">deleted</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="org-sort">Sort by</label>
          <select id="org-sort" className="select-input" value={filters.sort_by} onChange={(event) => setFilterValue("sort_by", event.target.value)}>
            <option value="created_at">created_at</option>
            <option value="updated_at">updated_at</option>
            <option value="name">name</option>
            <option value="status">status</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="org-order">Order</label>
          <select id="org-order" className="select-input" value={filters.order} onChange={(event) => setFilterValue("order", event.target.value)}>
            <option value="desc">desc</option>
            <option value="asc">asc</option>
          </select>
        </div>
      </ListToolbar>

      <section className="panel">
        <h3 className="section-heading">Available organizations</h3>
        {loading ? <LoadingGrid cards={3} /> : null}
        {!loading && !organizations.length ? <p className="muted">No organizations returned yet.</p> : null}
        <div className="data-list">
          {organizations.map((organization) => (
            <article key={organization.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>{organization.name}</h3>
                  <p>{organization.slug}</p>
                </div>
                <StatusPill value={organization.status || "active"} />
              </div>
              {organization.current_user_role_code ? <p className="helper-text">Your role: <span className="inline-code">{organization.current_user_role_code}</span></p> : null}
              <div className="list-row">
                <div>
                  <p className="data-meta">ID</p>
                  <strong>{formatId(organization.id)}</strong>
                </div>
                <div>
                  <p className="data-meta">Updated</p>
                  <strong>{formatDate(organization.updated_at)}</strong>
                </div>
              </div>
              <div className="toolbar-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    selectOrganization(organization.id, organization);
                    setSuccess(`Selected ${organization.name} as the active organization.`);
                  }}
                >
                  {organizationId === organization.id ? "Selected" : "Use this organization"}
                </button>
                {canManage ? (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleDeleteFromList(organization.id)}
                    disabled={deletingOrgId === organization.id}
                  >
                    {deletingOrgId === organization.id ? "Archiving..." : "Archive"}
                  </button>
                ) : null}
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
      </>
      ) : null}
    </section>
  );
}