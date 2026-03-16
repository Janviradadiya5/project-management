const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
let refreshHandler = null;
let authStateAccessor = null;
let authFailureHandler = null;

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function setAuthRefreshHandler(handler) {
  refreshHandler = handler;
}

export function setAuthStateAccessor(accessor) {
  authStateAccessor = accessor;
}

export function setAuthFailureHandler(handler) {
  authFailureHandler = handler;
}

function buildUrl(path, query) {
  const url = new URL(path, `${BASE_URL}/`);

  Object.entries(query || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  return url;
}

async function parseResponse(response) {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

function getErrorMessage(payload, fallback) {
  const baseMessage = payload?.message || payload?.detail || fallback;
  const details = payload?.details;

  if (details && typeof details === "object") {
    const firstEntry = Object.entries(details).find(([, value]) => {
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return Boolean(value);
    });

    if (firstEntry) {
      const [field, value] = firstEntry;
      const detailMessage = Array.isArray(value) ? value[0] : value;
      if (typeof detailMessage === "string" && detailMessage.trim()) {
        return `${baseMessage} (${field}: ${detailMessage})`;
      }
    }
  }

  return baseMessage;
}

export async function apiRequest(path, options = {}) {
  const {
    method = "GET",
    token,
    refreshToken,
    organizationId,
    body,
    formData,
    query,
    signal,
    retryOnAuthFail = true
  } = options;

  const authState = typeof authStateAccessor === "function" ? authStateAccessor() : null;
  const resolvedToken = token || authState?.accessToken;
  const resolvedRefreshToken = refreshToken || authState?.refreshToken;

  const headers = {
    Accept: "application/json"
  };

  if (body !== undefined && !formData) {
    headers["Content-Type"] = "application/json";
  }

  if (resolvedToken) {
    headers.Authorization = `Bearer ${resolvedToken}`;
  }

  if (organizationId) {
    headers["X-Organization-ID"] = organizationId;
  }

  const url = buildUrl(path, query);

  const response = await fetch(url, {
    method,
    headers,
    body: formData || (body !== undefined ? JSON.stringify(body) : undefined),
    signal
  });

  const payload = await parseResponse(response);

  if (
    response.status === 401
    && retryOnAuthFail
    && resolvedToken
    && resolvedRefreshToken
    && typeof refreshHandler === "function"
  ) {
    try {
      const updatedTokens = await refreshHandler({
        accessToken: resolvedToken,
        refreshToken: resolvedRefreshToken
      });

      if (updatedTokens?.accessToken && updatedTokens?.refreshToken) {
        return apiRequest(path, {
          method,
          token: updatedTokens.accessToken,
          refreshToken: updatedTokens.refreshToken,
          organizationId,
          body,
          formData,
          query,
          signal,
          retryOnAuthFail: false
        });
      }
    } catch {
      if (typeof authFailureHandler === "function") {
        authFailureHandler();
      }
      // Fall through and throw the original 401 error.
    }
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload, `Request failed with status ${response.status}`),
      response.status,
      payload
    );
  }

  return payload;
}

export async function pingApiHealth() {
  const endpoints = ["/health/", "/api/health/"];

  for (const endpoint of endpoints) {
    try {
      const response = await fetch(buildUrl(endpoint));
      if (response.ok) {
        return {
          ok: true,
          endpoint,
          status: response.status
        };
      }
    } catch {
      // Try next endpoint.
    }
  }

  return {
    ok: false,
    endpoint: "unreachable",
    status: 0
  };
}

export function getHealth() {
  return apiRequest("/health/", {
    retryOnAuthFail: false
  });
}

export function loginUser(credentials) {
  return apiRequest("/api/v1/auth/login", {
    method: "POST",
    body: credentials
  });
}

export function registerUser(payload) {
  return apiRequest("/api/v1/auth/register", {
    method: "POST",
    body: payload,
    retryOnAuthFail: false
  });
}

export function requestEmailVerification(payload) {
  return apiRequest("/api/v1/auth/email-verification/request", {
    method: "POST",
    body: payload,
    retryOnAuthFail: false
  });
}

export function confirmEmailVerification(payload) {
  return apiRequest("/api/v1/auth/verify-email", {
    method: "POST",
    body: payload,
    retryOnAuthFail: false
  });
}

export function requestPasswordReset(payload) {
  return apiRequest("/api/v1/auth/password-reset/request", {
    method: "POST",
    body: payload,
    retryOnAuthFail: false
  });
}

export function confirmPasswordReset(payload) {
  return apiRequest("/api/v1/auth/password-reset/confirm", {
    method: "POST",
    body: payload,
    retryOnAuthFail: false
  });
}

export function refreshAuthTokens(accessToken, refreshToken) {
  return apiRequest("/api/v1/auth/token/refresh", {
    method: "POST",
    token: accessToken,
    body: {
      refresh_token: refreshToken
    },
    retryOnAuthFail: false
  });
}

export function logoutUser(accessToken, refreshToken) {
  return apiRequest("/api/v1/auth/logout", {
    method: "POST",
    token: accessToken,
    body: {
      refresh_token: refreshToken
    },
    retryOnAuthFail: false
  });
}

export function getProfile(token) {
  return apiRequest("/api/v1/users/me", { token });
}

export function updateProfile(token, body) {
  return apiRequest("/api/v1/users/me/update", {
    method: "PATCH",
    token,
    body
  });
}

export function replaceProfile(token, body) {
  return apiRequest("/api/v1/users/me/update", {
    method: "PUT",
    token,
    body
  });
}

export function acceptOrganizationInvite(token, body) {
  return apiRequest("/api/v1/invites/accept", {
    method: "POST",
    token,
    body
  });
}

export function listOrganizations(token, query) {
  return apiRequest("/api/v1/organizations/", { token, query });
}

export function createOrganization(token, body) {
  return apiRequest("/api/v1/organizations/", {
    method: "POST",
    token,
    body
  });
}

export function getOrganization(token, organizationId) {
  return apiRequest(`/api/v1/organizations/${organizationId}`, {
    token
  });
}

export function updateOrganization(token, organizationId, body) {
  return apiRequest(`/api/v1/organizations/${organizationId}`, {
    method: "PATCH",
    token,
    body
  });
}

export function replaceOrganization(token, organizationId, body) {
  return apiRequest(`/api/v1/organizations/${organizationId}`, {
    method: "PUT",
    token,
    body
  });
}

export function deleteOrganization(token, organizationId) {
  return apiRequest(`/api/v1/organizations/${organizationId}`, {
    method: "DELETE",
    token
  });
}

export function listOrganizationMembers(token, organizationId, query) {
  return apiRequest(`/api/v1/organizations/${organizationId}/members`, {
    token,
    query
  });
}

export function updateOrganizationMember(token, organizationId, userId, body) {
  return apiRequest(`/api/v1/organizations/${organizationId}/members/${userId}`, {
    method: "PATCH",
    token,
    body
  });
}

export function removeOrganizationMember(token, organizationId, userId) {
  return apiRequest(`/api/v1/organizations/${organizationId}/members/${userId}`, {
    method: "DELETE",
    token
  });
}

export function listOrganizationInvites(token, organizationId, query) {
  return apiRequest(`/api/v1/organizations/${organizationId}/invites`, {
    token,
    query
  });
}

export function inviteOrganizationMember(token, organizationId, body) {
  return apiRequest(`/api/v1/organizations/${organizationId}/invites`, {
    method: "POST",
    token,
    body
  });
}

export function revokeOrganizationInvite(token, organizationId, inviteId) {
  return apiRequest(`/api/v1/organizations/${organizationId}/invites/${inviteId}`, {
    method: "DELETE",
    token
  });
}

export function listProjects(token, organizationId, query) {
  return apiRequest("/api/v1/projects/", {
    token,
    organizationId,
    query
  });
}

export function getProject(token, organizationId, projectId, query) {
  return apiRequest(`/api/v1/projects/${projectId}`, {
    token,
    organizationId,
    query
  });
}

export function createProject(token, organizationId, body) {
  return apiRequest("/api/v1/projects/", {
    method: "POST",
    token,
    organizationId,
    body
  });
}

export function updateProject(token, organizationId, projectId, body) {
  return apiRequest(`/api/v1/projects/${projectId}`, {
    method: "PATCH",
    token,
    organizationId,
    body
  });
}

export function archiveProject(token, organizationId, projectId) {
  return apiRequest(`/api/v1/projects/${projectId}`, {
    method: "DELETE",
    token,
    organizationId
  });
}

export function addProjectMember(token, organizationId, projectId, body) {
  return apiRequest(`/api/v1/projects/${projectId}/members`, {
    method: "POST",
    token,
    organizationId,
    body
  });
}

export function listProjectMembers(token, organizationId, projectId, query) {
  return apiRequest(`/api/v1/projects/${projectId}/members`, {
    token,
    organizationId,
    query
  });
}

export function removeProjectMember(token, organizationId, projectId, projectMemberId) {
  return apiRequest(`/api/v1/projects/${projectId}/members/${projectMemberId}`, {
    method: "DELETE",
    token,
    organizationId
  });
}

export function listTasks(token, organizationId, query) {
  return apiRequest("/api/v1/tasks/", {
    token,
    organizationId,
    query
  });
}

export function getTask(token, organizationId, taskId, query) {
  return apiRequest(`/api/v1/tasks/${taskId}`, {
    token,
    organizationId,
    query
  });
}

export function createTask(token, organizationId, body) {
  return apiRequest("/api/v1/tasks/", {
    method: "POST",
    token,
    organizationId,
    body
  });
}

export function updateTask(token, organizationId, taskId, body) {
  return apiRequest(`/api/v1/tasks/${taskId}`, {
    method: "PATCH",
    token,
    organizationId,
    body
  });
}

export function deleteTask(token, organizationId, taskId) {
  return apiRequest(`/api/v1/tasks/${taskId}`, {
    method: "DELETE",
    token,
    organizationId
  });
}

export function createComment(token, organizationId, taskId, body) {
  return apiRequest(`/api/v1/tasks/${taskId}/comments`, {
    method: "POST",
    token,
    organizationId,
    body
  });
}

export function listTaskComments(token, organizationId, taskId, query) {
  return apiRequest(`/api/v1/tasks/${taskId}/comments`, {
    token,
    organizationId,
    query
  });
}

export function updateComment(token, organizationId, commentId, body) {
  return apiRequest(`/api/v1/comments/${commentId}`, {
    method: "PATCH",
    token,
    organizationId,
    body
  });
}

export function deleteComment(token, organizationId, commentId) {
  return apiRequest(`/api/v1/comments/${commentId}`, {
    method: "DELETE",
    token,
    organizationId
  });
}

export function listAttachments(token, organizationId, taskId, query) {
  return apiRequest(`/api/v1/tasks/${taskId}/attachments`, {
    token,
    organizationId,
    query
  });
}

export function uploadAttachment(token, organizationId, taskId, payload) {
  return apiRequest(`/api/v1/tasks/${taskId}/attachments`, {
    method: "POST",
    token,
    organizationId,
    formData: payload instanceof FormData ? payload : undefined,
    body: payload instanceof FormData ? undefined : payload
  });
}

export function deleteAttachment(token, organizationId, attachmentId) {
  return apiRequest(`/api/v1/attachments/${attachmentId}`, {
    method: "DELETE",
    token,
    organizationId
  });
}

export function listNotifications(token, organizationId, query) {
  return apiRequest("/api/v1/notifications/", {
    token,
    organizationId,
    query
  });
}

export function markNotificationRead(token, organizationId, notificationId) {
  return apiRequest(`/api/v1/notifications/${notificationId}/read`, {
    method: "PATCH",
    token,
    organizationId,
    body: {
      is_read: true
    }
  });
}

export function listActivityLogs(token, organizationId, query) {
  return apiRequest("/api/v1/activity-logs/", {
    token,
    organizationId,
    query
  });
}
