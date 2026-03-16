================================================================
ORGANIZATION MEMBERS & INVITES APIs
================================================================

+------------------------+--------------------------------------------------------------+
| Item                   | Value                                                        |
+------------------------+--------------------------------------------------------------+
| Module                 | Organization Members & Invites                               |
| Base URL               | https://api.example.com/v1                                   |
| Content-Type           | application/json                                             |
| Authentication         | Authorization: Bearer <JWT> (OIDC/Auth0)                     |
| Permission / Scopes    | Roles: super_admin, organization_admin for write actions.    |
|                        | project_manager, team_member, viewer for read actions.       |
|                        | Invite acceptance is public (token-based).                   |
|                        | Scopes: organizations:read, organizations:write,             |
|                        |         organizations:admin                                  |
| Timestamps             | ISO-8601 UTC (e.g., 2026-03-13T06:30:00Z)                    |
| IDs                    | UUID v4                                                      |
| Notes                  | Membership is unique per (organization_id, user_id) pair.    |
|                        | Invite token is unique per (organization_id, email) pair.    |
|                        | Invite expires_at must be a future datetime at creation.     |
|                        | Acceptance only allowed for valid, non-expired, non-revoked, |
|                        | and non-accepted invite tokens.                              |
|                        | Member status values: invited, active, suspended, removed.   |
+------------------------+--------------------------------------------------------------+

Authentication: Auth0 JWT - Bearer <Token>
Permission:     super_admin, organization_admin (write/admin)
                project_manager, team_member, viewer (read)

---------------------------------------------------------------
Endpoint 1: GET /v1/organizations/:org_id/members - List Organization Members
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager
  - Scopes: organizations:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | org_id       | string   | Yes      | UUID v4           | Organization unique ID       |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | Name            | Type     | Default    | Description                             | Allowed                   |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | page            | integer  | 1          | Page number                             | >= 1                      |
  | limit           | integer  | 20         | Records per page                        | 1-100                     |
  | search          | string   | null       | Search by user name or email            | -                         |
  | sort_by         | string   | joined_at  | Field to sort by                        | joined_at, status,        |
  |                 |          |            |                                         | created_at                |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | status          | string   | null       | Filter by membership status             | invited, active,          |
  |                 |          |            |                                         | suspended, removed        |
  | role_id         | string   | null       | Filter by role ID                       | UUID v4                   |
  | fields          | string   | all        | Comma-separated field projection        | id, user_id, role_id,     |
  |                 |          |            |                                         | status, joined_at         |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "items": [
      {
        "id":                 "m1b2c3d4-...",
        "organization_id":    "3f5a2b1c-...",
        "user_id":            "a1b2c3d4-...",
        "role_id":            "r1c2d3e4-...",
        "role_code":          "organization_admin",
        "status":             "active",
        "joined_at":          "2026-01-01T00:00:00Z",
        "invited_by_user_id": "owner-uuid",
        "created_at":         "2026-01-01T00:00:00Z",
        "updated_at":         "2026-03-13T06:30:00Z",
        "created_by":         "owner-uuid",
        "updated_by":         "owner-uuid"
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
  "message": "Organization members retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query parameters failed validation   |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  8  | RESOURCE_CONFLICT                | 409  | Resource state conflict detected                 |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "org_id": "3f5a2b1c-4d6e-7890-abcd-ef1234567890"
    },
    "message": "You do not have access to this organization's member list."
  }

---------------------------------------------------------------
Endpoint 2: PATCH /v1/organizations/:org_id/members/:user_id - Update Member Role or Status
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin
  - Scopes: organizations:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | org_id       | string   | Yes      | UUID v4           | Organization unique ID       |
  | user_id      | string   | Yes      | UUID v4           | Member user unique ID        |
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
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "role_id": "string",    // -> New role UUID from role catalog (optional)
  "status":  "string"     // -> New membership status (optional)
                          //    Allowed: active, suspended
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                 "m1b2c3d4-...",
    "organization_id":    "3f5a2b1c-...",
    "user_id":            "a1b2c3d4-...",
    "role_id":            "r2c3d4e5-...",
    "role_code":          "project_manager",
    "status":             "active",
    "joined_at":          "2026-01-01T00:00:00Z",
    "invited_by_user_id": "owner-uuid",
    "created_at":         "2026-01-01T00:00:00Z",
    "updated_at":         "2026-03-13T09:00:00Z",
    "created_by":         "owner-uuid",
    "updated_by":         "a1b2c3d4-admin-uuid"
  },
  "message": "Member updated successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more input fields failed validation       |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to update this member   |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | RESOURCE_CONFLICT                | 409  | Member role or status conflict detected          |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "user_id": "a1b2c3d4-...",
      "org_id":  "3f5a2b1c-..."
    },
    "message": "You do not have permission to update a member in this organization."
  }

---------------------------------------------------------------
Endpoint 3: DELETE /v1/organizations/:org_id/members/:user_id - Remove Member
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin
  - Scopes: organizations:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | org_id       | string   | Yes      | UUID v4           | Organization unique ID       |
  | user_id      | string   | Yes      | UUID v4           | Member user unique ID        |
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
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":              "m1b2c3d4-...",
    "organization_id": "3f5a2b1c-...",
    "user_id":         "a1b2c3d4-...",
    "status":          "removed",
    "removed_at":      "2026-03-13T09:30:00Z",
    "updated_at":      "2026-03-13T09:30:00Z",
    "updated_by":      "admin-uuid",
    "created_at":      "2026-01-01T00:00:00Z",
    "created_by":      "owner-uuid"
  },
  "message": "Member removed from organization successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided path parameters are invalid             |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to remove this member   |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | RESOURCE_CONFLICT                | 409  | Cannot remove the organization owner             |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "user_id": "a1b2c3d4-...",
      "reason":  "owner_cannot_be_removed"
    },
    "message": "The organization owner cannot be removed from the organization."
  }

---------------------------------------------------------------
Endpoint 4: POST /v1/organizations/:org_id/invites - Send Invitation
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin
  - Scopes: organizations:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | org_id       | string   | Yes      | UUID v4           | Organization unique ID       |
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
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "email":   "string",    // -> Email address of the person being invited (required)
  "role_id": "string"     // -> UUID of the role to assign upon acceptance (required)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":                 "inv-uuid-...",
    "organization_id":    "3f5a2b1c-...",
    "email":              "invited@example.com",
    "role_id":            "r2c3d4e5-...",
    "role_code":          "team_member",
    "expires_at":         "2026-03-20T09:00:00Z",
    "accepted_at":        null,
    "revoked_at":         null,
    "invited_by_user_id": "admin-uuid",
    "created_at":         "2026-03-13T09:00:00Z",
    "updated_at":         "2026-03-13T09:00:00Z",
    "created_by":         "admin-uuid",
    "updated_by":         "admin-uuid"
  },
  "message": "Invitation sent successfully to invited@example.com."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Email or role_id field failed validation         |
  |  2  | RESOURCE_CONFLICT                | 409  | An active invite already exists for this email   |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  4  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  5  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  6  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to send invitations     |
  |  7  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  8  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many invite requests. Please try again later |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "email":   "invited@example.com",
      "org_id":  "3f5a2b1c-..."
    },
    "message": "An active invitation already exists for this email in the organization."
  }

---------------------------------------------------------------
Endpoint 5: GET /v1/organizations/:org_id/invites - List Organization Invitations
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin
  - Scopes: organizations:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | org_id       | string   | Yes      | UUID v4           | Organization unique ID       |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | Name            | Type     | Default    | Description                             | Allowed                   |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+
  | page            | integer  | 1          | Page number                             | >= 1                      |
  | limit           | integer  | 20         | Records per page                        | 1-100                     |
  | search          | string   | null       | Search by invited email                 | -                         |
  | sort_by         | string   | created_at | Field to sort by                        | created_at, expires_at    |
  | order           | string   | desc       | Sort direction                          | asc, desc                 |
  | status          | string   | null       | Filter by invite status                 | pending, accepted, revoked|
  | fields          | string   | all        | Comma-separated field projection        | id, email, role_id,       |
  |                 |          |            |                                         | expires_at, accepted_at   |
  +-----------------+----------+------------+-----------------------------------------+---------------------------+

3. Headers

  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Name                     | Type     | Required | Constraints              | Description                      |
  +--------------------------+----------+----------+--------------------------+----------------------------------+
  | Authorization            | string   | Yes      | Bearer <JWT>             | Valid access token               |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "items": [
      {
        "id":                 "inv-uuid-...",
        "organization_id":    "3f5a2b1c-...",
        "email":              "invited@example.com",
        "role_id":            "r2c3d4e5-...",
        "role_code":          "team_member",
        "expires_at":         "2026-03-20T09:00:00Z",
        "accepted_at":        null,
        "revoked_at":         null,
        "invited_by_user_id": "admin-uuid",
        "created_at":         "2026-03-13T09:00:00Z",
        "updated_at":         "2026-03-13T09:00:00Z",
        "created_by":         "admin-uuid",
        "updated_by":         "admin-uuid"
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
  "message": "Invitations retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query parameters failed validation   |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to list invitations     |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "org_id": "3f5a2b1c-..."
    },
    "message": "You do not have permission to view invitations for this organization."
  }

---------------------------------------------------------------
Endpoint 6: DELETE /v1/organizations/:org_id/invites/:invite_id - Revoke Invitation
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin
  - Scopes: organizations:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | org_id       | string   | Yes      | UUID v4           | Organization unique ID       |
  | invite_id    | string   | Yes      | UUID v4           | Invitation unique ID         |
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
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
N/A

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":              "inv-uuid-...",
    "organization_id": "3f5a2b1c-...",
    "email":           "invited@example.com",
    "revoked_at":      "2026-03-13T10:00:00Z",
    "updated_at":      "2026-03-13T10:00:00Z",
    "updated_by":      "admin-uuid",
    "created_at":      "2026-03-13T09:00:00Z",
    "created_by":      "admin-uuid"
  },
  "message": "Invitation revoked successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided path parameters are invalid             |
  |  2  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation is already revoked or has expired     |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  4  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  5  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  6  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to revoke invitations   |
  |  7  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  8  | RESOURCE_CONFLICT                | 409  | Invitation has already been accepted             |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "invite_id": "inv-uuid-...",
      "accepted_at": "2026-03-15T08:00:00Z"
    },
    "message": "This invitation has already been accepted and cannot be revoked."
  }

---------------------------------------------------------------
Endpoint 7: POST /v1/invites/accept - Accept Organization Invitation
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): Public (token-based, email-verified user)
  - Scopes: None

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
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "token": "string"    // -> Unique invite token received via email (required)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "membership": {
      "id":                 "m1b2c3d4-...",
      "organization_id":    "3f5a2b1c-...",
      "user_id":            "a1b2c3d4-...",
      "role_id":            "r2c3d4e5-...",
      "role_code":          "team_member",
      "status":             "active",
      "joined_at":          "2026-03-13T10:30:00Z",
      "invited_by_user_id": "admin-uuid",
      "created_at":         "2026-03-13T10:30:00Z",
      "updated_at":         "2026-03-13T10:30:00Z",
      "created_by":         "system",
      "updated_by":         "system"
    },
    "invite": {
      "id":          "inv-uuid-...",
      "accepted_at": "2026-03-13T10:30:00Z"
    }
  },
  "message": "Invitation accepted. You are now a member of the organization."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Token field is required and cannot be empty      |
  |  2  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  |  3  | RESOURCE_CONFLICT                | 409  | This invitation has already been accepted        |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to accept invite  |
  |  5  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Provided token is invalid or has expired         |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  7  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  8  | ORG_ACCESS_DENIED                | 403  | You are not authorized to accept this invitation |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "INVITE_INVALID_OR_EXPIRED",
    "details": {
      "token":   "provided-invite-token",
      "reason":  "expired"
    },
    "message": "The invitation token is invalid or has expired. Please request a new invitation."
  }

================================================================
END OF ORGANIZATION MEMBERS & INVITES APIs
================================================================
