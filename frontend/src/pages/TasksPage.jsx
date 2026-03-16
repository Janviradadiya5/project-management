import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createTask, deleteTask, listProjects, listTasks, updateTask } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import ListToolbar from "../components/ListToolbar.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PaginationBar from "../components/PaginationBar.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate, formatId, toApiDateTime } from "../utils/format.js";
import { canContribute, canManageProjects } from "../utils/roles.js";
import { isNonEmpty } from "../utils/validation.js";

const initialForm = {
  project_id: "",
  title: "",
  description: "",
  priority: "medium",
  status: "todo",
  dueAt: ""
};

const statusLanes = [
  { key: "todo", title: "Halt" },
  { key: "in_progress", title: "In Progress" },
  { key: "done", title: "Done" }
];

function humanizeStatus(value) {
  if (!value) {
    return "Unknown";
  }

  return value.replaceAll("_", " ");
}

export default function TasksPage() {
  const { accessToken, isAuthenticated, isSuperAdmin, organizationId, organizationRole, user } = useSession();
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [taskEdits, setTaskEdits] = useState({});
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [pendingAction, setPendingAction] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activeSection, setActiveSection] = useState("create");
  const [draggingTaskId, setDraggingTaskId] = useState("");
  const [dropLane, setDropLane] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    status: "",
    priority: "",
    sort_by: "created_at",
    order: "desc",
    limit: "20",
    page: 1
  });
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });
  const canWriteTasks = canContribute(organizationRole, isSuperAdmin);
  const canDeleteTasks = canManageProjects(organizationRole, isSuperAdmin);
  const projectNameById = new Map(projects.map((project) => [project.id, project.name]));
  const tasksByLane = statusLanes.map((lane) => ({
    ...lane,
    items: tasks.filter((task) => task.status === lane.key)
  }));

  useEffect(() => {
    async function loadData() {
      if (!isAuthenticated || !organizationId) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [projectsResponse, tasksResponse] = await Promise.all([
          listProjects(accessToken, organizationId),
          listTasks(accessToken, organizationId, {
            search: filters.search || undefined,
            status: filters.status || undefined,
            priority: filters.priority || undefined,
            sort_by: filters.sort_by,
            order: filters.order,
            limit: Number(filters.limit),
            page: filters.page
          })
        ]);

        const projectItems = projectsResponse?.data?.items || [];
        const taskItems = tasksResponse?.data?.items || [];
        setProjects(projectItems);
        setTasks(taskItems);
        setPagination(tasksResponse?.data?.pagination || { page: 1, total_pages: 1, total_items: taskItems.length });
        setForm((current) => ({
          ...current,
          project_id: current.project_id || projectItems[0]?.id || ""
        }));
      } catch (requestError) {
        setError(requestError.message || "Unable to load tasks.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [accessToken, filters, isAuthenticated, organizationId]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!canWriteTasks) {
      setError("Your role can view tasks but cannot create new ones.");
      return;
    }

    setCreating(true);
    setError("");
    setSuccess("");

    if (!isNonEmpty(form.title, 3)) {
      setCreating(false);
      setError("Task title must be at least 3 characters.");
      return;
    }

    if (!form.project_id) {
      setCreating(false);
      setError("Please select a project.");
      return;
    }

    if (!form.dueAt) {
      setCreating(false);
      setError("Please select a deadline.");
      return;
    }

    try {
      const response = await createTask(accessToken, organizationId, {
        project_id: form.project_id,
        title: form.title,
        description: form.description,
        priority: form.priority,
        status: form.status,
        due_at: toApiDateTime(form.dueAt)
      });

      setTasks((current) => [response?.data, ...current]);
      setForm((current) => ({
        ...initialForm,
        project_id: current.project_id
      }));
      setSuccess("Task created successfully.");
    } catch (requestError) {
      setError(requestError.message || "Unable to create task.");
    } finally {
      setCreating(false);
    }
  }

  function setFilterValue(name, value) {
    setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  }

  async function handleTaskUpdate(taskId) {
    const patch = taskEdits[taskId];

    if (!patch || (!patch.status && !patch.priority)) {
      setError("Select a new status or priority first.");
      return;
    }

    setPendingAction(`task-update:${taskId}`);
    setError("");

    try {
      const response = await updateTask(accessToken, organizationId, taskId, {
        status: patch.status,
        priority: patch.priority
      });
      const updated = response?.data;
      setTasks((current) => current.map((task) => (task.id === taskId ? { ...task, ...updated } : task)));
      setSuccess("Task updated.");
    } catch (requestError) {
      setError(requestError.message || "Unable to update task.");
    } finally {
      setPendingAction("");
    }
  }

  async function handleTaskDelete(taskId) {
    setPendingAction(`task-delete:${taskId}`);
    setError("");

    try {
      await deleteTask(accessToken, organizationId, taskId);
      setTasks((current) => current.filter((task) => task.id !== taskId));
      setSuccess("Task removed.");
    } catch (requestError) {
      setError(requestError.message || "Unable to delete task.");
    } finally {
      setPendingAction("");
    }
  }

  function getAssigneeLabel(task) {
    if (!task?.assignee_user_id) {
      return "Unassigned";
    }

    if (task.assignee_user_id === user?.id) {
      return "Own";
    }

    return task.assignee_user_name || formatId(task.assignee_user_id);
  }

  function getCreatorLabel(task) {
    if (!task?.created_by_user_id) {
      return "Unknown";
    }

    if (task.created_by_user_id === user?.id) {
      return "Own";
    }

    return task.created_by_user_name || formatId(task.created_by_user_id);
  }

  function getLaneTone(status) {
    if (status === "done") {
      return "emerald";
    }

    if (status === "in_progress") {
      return "blue";
    }

    return "amber";
  }

  function getPriorityTone(priority) {
  async function handleBoardDrop(nextStatus) {
    if (!draggingTaskId || !canWriteTasks) {
      setDropLane("");
      setDraggingTaskId("");
      return;
    }

    const draggedTask = tasks.find((task) => task.id === draggingTaskId);
    if (!draggedTask || draggedTask.status === nextStatus) {
      setDropLane("");
      setDraggingTaskId("");
      return;
    }

    const previousTasks = tasks;
    setTasks((current) => current.map((task) => (task.id === draggingTaskId ? { ...task, status: nextStatus } : task)));
    setDropLane("");
    setDraggingTaskId("");
    setPendingAction(`task-drag:${draggedTask.id}`);
    setError("");

    try {
      const response = await updateTask(accessToken, organizationId, draggedTask.id, { status: nextStatus });
      const updated = response?.data;
      setTasks((current) => current.map((task) => (task.id === draggedTask.id ? { ...task, ...updated } : task)));
      setSuccess(`Moved to ${humanizeStatus(nextStatus)}.`);
    } catch (requestError) {
      setTasks(previousTasks);
      setError(requestError.message || "Unable to move task.");
    } finally {
      setPendingAction("");
    }
  }
    if (priority === "high") {
      return "rose";
    }

    if (priority === "low") {
      return "mint";
    }

    return "sky";
  }

  async function handleBoardDrop(nextStatus, droppedTaskId = "") {
    const taskId = droppedTaskId || draggingTaskId;

    if (!taskId || !canWriteTasks) {
      setDropLane("");
      setDraggingTaskId("");
      return;
    }

    const draggedTask = tasks.find((task) => task.id === taskId);
    if (!draggedTask || draggedTask.status === nextStatus) {
      setDropLane("");
      setDraggingTaskId("");
      return;
    }

    const previousTasks = tasks;
    setTasks((current) => current.map((task) => (task.id === taskId ? { ...task, status: nextStatus } : task)));
    setDropLane("");
    setDraggingTaskId("");
    setPendingAction(`task-drag:${draggedTask.id}`);
    setError("");

    try {
      const response = await updateTask(accessToken, organizationId, draggedTask.id, { status: nextStatus });
      const updated = response?.data;
      setTasks((current) => current.map((task) => (task.id === draggedTask.id ? { ...task, ...updated } : task)));
      setSuccess(`Moved to ${humanizeStatus(nextStatus)}.`);
    } catch (requestError) {
      setTasks(previousTasks);
      setError(requestError.message || "Unable to move task.");
    } finally {
      setPendingAction("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to load tasks"
          description="Task listing and creation are protected operations that require an authenticated session."
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
          description="Tasks require the organization header and typically rely on projects inside that organization."
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
    <section className="page page-tasks-clear">
      <PageHeader
        eyebrow="Tasks"
        title="Task management"
        description="Manage project tasks quickly."
        actions={
          <>
            <Link to="/projects" className="btn btn-secondary">Open projects</Link>
            <Link to="/notifications" className="btn btn-primary">Open inbox</Link>
          </>
        }
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Workspace mode</p>
          <h3 className="section-heading">Project task workspace</h3>
          <p className="helper-text">Choose a section and continue.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Task sections">
            <button
              type="button"
              className={`tasks-view-button${activeSection === "create" ? " active" : ""}`}
              onClick={() => setActiveSection("create")}
            >
              Create task
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "list" ? " active" : ""}`}
              onClick={() => setActiveSection("list")}
            >
              Detailed task list
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "board" ? " active" : ""}`}
              onClick={() => setActiveSection("board")}
            >
              Task board
            </button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Total tasks</p>
            <strong>{pagination.total_items || tasks.length}</strong>
          </div>
          <div>
            <p className="data-meta">Projects</p>
            <strong>{projects.length}</strong>
          </div>
          <div>
            <p className="data-meta">Mode</p>
            <strong>{canWriteTasks ? "Editor" : "Viewer"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection === "create" ? "Planning" : activeSection === "list" ? "Tracking" : "Execution"}</strong>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}

      {activeSection === "create" ? (
        <section className="split-grid tasks-section-shell">
          <form className="panel form-shell tasks-form-panel tasks-form-panel-pro" onSubmit={handleSubmit}>
            <div className="tasks-section-heading">
              <p className="section-label">Create task</p>
              <h3 className="section-heading">Add task</h3>
              <p className="helper-text">Fill required fields only.</p>
            </div>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="project_id">Project</label>
                <select id="project_id" name="project_id" className="select-input" value={form.project_id} onChange={handleChange} required>
                  <option value="">Select a project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="title">Title</label>
                <input id="title" name="title" className="text-input" value={form.title} onChange={handleChange} required />
              </div>
              <div className="field">
                <label htmlFor="priority">Priority</label>
                <select id="priority" name="priority" className="select-input" value={form.priority} onChange={handleChange}>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="status">Status</label>
                <select id="status" name="status" className="select-input" value={form.status} onChange={handleChange}>
                  <option value="todo">todo</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                </select>
              </div>
              <div className="field field-full">
                <label htmlFor="description">Description</label>
                <textarea id="description" name="description" className="textarea-input" value={form.description} onChange={handleChange} />
              </div>
              <div className="field">
                <label htmlFor="dueAt">Deadline</label>
                <input id="dueAt" name="dueAt" type="datetime-local" className="text-input" value={form.dueAt} onChange={handleChange} required />
              </div>
            </div>
            <div className="toolbar-actions">
              <button type="submit" className="btn btn-primary" disabled={creating || !projects.length || !canWriteTasks}>
                {creating ? "Creating..." : "Create task"}
              </button>
            </div>
          </form>

          <section className="panel tasks-context-panel tasks-context-panel-pro">
            <p className="section-label">Context</p>
            <h3 className="section-heading">Project snapshot</h3>
            <p className="kpi-caption">Quick context.</p>
            <div className="tasks-context-grid">
              <div className="tasks-context-card">
                <p className="data-meta">Primary project</p>
                <strong>{projects[0]?.name || "Workspace ready"}</strong>
              </div>
              <div className="tasks-context-card">
                <p className="data-meta">Projects loaded</p>
                <strong>{projects.length}</strong>
              </div>
              <div className="tasks-context-card">
                <p className="data-meta">Tasks loaded</p>
                <strong>{tasks.length}</strong>
              </div>
              <div className="tasks-context-card">
                <p className="data-meta">Role mode</p>
                <strong>{canWriteTasks ? "editor" : "viewer"}</strong>
              </div>
            </div>
            <div className="tasks-intro-chips">
              <span className="tasks-chip">Plan</span>
              <span className="tasks-chip">Assign</span>
              <span className="tasks-chip">Deliver</span>
            </div>
            <div className="tasks-context-actions">
              <Link to="/organizations" className="btn btn-secondary">Switch organization</Link>
              <Link to="/projects" className="btn btn-secondary">Manage projects</Link>
            </div>
          </section>
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
              <label htmlFor="task-status-filter">Status</label>
              <select id="task-status-filter" className="select-input" value={filters.status} onChange={(event) => setFilterValue("status", event.target.value)}>
                <option value="">all</option>
                <option value="todo">todo</option>
                <option value="in_progress">in_progress</option>
                <option value="done">done</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="task-priority-filter">Priority</label>
              <select id="task-priority-filter" className="select-input" value={filters.priority} onChange={(event) => setFilterValue("priority", event.target.value)}>
                <option value="">all</option>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="task-sort">Sort by</label>
              <select id="task-sort" className="select-input" value={filters.sort_by} onChange={(event) => setFilterValue("sort_by", event.target.value)}>
                <option value="created_at">created_at</option>
                <option value="due_at">due_at</option>
                <option value="priority">priority</option>
                <option value="status">status</option>
                <option value="title">title</option>
              </select>
            </div>
          </ListToolbar>

          <section className="panel tasks-section-shell tasks-list-shell-pro">
            <div className="tasks-board-header">
              <div>
                <p className="section-label">Detailed task list</p>
                <h3 className="section-heading">Task records</h3>
              </div>
              <p className="helper-text">Compact cards with quick actions.</p>
            </div>
            {loading ? <LoadingGrid cards={3} /> : null}
            {!loading && !tasks.length ? <p className="muted">No tasks returned yet.</p> : null}
            <div className="tasks-detail-list">
              {tasks.map((task) => (
                <article key={task.id} className={`tasks-detail-card lane-${getLaneTone(task.status)}`}>
                  <div className="tasks-detail-head">
                    <div className="tasks-detail-headline">
                      <span className={`tasks-priority-pill ${getPriorityTone(task.priority)}`}>{task.priority} priority</span>
                      <h3>{task.title}</h3>
                      <p>{task.description || "No task description provided."}</p>
                    </div>
                    <StatusPill value={task.status} />
                  </div>

                  <div className="tasks-detail-meta-row compact">
                    <div className="tasks-detail-stat">
                      <p className="data-meta">Project</p>
                      <strong>{projectNameById.get(task.project_id) || formatId(task.project_id)}</strong>
                    </div>
                    <div className="tasks-detail-stat">
                      <p className="data-meta">Assigned to</p>
                      <strong>{getAssigneeLabel(task)}</strong>
                    </div>
                    <div className="tasks-detail-stat">
                      <p className="data-meta">Created by</p>
                      <strong>{getCreatorLabel(task)}</strong>
                    </div>
                    <div className="tasks-detail-stat">
                      <p className="data-meta">Due at</p>
                      <strong>{formatDate(task.due_at)}</strong>
                    </div>
                  </div>

                  <div className="tasks-detail-actions-row">
                    <Link to={`/tasks/${task.id}`} className="btn btn-secondary">
                      Open workspace
                    </Link>
                    {canWriteTasks ? (
                      <>
                        <select
                          className="select-input"
                          value={taskEdits[task.id]?.status || task.status}
                          onChange={(event) =>
                            setTaskEdits((current) => ({
                              ...current,
                              [task.id]: { ...current[task.id], status: event.target.value, priority: current[task.id]?.priority || task.priority }
                            }))
                          }
                        >
                          <option value="todo">todo</option>
                          <option value="in_progress">in_progress</option>
                          <option value="done">done</option>
                        </select>
                        <select
                          className="select-input"
                          value={taskEdits[task.id]?.priority || task.priority}
                          onChange={(event) =>
                            setTaskEdits((current) => ({
                              ...current,
                              [task.id]: { ...current[task.id], priority: event.target.value, status: current[task.id]?.status || task.status }
                            }))
                          }
                        >
                          <option value="low">low</option>
                          <option value="medium">medium</option>
                          <option value="high">high</option>
                        </select>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          disabled={pendingAction === `task-update:${task.id}`}
                          onClick={() => handleTaskUpdate(task.id)}
                        >
                          {pendingAction === `task-update:${task.id}` ? "Saving..." : "Save"}
                        </button>
                      </>
                    ) : null}
                    {canDeleteTasks ? (
                      <button
                        type="button"
                        className="btn btn-secondary"
                        disabled={pendingAction === `task-delete:${task.id}`}
                        onClick={() => handleTaskDelete(task.id)}
                      >
                        {pendingAction === `task-delete:${task.id}` ? "Deleting..." : "Delete"}
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

      {activeSection === "board" ? (
        <>
          <ListToolbar
            search={filters.search}
            onSearchChange={(value) => setFilterValue("search", value)}
            onApply={() => setFilters((current) => ({ ...current, page: 1 }))}
            loading={loading}
          >
            <div className="field">
              <label htmlFor="board-status-filter">Status</label>
              <select id="board-status-filter" className="select-input" value={filters.status} onChange={(event) => setFilterValue("status", event.target.value)}>
                <option value="">all</option>
                <option value="todo">todo</option>
                <option value="in_progress">in_progress</option>
                <option value="done">done</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="board-priority-filter">Priority</label>
              <select id="board-priority-filter" className="select-input" value={filters.priority} onChange={(event) => setFilterValue("priority", event.target.value)}>
                <option value="">all</option>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="board-sort">Sort by</label>
              <select id="board-sort" className="select-input" value={filters.sort_by} onChange={(event) => setFilterValue("sort_by", event.target.value)}>
                <option value="created_at">created_at</option>
                <option value="due_at">due_at</option>
                <option value="priority">priority</option>
                <option value="status">status</option>
                <option value="title">title</option>
              </select>
            </div>
          </ListToolbar>

          <section className="panel tasks-section-shell tasks-board-shell-pro">
            <div className="tasks-board-header">
              <div>
                <p className="section-label">Task board</p>
                <h3 className="section-heading">Move tasks</h3>
              </div>
              <p className="helper-text">Drag and drop to update status.</p>
            </div>
            {loading ? <LoadingGrid cards={3} /> : null}
            {!loading && !tasks.length ? <p className="muted">No tasks returned yet.</p> : null}
            <div className="tasks-kanban-grid tasks-kanban-grid-pro">
              {tasksByLane.map((lane) => (
                <article
                  key={lane.key}
                  className={`tasks-kanban-lane lane-${getLaneTone(lane.key)}${dropLane === lane.key ? " drag-target" : ""}`}
                  onDragOver={(event) => {
                    if (!canWriteTasks) {
                      return;
                    }
                    event.preventDefault();
                    setDropLane(lane.key);
                  }}
                  onDragLeave={() => {
                    if (dropLane === lane.key) {
                      setDropLane("");
                    }
                  }}
                  onDrop={(event) => {
                    event.preventDefault();
                    const droppedId = event.dataTransfer.getData("text/task-id") || "";
                    void handleBoardDrop(lane.key, droppedId);
                  }}
                >
                  <header>
                    <div>
                      <p className="tasks-lane-caption">{lane.key === "todo" ? "Queue" : lane.key === "in_progress" ? "Execution" : "Delivery"}</p>
                      <h4>{lane.title}</h4>
                    </div>
                    <span>{lane.items.length}</span>
                  </header>
                  <div className="tasks-kanban-stack">
                    {lane.items.slice(0, 6).map((task) => (
                      <div
                        key={task.id}
                        className={`tasks-kanban-card tasks-kanban-card-pro${draggingTaskId === task.id ? " dragging" : ""}`}
                        draggable={canWriteTasks}
                        onDragStart={(event) => {
                          event.dataTransfer.setData("text/task-id", task.id);
                          event.dataTransfer.effectAllowed = "move";
                          setDraggingTaskId(task.id);
                        }}
                        onDragEnd={() => {
                          setDraggingTaskId("");
                          setDropLane("");
                        }}
                      >
                        <div className="tasks-kanban-card-top">
                          <p className="tasks-card-project">{projectNameById.get(task.project_id) || "Project"}</p>
                          <span className={`tasks-priority-pill ${getPriorityTone(task.priority)}`}>{task.priority}</span>
                        </div>
                        <strong>{task.title}</strong>
                        <p className="tasks-board-card-copy">{task.description || "Project task ready."}</p>
                        <div className="tasks-card-meta">
                          <span>{formatDate(task.due_at)}</span>
                          <span>{getAssigneeLabel(task)}</span>
                        </div>
                        <div className="tasks-board-card-foot">
                          <span className="tasks-drag-hint">Drag</span>
                          {pendingAction === `task-drag:${task.id}` ? <span className="tasks-drag-saving">Saving...</span> : null}
                        </div>
                        <div className="tasks-board-actions">
                          <Link to={`/tasks/${task.id}`} className="btn btn-secondary tasks-board-action-btn">Open</Link>
                          {canDeleteTasks ? (
                            <button
                              type="button"
                              className="btn btn-secondary tasks-board-action-btn"
                              disabled={pendingAction === `task-delete:${task.id}`}
                              onClick={() => handleTaskDelete(task.id)}
                            >
                              {pendingAction === `task-delete:${task.id}` ? "Deleting..." : "Delete"}
                            </button>
                          ) : null}
                        </div>
                      </div>
                    ))}
                    {!lane.items.length ? <p className="muted">No tasks in this lane.</p> : null}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </section>
  );
}