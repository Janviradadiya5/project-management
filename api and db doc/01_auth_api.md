================================================================
AUTHENTICATION APIs
================================================================

+------------------------+--------------------------------------------------------------+
| Item                   | Value                                                        |
+------------------------+--------------------------------------------------------------+
| Module                 | Authentication                                               |
| Base URL               | https://api.example.com/v1                                   |
| Content-Type           | application/json                                             |
| Authentication         | Authorization: Bearer <JWT> (OIDC/Auth0)                     |
| Permission / Scopes    | Public endpoints: No token required for register, login,     |
|                        | verify-email, and password-reset flows.                      |
|                        | Protected endpoints: Any authenticated role for logout       |
|                        | and token refresh. Scopes: auth:read, auth:write             |
| Timestamps             | ISO-8601 UTC (e.g., 2026-03-13T06:30:00Z)                    |
| IDs                    | UUID v4                                                      |
| Notes                  | Access token TTL: 15 minutes. Refresh token TTL: 7 days.     |
|                        | Password: min 12 chars with uppercase, lowercase, digit,     |
|                        | and symbol. Email must be verified before accessing          |
|                        | protected resources. Refresh token rotation is mandatory.    |
|                        | Logout and password reset revoke all active refresh          |
|                        | sessions for the user.                                       |
+------------------------+--------------------------------------------------------------+

Authentication: Auth0 JWT - Bearer <Token>
Permission:     Public for registration and authentication flows.
                Any authenticated role for session management.

---------------------------------------------------------------
Endpoint 1: POST /v1/auth/register - Register New User
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): Public - No authentication required
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
  "email":      "string",    // -> Valid email address, lowercase normalized, globally unique (required)
  "password":   "string",    // -> Min 12 chars, must include uppercase, lowercase, digit, symbol (required)
  "first_name": "string",    // -> User first name (required)
  "last_name":  "string"     // -> User last name (required)
}

5. Success Response - 201 Created (JSON)
{
  "success": true,
  "data": {
    "id":                   "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "email":                "john.doe@example.com",
    "first_name":           "John",
    "last_name":            "Doe",
    "is_email_verified":    false,
    "is_active":            true,
    "verification_sent_to": "john.doe@example.com",
    "created_at":           "2026-03-13T06:30:00Z",
    "updated_at":           "2026-03-13T06:30:00Z",
    "created_by":           "system",
    "updated_by":           "system"
  },
  "message": "Registration successful. Please verify your email address."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Input validation failed for one or more fields   |
  |  2  | RESOURCE_CONFLICT                | 409  | An account with this email already exists        |
  |  3  | RATE_LIMIT_EXCEEDED              | 429  | Too many registration attempts. Try again later  |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Account exists but email is not yet verified     |
  |  5  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Provided token is invalid or has expired         |
  |  6  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are incorrect               |
  |  7  | AUTH_REFRESH_REVOKED             | 401  | Refresh token has been revoked or invalidated    |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RESOURCE_CONFLICT",
    "details": {
      "email": "john.doe@example.com"
    },
    "message": "An account with this email address already exists."
  }

---------------------------------------------------------------
Endpoint 2: POST /v1/auth/verify-email - Verify Email Address
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): Public - No authentication required
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
  "token": "string"    // -> Email verification token sent to user's email address (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "id":                  "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "email":               "john.doe@example.com",
    "is_email_verified":   true,
    "verified_at":         "2026-03-13T06:35:00Z",
    "updated_at":          "2026-03-13T06:35:00Z",
    "updated_by":          "system"
  },
  "message": "Email address verified successfully. You may now log in."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Token field is required and cannot be empty      |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Verification token is invalid or has expired     |
  |  3  | RESOURCE_CONFLICT                | 409  | Email address has already been verified          |
  |  4  | RATE_LIMIT_EXCEEDED              | 429  | Too many verification attempts. Try again later  |
  |  5  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Account pending verification                     |
  |  6  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are incorrect               |
  |  7  | AUTH_REFRESH_REVOKED             | 401  | Session token has been revoked or invalidated    |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "AUTH_TOKEN_INVALID_OR_EXPIRED",
    "details": {
      "token": "provided-token-value"
    },
    "message": "The verification token is invalid or has expired. Please request a new one."
  }

---------------------------------------------------------------
Endpoint 3: POST /v1/auth/login - Authenticate User
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): Public - No authentication required
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
  "email":    "string",    // -> Registered email address (required)
  "password": "string"     // -> Account password (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "user": {
      "id":                "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
      "email":             "john.doe@example.com",
      "first_name":        "John",
      "last_name":         "Doe",
      "is_email_verified": true,
      "is_active":         true,
      "last_login_at":     "2026-03-13T06:40:00Z"
    },
    "tokens": {
      "access_token":       "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token":      "dGhpcyBpcyBhIHNhbXBsZSByZWZyZXNoIHRva2Vu...",
      "token_type":         "Bearer",
      "access_expires_in":  900,
      "refresh_expires_in": 604800
    },
    "session": {
      "session_id":  "a1b2c3d4-...",
      "issued_at":   "2026-03-13T06:40:00Z",
      "expires_at":  "2026-03-20T06:40:00Z"
    },
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-03-13T06:40:00Z",
    "created_by": "system",
    "updated_by": "system"
  },
  "message": "Login successful."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Email and password fields are required           |
  |  2  | AUTH_INVALID_CREDENTIALS         | 401  | Invalid email address or password                |
  |  3  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address not verified. Check your inbox     |
  |  4  | RATE_LIMIT_EXCEEDED              | 429  | Too many login attempts. Try again later         |
  |  5  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Provided token is invalid or has expired         |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Prior session revoked. Please log in again       |
  |  7  | RESOURCE_CONFLICT                | 409  | Session conflict detected for this account       |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "AUTH_INVALID_CREDENTIALS",
    "details": {
      "email": "john.doe@example.com"
    },
    "message": "Invalid email address or password. Please try again."
  }

---------------------------------------------------------------
Endpoint 4: POST /v1/auth/logout - Logout and Revoke Sessions
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer (Any authenticated user)
  - Scopes: auth:write

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
  "refresh_token": "string"    // -> Active refresh token to revoke (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "user_id":    "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "revoked_at": "2026-03-13T07:00:00Z",
    "updated_at": "2026-03-13T07:00:00Z",
    "updated_by": "3f5a2b1c-4d6e-7890-abcd-ef1234567890"
  },
  "message": "Logged out successfully. All active sessions have been revoked."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Refresh token field is required                  |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Access token is invalid or has expired           |
  |  3  | AUTH_REFRESH_REVOKED             | 401  | Refresh token has already been revoked           |
  |  4  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  5  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address not verified                       |
  |  6  | RATE_LIMIT_EXCEEDED              | 429  | Too many requests. Try again later               |
  |  7  | RESOURCE_CONFLICT                | 409  | Session conflict detected for this account       |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Provided token is invalid or expired             |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "AUTH_TOKEN_INVALID_OR_EXPIRED",
    "details": {
      "token_type": "access_token"
    },
    "message": "The provided access token is invalid or has expired."
  }

---------------------------------------------------------------
Endpoint 5: POST /v1/auth/token/refresh - Rotate Refresh Token
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): super_admin, organization_admin, project_manager,
                         team_member, viewer (Any authenticated user)
  - Scopes: auth:write

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
  "refresh_token": "string"    // -> Valid refresh token for rotation (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "tokens": {
      "access_token":       "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token":      "bmV3UmVmcmVzaFRva2VuU2FtcGxl...",
      "token_type":         "Bearer",
      "access_expires_in":  900,
      "refresh_expires_in": 604800
    },
    "session": {
      "session_id":    "b2c3d4e5-...",
      "prior_jti":     "a1b2c3d4-prior-jti",
      "issued_at":     "2026-03-13T07:15:00Z",
      "expires_at":    "2026-03-20T07:15:00Z"
    },
    "updated_at": "2026-03-13T07:15:00Z",
    "updated_by": "3f5a2b1c-4d6e-7890-abcd-ef1234567890"
  },
  "message": "Token refreshed successfully."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Refresh token field is required                  |
  |  2  | AUTH_REFRESH_REVOKED             | 401  | Refresh token has been revoked or already used   |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Refresh token is invalid or has expired          |
  |  4  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  5  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address not verified                       |
  |  6  | RATE_LIMIT_EXCEEDED              | 429  | Too many refresh attempts. Try again later       |
  |  7  | RESOURCE_CONFLICT                | 409  | Session conflict detected. Please log in again   |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Provided token is invalid or expired             |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "AUTH_REFRESH_REVOKED",
    "details": {
      "refresh_jti": "a1b2c3d4-prior-jti"
    },
    "message": "This refresh token has been revoked. Please log in again."
  }

---------------------------------------------------------------
Endpoint 6: POST /v1/auth/password-reset/request - Request Password Reset
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): Public - No authentication required
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
  "email": "string"    // -> Registered email address to receive reset instructions (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "email":          "john.doe@example.com",
    "message_sent_to": "john.doe@example.com",
    "expires_in":     3600,
    "updated_at":     "2026-03-13T07:20:00Z",
    "updated_by":     "system"
  },
  "message": "Password reset instructions have been sent to the provided email address."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Email field is required and must be valid        |
  |  2  | RATE_LIMIT_EXCEEDED              | 429  | Too many reset requests. Try again later         |
  |  3  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Provided token is invalid or has expired         |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Email address has not been verified              |
  |  5  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are incorrect               |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Refresh token has been revoked or invalidated    |
  |  7  | RESOURCE_CONFLICT                | 409  | A pending reset request already exists           |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Invitation token is invalid, expired, or revoked |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "email": "john.doe@example.com",
      "retry_after_seconds": 60
    },
    "message": "Too many password reset requests. Please try again after 60 seconds."
  }

---------------------------------------------------------------
Endpoint 7: POST /v1/auth/password-reset/confirm - Confirm Password Reset
---------------------------------------------------------------

Auth / Access Control:
  - Permissions (Roles): Public - No authentication required
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
  "token":        "string",    // -> Password reset token received via email (required)
  "new_password": "string"     // -> New password: min 12 chars, uppercase, lowercase,
                               //    digit, and symbol (required)
}

5. Success Response - 200 OK (JSON)
{
  "success": true,
  "data": {
    "user_id":    "3f5a2b1c-4d6e-7890-abcd-ef1234567890",
    "email":      "john.doe@example.com",
    "reset_at":   "2026-03-13T07:30:00Z",
    "sessions_revoked": true,
    "updated_at": "2026-03-13T07:30:00Z",
    "updated_by": "3f5a2b1c-4d6e-7890-abcd-ef1234567890"
  },
  "message": "Password reset successfully. All active sessions have been revoked."
}

6. Error Responses

  +-----+----------------------------------+------+--------------------------------------------------+
  |  #  | Error Code                       | HTTP | Message                                          |
  +-----+----------------------------------+------+--------------------------------------------------+
  |  1  | VALIDATION_FAILED                | 400  | Token and new_password fields are required       |
  |  2  | AUTH_TOKEN_INVALID_OR_EXPIRED    | 401  | Reset token is invalid or has expired            |
  |  3  | RESOURCE_CONFLICT                | 409  | This reset token has already been used           |
  |  4  | AUTH_EMAIL_NOT_VERIFIED          | 403  | Account email address is not verified            |
  |  5  | AUTH_INVALID_CREDENTIALS         | 401  | Provided credentials are not valid               |
  |  6  | AUTH_REFRESH_REVOKED             | 401  | Active sessions have been revoked                |
  |  7  | RATE_LIMIT_EXCEEDED              | 429  | Too many reset attempts. Try again later         |
  |  8  | ORG_ACCESS_DENIED                | 403  | Insufficient permissions to perform this action  |
  |  9  | INVITE_INVALID_OR_EXPIRED        | 400  | Provided token is invalid, expired, or revoked   |
  | 10  | INTERNAL_ERROR                   | 500  | An unexpected server error occurred              |
  +-----+----------------------------------+------+--------------------------------------------------+

  Error Response Example:
  {
    "success": false,
    "error_code": "AUTH_TOKEN_INVALID_OR_EXPIRED",
    "details": {
      "token": "provided-reset-token"
    },
    "message": "The password reset token is invalid or has expired. Please request a new one."
  }

================================================================
END OF AUTHENTICATION APIs
================================================================
