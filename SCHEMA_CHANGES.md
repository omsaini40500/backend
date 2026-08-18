# Schema Changes — Backend ↔ Frontend Integration

## A1. CamelCase Serialization
- Added `app/schemas/base.py` with `CamelModel` using `alias_generator=to_camel`
- All `*Out` schemas inherit from `CamelModel`
- Global serialization uses aliases (`response_model_by_alias=True` via Pydantic config)

## A2. Task Extensions
- New `checklist_items` table: `id`, `task_id`, `text`, `done`
- New `task_watchers` association table
- `Task.assigned_by` column (set from current user at creation)
- `TaskOut` exposes: `tags`, `checklist`, `comments` (count), `attachments` (count), `watchers`, `assignedTo`, `assignedBy`, `projectId`, `departmentId`
- `attachments` count is real (from `attachments` table) but file storage is stubbed — upload endpoint returns URL only

## A3. Project Extensions
- New `project_team_members` association table
- `ProjectOut` exposes: `team` (List[userId]), `tasks` (COUNT), `completedTasks` (COUNT filtered by status=done)
- `category` and `color` confirmed as real columns on `Project` model

## A4. User Extensions
- `avatar` computed from name initials via `@computed_field`
- `status` computed from `is_active` via `@computed_field`
- `joinedAt` aliases `created_at`
- `lastActive` aliases new `last_active_at` timestamp column (updated on login + token refresh)
- `tasksCompleted` / `tasksTotal` computed via COUNT on Task through assignee association

## A5. Notification & ActivityLog
- `NotificationOut`: `createdAt` is ISO timestamp from `created_at`
- `ActivityLogOut`: `user` is resolved display name (`user_name` column)
- `ip` / `browser` captured from request in `app/services/audit.py`
- `location` stubbed as `"Unknown"` — flagged for GeoIP service

## A6. ID vs. Name Resolution Decision
**Rule:** All cross-entity references in list/detail endpoints return raw IDs, not resolved display names.
- `TaskOut`: `projectId`, `departmentId` are IDs
- `ProjectOut`: `clientId`, `managerId` are IDs
- `UserOut`: `departmentId`, `teamId` are IDs

**Rationale:** Avoids expensive N+1 joins on every list endpoint. Frontend fetches `/departments`, `/teams`, `/projects`, `/clients` once and caches them in lookup maps for name resolution.

**Frontend resolution happens in `src/api/*.ts` modules, not components.**

## A7. Migrations
- Alembic initialized at `alembic/`
- Migrations generated per logical group (Task, Project, User, ActivityLog extensions)
- Run against local SQLite dev DB; seed logic confirmed working

## A8. Stubbed / Future Work
- `attachments` count is real but file storage is minimal (filename/url only, no S3 integration)
- `location` in activity logs is `"Unknown"` pending GeoIP service
- Not built in this pass: Campaigns, Meetings, Announcements, Workflow Automation, System Monitoring, AI Assistant, Import/Export, Calendar, Reports
  - These need explicit go-ahead before migrations are generated
