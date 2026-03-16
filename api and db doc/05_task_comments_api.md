================================================================
TASK & COMMENT APIs
================================================================

+------------------------+--------------------------------------------------------------+
| Item                   | Value                                                        |
+------------------------+--------------------------------------------------------------+
| Module                 | Task & Comment                                               |
| Base URL               | https://api.example.com/v1                                   |
| Content-Type           | application/json                                             |
| Authentication         | Authorization: Bearer <JWT> (OIDC/Auth0)                     |
| Permission / Scopes    | Task read: super_admin, organization_admin, project_manager, |
|                        | team_member, viewer.                                         |
|                        | Task write: super_admin, organization_admin, project_manager,|
|                        | team_member (policy-limited).                                |
|                        | Comment write: super_admin, organization_admin,              |
|                        | project_manager, team_member.                                |
|                        | Scopes: tasks:read, tasks:write, tasks:admin,               |
|                        |         comments:read, comments:write, comments:admin        |
| Timestamps             | ISO-8601 UTC (e.g., 2026-03-13T06:30:00Z)                    |
| IDs                    | UUID v4                                                      |
| Notes                  | Task title length 3-300.                                     |
|                        | Task priority enum: low, medium, high.                       |
|                        | Task status enum: todo, in_progress, done.                   |
|                        | due_at must be >= task creation time.                        |
|                        | assignee_user_id must be active member in project/org.       |
|                        | team_member can update only self-assigned tasks unless       |
|                        | elevated role policy exists.                                 |
|                        | Comment body length 1-5000.                                  |
|                        | parent_comment_id must reference comment in same task.       |
|                        | Comment delete is soft delete via deleted_at.                |
+------------------------+--------------------------------------------------------------+

Authentication: Auth0 JWT - Bearer <Token>
Permission:     Based on task/comment role rules and scopes

---------------------------------------------------------------
Endpoint 1: GET /v1/tasks - List Tasks
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer
  - Scopes: tasks:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | N/A          | N/A      | N/A      | N/A               | N/A                          |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | Name            | Type     | Default    | Description                             | Allowed                   |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | page            | integer  | 1          | Page number                             | >= 1                      |
  | limit           | integer  | 20         | Records per page                        | 1-100                     |
  | search          | string   | null       | Search by task title                    | -                         |
  | sort_by         | string   | created_at | Field to sort by                        | title, priority, status,  |
  |                 |          |            |                                         | due_at, created_at        |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | project_id      | string   | null       | Filter by project                       | UUID v4                   |
  | status          | string   | null       | Filter by task status                   | todo, in_progress, done   |
  | priority        | string   | null       | Filter by task priority                 | low, medium, high         |
  | assignee_user_id| string   | null       | Filter by assignee                      | UUID v4                   |
  | fields          | string   | all        | Comma-separated field projection        | id, title, status,        |
  |                 |          |            |                                         | priority, due_at          |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "items": [
      {
        "id":                 "t1b2c3d4-...",
        "project_id":         "p1b2c3d4-...",
        "title":              "Finalize API specification",
        "description":        "Complete and review API contract",
        "priority":           "high",
        "status":             "in_progress",
        "due_at":             "2026-03-20T18:00:00Z",
        "assignee_user_id":   "u1b2c3d4-...",
        "created_by_user_id": "pm-uuid",
        "created_at":         "2026-03-13T08:00:00Z",
        "updated_at":         "2026-03-13T10:00:00Z",
        "completed_at":       null,
        "created_by":         "pm-uuid",
        "updated_by":         "u1b2c3d4-..."
      }
    ],
    "pagination": {
      "page":        1,
      "limit":       20,
      "total_items": 1,
      "total_pages": 1,
      "has_next":    false,
      "has_prev":    false
    }
  },
  "message": "Tasks retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query/header fields are invalid      |
  |  2  | TASK_STATUS_INVALID              | 400  | Invalid task status filter                       |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  4  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "TASK_STATUS_INVALID",
    "details": {
      "status": "blocked"
    },
    "message": "Task status must be one of: todo, in_progress, done."
  }

---------------------------------------------------------------
Endpoint 2: POST /v1/tasks - Create Task
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member
  - Scopes: tasks:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | N/A          | N/A      | N/A      | N/A               | N/A                          |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | N/A             | N/A      | N/A      | N/A                                     | N/A                  |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "project_id":       "string",    // -> UUID of parent project (required)
  "title":            "string",    // -> Task title, length 3-300 (required)
  "description":      "string",    // -> Task description (optional)
  "priority":         "string",    // -> low, medium, high (required)
  "status":           "string",    // -> todo, in_progress, done (required)
  "due_at":           "string",    // -> ISO-8601 datetime >= current time (optional)
  "assignee_user_id": "string"     // -> Assigned user UUID, must be project member (optional)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":                 "t1b2c3d4-...",
    "project_id":         "p1b2c3d4-...",
    "title":              "Finalize API specification",
    "description":        "Complete and review API contract",
    "priority":           "high",
    "status":             "todo",
    "due_at":             "2026-03-20T18:00:00Z",
    "assignee_user_id":   "u1b2c3d4-...",
    "created_by_user_id": "pm-uuid",
    "created_at":         "2026-03-13T12:30:00Z",
    "updated_at":         "2026-03-13T12:30:00Z",
    "completed_at":       null,
    "created_by":         "pm-uuid",
    "updated_by":         "pm-uuid"
  },
  "message": "Task created successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more payload/header fields are invalid    |
  |  2  | TASK_STATUS_INVALID              | 400  | Task status must be todo/in_progress/done        |
  |  3  | TASK_ASSIGNEE_NOT_MEMBER         | 400  | Assignee must be active project/org member       |
  |  4  | PROJECT_DEADLINE_INVALID         | 400  | due_at must be greater than task creation time   |
  |  5  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  7  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to create task          |
  |  8  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization or project not found                |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "TASK_ASSIGNEE_NOT_MEMBER",
    "details": {
      "assignee_user_id": "u1b2c3d4-...",
      "project_id": "p1b2c3d4-..."
    },
    "message": "The selected assignee is not an active member of this project."
  }

---------------------------------------------------------------
Endpoint 3: GET /v1/tasks/:id - Get Task by ID
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer
  - Scopes: tasks:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Task unique ID               |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | fields          | string   | all      | Comma-separated field projection        | id, project_id,      |
  |                 |          |          |                                         | title, status,       |
  |                 |          |          |                                         | priority, due_at     |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                 "t1b2c3d4-...",
    "project_id":         "p1b2c3d4-...",
    "title":              "Finalize API specification",
    "description":        "Complete and review API contract",
    "priority":           "high",
    "status":             "in_progress",
    "due_at":             "2026-03-20T18:00:00Z",
    "assignee_user_id":   "u1b2c3d4-...",
    "created_by_user_id": "pm-uuid",
    "created_at":         "2026-03-13T12:30:00Z",
    "updated_at":         "2026-03-13T13:00:00Z",
    "completed_at":       null,
    "created_by":         "pm-uuid",
    "updated_by":         "u1b2c3d4-..."
  },
  "message": "Task retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Path/header/query validation failed              |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this task              |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | TASK_UPDATE_FORBIDDEN            | 403  | Role policy denied task access                   |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "task_id": "t1b2c3d4-..."
    },
    "message": "You do not have permission to access this task."
  }

---------------------------------------------------------------
Endpoint 4: PATCH /v1/tasks/:id - Update Task
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member (self-assigned tasks unless elevated policy)
  - Scopes: tasks:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Task unique ID               |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | N/A             | N/A      | N/A      | N/A                                     | N/A                  |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "title":            "string",    // -> Task title, length 3-300 (optional)
  "description":      "string",    // -> Task description (optional)
  "priority":         "string",    // -> low, medium, high (optional)
  "status":           "string",    // -> todo, in_progress, done (optional)
  "due_at":           "string",    // -> ISO-8601 datetime >= task creation time (optional)
  "assignee_user_id": "string"     // -> New assignee UUID, must be project member (optional)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                 "t1b2c3d4-...",
    "project_id":         "p1b2c3d4-...",
    "title":              "Finalize API specification v2",
    "description":        "Finalize sections and complete peer review",
    "priority":           "high",
    "status":             "done",
    "due_at":             "2026-03-20T18:00:00Z",
    "assignee_user_id":   "u1b2c3d4-...",
    "created_by_user_id": "pm-uuid",
    "created_at":         "2026-03-13T12:30:00Z",
    "updated_at":         "2026-03-13T14:00:00Z",
    "completed_at":       "2026-03-13T14:00:00Z",
    "created_by":         "pm-uuid",
    "updated_by":         "u1b2c3d4-..."
  },
  "message": "Task updated successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more payload/header fields are invalid    |
  |  2  | TASK_STATUS_INVALID              | 400  | Task status must be todo/in_progress/done        |
  |  3  | TASK_ASSIGNEE_NOT_MEMBER         | 400  | Assignee must be active project/org member       |
  |  4  | TASK_UPDATE_FORBIDDEN            | 403  | Team member cannot update unassigned task        |
  |  5  | PROJECT_DEADLINE_INVALID         | 400  | due_at must be greater than task creation time   |
  |  6  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  7  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to update task          |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "TASK_UPDATE_FORBIDDEN",
    "details": {
      "task_id": "t1b2c3d4-...",
      "assignee_user_id": "u9x8y7z6-..."
    },
    "message": "Team members may only update tasks assigned to themselves."
  }

---------------------------------------------------------------
Endpoint 5: DELETE /v1/tasks/:id - Soft Delete Task
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager
  - Scopes: tasks:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Task unique ID               |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | N/A             | N/A      | N/A      | N/A                                     | N/A                  |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                 "t1b2c3d4-...",
    "project_id":         "p1b2c3d4-...",
    "title":              "Finalize API specification v2",
    "status":             "done",
    "deleted_at":         "2026-03-13T14:30:00Z",
    "updated_at":         "2026-03-13T14:30:00Z",
    "updated_by":         "pm-uuid",
    "created_at":         "2026-03-13T12:30:00Z",
    "created_by":         "pm-uuid"
  },
  "message": "Task soft-deleted successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided path/header fields are invalid          |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to delete task          |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/task not found or deleted           |
  |  7  | TASK_UPDATE_FORBIDDEN            | 403  | Task delete denied by role policy                |
  |  8  | RESOURCE_CONFLICT                | 409  | Task already deleted or state conflict           |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "task_id": "t1b2c3d4-...",
      "current_state": "deleted"
    },
    "message": "This task has already been deleted."
  }

---------------------------------------------------------------
Endpoint 6: POST /v1/tasks/:task_id/comments - Create Comment or Reply
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member
  - Scopes: comments:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | task_id       | string   | Yes      | UUID v4          | Task unique ID               |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | N/A             | N/A      | N/A      | N/A                                     | N/A                  |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "body":              "string",    // -> Comment body, length 1-5000 (required)
  "parent_comment_id": "string"     // -> UUID of parent comment for replies (optional)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":                "c1b2c3d4-...",
    "task_id":           "t1b2c3d4-...",
    "author_user_id":    "u1b2c3d4-...",
    "parent_comment_id": null,
    "body":              "I have completed the first draft.",
    "is_edited":         false,
    "deleted_at":        null,
    "created_at":        "2026-03-13T15:00:00Z",
    "updated_at":        "2026-03-13T15:00:00Z",
    "created_by":        "u1b2c3d4-...",
    "updated_by":        "u1b2c3d4-..."
  },
  "message": "Comment created successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Input payload/header validation failed           |
  |  2  | COMMENT_PARENT_MISMATCH          | 400  | parent_comment_id must belong to same task       |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  4  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have permission to comment            |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/task not found or deleted           |
  |  7  | TASK_UPDATE_FORBIDDEN            | 403  | Role policy denied this comment action           |
  |  8  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "COMMENT_PARENT_MISMATCH",
    "details": {
      "task_id": "t1b2c3d4-...",
      "parent_comment_id": "c9x8y7z6-..."
    },
    "message": "The parent comment must belong to the same task."
  }

---------------------------------------------------------------
Endpoint 7: PATCH /v1/comments/:id - Update Comment
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member (author or elevated policy)
  - Scopes: comments:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Comment unique ID            |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | N/A             | N/A      | N/A      | N/A                                     | N/A                  |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "body": "string"    // -> Updated comment body, length 1-5000 (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                "c1b2c3d4-...",
    "task_id":           "t1b2c3d4-...",
    "author_user_id":    "u1b2c3d4-...",
    "parent_comment_id": null,
    "body":              "I have completed the first draft and validated examples.",
    "is_edited":         true,
    "deleted_at":        null,
    "created_at":        "2026-03-13T15:00:00Z",
    "updated_at":        "2026-03-13T15:30:00Z",
    "created_by":        "u1b2c3d4-...",
    "updated_by":        "u1b2c3d4-..."
  },
  "message": "Comment updated successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Input payload/header validation failed           |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ORG_ACCESS_DENIED                | 403  | You do not have permission to update comment     |
  |  5  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/comment not found or deleted        |
  |  6  | TASK_UPDATE_FORBIDDEN            | 403  | Role policy denied this comment update           |
  |  7  | COMMENT_PARENT_MISMATCH          | 400  | Comment relationship validation failed           |
  |  8  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "TASK_UPDATE_FORBIDDEN",
    "details": {
      "comment_id": "c1b2c3d4-...",
      "actor_user_id": "u9x8y7z6-..."
    },
    "message": "You are not allowed to edit this comment."
  }

---------------------------------------------------------------
Endpoint 8: DELETE /v1/comments/:id - Soft Delete Comment
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member (author or elevated policy)
  - Scopes: comments:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Comment unique ID            |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | N/A             | N/A      | N/A      | N/A                                     | N/A                  |
  +-----------------+----------+----------+-----------------------------------------+----------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  | X-Organization-ID        | string   | Yes      | UUID v4                  | Organization context             |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                "c1b2c3d4-...",
    "task_id":           "t1b2c3d4-...",
    "author_user_id":    "u1b2c3d4-...",
    "deleted_at":        "2026-03-13T16:00:00Z",
    "updated_at":        "2026-03-13T16:00:00Z",
    "updated_by":        "u1b2c3d4-...",
    "created_at":        "2026-03-13T15:00:00Z",
    "created_by":        "u1b2c3d4-..."
  },
  "message": "Comment soft-deleted successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided path/header values are invalid          |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ORG_ACCESS_DENIED                | 403  | You do not have permission to delete comment     |
  |  5  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/comment not found or deleted        |
  |  6  | TASK_UPDATE_FORBIDDEN            | 403  | Role policy denied this comment delete           |
  |  7  | RESOURCE_CONFLICT                | 409  | Comment already deleted or state conflict        |
  |  8  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "comment_id": "c1b2c3d4-...",
      "current_state": "deleted"
    },
    "message": "This comment has already been deleted."
  }

================================================================
END OF TASK & COMMENT APIs
================================================================
