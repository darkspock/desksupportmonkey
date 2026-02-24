# Tasks: F4 — Incident Dashboard

**Feature:** [requirements.md](requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Application: GetDashboardQuery + handler with DashboardDto | M | App |
| 2 | Repository: add MTTC calculation + upcoming deadlines to get_dashboard_stats | M | Infra |
| 3 | HTTP: DashboardResponse schema + GET /incidents/dashboard endpoint | S | HTTP |
| 4 | Unit tests: dashboard query handler | S | Test |
| 5 | Integration tests: dashboard endpoint | M | Test |
| 6 | Frontend: TypeScript types for IncidentDashboard | S | FE |
| 7 | Frontend: IncidentDashboardPage with stat cards, charts, deadlines, recent incidents | L | FE |
| 8 | Frontend: route + sidebar entry | S | FE |
| 9 | i18n: EN/ES translations for dashboard | S | FE |

## Detailed Tasks

### Phase 1: Application + Infrastructure

#### Task 1: GetDashboardQuery + handler
- **File:** `src/incident_bc/incident/application/queries/get_dashboard.py`
- **What:** GetDashboardQuery(company_id). Handler calls repo.get_dashboard_stats(), maps dict to DashboardDto with UpcomingDeadlineDto and IncidentListDto sub-DTOs. DashboardDto: total_active, total_closed, active_by_severity, by_type, mttc_hours, mttr_hours, upcoming_deadlines, recent_incidents.
- **Acceptance:** Returns typed DashboardDto with all fields
- [x] Done

#### Task 2: Repository MTTC + upcoming deadlines
- **File:** `src/incident_bc/incident/infrastructure/repository.py`
- **What:** Add MTTC calculation (average time from detected_at to earliest status_change timeline entry with new_status=contained). Add upcoming_deadlines query (regulatory reports due in next 7 days, joined with incidents for title). Add company_id filter for deadline query. Return in get_dashboard_stats dict.
- **Deps:** Task 1
- **Acceptance:** mttc_hours computed from timeline, upcoming_deadlines returned
- [x] Done

### Phase 2: HTTP Layer

#### Task 3: DashboardResponse schema + endpoint
- **File:** `adapters/http/api/incidents/schemas.py`, `adapters/http/api/incidents/routers.py`
- **What:** Add DashboardResponse, UpcomingDeadlineResponse, RecentIncidentResponse schemas. Add GET `/incidents/dashboard` endpoint (technician+). Map DashboardDto to DashboardResponse.
- **Deps:** Task 1
- **Acceptance:** Endpoint returns structured dashboard data
- [x] Done

### Phase 3: Tests

#### Task 4: Unit tests
- **File:** `tests/unit/incident_bc/incident/application/queries/test_get_dashboard.py`
- **What:** Test handler maps repo dict to DashboardDto correctly. Test with empty data. Test recent_incidents mapping.
- **Acceptance:** All tests pass
- [x] Done

#### Task 5: Integration tests
- **File:** `tests/integration/test_incidents_endpoints.py`
- **What:** Test GET /incidents/dashboard returns 200. Test active/closed counts. Test by_type and active_by_severity. Test recent_incidents. Test requires technician+ role.
- **Acceptance:** All tests pass with real DB
- [x] Done

### Phase 4: Frontend

#### Task 6: TypeScript types
- **File:** `web/app/src/types/index.ts`
- **What:** Add IncidentDashboard, UpcomingDeadline, RecentIncident interfaces.
- [x] Done

#### Task 7: IncidentDashboardPage
- **File:** `web/app/src/pages/technician/IncidentDashboardPage.tsx` (NEW)
- **What:** Stat cards for total_active, total_closed, MTTC, MTTR. Severity distribution cards (P1/P2/P3/P4). Type distribution bar chart (recharts). Upcoming deadlines list with countdown. Recent incidents table with links.
- **Acceptance:** Full dashboard renders with charts and data
- [x] Done

#### Task 8: Route + sidebar entry
- **File:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Add route `/incidents/dashboard`. Add sidebar entry under Security section.
- [x] Done

#### Task 9: i18n translations
- **File:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** All dashboard labels, stat card titles, section headers.
- [x] Done
