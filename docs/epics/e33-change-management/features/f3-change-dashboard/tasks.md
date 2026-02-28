# Implementation Tasks: Change Dashboard (F3)

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-28
**Total Tasks:** 9

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Repository Interface | 1 (TASK-001) | S |
| Infrastructure - Repository | 1 (TASK-002) | M |
| Application - Query Handler | 1 (TASK-003) | M |
| HTTP - Schemas | 1 (TASK-004) | S |
| HTTP - Router | 1 (TASK-005) | S |
| Unit Tests | 1 (TASK-006) | M |
| Integration Tests | 1 (TASK-007) | M |
| Frontend | 1 (TASK-008) | M |
| i18n + Navigation | 1 (TASK-009) | S |

---

### TASK-001: Add Dashboard Repository Interface Method

- [x] Add `get_dashboard_data(company_id: str) -> dict` abstract method

### TASK-002: Implement Dashboard Repository Method

- [x] SQL counts by status (all 8)
- [x] SQL counts by type (3)
- [x] Upcoming scheduled (next 30 days, limit 20)
- [x] Recently implemented (last 30 days with PIR outcome, limit 20)
- [x] Rolled back count (last 90 days)
- [x] Scheduled this week count

### TASK-003: Dashboard Query Handler + DTOs

- [x] UpcomingChangeDto, RecentImplementedDto, ChangeDashboardDto
- [x] ChangeDashboardQuery + ChangeDashboardQueryHandler
- [x] User name resolution for assigned_to
- [x] Compute total_open from status counts

### TASK-004: Dashboard Pydantic Schemas

- [x] UpcomingChangeResponse, RecentImplementedResponse, ChangeDashboardResponse

### TASK-005: Dashboard Router Endpoint

- [x] GET /dashboard (admin-only, before /{change_id} routes)
- [x] Map DTO to Pydantic response

### TASK-006: Unit Tests for Dashboard Query Handler

- [x] Happy path with counts and lists
- [x] Empty data returns zeros/empty lists
- [x] User name resolution

### TASK-007: Integration Tests for Dashboard Endpoint

- [x] Admin gets dashboard 200
- [x] Non-admin gets 403
- [x] Dashboard with data returns correct structure

### TASK-008: Frontend Dashboard Page

- [x] ChangeDashboardPage.tsx with stat cards, charts, tables
- [x] Route in router.tsx
- [x] Types in types/index.ts

### TASK-009: i18n Keys + Navigation Entry

- [x] English and Spanish i18n keys
- [x] Nav entry in navSections.ts

---

## Execution Order

**Batch 1:** TASK-001, TASK-009
**Batch 2:** TASK-002
**Batch 3:** TASK-003
**Batch 4:** TASK-004
**Batch 5:** TASK-005
**Batch 6 (Parallel):** TASK-006, TASK-007, TASK-008

## Final Checklist

- [x] All 9 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] TypeScript compiles (`npx tsc --noEmit`)
- [x] Progress tracking updated
