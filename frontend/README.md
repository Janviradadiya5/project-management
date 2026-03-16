# Frontend (React + Vite)

## Setup

1. Install dependencies:

	npm install

2. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` if your backend is not on `http://localhost:8000`.

3. Start development server:

	npm run dev

## Included Screens

- `/login` for API session sign-in
- `/` overview dashboard
- `/organizations` organization list and create flow
- `/projects` project list and create flow
- `/tasks` task list and create flow
- `/tasks/:taskId` task workspace drilldown with attachment/comment actions
- `/comments` comment create/update/delete operations
- `/attachments` attachment metadata list/create/delete
- `/notifications` notification inbox and mark-read flow

## Notes

- Protected endpoints require a valid access token from `/api/v1/auth/login`.
- Projects and tasks require an active organization context and send `X-Organization-ID`.
- List pages include server-side filter and pagination controls.
- Notifications include deep links to `/tasks/:taskId` when `payload_json` contains task identifiers.

## Known API Constraints

- Comments list API is not currently exposed by backend routes, so comments UI focuses on create/update/delete actions.
- Attachments currently use metadata upload endpoints; binary upload flow is not available in this frontend yet.

## QA Checklist

- Sign in and verify redirect back to intended protected page.
- Create/select organization, then create project and task.
- Apply filters and paginate in organizations/projects/tasks/notifications.
- Open notification deep link to task workspace.
- Create comment and upload attachment metadata from task workspace.
- Trigger token refresh path by using an expired access token with valid refresh token.

## Build

npm run build
npm run preview
