import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  addProjectMember,
  archiveProject,
  createProject,
  getProject,
  listOrganizationMembers,
  listProjectMembers,
  listProjects,
  removeProjectMember,
  updateProject
} from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import ListToolbar from "../components/ListToolbar.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PaginationBar from "../components/PaginationBar.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate, toApiDateTime } from "../utils/format.js";
import { canManageProjects } from "../utils/roles.js";
import { getMemberOptionLabel, getPersonLabel } from "../utils/display.js";
import { isNonEmpty } from "../utils/validation.js";

const initialForm = {
  name: "",
  description: "",
  status: "active",
  deadlineAt: ""
};

export default function ProjectsPage() {
  const { accessToken, currentOrganization, isAuthenticated, isSuperAdmin, organizationId, organizationRole, user } = useSession();
  const [projects, setProjects] = useState([]);
  const [organizationMembers, setOrganizationMembers] = useState([]);
  const [projectMembers, setProjectMembers] = useState([]);
  const [selectedProjectDetail, setSelectedProjectDetail] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedProjectMemberId, setSelectedProjectMemberId] = useState("");
  const [memberUserId, setMemberUserId] = useState("");
  const [memberRole, setMemberRole] = useState("contributor");
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [membersLoading, setMembersLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [activeSection, setActiveSection] = useState("create");
  const [pendingAction, setPendingAction] = useState("");
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
  const canManage = canManageProjects(organizationRole, isSuperAdmin);

  const availableMemberOptions = useMemo(() => {
    const assignedUserIds = new Set(projectMembers.map((member) => member.user_id));
    return organizationMembers
      .filter((member) => !assignedUserIds.has(member.user_id))
      .map((member) => ({
        value: member.user_id,
        label: getMemberOptionLabel({
          id: member.user_id,
          name: member.user_name,
          email: member.user_email,
          roleName: member.role_name || member.role_code
        })
      }));
  }, [organizationMembers, projectMembers]);

  const projectMemberOptions = useMemo(
    () => projectMembers.map((member) => ({
      value: member.id,
      label: `${getPersonLabel({ id: member.user_id, name: member.user_name, email: member.user_email, currentUserId: user?.id })} · ${member.project_role}`
    })),
    [projectMembers, user?.id]
  );

  useEffect(() => {
    async function loadProjectsData() {
      if (!isAuthenticated || !organizationId) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [projectsResponse, membersResponse] = await Promise.all([
          listProjects(accessToken, organizationId, {
            search: filters.search || undefined,
            status: filters.status || undefined,
            sort_by: filters.sort_by,
            order: filters.order,
            limit: Number(filters.limit),
            page: filters.page
          }),
          listOrganizationMembers(accessToken, organizationId, {
            limit: 100,
            page: 1,
            sort_by: "joined_at",
            order: "desc"
          })
        ]);

        const items = projectsResponse?.data?.items || [];
        const loadedMembers = membersResponse?.data?.items || [];

        setProjects(items);
        setOrganizationMembers(loadedMembers);
        setPagination(projectsResponse?.data?.pagination || { page: 1, total_pages: 1, total_items: items.length });
        setSelectedProjectId((current) => (items.some((project) => project.id === current) ? current : items[0]?.id || ""));
        setMemberUserId((current) => (loadedMembers.some((member) => member.user_id === current) ? current : loadedMembers[0]?.user_id || ""));
      } catch (requestError) {
        setError(requestError.message || "Unable to load projects.");
      } finally {
        setLoading(false);
      }
    }

    loadProjectsData();
  }, [accessToken, filters, isAuthenticated, organizationId]);

  useEffect(() => {
    async function loadProjectTeam() {
      if (!selectedProjectId || !organizationId || !isAuthenticated) {
        setProjectMembers([]);
        setSelectedProjectMemberId("");
        return;
      }

      setMembersLoading(true);

      try {
        const response = await listProjectMembers(accessToken, organizationId, selectedProjectId, {
          limit: 100,
          page: 1
        });
        const loaded = response?.data?.items || [];
        setProjectMembers(loaded);
        setSelectedProjectMemberId((current) => (loaded.some((member) => member.id === current) ? current : loaded[0]?.id || ""));
      } catch (requestError) {
        setError(requestError.message || "Unable to load project members.");
      } finally {
        setMembersLoading(false);
      }
    }

    loadProjectTeam();
  }, [accessToken, isAuthenticated, organizationId, selectedProjectId]);

  useEffect(() => {
    async function loadSelectedProjectDetail() {
      if (!selectedProjectId || !organizationId || !isAuthenticated) {
        setSelectedProjectDetail(null);
        return;
      }

      try {
        const response = await getProject(accessToken, organizationId, selectedProjectId);
        setSelectedProjectDetail(response?.data || null);
      } catch {
        setSelectedProjectDetail(null);
      }
    }

    loadSelectedProjectDetail();
  }, [accessToken, isAuthenticated, organizationId, selectedProjectId]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!canManage) {
      setError("Your current role can review projects but cannot create new ones.");
      return;
    }

    setCreating(true);
    setError("");
    setSuccess("");

    if (!isNonEmpty(form.name, 3)) {
      setCreating(false);
      setError("Project name must be at least 3 characters.");
      return;
    }

    if (form.deadlineAt && !toApiDateTime(form.deadlineAt)) {
      setCreating(false);
      setError("Deadline is invalid.");
      return;
    }

    if (!form.deadlineAt) {
      setCreating(false);
      setError("Deadline is required.");
      return;
    }

    try {
      const response = await createProject(accessToken, organizationId, {
        name: form.name,
        description: form.description,
        status: form.status,
        deadline_at: toApiDateTime(form.deadlineAt)
      });

      const created = response?.data;
      setProjects((current) => (created ? [created, ...current] : current));
      setSelectedProjectId((current) => current || created?.id || "");
      setForm(initialForm);
      setSuccess("Project created successfully.");
    } catch (requestError) {
      setError(requestError.message || "Unable to create project.");
    } finally {
      setCreating(false);
    }
  }

  function setFilterValue(name, value) {
    setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  }

  async function handleProjectStatusChange(projectId, status) {
    setPendingAction(`project-update:${projectId}`);
    setError("");

    try {
      const response = await updateProject(accessToken, organizationId, projectId, { status });
      const updated = response?.data;
      setProjects((current) => current.map((project) => (project.id === projectId ? { ...project, ...updated } : project)));
      setSuccess("Project updated.");
    } catch (requestError) {
      setError(requestError.message || "Unable to update project.");
    } finally {
      setPendingAction("");
    }
  }

  async function handleArchiveProject(projectId) {
    setPendingAction(`project-archive:${projectId}`);
    setError("");

    try {
      const response = await archiveProject(accessToken, organizationId, projectId);
      const archived = response?.data;
      setProjects((current) => current.map((project) => (project.id === projectId ? { ...project, ...archived } : project)));
      setSuccess("Project archived.");
    } catch (requestError) {
      setError(requestError.message || "Unable to archive project.");
    } finally {
      setPendingAction("");
    }
  }

  async function refreshProjectMembers() {
    if (!selectedProjectId) {
      return;
    }

    const response = await listProjectMembers(accessToken, organizationId, selectedProjectId, { limit: 100, page: 1 });
    const loaded = response?.data?.items || [];
    setProjectMembers(loaded);
    setSelectedProjectMemberId(loaded[0]?.id || "");
  }

  async function handleAddMember(event) {
    event.preventDefault();

    if (!selectedProjectId || !memberUserId) {
      setError("Choose both a project and a team member.");
      return;
    }

    setPendingAction("member-add");
    setError("");

    try {
      await addProjectMember(accessToken, organizationId, selectedProjectId, {
        user_id: memberUserId,
        project_role: memberRole
      });
      setSuccess("Project member added.");
      await refreshProjectMembers();
    } catch (requestError) {
      setError(requestError.message || "Unable to add project member.");
    } finally {
      setPendingAction("");
    }
  }

  async function handleRemoveMember(event) {
    event.preventDefault();

    if (!selectedProjectId || !selectedProjectMemberId) {
      setError("Choose a project member to remove.");
      return;
    }

    setPendingAction("member-remove");
    setError("");

    try {
      await removeProjectMember(accessToken, organizationId, selectedProjectId, selectedProjectMemberId);
      setSuccess("Project member removed.");
      await refreshProjectMembers();
    } catch (requestError) {
      setError(requestError.message || "Unable to remove project member.");
    } finally {
      setPendingAction("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to load projects"
          description="Open your account to view the portfolio and create new projects with your team."
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
          title="Select an organization first"
          description="Pick a workspace first, then manage that organization's project portfolio."
          action={
            <Link to="/organizations" className="btn btn-primary">
              Choose workspace
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Projects"
        title="Project portfolio"
        description="Project planning and delivery."
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Workspace mode</p>
          <h3 className="section-heading">Project controls</h3>
          <p className="helper-text">Open one section and continue.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Project sections">
            <button
              type="button"
              className={`tasks-view-button${activeSection === "create" ? " active" : ""}`}
              onClick={() => setActiveSection("create")}
            >
              Create
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "team" ? " active" : ""}`}
              onClick={() => setActiveSection("team")}
              disabled={!canManage}
            >
              Team
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
            <p className="data-meta">Projects</p>
            <strong>{pagination.total_items || projects.length}</strong>
          </div>
          <div>
            <p className="data-meta">Team pool</p>
            <strong>{organizationMembers.length}</strong>
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
          <h3 className="section-heading">Create project</h3>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" name="name" className="text-input" value={form.name} onChange={handleChange} required />
            </div>
            <div className="field">
              <label htmlFor="status">Status</label>
              <select id="status" name="status" className="select-input" value={form.status} onChange={handleChange}>
                <option value="active">active</option>
                <option value="completed">completed</option>
                <option value="archived">archived</option>
              </select>
            </div>
            <div className="field field-full">
              <label htmlFor="description">Description</label>
              <textarea id="description" name="description" className="textarea-input" value={form.description} onChange={handleChange} />
            </div>
            <div className="field">
              <label htmlFor="deadlineAt">Deadline</label>
              <input id="deadlineAt" name="deadlineAt" type="datetime-local" className="text-input" value={form.deadlineAt} onChange={handleChange} required />
            </div>
          </div>
          <div className="toolbar-actions">
            <button type="submit" className="btn btn-primary" disabled={creating || !canManage}>
              {creating ? "Creating..." : "Create project"}
            </button>
          </div>
        </form>

        <section className="panel">
          <h3 className="section-heading">Active workspace</h3>
          <p className="kpi-value">{currentOrganization?.name || "Workspace selected"}</p>
          <p className="kpi-caption">Portfolio planning and team ownership stay anchored to the current workspace.</p>
          <div className="list-row">
            <div>
              <p className="data-meta">Projects loaded</p>
              <strong>{projects.length}</strong>
            </div>
            <div>
              <p className="data-meta">Team available</p>
              <strong>{organizationMembers.length}</strong>
            </div>
            <div>
              <p className="data-meta">Role mode</p>
              <strong>{canManage ? "manager" : "viewer"}</strong>
            </div>
          </div>
          <div className="list-row">
            <div>
              <p className="data-meta">Selected project</p>
              <strong>{selectedProjectDetail?.name || "Choose from list"}</strong>
            </div>
            <div>
              <p className="data-meta">Selected status</p>
              <strong>{selectedProjectDetail?.status || "-"}</strong>
            </div>
            <div>
              <p className="data-meta">Selected deadline</p>
              <strong>{formatDate(selectedProjectDetail?.deadline_at)}</strong>
            </div>
          </div>
        </section>
      </section>
      ) : null}

      {activeSection === "team" && canManage ? (
        <section className="split-grid">
          <form className="panel form-shell" onSubmit={handleAddMember}>
            <h3 className="section-heading">Add project member</h3>
            <div className="field">
              <label htmlFor="project-team-project">Project</label>
              <select id="project-team-project" className="select-input" value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)} required>
                <option value="">Choose project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="project-team-member">Person</label>
              <select id="project-team-member" className="select-input" value={memberUserId} onChange={(event) => setMemberUserId(event.target.value)} required>
                <option value="">Choose person</option>
                {availableMemberOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="project-member-role">Project role</label>
              <select id="project-member-role" className="select-input" value={memberRole} onChange={(event) => setMemberRole(event.target.value)}>
                <option value="manager">manager</option>
                <option value="contributor">contributor</option>
                <option value="viewer">viewer</option>
              </select>
            </div>
            <button type="submit" className="btn btn-primary" disabled={pendingAction === "member-add" || !selectedProjectId}>
              {pendingAction === "member-add" ? "Adding..." : "Add member"}
            </button>
          </form>

          <form className="panel form-shell" onSubmit={handleRemoveMember}>
            <h3 className="section-heading">Remove project member</h3>
            <div className="field">
              <label htmlFor="project-member-remove-project">Project</label>
              <select id="project-member-remove-project" className="select-input" value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)} required>
                <option value="">Choose project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="project-member-remove">Team member</label>
              <select id="project-member-remove" className="select-input" value={selectedProjectMemberId} onChange={(event) => setSelectedProjectMemberId(event.target.value)} required>
                <option value="">Choose team member</option>
                {projectMemberOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn btn-secondary" disabled={pendingAction === "member-remove" || !selectedProjectMemberId}>
              {pendingAction === "member-remove" ? "Removing..." : "Remove member"}
            </button>
            <p className="helper-text">{membersLoading ? "Refreshing project team..." : `${projectMembers.length} people currently assigned to this project.`}</p>
          </form>
        </section>
      ) : null}

      {activeSection === "list" ? (
      <>
      <ListToolbar
        search={filters.search}
        onSearchChange={(value) => setFilterValue("search", value)}
        onApply={() => setFilters((current) => ({ ...current, page: 1 }))}
        loading={loading}
      >
        <div className="field">
          <label htmlFor="project-status-filter">Status</label>
          <select id="project-status-filter" className="select-input" value={filters.status} onChange={(event) => setFilterValue("status", event.target.value)}>
            <option value="">all</option>
            <option value="active">active</option>
            <option value="completed">completed</option>
            <option value="archived">archived</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="project-sort">Sort by</label>
          <select id="project-sort" className="select-input" value={filters.sort_by} onChange={(event) => setFilterValue("sort_by", event.target.value)}>
            <option value="created_at">created</option>
            <option value="updated_at">updated</option>
            <option value="deadline_at">deadline</option>
            <option value="name">name</option>
            <option value="status">status</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="project-order">Order</label>
          <select id="project-order" className="select-input" value={filters.order} onChange={(event) => setFilterValue("order", event.target.value)}>
            <option value="desc">newest first</option>
            <option value="asc">oldest first</option>
          </select>
        </div>
      </ListToolbar>

      <section className="panel">
        <h3 className="section-heading">Project list</h3>
        {loading ? <LoadingGrid cards={3} /> : null}
        {!loading && !projects.length ? <p className="muted">No projects returned yet.</p> : null}
        <div className="data-list">
          {projects.map((project) => (
            <article key={project.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>{project.name}</h3>
                  <p>{project.description || "No description provided."}</p>
                </div>
                <StatusPill value={project.status} />
              </div>
              <div className="list-row">
                <div>
                  <p className="data-meta">Deadline</p>
                  <strong>{formatDate(project.deadline_at)}</strong>
                </div>
                <div>
                  <p className="data-meta">Created by</p>
                  <strong>{project.created_by_user_name || "Workspace owner"}</strong>
                </div>
                <div>
                  <p className="data-meta">Updated</p>
                  <strong>{formatDate(project.updated_at)}</strong>
                </div>
              </div>
              {canManage ? (
                <div className="toolbar-actions">
                  {project.status !== "completed" ? (
                    <button type="button" className="btn btn-secondary" disabled={pendingAction === `project-update:${project.id}`} onClick={() => handleProjectStatusChange(project.id, "completed")}>
                      Mark completed
                    </button>
                  ) : null}
                  {project.status !== "active" ? (
                    <button type="button" className="btn btn-secondary" disabled={pendingAction === `project-update:${project.id}`} onClick={() => handleProjectStatusChange(project.id, "active")}>
                      Reopen
                    </button>
                  ) : null}
                  {project.status !== "archived" ? (
                    <button type="button" className="btn btn-secondary" disabled={pendingAction === `project-archive:${project.id}`} onClick={() => handleArchiveProject(project.id)}>
                      Archive
                    </button>
                  ) : null}
                </div>
              ) : null}
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