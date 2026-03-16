import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createComment, deleteComment, listProjects, listTaskComments, listTasks, updateComment } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate } from "../utils/format.js";
import { getCommentOptionLabel, getPersonLabel, getTaskOptionLabel } from "../utils/display.js";
import { isNonEmpty } from "../utils/validation.js";

const initialCreateForm = {
  body: "",
  parentCommentId: ""
};

export default function CommentsPage() {
  const { accessToken, isAuthenticated, organizationId, user } = useSession();
  const { pushToast } = useNotifications();
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [comments, setComments] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [createForm, setCreateForm] = useState(initialCreateForm);
  const [editingCommentId, setEditingCommentId] = useState("");
  const [editingBody, setEditingBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const [activeSection, setActiveSection] = useState("compose");

  const projectNameById = useMemo(() => new Map(projects.map((project) => [project.id, project.name])), [projects]);
  const selectedTask = useMemo(() => tasks.find((task) => task.id === selectedTaskId) || null, [tasks, selectedTaskId]);

  useEffect(() => {
    async function loadContext() {
      if (!isAuthenticated || !organizationId) {
        return;
      }

      setLoading(true);
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
        setError(requestError.message || "Unable to load discussion context.");
      } finally {
        setLoading(false);
      }
    }

    loadContext();
  }, [accessToken, isAuthenticated, organizationId]);

  useEffect(() => {
    async function loadComments() {
      if (!selectedTaskId || !organizationId || !isAuthenticated) {
        setComments([]);
        return;
      }

      setCommentsLoading(true);
      setError("");

      try {
        const response = await listTaskComments(accessToken, organizationId, selectedTaskId, {
          limit: 100,
          page: 1,
          order: "desc"
        });
        setComments(response?.data?.items || []);
      } catch (requestError) {
        setError(requestError.message || "Unable to load comments.");
      } finally {
        setCommentsLoading(false);
      }
    }

    loadComments();
  }, [accessToken, isAuthenticated, organizationId, selectedTaskId]);

  async function handleCreate(event) {
    event.preventDefault();

    if (!selectedTaskId) {
      setError("Choose a task first.");
      return;
    }

    if (!isNonEmpty(createForm.body, 1)) {
      setError("Comment body is required.");
      return;
    }

    setError("");
    setPending("create");

    try {
      await createComment(accessToken, organizationId, selectedTaskId, {
        body: createForm.body,
        parent_comment_id: createForm.parentCommentId || undefined
      });
      setCreateForm(initialCreateForm);
      pushToast("Comment created.", "success");
      const response = await listTaskComments(accessToken, organizationId, selectedTaskId, { limit: 100, page: 1, order: "desc" });
      setComments(response?.data?.items || []);
    } catch (requestError) {
      setError(requestError.message || "Unable to create comment.");
      pushToast("Comment create failed.", "error");
    } finally {
      setPending("");
    }
  }

  function startEditing(comment) {
    setEditingCommentId(comment.id);
    setEditingBody(comment.body || "");
  }

  async function handleUpdate(commentId) {
    if (!isNonEmpty(editingBody, 1)) {
      setError("Updated comment body is required.");
      return;
    }

    setError("");
    setPending(`update:${commentId}`);

    try {
      const response = await updateComment(accessToken, organizationId, commentId, {
        body: editingBody
      });
      const updated = response?.data;
      setComments((current) => current.map((comment) => (comment.id === commentId ? { ...comment, ...updated } : comment)));
      setEditingCommentId("");
      setEditingBody("");
      pushToast("Comment updated.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to update comment.");
      pushToast("Comment update failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleDelete(commentId) {
    setError("");
    setPending(`delete:${commentId}`);

    try {
      await deleteComment(accessToken, organizationId, commentId);
      setComments((current) => current.filter((comment) => comment.id !== commentId));
      pushToast("Comment deleted.", "warning");
    } catch (requestError) {
      setError(requestError.message || "Unable to delete comment.");
      pushToast("Comment delete failed.", "error");
    } finally {
      setPending("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to work with comments"
          description="Sign in to add discussion, edit updates, and keep decisions documented on tasks."
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
          description="Choose a workspace before posting or managing comments."
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
        eyebrow="Comments"
        title="Team discussion"
        description="Keep discussion short, clear, and linked to tasks."
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Discussion mode</p>
          <h3 className="section-heading">Open one section at a time</h3>
          <p className="helper-text">Compose, review, and task context in focused mode.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Discussion sections">
            <button type="button" className={`tasks-view-button${activeSection === "compose" ? " active" : ""}`} onClick={() => setActiveSection("compose")}>Compose</button>
            <button type="button" className={`tasks-view-button${activeSection === "discussion" ? " active" : ""}`} onClick={() => setActiveSection("discussion")}>Discussion</button>
            <button type="button" className={`tasks-view-button${activeSection === "context" ? " active" : ""}`} onClick={() => setActiveSection("context")}>Context</button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Tasks</p>
            <strong>{tasks.length}</strong>
          </div>
          <div>
            <p className="data-meta">Comments</p>
            <strong>{comments.length}</strong>
          </div>
          <div>
            <p className="data-meta">Selected</p>
            <strong>{selectedTaskId ? "Task linked" : "No task"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection}</strong>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      {activeSection === "compose" ? (
      <section className="split-grid comments-layout-grid">
        <form className="panel form-shell comment-create-form" onSubmit={handleCreate}>
          <h3 className="section-heading">Start a comment</h3>
          <div className="field">
            <label htmlFor="comment-task-select">Task</label>
            <select id="comment-task-select" className="select-input" value={selectedTaskId} onChange={(event) => setSelectedTaskId(event.target.value)} required>
              <option value="">Choose task</option>
              {tasks.map((task) => (
                <option key={task.id} value={task.id}>
                  {getTaskOptionLabel(task, projectNameById)}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="comment-parent-select">Reply to (optional)</label>
            <select
              id="comment-parent-select"
              className="select-input"
              value={createForm.parentCommentId}
              onChange={(event) => setCreateForm((current) => ({ ...current, parentCommentId: event.target.value }))}
            >
              <option value="">Start a fresh thread</option>
              {comments.map((comment) => (
                <option key={comment.id} value={comment.id}>
                  {getCommentOptionLabel(comment, user?.id)}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="comment-body">Comment</label>
            <textarea
              id="comment-body"
              className="textarea-input"
              value={createForm.body}
              onChange={(event) => setCreateForm((current) => ({ ...current, body: event.target.value }))}
              required
            />
          </div>
          <div className="toolbar-actions comment-actions">
            <button type="submit" className="btn btn-primary" disabled={pending === "create" || !selectedTaskId}>
              {pending === "create" ? "Posting..." : "Post comment"}
            </button>
            {selectedTaskId ? (
              <Link to={`/tasks/${selectedTaskId}`} className="btn btn-secondary">
                Open task workspace
              </Link>
            ) : null}
          </div>
        </form>

        <section className="panel">
          <h3 className="section-heading">Quick context</h3>
          <div className="list-row">
            <div>
              <p className="data-meta">Current task</p>
              <strong>{selectedTask ? getTaskOptionLabel(selectedTask, projectNameById) : "Choose task"}</strong>
            </div>
            <div>
              <p className="data-meta">Threads</p>
              <strong>{comments.filter((comment) => !comment.parent_comment_id).length}</strong>
            </div>
            <div>
              <p className="data-meta">Replies</p>
              <strong>{comments.filter((comment) => !!comment.parent_comment_id).length}</strong>
            </div>
          </div>
          <p className="helper-text">Use the Discussion tab to manage and edit full conversation history.</p>
          {selectedTaskId ? (
            <Link to={`/tasks/${selectedTaskId}`} className="btn btn-secondary">
              Open task workspace
            </Link>
          ) : null}
        </section>
      </section>
      ) : null}

      {activeSection === "discussion" ? (
      <section className="panel">
        <h3 className="section-heading">Discussion feed</h3>
        {loading || commentsLoading ? <LoadingGrid cards={2} /> : null}
        {!loading && !commentsLoading && !comments.length ? <p className="muted">No comments yet for this task.</p> : null}
        <div className="data-list">
          {comments.map((comment) => {
            const isEditing = editingCommentId === comment.id;
            const authorLabel = getPersonLabel({
              id: comment.author_user_id,
              name: comment.author_user_name,
              email: comment.author_user_email,
              currentUserId: user?.id
            });

            return (
              <article key={comment.id} className="data-card">
                <div className="data-card-header">
                  <div>
                    <h3>{authorLabel}</h3>
                    <p>{comment.author_user_email || "No email available"}</p>
                  </div>
                  <StatusPill value={comment.is_edited ? "edited" : "posted"} />
                </div>
                <div className="list-row">
                  <div>
                    <p className="data-meta">Posted</p>
                    <strong>{formatDate(comment.created_at)}</strong>
                  </div>
                  <div>
                    <p className="data-meta">Reply</p>
                    <strong>{comment.parent_comment_id ? "Thread reply" : "Root comment"}</strong>
                  </div>
                  <div>
                    <p className="data-meta">Updated</p>
                    <strong>{formatDate(comment.updated_at)}</strong>
                  </div>
                </div>
                {isEditing ? (
                  <div className="field">
                    <label htmlFor={`edit-comment-${comment.id}`}>Edit comment</label>
                    <textarea id={`edit-comment-${comment.id}`} className="textarea-input" value={editingBody} onChange={(event) => setEditingBody(event.target.value)} />
                  </div>
                ) : (
                  <p>{comment.body}</p>
                )}
                <div className="toolbar-actions">
                  {isEditing ? (
                    <>
                      <button type="button" className="btn btn-primary" disabled={pending === `update:${comment.id}`} onClick={() => handleUpdate(comment.id)}>
                        {pending === `update:${comment.id}` ? "Saving..." : "Save"}
                      </button>
                      <button type="button" className="btn btn-secondary" onClick={() => { setEditingCommentId(""); setEditingBody(""); }}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button type="button" className="btn btn-secondary" onClick={() => startEditing(comment)}>
                      Edit
                    </button>
                  )}
                  <button type="button" className="btn btn-secondary" disabled={pending === `delete:${comment.id}`} onClick={() => handleDelete(comment.id)}>
                    {pending === `delete:${comment.id}` ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </section>
      ) : null}

      {activeSection === "context" ? (
      <section className="panel">
        <h3 className="section-heading">Discussion context</h3>
        <div className="list-row">
          <div>
            <p className="data-meta">Projects loaded</p>
            <strong>{projects.length}</strong>
          </div>
          <div>
            <p className="data-meta">Tasks loaded</p>
            <strong>{tasks.length}</strong>
          </div>
          <div>
            <p className="data-meta">Current task comments</p>
            <strong>{comments.length}</strong>
          </div>
        </div>
        <div className="field">
          <label htmlFor="comment-task-context-select">Switch task</label>
          <select id="comment-task-context-select" className="select-input" value={selectedTaskId} onChange={(event) => setSelectedTaskId(event.target.value)} required>
            <option value="">Choose task</option>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>
                {getTaskOptionLabel(task, projectNameById)}
              </option>
            ))}
          </select>
        </div>
      </section>
      ) : null}
    </section>
  );
}