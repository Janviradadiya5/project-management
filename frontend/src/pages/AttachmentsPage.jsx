import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { deleteAttachment, listAttachments, listProjects, listTasks, uploadAttachment } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import ListToolbar from "../components/ListToolbar.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PaginationBar from "../components/PaginationBar.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate } from "../utils/format.js";
import { getPersonLabel, getTaskOptionLabel } from "../utils/display.js";
import { isValidAttachmentSize } from "../utils/validation.js";

const initialForm = {
  file_name: "",
  content_type: "application/pdf"
};

export default function AttachmentsPage() {
  const { accessToken, isAuthenticated, organizationId, user } = useSession();
  const { pushToast } = useNotifications();
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [attachments, setAttachments] = useState([]);
  const [activeSection, setActiveSection] = useState("upload");
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const [filters, setFilters] = useState({
    search: "",
    content_type: "",
    sort_by: "created_at",
    order: "desc",
    limit: "20",
    page: 1
  });
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total_items: 0 });

  const projectNameById = useMemo(() => new Map(projects.map((project) => [project.id, project.name])), [projects]);

  useEffect(() => {
    async function loadContext() {
      if (!isAuthenticated || !organizationId) {
        return;
      }

      setPending("context");
      setError("");

      try {
        const [projectsResponse, tasksResponse] = await Promise.all([
          listProjects(accessToken, organizationId, { limit: 100, page: 1 }),
          listTasks(accessToken, organizationId, { limit: 100, page: 1, sort_by: "created_at", order: "desc" })
        ]);
        const loadedProjects = projectsResponse?.data?.items || [];
        const loadedTasks = tasksResponse?.data?.items || [];
        setProjects(loadedProjects);
        setTasks(loadedTasks);
        setSelectedTaskId((current) => (loadedTasks.some((task) => task.id === current) ? current : loadedTasks[0]?.id || ""));
      } catch (requestError) {
        setError(requestError.message || "Unable to load task files context.");
      } finally {
        setPending("");
      }
    }

    loadContext();
  }, [accessToken, isAuthenticated, organizationId]);

  useEffect(() => {
    if (!selectedTaskId) {
      setAttachments([]);
      return;
    }

    loadAttachments(filters, selectedTaskId);
  }, [filters.page, selectedTaskId]);

  function handleFormChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function loadAttachments(activeFilters = filters, taskId = selectedTaskId) {
    if (!taskId) {
      setAttachments([]);
      return;
    }

    setPending("load");
    setError("");

    try {
      const response = await listAttachments(accessToken, organizationId, taskId, {
        search: activeFilters.search || undefined,
        content_type: activeFilters.content_type || undefined,
        sort_by: activeFilters.sort_by,
        order: activeFilters.order,
        limit: Number(activeFilters.limit),
        page: activeFilters.page
      });
      const items = response?.data?.items || [];
      setAttachments(items);
      setPagination(response?.data?.pagination || { page: 1, total_pages: 1, total_items: items.length });
    } catch (requestError) {
      setError(requestError.message || "Unable to load attachments.");
      pushToast("Attachment load failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleUpload(event) {
    event.preventDefault();
    setPending("upload");
    setError("");

    if (!selectedTaskId) {
      setPending("");
      setError("Choose a task first.");
      return;
    }

    if (!selectedFile) {
      setPending("");
      setError("Choose a file to upload.");
      return;
    }

    if (!isValidAttachmentSize(selectedFile.size)) {
      setPending("");
      setError("Size must be an integer between 1 and 26214400 bytes.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("file_name", form.file_name || selectedFile.name);
      formData.append("content_type", selectedFile.type || form.content_type || "application/octet-stream");
      formData.append("size_bytes", String(selectedFile.size));
      formData.append("storage_key", "pending");
      formData.append("checksum", "pending");

      const response = await uploadAttachment(accessToken, organizationId, selectedTaskId, formData);
      const created = response?.data;
      if (created) {
        setAttachments((current) => [created, ...current]);
      }
      setForm(initialForm);
      setSelectedFile(null);
      pushToast("File uploaded.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to upload attachment.");
      pushToast("Attachment upload failed.", "error");
    } finally {
      setPending("");
    }
  }

  function setFilterValue(name, value) {
    setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  }

  async function handleDelete(attachmentId) {
    setPending(`delete:${attachmentId}`);
    setError("");

    try {
      await deleteAttachment(accessToken, organizationId, attachmentId);
      setAttachments((current) => current.filter((item) => item.id !== attachmentId));
      pushToast("Attachment deleted.", "warning");
    } catch (requestError) {
      setError(requestError.message || "Unable to delete attachment.");
      pushToast("Attachment delete failed.", "error");
    } finally {
      setPending("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to work with attachments"
          description="Sign in to manage task files, upload records, and keep delivery assets organized."
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
          description="Choose a workspace before opening task files and uploads."
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
        eyebrow="Attachments"
        title="Task files"
        description="Upload and manage task files."
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Workspace mode</p>
          <h3 className="section-heading">File controls</h3>
          <p className="helper-text">Open one section and continue.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Attachment sections">
            <button
              type="button"
              className={`tasks-view-button${activeSection === "upload" ? " active" : ""}`}
              onClick={() => setActiveSection("upload")}
            >
              Upload
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "browse" ? " active" : ""}`}
              onClick={() => setActiveSection("browse")}
            >
              Browse
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "files" ? " active" : ""}`}
              onClick={() => setActiveSection("files")}
            >
              Files list
            </button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Tasks</p>
            <strong>{tasks.length}</strong>
          </div>
          <div>
            <p className="data-meta">Files shown</p>
            <strong>{attachments.length}</strong>
          </div>
          <div>
            <p className="data-meta">Pending</p>
            <strong>{pending || "idle"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection}</strong>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      {activeSection === "upload" ? (
        <section className="split-grid">
          <form className="panel form-shell" onSubmit={handleUpload}>
            <h3 className="section-heading">Upload file</h3>
            <div className="field">
              <label htmlFor="attachment-task-select">Task</label>
              <select id="attachment-task-select" className="select-input" value={selectedTaskId} onChange={(event) => setSelectedTaskId(event.target.value)} required>
                <option value="">Choose task</option>
                {tasks.map((task) => (
                  <option key={task.id} value={task.id}>
                    {getTaskOptionLabel(task, projectNameById)}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="attachment-file">Choose file</label>
                <input
                  id="attachment-file"
                  type="file"
                  className="text-input"
                  onChange={(event) => {
                    const file = event.target.files?.[0] || null;
                    setSelectedFile(file);
                    if (file) {
                      setForm((current) => ({ ...current, file_name: file.name, content_type: file.type || current.content_type }));
                    }
                  }}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="content-type">Content type</label>
                <input id="content-type" name="content_type" className="text-input" value={form.content_type} onChange={handleFormChange} />
              </div>
              <div className="field">
                <label htmlFor="file-name">File name</label>
                <input id="file-name" name="file_name" className="text-input" value={form.file_name} onChange={handleFormChange} required />
              </div>
              <div className="field">
                <label>File size</label>
                <input className="text-input" value={selectedFile ? `${selectedFile.size} bytes` : "No file selected"} disabled />
              </div>
            </div>
            <div className="toolbar-actions">
              <button type="submit" className="btn btn-secondary" disabled={pending === "upload" || !selectedTaskId}>
                {pending === "upload" ? "Saving..." : "Save attachment"}
              </button>
              {selectedTaskId ? (
                <Link to={`/tasks/${selectedTaskId}`} className="btn btn-secondary">
                  Open task workspace
                </Link>
              ) : null}
            </div>
          </form>

          <section className="panel form-shell">
            <h3 className="section-heading">Upload guide</h3>
            <p className="helper-text">Select task, pick file, and save.</p>
            <div className="list-row">
              <div>
                <p className="data-meta">Selected task</p>
                <strong>{selectedTaskId ? "Ready" : "Not selected"}</strong>
              </div>
              <div>
                <p className="data-meta">File selected</p>
                <strong>{selectedFile?.name || "None"}</strong>
              </div>
            </div>
          </section>
        </section>
      ) : null}

      {activeSection === "browse" ? (
        <section className="panel form-shell">
          <h3 className="section-heading">Browse task files</h3>
          <p className="helper-text">Pick a task, then continue to Files list section.</p>
          <div className="field">
            <label htmlFor="attachment-task-browse">Current task</label>
            <select id="attachment-task-browse" className="select-input" value={selectedTaskId} onChange={(event) => setSelectedTaskId(event.target.value)} required>
              <option value="">Choose task</option>
              {tasks.map((task) => (
                <option key={task.id} value={task.id}>
                  {getTaskOptionLabel(task, projectNameById)}
                </option>
              ))}
            </select>
          </div>
          <div className="list-row">
            <div>
              <p className="data-meta">Tasks available</p>
              <strong>{tasks.length}</strong>
            </div>
            <div>
              <p className="data-meta">Files shown</p>
              <strong>{attachments.length}</strong>
            </div>
          </div>
        </section>
      ) : null}

      {activeSection === "files" ? (
      <>
      <ListToolbar
        search={filters.search}
        onSearchChange={(value) => setFilterValue("search", value)}
        onApply={() => {
          const nextFilters = { ...filters, page: 1 };
          setFilters(nextFilters);
          loadAttachments(nextFilters);
        }}
        loading={pending === "load"}
      >
        <div className="field">
          <label htmlFor="attachment-content-filter">Content type</label>
          <input id="attachment-content-filter" className="text-input" value={filters.content_type} onChange={(event) => setFilterValue("content_type", event.target.value)} placeholder="application/pdf" />
        </div>
        <div className="field">
          <label htmlFor="attachment-sort">Sort by</label>
          <select id="attachment-sort" className="select-input" value={filters.sort_by} onChange={(event) => setFilterValue("sort_by", event.target.value)}>
            <option value="created_at">created</option>
            <option value="file_name">file name</option>
            <option value="size_bytes">file size</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="attachment-order">Order</label>
          <select id="attachment-order" className="select-input" value={filters.order} onChange={(event) => setFilterValue("order", event.target.value)}>
            <option value="desc">newest first</option>
            <option value="asc">oldest first</option>
          </select>
        </div>
      </ListToolbar>

      <section className="panel">
        <h3 className="section-heading">Attachment list</h3>
        {pending === "load" || pending === "context" ? <LoadingGrid cards={3} /> : null}
        {!attachments.length ? <p className="muted">No attachments loaded yet.</p> : null}
        <div className="data-list">
          {attachments.map((attachment) => (
            <article key={attachment.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>{attachment.file_name}</h3>
                  <p>{attachment.content_type}</p>
                </div>
                <StatusPill value={attachment.deleted_at ? "archived" : "active"} />
              </div>
              <div className="list-row">
                <div>
                  <p className="data-meta">Size</p>
                  <strong>{attachment.size_bytes} bytes</strong>
                </div>
                <div>
                  <p className="data-meta">Uploaded by</p>
                  <strong>{getPersonLabel({ id: attachment.uploaded_by_user_id, name: attachment.uploaded_by_user_name, currentUserId: user?.id })}</strong>
                </div>
                <div>
                  <p className="data-meta">Created</p>
                  <strong>{formatDate(attachment.created_at)}</strong>
                </div>
              </div>
              <div className="toolbar-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleDelete(attachment.id)}
                  disabled={pending === `delete:${attachment.id}` || Boolean(attachment.deleted_at)}
                >
                  {pending === `delete:${attachment.id}` ? "Deleting..." : "Delete"}
                </button>
              </div>
            </article>
          ))}
        </div>
        <PaginationBar
          pagination={pagination}
          loading={pending === "load"}
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