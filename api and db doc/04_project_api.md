================================================================
PROJECT APIs
================================================================

+------------------------+--------------------------------------------------------------+
| Item                   | Value                                                        |
+------------------------+--------------------------------------------------------------+
| Module                 | Project                                                      |
| Base URL               | https://api.example.com/v1                                   |
| Content-Type           | application/json                                             |
| Authentication         | Authorization: Bearer <JWT> (OIDC/Auth0)                     |
| Permission / Scopes    | Roles: super_admin, organization_admin, project_manager      |
|                        | Read access may include team_member and viewer in context.   |
|                        | Scopes: projects:read, projects:write, projects:admin        |
| Timestamps             | ISO-8601 UTC (e.g., 2026-03-13T06:30:00Z)                    |
| IDs                    | UUID v4                                                      |
| Notes                  | Project name required, length 3-200, unique within           |
|                        | organization among non-deleted records.                      |
|                        | status enum: active, completed, archived.                    |
|                        | deadline_at must be >= created_at.                           |
|                        | Write operations require X-Organization-ID header.           |
+------------------------+--------------------------------------------------------------+

Authentication: Auth0 JWT - Bearer <Token>
Permission:     super_admin, organization_admin, project_manager

---------------------------------------------------------------
Endpoint 1: GET /v1/projects - List Projects
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer
  - Scopes: projects:read

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
  | search          | string   | null       | Search by project name                  | -                         |
  | sort_by         | string   | created_at | Field to sort by                        | name, status, deadline_at,|
  |                 |          |            |                                         | created_at, updated_at    |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | status          | string   | null       | Filter by status                        | active, completed,        |
  |                 |          |            |                                         | archived                  |
  | organization_id | string   | null       | Filter by organization                  | UUID v4                   |
  | fields          | string   | all        | Comma-separated field projection        | id, organization_id,      |
  |                 |          |            |                                         | name, status, deadline_at |
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
        "id":                 "p1b2c3d4-...",
        "organization_id":    "3f5a2b1c-...",
        "name":               "Q2 Platform Launch",
        "description":        "Delivery project for Q2 launch milestones",
        "status":             "active",
        "deadline_at":        "2026-06-30T23:59:59Z",
        "created_by_user_id": "admin-uuid",
        "created_at":         "2026-03-01T09:00:00Z",
        "updated_at":         "2026-03-13T10:00:00Z",
        "created_by":         "admin-uuid",
        "updated_by":         "pm-uuid"
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
  "message": "Projects retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query/header fields are invalid      |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | PROJECT_STATUS_INVALID           | 400  | Status filter value is invalid                   |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "organization_id": "3f5a2b1c-..."
    },
    "message": "You do not have permission to view projects in this organization."
  }

---------------------------------------------------------------
Endpoint 2: POST /v1/projects - Create Project
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager
  - Scopes: projects:write

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
  "name":        "string",    // -> Project name, length 3-200, unique within organization (required)
  "description": "string",    // -> Project description (optional)
  "status":      "string",    // -> active, completed, archived (required)
  "deadline_at": "string"     // -> ISO-8601 datetime >= current time (optional)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":                 "p1b2c3d4-...",
    "organization_id":    "3f5a2b1c-...",
    "name":               "Q2 Platform Launch",
    "description":        "Delivery project for Q2 launch milestones",
    "status":             "active",
    "deadline_at":        "2026-06-30T23:59:59Z",
    "created_by_user_id": "admin-uuid",
    "created_at":         "2026-03-13T10:30:00Z",
    "updated_at":         "2026-03-13T10:30:00Z",
    "created_by":         "admin-uuid",
    "updated_by":         "admin-uuid"
  },
  "message": "Project created successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more input/header fields are invalid      |
  |  2  | RESOURCE_CONFLICT                | 409  | Project name already exists in this organization |
  |  3  | PROJECT_STATUS_INVALID           | 400  | Project status must be active/completed/archived |
  |  4  | PROJECT_DEADLINE_INVALID         | 400  | deadline_at must be greater than created_at      |
  |  5  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  7  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to create project       |
  |  8  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "PROJECT_DEADLINE_INVALID",
    "details": {
      "deadline_at": "2026-01-01T00:00:00Z"
    },
    "message": "Project deadline must be greater than or equal to the creation time."
  }

---------------------------------------------------------------
Endpoint 3: GET /v1/projects/:id - Get Project by ID
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer
  - Scopes: projects:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Project unique ID            |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | fields          | string   | all      | Comma-separated field projection        | id, organization_id, |
  |                 |          |          |                                         | name, status,        |
  |                 |          |          |                                         | deadline_at,         |
  |                 |          |          |                                         | description          |
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
    "id":                 "p1b2c3d4-...",
    "organization_id":    "3f5a2b1c-...",
    "name":               "Q2 Platform Launch",
    "description":        "Delivery project for Q2 launch milestones",
    "status":             "active",
    "deadline_at":        "2026-06-30T23:59:59Z",
    "created_by_user_id": "admin-uuid",
    "created_at":         "2026-03-01T09:00:00Z",
    "updated_at":         "2026-03-13T10:30:00Z",
    "created_by":         "admin-uuid",
    "updated_by":         "pm-uuid"
  },
  "message": "Project retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Path/header/query validation failed              |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this project           |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | RESOURCE_CONFLICT                | 409  | Project state conflict detected                  |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "project_id": "p1b2c3d4-...",
      "status": "archived"
    },
    "message": "Project is archived and cannot be modified with this operation."
  }

---------------------------------------------------------------
Endpoint 4: PATCH /v1/projects/:id - Update Project
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager
  - Scopes: projects:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Project unique ID            |
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
  "name":        "string",    // -> Project name, length 3-200 (optional)
  "description": "string",    // -> Project description (optional)
  "status":      "string",    // -> active, completed, archived (optional)
  "deadline_at": "string"     // -> ISO-8601 datetime >= project created_at (optional)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                 "p1b2c3d4-...",
    "organization_id":    "3f5a2b1c-...",
    "name":               "Q2 Platform Launch Revised",
    "description":        "Revised milestones and launch plan",
    "status":             "active",
    "deadline_at":        "2026-07-15T23:59:59Z",
    "created_by_user_id": "admin-uuid",
    "created_at":         "2026-03-01T09:00:00Z",
    "updated_at":         "2026-03-13T11:00:00Z",
    "created_by":         "admin-uuid",
    "updated_by":         "pm-uuid"
  },
  "message": "Project updated successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more input/header fields are invalid      |
  |  2  | PROJECT_STATUS_INVALID           | 400  | Project status must be active/completed/archived |
  |  3  | PROJECT_DEADLINE_INVALID         | 400  | deadline_at must be greater than created_at      |
  |  4  | RESOURCE_CONFLICT                | 409  | Project name conflict within organization         |
  |  5  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  7  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to update project       |
  |  8  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "PROJECT_STATUS_INVALID",
    "details": {
      "status": "paused"
    },
    "message": "Project status must be one of: active, completed, archived."
  }

---------------------------------------------------------------
Endpoint 5: DELETE /v1/projects/:id - Archive Project
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin
  - Scopes: projects:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Project unique ID            |
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
    "id":                 "p1b2c3d4-...",
    "organization_id":    "3f5a2b1c-...",
    "name":               "Q2 Platform Launch Revised",
    "status":             "archived",
    "deadline_at":        "2026-07-15T23:59:59Z",
    "created_by_user_id": "admin-uuid",
    "created_at":         "2026-03-01T09:00:00Z",
    "updated_at":         "2026-03-13T11:30:00Z",
    "created_by":         "admin-uuid",
    "updated_by":         "admin-uuid"
  },
  "message": "Project archived successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided path/header values are invalid          |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to archive project      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | RESOURCE_CONFLICT                | 409  | Project already archived or deletion conflict    |
  |  8  | PROJECT_STATUS_INVALID           | 400  | Invalid status transition requested              |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "project_id": "p1b2c3d4-...",
      "current_status": "archived"
    },
    "message": "The project is already archived and cannot be archived again."
  }

---------------------------------------------------------------
Endpoint 6: POST /v1/projects/:id/members - Add Project Member
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager
  - Scopes: projects:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Project unique ID            |
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
  "user_id":      "string",    // -> User UUID to be added to project (required)
  "project_role": "string"     // -> manager, contributor, viewer (required)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":               "pm1b2c3d4-...",
    "project_id":       "p1b2c3d4-...",
    "user_id":          "u1b2c3d4-...",
    "project_role":     "contributor",
    "added_by_user_id": "pm-uuid",
    "created_at":       "2026-03-13T12:00:00Z",
    "updated_at":       "2026-03-13T12:00:00Z",
    "created_by":       "pm-uuid",
    "updated_by":       "pm-uuid"
  },
  "message": "Project member added successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Input payload/header validation failed           |
  |  2  | TASK_ASSIGNEE_NOT_MEMBER         | 400  | User must be active org member before assignment |
  |  3  | RESOURCE_CONFLICT                | 409  | User is already a member of this project         |
  |  4  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  5  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  6  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to add project members  |
  |  7  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  8  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "TASK_ASSIGNEE_NOT_MEMBER",
    "details": {
      "user_id": "u1b2c3d4-...",
      "project_id": "p1b2c3d4-..."
    },
    "message": "The specified user is not an active organization member and cannot be added to the project."
  }

================================================================
END OF PROJECT APIs
================================================================
