# Tasks: F1 — Maintenance Lifecycle

**Requirement:** [../../requirements.md](../../requirements.md)
**Created:** 2026-02-18

## Tasks

- [x] Implement lifecycle commands (create, assign, start, complete, cancel, skip, update)
- [x] Implement lifecycle queries (get, list, dashboard, my queue)
- [x] Add maintenance HTTP endpoints under `/api/v1/maintenance`
- [x] Add `/api/v1/my/maintenance` endpoint
- [x] Add `/api/v1/dashboard/maintenance` endpoint
- [x] Add maintenance notification event types
- [x] Add maintenance event factory and target resolver support
- [x] Add Celery maintenance tasks (reminders, overdue, recurring stub)
- [x] Add unit tests for commands, queries, tasks, and notification resolver updates
- [x] Add integration tests for maintenance endpoints
- [x] Run targeted unit + integration test suites
