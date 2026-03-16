========================================================================================================================
SECTION 1 - COVER PAGE
========================================================================================================================

+----------------------+--------------------------------------------------------------+
| Item                 | Value                                                        |
+----------------------+--------------------------------------------------------------+
| Project Name         | Multi-Tenant Project Collaboration Platform                  |
| Version              | 1.0                                                          |
| Author               | Enterprise Database Architect GPT                            |
| Company              | -                                                            |
| Date                 | 2026-03-13                                                   |
| Database Engine      | PostgreSQL                                                   |
| Architecture Base    | Microsoft Azure Data Architecture Best Practices             |
+----------------------+--------------------------------------------------------------+

========================================================================================================================
SECTION 2 - DOCUMENT CONTROL
========================================================================================================================

+----------+------------+--------------------------------------+-----------------------------------------------------------+
| Version  | Date       | Author                               | Description                                               |
+----------+------------+--------------------------------------+-----------------------------------------------------------+
| 0.1      | 2026-03-13 | Enterprise Database Architect GPT    | Initial draft based on domain entities and workflows      |
| 1.0      | 2026-03-13 | Enterprise Database Architect GPT    | Finalized logical, physical, indexing, and ERD sections   |
+----------+------------+--------------------------------------+-----------------------------------------------------------+

========================================================================================================================
SECTION 3 - INTRODUCTION
========================================================================================================================

3.1 Purpose
Design an enterprise-grade, normalized, secure, and scalable PostgreSQL database for a multi-tenant project collaboration platform covering authentication, organization management, projects, tasks, comments, attachments, notifications, and audit logging.

3.2 Scope
Users, Roles, Organizations, Memberships, Invites, Projects, Project Members, Tasks, Comments, Attachments, Notifications, Activity Logs, Auth Token Sessions, Email Verification Tokens, Password Reset Tokens.

3.3 Audience
Solution Architects, Backend Developers, Database Administrators, DevOps Engineers, Security Engineers, QA Engineers.

========================================================================================================================
SECTION 4 - SYSTEM OVERVIEW
========================================================================================================================

Core workflow
1. User registers and verifies email.
2. User authenticates and receives JWT access/refresh tokens.
3. User creates or joins organization.
4. Organization admins invite members and assign roles.
5. Authorized users create projects and assign project members.
6. Authorized users create and update tasks, comments, and attachments.
7. System emits notifications and immutable activity logs for auditable actions.

User types
- super_admin
- organization_admin
- project_manager
- team_member
- viewer

Module responsibilities
- Identity and Access: User, Role, AuthTokenSession, EmailVerificationToken, PasswordResetToken
- Tenant and Membership: Organization, OrganizationMembership, OrganizationInvite
- Delivery and Collaboration: Project, ProjectMember, Task, Comment, Attachment
- Engagement and Audit: Notification, ActivityLog

========================================================================================================================
SECTION 5 - NON-FUNCTIONAL REQUIREMENTS (NFRs)
========================================================================================================================

+----------------------+--------------------------------------------------------------------------------------------------------------+
| NFR Category         | Requirements                                                                                                 |
+----------------------+--------------------------------------------------------------------------------------------------------------+
| Scalability          | Horizontal read scaling with read replicas; partition large append-heavy tables by time and tenant context  |
| Performance          | P95 API reads under 200 ms for indexed queries; pagination mandatory for list endpoints                    |
| Security             | JWT-based authentication; RBAC enforcement at service layer; TLS in transit; encryption at rest             |
| Availability         | High availability PostgreSQL deployment with automated failover                                              |
| Compliance           | Auditability for critical events; soft delete policy for retention-sensitive entities                        |
| PII Protection       | Email and user profile data access restricted by role and organization context                               |
| Audit Requirements   | Immutable ActivityLog; request_id traceability; created_at and actor tracking for auditable writes          |
| Backup and Recovery  | Daily full backup, 15-minute WAL/PITR window, tested restore runbooks                                       |
| Multi-Tenant Safety  | Organization context isolation in all tenant-owned tables and access paths                                   |
+----------------------+--------------------------------------------------------------------------------------------------------------+

========================================================================================================================
SECTION 6 - LOGICAL DATA MODEL
========================================================================================================================

6.1 Entity descriptions
- User: identity principal with credential and verification state
- Role: role catalog used for authorization policies
- Organization: tenant boundary and ownership root
- OrganizationMembership: user-to-organization mapping with role and status
- OrganizationInvite: invitation lifecycle for onboarding
- Project: scoped work container under organization
- ProjectMember: user-to-project mapping with project role
- Task: unit of work under project
- Comment: discussion records on tasks with optional parent threading
- Attachment: file metadata linked to tasks
- Notification: user-facing event delivery records
- ActivityLog: immutable audit trail of domain actions
- AuthTokenSession: refresh token lifecycle tracking
- EmailVerificationToken: email verification lifecycle
- PasswordResetToken: password reset lifecycle

6.2 Relationship summary
- Organization 1 to many Project
- Organization 1 to many OrganizationMembership
- Organization 1 to many OrganizationInvite
- Organization 1 to many Notification
- Organization 1 to many ActivityLog
- User 1 to many OrganizationMembership
- Role 1 to many OrganizationMembership
- User 1 to many OrganizationInvite (invited_by)
- Project 1 to many Task
- Project 1 to many ProjectMember
- User 1 to many ProjectMember
- Task 1 to many Comment
- Comment 1 to many Comment (self-reference)
- Task 1 to many Attachment
- User 1 to many Comment
- User 1 to many Attachment
- User 1 to many Notification
- User 1 to many ActivityLog
- User 1 to many AuthTokenSession
- User 1 to many EmailVerificationToken
- User 1 to many PasswordResetToken

========================================================================================================================
SECTION 7 - PHYSICAL DATA MODEL (PK/FK + STRUCTURAL FIELDS ONLY)
========================================================================================================================

Table: users
+----------------+---------------------------+----+----------------+------+---------------------+-----------------------------------------------+
| Field          | Type                      | PK | FK             | Null | Default             | Description                                   |
+----------------+---------------------------+----+----------------+------+---------------------+-----------------------------------------------+
| id             | uuid                      | Y  | -              | N    | gen_random_uuid()   | Primary key                                   |
| created_at     | timestamptz               | N  | -              | N    | now()               | Creation timestamp                            |
| updated_at     | timestamptz               | N  | -              | N    | now()               | Last update timestamp                         |
| deleted_at     | timestamptz               | N  | -              | Y    | null                | Soft delete timestamp                         |
| created_by     | uuid                      | N  | users.id       | Y    | null                | Actor who created record                      |
| updated_by     | uuid                      | N  | users.id       | Y    | null                | Actor who last updated record                 |
+----------------+---------------------------+----+----------------+------+---------------------+-----------------------------------------------+

Table: roles
+----------------+---------------------------+----+----------------+------+---------------------+-----------------------------------------------+
| Field          | Type                      | PK | FK             | Null | Default             | Description                                   |
+----------------+---------------------------+----+----------------+------+---------------------+-----------------------------------------------+
| id             | uuid                      | Y  | -              | N    | gen_random_uuid()   | Primary key                                   |
| created_at     | timestamptz               | N  | -              | N    | now()               | Creation timestamp                            |
| updated_at     | timestamptz               | N  | -              | N    | now()               | Last update timestamp                         |
| created_by     | uuid                      | N  | users.id       | Y    | null                | Actor who created record                      |
| updated_by     | uuid                      | N  | users.id       | Y    | null                | Actor who last updated record                 |
+----------------+---------------------------+----+----------------+------+---------------------+-----------------------------------------------+

Table: organizations
+----------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field          | Type                      | PK | FK                | Null | Default             | Description                                   |
+----------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id             | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| owner_user_id  | uuid                      | N  | users.id          | N    | -                   | Organization owner                            |
| created_at     | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at     | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| deleted_at     | timestamptz               | N  | -                 | Y    | null                | Soft delete timestamp                         |
| created_by     | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by     | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+----------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: organization_memberships
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| organization_id     | uuid                      | N  | organizations.id  | N    | -                   | Parent organization                           |
| user_id             | uuid                      | N  | users.id          | N    | -                   | Member user                                   |
| role_id             | uuid                      | N  | roles.id          | N    | -                   | Assigned role                                 |
| invited_by_user_id  | uuid                      | N  | users.id          | Y    | null                | Inviter                                       |
| joined_at           | timestamptz               | N  | -                 | Y    | null                | Membership join timestamp                     |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: organization_invites
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| organization_id     | uuid                      | N  | organizations.id  | N    | -                   | Parent organization                           |
| role_id             | uuid                      | N  | roles.id          | N    | -                   | Role to assign on acceptance                  |
| invited_by_user_id  | uuid                      | N  | users.id          | N    | -                   | Inviter                                       |
| accepted_at         | timestamptz               | N  | -                 | Y    | null                | Accepted timestamp                            |
| revoked_at          | timestamptz               | N  | -                 | Y    | null                | Revoked timestamp                             |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: projects
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| organization_id     | uuid                      | N  | organizations.id  | N    | -                   | Parent organization                           |
| created_by_user_id  | uuid                      | N  | users.id          | N    | -                   | Project creator                               |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| deleted_at          | timestamptz               | N  | -                 | Y    | null                | Soft delete timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: project_members
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| project_id          | uuid                      | N  | projects.id       | N    | -                   | Parent project                                |
| user_id             | uuid                      | N  | users.id          | N    | -                   | Member user                                   |
| added_by_user_id    | uuid                      | N  | users.id          | Y    | null                | Actor that added member                       |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: tasks
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| project_id          | uuid                      | N  | projects.id       | N    | -                   | Parent project                                |
| assignee_user_id    | uuid                      | N  | users.id          | Y    | null                | Assigned user                                 |
| created_by_user_id  | uuid                      | N  | users.id          | N    | -                   | Task creator                                  |
| completed_at        | timestamptz               | N  | -                 | Y    | null                | Task completion timestamp                     |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| deleted_at          | timestamptz               | N  | -                 | Y    | null                | Soft delete timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: comments
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| task_id             | uuid                      | N  | tasks.id          | N    | -                   | Parent task                                   |
| author_user_id      | uuid                      | N  | users.id          | N    | -                   | Comment author                                |
| parent_comment_id   | uuid                      | N  | comments.id       | Y    | null                | Parent comment for reply threading            |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| deleted_at          | timestamptz               | N  | -                 | Y    | null                | Soft delete timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: attachments
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| task_id             | uuid                      | N  | tasks.id          | N    | -                   | Parent task                                   |
| uploaded_by_user_id | uuid                      | N  | users.id          | N    | -                   | Uploader                                      |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| deleted_at          | timestamptz               | N  | -                 | Y    | null                | Soft delete timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: notifications
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| recipient_user_id   | uuid                      | N  | users.id          | N    | -                   | Notification recipient                        |
| organization_id     | uuid                      | N  | organizations.id  | N    | -                   | Organization context                          |
| read_at             | timestamptz               | N  | -                 | Y    | null                | Read timestamp                                |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: activity_logs
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| organization_id     | uuid                      | N  | organizations.id  | N    | -                   | Organization context                          |
| actor_user_id       | uuid                      | N  | users.id          | N    | -                   | Action actor                                  |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Event timestamp                               |
| request_id          | varchar(64)               | N  | -                 | N    | -                   | Correlation identifier                        |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: auth_token_sessions
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| user_id             | uuid                      | N  | users.id          | N    | -                   | Session owner                                 |
| issued_at           | timestamptz               | N  | -                 | N    | now()               | Token issued time                             |
| expires_at          | timestamptz               | N  | -                 | N    | -                   | Token expiry time                             |
| revoked_at          | timestamptz               | N  | -                 | Y    | null                | Revocation timestamp                          |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: email_verification_tokens
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| user_id             | uuid                      | N  | users.id          | N    | -                   | Token owner                                   |
| expires_at          | timestamptz               | N  | -                 | N    | -                   | Token expiry                                  |
| used_at             | timestamptz               | N  | -                 | Y    | null                | Token consumed time                           |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

Table: password_reset_tokens
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| Field               | Type                      | PK | FK                | Null | Default             | Description                                   |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+
| id                  | uuid                      | Y  | -                 | N    | gen_random_uuid()   | Primary key                                   |
| user_id             | uuid                      | N  | users.id          | N    | -                   | Token owner                                   |
| expires_at          | timestamptz               | N  | -                 | N    | -                   | Token expiry                                  |
| used_at             | timestamptz               | N  | -                 | Y    | null                | Token consumed time                           |
| created_at          | timestamptz               | N  | -                 | N    | now()               | Creation timestamp                            |
| updated_at          | timestamptz               | N  | -                 | N    | now()               | Last update timestamp                         |
| created_by          | uuid                      | N  | users.id          | Y    | null                | Actor who created record                      |
| updated_by          | uuid                      | N  | users.id          | Y    | null                | Actor who last updated record                 |
+---------------------+---------------------------+----+-------------------+------+---------------------+-----------------------------------------------+

========================================================================================================================
SECTION 8 - NORMALIZATION
========================================================================================================================

+-------------------------+-----------------------------------------------------------------------------------------------------------+
| Normal Form             | Compliance Summary                                                                                        |
+-------------------------+-----------------------------------------------------------------------------------------------------------+
| 1NF                     | Atomic columns, no repeating groups                                                                       |
| 2NF                     | Non-key attributes fully dependent on primary key in each table                                           |
| 3NF                     | Transitive dependencies minimized through role, membership, invite, and junction entity separation        |
| M:N Resolution          | organization_memberships resolves users to organizations; project_members resolves users to projects      |
| Referential Integrity   | All ownership and association links enforced via foreign keys                                              |
| Update Anomalies        | Reduced through decomposition into normalized entities                                                     |
+-------------------------+-----------------------------------------------------------------------------------------------------------+

========================================================================================================================
SECTION 9 - INDEX STRATEGY
========================================================================================================================

9.1 B-tree indexes
- Primary key indexes on all id columns
- Foreign key indexes on all FK columns
- B-tree on activity_logs (organization_id, created_at desc)
- B-tree on notifications (recipient_user_id, created_at desc)
- B-tree on tasks (project_id, created_at desc)

9.2 Composite indexes
- organization_memberships (organization_id, user_id) unique
- project_members (project_id, user_id) unique
- organization_invites (organization_id, invited_by_user_id, created_at desc)
- projects (organization_id, created_at desc)
- tasks (project_id, assignee_user_id, created_at desc)
- comments (task_id, parent_comment_id, created_at asc)

9.3 GIN indexes (PostgreSQL FTS and JSON)
- GIN on notifications payload_json for containment queries
- GIN tsvector index for searchable text fields in tasks and comments where full-text search is required

9.4 Azure-aligned partitioning guidance
- Range partition activity_logs by created_at monthly
- Range partition notifications by created_at monthly with retention-based pruning
- Optional hash sub-partition by organization_id for high-scale tenants

9.5 Operational reliability
- Autovacuum tuning per high-write table
- REINDEX/maintenance windows for large partitions
- PITR enabled using WAL archiving

========================================================================================================================
SECTION 10 - PROFESSIONAL ER DIAGRAM (ASCII, CROW'S FOOT STYLE)
========================================================================================================================

Legend
- PK = Primary Key
- FK = Foreign Key
- 1-----< = one to many

+---------------------------+         +---------------------------+
| users                     |         | roles                     |
|---------------------------|         |---------------------------|
| PK id                     |         | PK id                     |
+---------------------------+         +---------------------------+
         | 1-----<                          | 1-----<
         |                                  |
         v                                  v
+---------------------------+         +---------------------------+
| organization_memberships  |         | organization_memberships  |
|---------------------------|         |---------------------------|
| PK id                     |         | PK id                     |
| FK organization_id        |         | FK role_id                |
| FK user_id                |         +---------------------------+
| FK role_id                |
| FK invited_by_user_id     |
+---------------------------+
         ^
         | 1-----<
+---------------------------+
| organizations             |
|---------------------------|
| PK id                     |
| FK owner_user_id          |
+---------------------------+
         | 1-----<
         v
+---------------------------+         +---------------------------+
| projects                  |         | organization_invites      |
|---------------------------|         |---------------------------|
| PK id                     |         | PK id                     |
| FK organization_id        |<-----1  | FK organization_id        |
| FK created_by_user_id     |         | FK role_id                |
+---------------------------+         | FK invited_by_user_id     |
         | 1-----<                    +---------------------------+
         v
+---------------------------+         +---------------------------+
| tasks                     |         | project_members           |
|---------------------------|         |---------------------------|
| PK id                     |         | PK id                     |
| FK project_id             | 1-----> | FK project_id             |
| FK assignee_user_id       |         | FK user_id                |
| FK created_by_user_id     |         | FK added_by_user_id       |
+---------------------------+         +---------------------------+
         | 1-----<
         |                    +---------------------------+
         +------------------->| comments                  |
         |                    |---------------------------|
         |                    | PK id                     |
         |                    | FK task_id                |
         |                    | FK author_user_id         |
         |                    | FK parent_comment_id      |
         |                    +---------------------------+
         | 1-----<
         v
+---------------------------+
| attachments               |
|---------------------------|
| PK id                     |
| FK task_id                |
| FK uploaded_by_user_id    |
+---------------------------+

+---------------------------+         +---------------------------+
| notifications             |         | activity_logs             |
|---------------------------|         |---------------------------|
| PK id                     |         | PK id                     |
| FK recipient_user_id      |         | FK organization_id        |
| FK organization_id        |         | FK actor_user_id          |
+---------------------------+         +---------------------------+
         ^ 1-----<                         ^ 1-----<
         |                                 |
+---------------------------+         +---------------------------+
| users                     |         | organizations             |
| PK id                     |         | PK id                     |
+---------------------------+         +---------------------------+

+---------------------------+
| auth_token_sessions       |
|---------------------------|
| PK id                     |
| FK user_id                |
+---------------------------+
          ^
          | 1-----<
+---------------------------+
| email_verification_tokens |
|---------------------------|
| PK id                     |
| FK user_id                |
+---------------------------+
          ^
          | 1-----<
+---------------------------+
| password_reset_tokens     |
|---------------------------|
| PK id                     |
| FK user_id                |
+---------------------------+

========================================================================================================================
END OF DATABASE DESIGN DOCUMENT
========================================================================================================================
