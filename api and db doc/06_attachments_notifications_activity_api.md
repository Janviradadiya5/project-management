================================================================
ATTACHMENT, NOTIFICATION & ACTIVITY LOG APIs
================================================================

+------------------------+--------------------------------------------------------------+
| Item                   | Value                                                        |
+------------------------+--------------------------------------------------------------+
| Module                 | Attachment, Notification, Activity Log                       |
| Base URL               | https://api.example.com/v1                                   |
| Content-Type           | application/json                                             |
| Authentication         | Authorization: Bearer <JWT> (OIDC/Auth0)                     |
| Permission / Scopes    | Attachment read/write: super_admin, organization_admin,      |
|                        | project_manager, team_member; viewer read-only where allowed |
|                        | Notification read/update: all authenticated roles in scope   |
|                        | Activity logs read: super_admin, organization_admin,         |
|                        | project_manager (as policy permits)                          |
|                        | Scopes: attachments:read, attachments:write, attachments:admin|
|                        |         notifications:read, notifications:write,             |
|                        |         activity_logs:read                                   |
| Timestamps             | ISO-8601 UTC (e.g., 2026-03-13T06:30:00Z)                    |
| IDs                    | UUID v4                                                      |
| Notes                  | Attachment max size: 25 MB (26214400 bytes).                |
|                        | Allowed content_type: application/pdf, image/jpeg, image/png,|
|                        | application/msword,                                          |
|                        | application/vnd.openxmlformats-officedocument.wordprocessingml.document,|
|                        | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,|
|                        | text/csv, text/plain.                                        |
|                        | checksum is required for integrity.                           |
|                        | Attachment delete is soft delete via deleted_at.             |
|                        | Notification is_read=true requires read_at non-null.         |
|                        | ActivityLog is immutable after creation.                     |
+------------------------+--------------------------------------------------------------+

Authentication: Auth0 JWT - Bearer <Token>
Permission:     Based on module role rules and scopes

---------------------------------------------------------------
Endpoint 1: POST /v1/tasks/:task_id/attachments - Upload Attachment Metadata
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member
  - Scopes: attachments:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | task_id      | string   | Yes      | UUID v4           | Task unique ID               |
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
  "file_name":    "string",    // -> Original filename (required)
  "content_type": "string",    // -> Allowed mime type (required)
  "size_bytes":   0,            // -> File size in bytes, max 26214400 (required)
  "storage_key":  "string",    // -> Object storage key/path (required)
  "checksum":     "string"     // -> Hash/checksum for file integrity (required)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":                  "att1b2c3d4-...",
    "task_id":             "t1b2c3d4-...",
    "uploaded_by_user_id": "u1b2c3d4-...",
    "file_name":           "requirements.pdf",
    "content_type":        "application/pdf",
    "size_bytes":          524288,
    "storage_key":         "org/3f5a2b1c/tasks/t1b2c3d4/requirements.pdf",
    "checksum":            "sha256:ab12cd34ef56...",
    "deleted_at":          null,
    "created_at":          "2026-03-13T16:30:00Z",
    "updated_at":          "2026-03-13T16:30:00Z",
    "created_by":          "u1b2c3d4-...",
    "updated_by":          "u1b2c3d4-..."
  },
  "message": "Attachment uploaded successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more payload/header fields are invalid    |
  |  2  | ATTACHMENT_TYPE_NOT_ALLOWED      | 415  | Attachment content type is not allowed           |
  |  3  | ATTACHMENT_SIZE_EXCEEDED         | 413  | Attachment exceeds maximum allowed size          |
  |  4  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  5  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  6  | ORG_ACCESS_DENIED                | 403  | You do not have permission to upload attachment  |
  |  7  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/task not found or deleted           |
  |  8  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ATTACHMENT_SIZE_EXCEEDED",
    "details": {
      "size_bytes": 52428801,
      "max_size_bytes": 26214400
    },
    "message": "Attachment exceeds the maximum allowed size of 25 MB."
  }

---------------------------------------------------------------
Endpoint 2: GET /v1/tasks/:task_id/attachments - List Attachments
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer (if task is accessible)
  - Scopes: attachments:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | task_id      | string   | Yes      | UUID v4           | Task unique ID               |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | Name            | Type     | Default    | Description                             | Allowed                   |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | page            | integer  | 1          | Page number                             | >= 1                      |
  | limit           | integer  | 20         | Records per page                        | 1-100                     |
  | search          | string   | null       | Search by file_name                     | -                         |
  | sort_by         | string   | created_at | Field to sort by                        | file_name, size_bytes,    |
  |                 |          |            |                                         | created_at                |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | content_type    | string   | null       | Filter by content type                  | allowed mime types        |
  | fields          | string   | all        | Comma-separated field projection        | id, file_name,            |
  |                 |          |            |                                         | content_type, size_bytes  |
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
        "id":                  "att1b2c3d4-...",
        "task_id":             "t1b2c3d4-...",
        "uploaded_by_user_id": "u1b2c3d4-...",
        "file_name":           "requirements.pdf",
        "content_type":        "application/pdf",
        "size_bytes":          524288,
        "storage_key":         "org/3f5a2b1c/tasks/t1b2c3d4/requirements.pdf",
        "checksum":            "sha256:ab12cd34ef56...",
        "deleted_at":          null,
        "created_at":          "2026-03-13T16:30:00Z",
        "updated_at":          "2026-03-13T16:30:00Z",
        "created_by":          "u1b2c3d4-...",
        "updated_by":          "u1b2c3d4-..."
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
  "message": "Attachments retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query/header fields are invalid      |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ATTACHMENT_ACCESS_FORBIDDEN      | 403  | You do not have permission to view attachment    |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/task not found or deleted           |
  |  7  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ATTACHMENT_ACCESS_FORBIDDEN",
    "details": {
      "task_id": "t1b2c3d4-..."
    },
    "message": "You are not authorized to view attachments for this task."
  }

---------------------------------------------------------------
Endpoint 3: DELETE /v1/attachments/:id - Soft Delete Attachment
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member (policy-based)
  - Scopes: attachments:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Attachment unique ID         |
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
    "id":                  "att1b2c3d4-...",
    "task_id":             "t1b2c3d4-...",
    "uploaded_by_user_id": "u1b2c3d4-...",
    "file_name":           "requirements.pdf",
    "deleted_at":          "2026-03-13T17:00:00Z",
    "updated_at":          "2026-03-13T17:00:00Z",
    "updated_by":          "u1b2c3d4-...",
    "created_at":          "2026-03-13T16:30:00Z",
    "created_by":          "u1b2c3d4-..."
  },
  "message": "Attachment soft-deleted successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided path/header values are invalid          |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ATTACHMENT_ACCESS_FORBIDDEN      | 403  | You do not have permission to delete attachment  |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/attachment not found or deleted     |
  |  7  | RESOURCE_CONFLICT                | 409  | Attachment already deleted or state conflict     |
  |  8  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "attachment_id": "att1b2c3d4-...",
      "current_state": "deleted"
    },
    "message": "This attachment has already been deleted."
  }

---------------------------------------------------------------
Endpoint 4: GET /v1/notifications - List Notifications
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer (for own notifications)
  - Scopes: notifications:read

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
  | search          | string   | null       | Search by title/body                    | -                         |
  | sort_by         | string   | created_at | Field to sort by                        | created_at, is_read       |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | is_read         | boolean  | null       | Filter by read status                   | true, false               |
  | type            | string   | null       | Filter by notification type             | domain-defined types      |
  | fields          | string   | all        | Comma-separated field projection        | id, type, title, is_read, |
  |                 |          |            |                                         | created_at, read_at       |
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
        "id":                "n1b2c3d4-...",
        "recipient_user_id": "u1b2c3d4-...",
        "organization_id":   "3f5a2b1c-...",
        "type":              "task.assigned",
        "title":             "Task assigned to you",
        "body":              "You were assigned to task 'Finalize API specification'.",
        "payload_json":      {
          "task_id": "t1b2c3d4-...",
          "project_id": "p1b2c3d4-..."
        },
        "is_read":           false,
        "created_at":        "2026-03-13T17:30:00Z",
        "read_at":           null,
        "updated_at":        "2026-03-13T17:30:00Z",
        "created_by":        "system",
        "updated_by":        "system"
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
  "message": "Notifications retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query/header fields are invalid      |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  5  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  6  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  7  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  8  | RESOURCE_CONFLICT                | 409  | Notification resource conflict detected          |
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
    "message": "You do not have permission to access notifications in this organization."
  }

---------------------------------------------------------------
Endpoint 5: PATCH /v1/notifications/:id/read - Mark Notification as Read
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer (for own notifications)
  - Scopes: notifications:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Notification unique ID       |
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
  "is_read": true    // -> Mark notification as read (required, must be true)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                "n1b2c3d4-...",
    "recipient_user_id": "u1b2c3d4-...",
    "organization_id":   "3f5a2b1c-...",
    "is_read":           true,
    "read_at":           "2026-03-13T18:00:00Z",
    "updated_at":        "2026-03-13T18:00:00Z",
    "updated_by":        "u1b2c3d4-...",
    "created_at":        "2026-03-13T17:30:00Z",
    "created_by":        "system"
  },
  "message": "Notification marked as read successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Payload/header validation failed                 |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ORG_ACCESS_DENIED                | 403  | You do not have permission to update this        |
  |     |                                  |      | notification                                     |
  |  5  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization/notification not found or deleted   |
  |  6  | RESOURCE_CONFLICT                | 409  | Notification already in read state               |
  |  7  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "notification_id": "n1b2c3d4-...",
      "is_read": true
    },
    "message": "This notification is already marked as read."
  }

---------------------------------------------------------------
Endpoint 6: GET /v1/activity-logs - List Activity Logs
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager
  - Scopes: activity_logs:read

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
  | search          | string   | null       | Search by event_type/target_type        | -                         |
  | sort_by         | string   | created_at | Field to sort by                        | created_at, event_type,   |
  |                 |          |            |                                         | target_type               |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | actor_user_id   | string   | null       | Filter by actor                         | UUID v4                   |
  | event_type      | string   | null       | Filter by event type                    | domain event names        |
  | target_type     | string   | null       | Filter by target type                   | user, organization,       |
  |                 |          |            |                                         | project, task, comment    |
  | fields          | string   | all        | Comma-separated field projection        | id, event_type,           |
  |                 |          |            |                                         | target_type, target_id,   |
  |                 |          |            |                                         | created_at, request_id    |
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
        "id":              "log1b2c3d4-...",
        "organization_id": "3f5a2b1c-...",
        "actor_user_id":   "u1b2c3d4-...",
        "event_type":      "task.updated",
        "target_type":     "task",
        "target_id":       "t1b2c3d4-...",
        "metadata_json":   {
          "field": "status",
          "from": "in_progress",
          "to": "done"
        },
        "request_id":      "req-20260313-abcdef123456",
        "created_at":      "2026-03-13T18:30:00Z",
        "updated_at":      "2026-03-13T18:30:00Z",
        "created_by":      "system",
        "updated_by":      "system"
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
  "message": "Activity logs retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query/header fields are invalid      |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | ORG_ACCESS_DENIED                | 403  | You do not have access to activity logs          |
  |  5  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  6  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  7  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  8  | RESOURCE_CONFLICT                | 409  | Resource conflict detected while reading logs    |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "required_scope": "activity_logs:read"
    },
    "message": "You do not have permission to read activity logs for this organization."
  }

================================================================
END OF ATTACHMENT, NOTIFICATION & ACTIVITY LOG APIs
================================================================
