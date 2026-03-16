import { formatId } from "./format.js";

export function getPersonLabel({ id, name, email, currentUserId, ownLabel = "Own" }) {
  if (!id && !name && !email) {
    return "Unknown";
  }

  if (id && currentUserId && id === currentUserId) {
    return ownLabel;
  }

  return name || email || formatId(id);
}

export function getMemberOptionLabel({ id, name, email, roleName }) {
  const primary = name || email || formatId(id);
  return roleName ? `${primary} · ${roleName}` : primary;
}

export function getTaskOptionLabel(task, projectNameById = new Map()) {
  if (!task) {
    return "Select task";
  }

  const projectName = projectNameById.get(task.project_id);
  return projectName ? `${task.title} · ${projectName}` : task.title;
}

export function getCommentOptionLabel(comment, currentUserId) {
  const author = getPersonLabel({
    id: comment.author_user_id,
    name: comment.author_user_name,
    email: comment.author_user_email,
    currentUserId,
    ownLabel: "Your comment"
  });
  const preview = String(comment.body || "").slice(0, 42).trim();
  return preview ? `${author} · ${preview}` : author;
}