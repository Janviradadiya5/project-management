================================================================
ORGANIZATION APIs
================================================================

+------------------------+--------------------------------------------------------------+
| Item                   | Value                                                        |
+------------------------+--------------------------------------------------------------+
| Module                 | Organization                                                 |
| Base URL               | https://api.example.com/v1                                   |
| Content-Type           | application/json                                             |
| Authentication         | Authorization: Bearer <JWT> (OIDC/Auth0)                     |
| Permission / Scopes    | Roles: super_admin, organization_admin                       |
|                        | Scopes: organizations:read, organizations:write,             |
|                        |         organizations:admin                                  |
| Timestamps             | ISO-8601 UTC (e.g., 2026-03-13T06:30:00Z)                    |
| IDs                    | UUID v4                                                      |
| Notes                  | Organization name: 3-120 characters.                         |
|                        | Slug: globally unique, lowercase kebab-case.                 |
|                        | Delete is a soft delete using deleted_at with 30-day         |
|                        | retention. Soft-deleted organizations block new project      |
|                        | and task writes. Creator becomes the owner_user_id and       |
|                        | gets organization_admin membership automatically.            |
+------------------------+--------------------------------------------------------------+

Authentication: Auth0 JWT - Bearer <Token>
Permission:     super_admin, organization_admin

---------------------------------------------------------------
Endpoint 1: GET /v1/organizations - List Organizations
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin (all orgs), organization_admin (own orgs)
  - Scopes: organizations:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | N/A          | N/A      | N/A      | N/A               | N/A                          |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+------------+-----------------------------------------+--------------------------+
  | Name            | Type     | Default    | Description                             | Allowed                  |
  +-----------------+----------+------------+-----------------------------------------+--------------------------+
  | page            | integer  | 1          | Page number                             | >= 1                     |
  | limit           | integer  | 20         | Records per page                        | 1-100                    |
  | search          | string   | null       | Search by name or slug                  | -                        |
  | sort_by         | string   | created_at | Field to sort by                        | name, slug, created_at,  |
  |                 |          |            |                                         | status, updated_at       |
  | order           | string   | desc       | Sort direction                          | asc, desc                |
  | status          | string   | null       | Filter by organization status           | active, archived,        |
  |                 |          |            |                                         | deleted                  |
  | fields          | string   | all        | Comma-separated field projection        | id, name, slug, status,  |
  |                 |          |            |                                         | created_at, updated_at   |
  +-----------------+----------+------------+-----------------------------------------+--------------------------+

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
        "id":             "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
        "name":           "Acme Corporation",
        "slug":           "acme-corporation",
        "owner_user_id":  "a1b2c3d4-...",
        "status":         "active",
        "deleted_at":     null,
        "created_at":     "2026-01-01T00:00:00Z",
        "updated_at":     "2026-03-13T06:30:00Z",
        "created_by":     "a1b2c3d4-...",
        "updated_by":     "a1b2c3d4-..."
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
  "message": "Organizations retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more query parameters failed validation   |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to list organizations   |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  8  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  |  9  | RESOURCE_CONFLICT                | 409  | Resource state conflict detected                 |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_ACCESS_DENIED",
    "details": {
      "required_scope": "organizations:read"
    },
    "message": "You do not have permission to list organizations."
  }

---------------------------------------------------------------
Endpoint 2: POST /v1/organizations - Create Organization
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin (any authenticated user
                         can create their own organization)
  - Scopes: organizations:write

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
  | Content-Type             | string   | Yes      | application/json         | Request body content type        |
  +--------------------------+----------+----------+--------------------------+----------------------------------+

4. Request Payload (JSON)
{
  "name": "string",    // -> Organization display name, length 3-120 (required)
  "slug": "string"     // -> Unique lowercase kebab-case identifier (required)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":            "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "name":          "Acme Corporation",
    "slug":          "acme-corporation",
    "owner_user_id": "a1b2c3d4-...",
    "status":        "active",
    "deleted_at":    null,
    "created_at":    "2026-03-13T06:30:00Z",
    "updated_at":    "2026-03-13T06:30:00Z",
    "created_by":    "a1b2c3d4-...",
    "updated_by":    "a1b2c3d4-..."
  },
  "message": "Organization created successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more input fields failed validation       |
  |  2  | RESOURCE_CONFLICT                | 409  | Organization slug is already in use              |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  6  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to create organization  |
  |  7  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  8  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  |  9  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization context not found                   |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "slug": "acme-corporation"
    },
    "message": "An organization with this slug already exists. Please choose a different slug."
  }

---------------------------------------------------------------
Endpoint 3: GET /v1/organizations/:id - Get Organization by ID
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin (own org),
                         project_manager, team_member, viewer (own org members)
  - Scopes: organizations:read

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Organization unique ID       |
  +--------------+----------+----------+-------------------+------------------------------+

2. Query Parameters

  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | Name            | Type     | Default  | Description                             | Allowed              |
  +-----------------+----------+----------+-----------------------------------------+----------------------+
  | fields          | string   | all      | Comma-separated field projection        | id, name, slug,      |
  |                 |          |          |                                         | status, owner_user_id|
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
    "id":            "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "name":          "Acme Corporation",
    "slug":          "acme-corporation",
    "owner_user_id": "a1b2c3d4-...",
    "status":        "active",
    "deleted_at":    null,
    "created_at":    "2026-01-01T00:00:00Z",
    "updated_at":    "2026-03-13T06:30:00Z",
    "created_by":    "a1b2c3d4-...",
    "updated_by":    "a1b2c3d4-..."
  },
  "message": "Organization retrieved successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided ID is not a valid UUID                  |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | You do not have access to this organization      |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  8  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  |  9  | RESOURCE_CONFLICT                | 409  | Resource state conflict detected                 |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_NOT_FOUND_OR_DELETED",
    "details": {
      "id": "3f5a2b1c-4d6e-7890-abcd-ef1234567890"
    },
    "message": "The requested organization was not found or has been deleted."
  }

---------------------------------------------------------------
Endpoint 4: PATCH /v1/organizations/:id - Update Organization
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin (own org)
  - Scopes: organizations:write

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Organization unique ID       |
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
  "name":   "string",    // -> Organization display name, length 3-120 (optional)
  "slug":   "string",    // -> Unique lowercase kebab-case identifier (optional)
  "status": "string"     // -> Organization status: active or archived (optional)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":            "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "name":          "Acme Corporation Updated",
    "slug":          "acme-corp-updated",
    "owner_user_id": "a1b2c3d4-...",
    "status":        "active",
    "deleted_at":    null,
    "created_at":    "2026-01-01T00:00:00Z",
    "updated_at":    "2026-03-13T08:00:00Z",
    "created_by":    "a1b2c3d4-...",
    "updated_by":    "a1b2c3d4-..."
  },
  "message": "Organization updated successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | One or more input fields failed validation       |
  |  2  | RESOURCE_CONFLICT                | 409  | Organization slug is already in use              |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to update organization  |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has been deleted       |
  |  7  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "slug": "acme-corp-updated"
    },
    "message": "The slug 'acme-corp-updated' is already taken. Please choose another."
  }

---------------------------------------------------------------
Endpoint 5: DELETE /v1/organizations/:id - Soft Delete Organization
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin (own org)
  - Scopes: organizations:admin

1. Path Parameters

  +--------------+----------+----------+-------------------+------------------------------+
  | Name         | Type     | Required | Constraints       | Description                  |
  +--------------+----------+----------+-------------------+------------------------------+
  | id           | string   | Yes      | UUID v4           | Organization unique ID       |
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
    "id":         "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "name":       "Acme Corporation",
    "slug":       "acme-corporation",
    "status":     "archived",
    "deleted_at": "2026-03-13T08:30:00Z",
    "updated_at": "2026-03-13T08:30:00Z",
    "updated_by": "a1b2c3d4-...",
    "created_at": "2026-01-01T00:00:00Z",
    "created_by": "a1b2c3d4-..."
  },
  "message": "Organization soft-deleted successfully. Data retained for 30 days."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Provided ID is not a valid UUID                  |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Session has been revoked. Please log in again    |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address must be verified to proceed        |
  |  5  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to delete organization  |
  |  6  | ORG_NOT_FOUND_OR_DELETED         | 404  | Organization not found or has already been       |
  |     |                                  |      | deleted                                          |
  |  7  | RESOURCE_CONFLICT                | 409  | Organization delete blocked by active dependency |
  |  8  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  9  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Please try again later        |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "ORG_NOT_FOUND_OR_DELETED",
    "details": {
      "id": "3f5a2b1c-4d6e-7890-abcd-ef1234567890"
    },
    "message": "The organization was not found or has already been deleted."
  }

================================================================
END OF ORGANIZATION APIs
================================================================
