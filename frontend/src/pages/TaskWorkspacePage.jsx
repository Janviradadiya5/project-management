import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  createComment,
  getTask,
  listTaskComments,
  listAttachments,
  uploadAttachment
} from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate, formatId } from "../utils/format.js";
import { getCommentOptionLabel } from "../utils/display.js";
import { isNonEmpty, isUuid, isValidAttachmentSize } from "../utils/validation.js";

const initialCommentForm = {
  body: "",
  parentCommentId: ""
};

const initialAttachmentForm = {
  file_name: "",
  content_type: "application/pdf"
};

export default function TaskWorkspacePage() {
  const { taskId } = useParams();
  const { accessToken, isAuthenticated, organizationId, user } = useSession();
  const { pushToast } = useNotifications();

  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [activity, setActivity] = useState([]);
  const [commentForm, setCommentForm] = useState(initialCommentForm);
  const [attachmentForm, setAttachmentForm] = useState(initialAttachmentForm);
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");

  useEffect(() => {
    async function loadWorkspace() {
      if (!isAuthenticated || !organizationId || !taskId) {
        return;
      }

      if (!isUuid(taskId)) {
        setError("Task ID is not a valid UUID.");
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [taskResponse, attachmentsResponse] = await Promise.all([
          getTask(accessToken, organizationId, taskId),
          listAttachments(accessToken, organizationId, taskId)
        ]);

        setTask(taskResponse?.data || null);
        setAttachments(attachmentsResponse?.data?.items || []);

        const commentsResponse = await listTaskComments(accessToken, organizationId, taskId, {
          limit: 100,
          page: 1,
          order: "desc"
        });
        setComments(commentsResponse?.data?.items || []);
      } catch (requestError) {
        setError(requestError.message || "Unable to load task workspace.");
      } finally {
        setLoading(false);
      }
    }

    loadWorkspace();
  }, [accessToken, isAuthenticated, organizationId, taskId]);

  function appendActivity(type, payload) {
    setActivity((current) => [
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type,
        at: new Date().toISOString(),
        payload
      },
      ...current
    ].slice(0, 8));
  }

  function getAssigneeLabel() {
    if (!task?.assignee_user_id) {
      return "Unassigned";
    }

    if (task.assignee_user_id === user?.id) {
      return "Own";
    }

    return task.assignee_user_name || formatId(task.assignee_user_id);
  }

  function getCreatorLabel() {
    if (!task?.created_by_user_id) {
      return "Unknown";
    }

    if (task.created_by_user_id === user?.id) {
      return "Own";
    }

    return task.created_by_user_name || formatId(task.created_by_user_id);
  }

  async function handleCreateComment(event) {
    event.preventDefault();

        if (!isNonEmpty(commentForm.body, 1)) {
          setError("Comment body is required.");
          setPending("");
          return;
        }

    setPending("comment");
    setError("");

    try {
      const response = await createComment(accessToken, organizationId, taskId, {
        body: commentForm.body,
        parent_comment_id: commentForm.parentCommentId || undefined
      });
      setCommentForm(initialCommentForm);
      appendActivity("Comment created", response?.data || null);
      setComments((current) => (response?.data ? [response.data, ...current] : current));
      pushToast("Comment created for task.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to create comment.");
      pushToast("Comment creation failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleUploadAttachment(event) {
    event.preventDefault();

    setPending("attachment");
    setError("");

    if (!selectedFile) {
      setPending("");
      setError("Choose a file first.");
      return;
    }

    if (!isValidAttachmentSize(selectedFile.size)) {
      setPending("");
      setError("Attachment size must be between 1 and 26214400 bytes.");
      return;
    }

    const resolvedName = attachmentForm.file_name || selectedFile.name;
    if (!isNonEmpty(resolvedName, 1)) {
      setPending("");
      setError("File name is required.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("file_name", resolvedName);
      formData.append("content_type", selectedFile.type || attachmentForm.content_type || "application/octet-stream");
      formData.append("size_bytes", String(selectedFile.size));
      formData.append("storage_key", "pending");
      formData.append("checksum", "pending");

      const response = await uploadAttachment(accessToken, organizationId, taskId, formData);

      const created = response?.data;
      setAttachments((current) => (created ? [created, ...current] : current));
      setAttachmentForm(initialAttachmentForm);
      setSelectedFile(null);
      appendActivity("Attachment uploaded", created || null);
      pushToast("Attachment uploaded.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to upload attachment.");
      pushToast("Attachment upload failed.", "error");
    } finally {
      setPending("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to open task workspace"
          description="Sign in to review task context, post updates, and manage related files."
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
          description="Choose a workspace before opening task-level collaboration and files."
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
        eyebrow="Task Workspace"
        title={task ? task.title : `Task ${formatId(taskId || "")}`}
        description="Manage this task from one place."
        actions={
          <Link to="/tasks" className="btn btn-secondary">
            Back to tasks
          </Link>
        }
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Workspace mode</p>
          <h3 className="section-heading">Task controls</h3>
          <p className="helper-text">Open one section and continue.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Task workspace sections">
            <button type="button" className={`tasks-view-button${activeSection === "overview" ? " active" : ""}`} onClick={() => setActiveSection("overview")}>Overview</button>
            <button type="button" className={`tasks-view-button${activeSection === "comments" ? " active" : ""}`} onClick={() => setActiveSection("comments")}>Comments</button>
            <button type="button" className={`tasks-view-button${activeSection === "files" ? " active" : ""}`} onClick={() => setActiveSection("files")}>Files</button>
            <button type="button" className={`tasks-view-button${activeSection === "activity" ? " active" : ""}`} onClick={() => setActiveSection("activity")}>Activity</button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Comments</p>
            <strong>{comments.length}</strong>
          </div>
          <div>
            <p className="data-meta">Attachments</p>
            <strong>{attachments.length}</strong>
          </div>
          <div>
            <p className="data-meta">Status</p>
            <strong>{task?.status || "-"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection}</strong>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <div className="panel"><p className="muted">Loading task context...</p></div> : null}

      {activeSection === "overview" && task ? (
        <section className="panel">
          <div className="data-card-header">
            <div>
              <h3>{task.title}</h3>
              <p>{task.description || "No description provided."}</p>
            </div>
            <StatusPill value={task.status} />
          </div>
          <div className="list-row">
            <div>
              <p className="data-meta">Priority</p>
              <strong>{task.priority}</strong>
            </div>
            <div>
              <p className="data-meta">Assigned to</p>
              <strong>{getAssigneeLabel()}</strong>
            </div>
            <div>
              <p className="data-meta">Due</p>
              <strong>{formatDate(task.due_at)}</strong>
            </div>
          </div>
          <div className="list-row">
            <div>
              <p className="data-meta">Created by</p>
              <strong>{getCreatorLabel()}</strong>
            </div>
            <div>
              <p className="data-meta">Project</p>
              <strong>{formatId(task.project_id)}</strong>
            </div>
            <div>
              <p className="data-meta">Completed</p>
              <strong>{formatDate(task.completed_at)}</strong>
            </div>
          </div>
        </section>
      ) : null}

      {activeSection === "comments" ? (
      <section className="panel form-shell">
        <h3 className="section-heading">Create comment</h3>
        <form onSubmit={handleCreateComment}>
          <div className="field">
            <label htmlFor="workspace-comment-body">Body</label>
            <textarea
              id="workspace-comment-body"
              className="textarea-input"
              rows="3"
              value={commentForm.body}
              onChange={(event) => setCommentForm((current) => ({ ...current, body: event.target.value }))}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="workspace-parent-comment">Reply to (optional)</label>
            <select
              id="workspace-parent-comment"
              className="select-input"
              value={commentForm.parentCommentId}
              onChange={(event) => setCommentForm((current) => ({ ...current, parentCommentId: event.target.value }))}
            >
              <option value="">Start a new thread</option>
              {comments.map((comment) => (
                <option key={comment.id} value={comment.id}>
                  {getCommentOptionLabel(comment, user?.id)}
                </option>
              ))}
            </select>
          </div>
          <div className="toolbar-actions">
            <button type="submit" className="btn btn-primary" disabled={pending === "comment"}>
              {pending === "comment" ? "Creating..." : "Create comment"}
            </button>
          </div>
        </form>

        <div>
          <h3 className="section-heading">Recent comments</h3>
          {!comments.length ? <p className="muted">No comments yet for this task.</p> : null}
          <div className="data-list">
            {comments.slice(0, 6).map((comment) => (
              <article key={comment.id} className="data-card">
                <div className="data-card-header">
                  <div>
                    <h3>{getCommentOptionLabel(comment, user?.id).split(" · ")[0]}</h3>
                    <p>{comment.body}</p>
                  </div>
                  <StatusPill value={comment.is_edited ? "edited" : "posted"} />
                </div>
                <div className="list-row">
                  <div>
                    <p className="data-meta">Posted</p>
                    <strong>{formatDate(comment.created_at)}</strong>
                  </div>
                  <div>
                    <p className="data-meta">Reply type</p>
                    <strong>{comment.parent_comment_id ? "Reply" : "Main thread"}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
      ) : null}

      {activeSection === "files" ? (
      <section className="split-grid">
        <form className="panel form-shell" onSubmit={handleUploadAttachment}>
          <h3 className="section-heading">Upload file</h3>
          <div className="form-grid">
            <div className="field field-full">
              <label htmlFor="workspace-file">Choose file</label>
              <input
                id="workspace-file"
                type="file"
                className="text-input"
                onChange={(event) => {
                  const file = event.target.files?.[0] || null;
                  setSelectedFile(file);
                  if (file) {
                    setAttachmentForm((current) => ({
                      ...current,
                      file_name: file.name,
                      content_type: file.type || current.content_type
                    }));
                  }
                }}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="workspace-file-name">File name</label>
              <input id="workspace-file-name" name="file_name" className="text-input" value={attachmentForm.file_name} onChange={(event) => setAttachmentForm((current) => ({ ...current, file_name: event.target.value }))} required />
            </div>
            <div className="field">
              <label htmlFor="workspace-content-type">Content type</label>
              <input id="workspace-content-type" name="content_type" className="text-input" value={attachmentForm.content_type} onChange={(event) => setAttachmentForm((current) => ({ ...current, content_type: event.target.value }))} required />
            </div>
            <div className="field field-full">
              <label>Size</label>
              <input className="text-input" value={selectedFile ? `${selectedFile.size} bytes` : "No file selected"} disabled />
            </div>
          </div>
          <button type="submit" className="btn btn-secondary" disabled={pending === "attachment"}>
            {pending === "attachment" ? "Saving..." : "Upload"}
          </button>
        </form>

        <section className="panel">
          <h3 className="section-heading">Attachments</h3>
          {!attachments.length ? <p className="muted">No attachments found for this task.</p> : null}
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
                    <p className="data-meta">Uploaded</p>
                    <strong>{formatDate(attachment.created_at)}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
      ) : null}

      {activeSection === "activity" ? (
      <section className="panel">
        <h3 className="section-heading">Recent activity</h3>
        {!activity.length ? <p className="muted">No actions yet in this session.</p> : null}
        <div className="data-list">
          {activity.map((entry) => (
            <article key={entry.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>{entry.type}</h3>
                  <p className="data-meta">{formatDate(entry.at)}</p>
                </div>
              </div>
              {entry.payload && typeof entry.payload === "object" ? (
                <div className="list-row">
                  {Object.entries(entry.payload)
                    .filter(([, v]) => v !== null && v !== undefined && v !== "")
                    .slice(0, 6)
                    .map(([key, value]) => (
                      <div key={key}>
                        <p className="data-meta">{key.replace(/_/g, " ")}</p>
                        <strong>
                          {typeof value === "object"
                            ? JSON.stringify(value)
                            : String(value).length > 60
                            ? String(value).slice(0, 60) + "…"
                            : String(value)}
                        </strong>
                      </div>
                    ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </section>
      ) : null}
    </section>
  );
}