# Tasks: F3 — Post-Mortem & Employee Reporting

**Feature:** [requirements.md](requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: PostMortem entity in entities.py | S | Domain |
| 2 | Application: CreatePostMortemCommand + handler | S | App |
| 3 | Application: UpdatePostMortemCommand + handler | S | App |
| 4 | Application: GetPostMortemQuery + handler | S | App |
| 5 | Application: ReportIncidentCommand + handler (employee) | S | App |
| 6 | Application: ListMyIncidentsQuery + handler | S | App |
| 7 | HTTP: schemas (PostMortem request/response, employee request/response) | S | HTTP |
| 8 | HTTP: 3 post-mortem endpoints on incidents router | M | HTTP |
| 9 | HTTP: 2 employee endpoints on my router | M | HTTP |
| 10 | Enrich IncidentDetailDto.postmortem with typed PostMortemDto | S | App |
| 11 | Unit tests: post-mortem and employee reporting command/query handlers | M | Test |
| 12 | Integration tests: post-mortem and employee reporting endpoints | M | Test |
| 13 | Frontend: post-mortem section on incident detail page | M | FE |
| 14 | Frontend: employee report incident form + my incidents page | M | FE |
| 15 | i18n: EN/ES translations | S | FE |

## Detailed Tasks

### Phase 1: Domain Layer

#### Task 1: PostMortem entity
- **File:** `src/incident_bc/incident/domain/entities.py`
- **What:** Add `PostMortem` dataclass with id, incident_id, root_cause, lessons_learned, corrective_actions, created_by, created_at, updated_at. Add `create()` factory method that validates required fields.
- **Acceptance:** Entity created with proper validation
- [x] Done

### Phase 2: Application Layer

#### Task 2: CreatePostMortemCommand + handler
- **File:** `src/incident_bc/incident/application/commands/create_postmortem.py`
- **What:** Command(incident_id, company_id, root_cause, lessons_learned, corrective_actions, actor_id). Handler: validates incident exists + status is recovered/closed (raises IncidentNotClosableForPostMortemError), checks no existing postmortem (raises PostMortemAlreadyExistsError), creates PostMortem entity, calls repo.save_postmortem(dict), creates POSTMORTEM_CREATED timeline entry.
- **Deps:** Task 1
- **Acceptance:** Post-mortem created, timeline entry created, proper error handling
- [x] Done

#### Task 3: UpdatePostMortemCommand + handler
- **File:** `src/incident_bc/incident/application/commands/update_postmortem.py`
- **What:** Command(incident_id, company_id, root_cause?, lessons_learned?, corrective_actions?, actor_id). Handler: validates incident exists, loads existing postmortem (raises PostMortemNotFoundError), updates fields, calls repo.save_postmortem(dict), creates POSTMORTEM_UPDATED timeline entry.
- **Acceptance:** Post-mortem updated, timeline entry created
- [x] Done

#### Task 4: GetPostMortemQuery + handler
- **File:** `src/incident_bc/incident/application/queries/get_postmortem.py`
- **What:** Query(incident_id, company_id). Handler: validates incident exists, loads postmortem via repo, enriches created_by with user name. Returns PostMortemDto.
- **Acceptance:** Returns typed DTO with creator name
- [x] Done

#### Task 5: ReportIncidentCommand + handler (employee)
- **File:** `src/incident_bc/incident/application/commands/report_incident_employee.py`
- **What:** Command(company_id, title, description, incident_type, reported_by). Handler: creates SecurityIncident with default severity P3, status=detected, detected_at=now(). Creates timeline entry. Creates 3 NIS2 regulatory reports. Publishes employee_reported notification event.
- **Acceptance:** Incident created with defaults, notifications sent to admins+technicians
- [x] Done

#### Task 6: ListMyIncidentsQuery + handler
- **File:** `src/incident_bc/incident/application/queries/list_my_incidents.py`
- **What:** Query(user_id, company_id). Handler: calls repo.find_my_incidents(), maps to MyIncidentDto (id, title, incident_type, severity, status, created_at — no sensitive fields).
- **Acceptance:** Returns restricted DTOs without attack_vector, data_breach_scope, timeline
- [x] Done

### Phase 3: HTTP Layer

#### Task 7: Schemas
- **File:** `adapters/http/api/incidents/schemas.py` and `adapters/http/api/my/schemas.py`
- **What:** Add CreatePostMortemRequest(root_cause, lessons_learned, corrective_actions), UpdatePostMortemRequest(root_cause?, lessons_learned?, corrective_actions?), PostMortemResponse(id, root_cause, lessons_learned, corrective_actions, created_by_name?, created_at?, updated_at?) to incidents schemas. Add ReportIncidentRequest(title, description, incident_type), MyIncidentResponse(id, title, incident_type, severity, status, created_at) to my schemas.
- **Acceptance:** All schemas defined with proper validation
- [x] Done

#### Task 8: Post-mortem endpoints on incidents router
- **File:** `adapters/http/api/incidents/routers.py`
- **What:** POST `/{id}/post-mortem` (admin only, create), GET `/{id}/post-mortem` (technician+, get), PUT `/{id}/post-mortem` (admin only, update). Proper error handling: 409 duplicate, 404 not found, 422 wrong status. Update _detail_to_response to map typed PostMortemDto to PostMortemResponse.
- **Deps:** Tasks 2-4, 7
- **Acceptance:** All 3 endpoints work, error codes correct
- [x] Done

#### Task 9: Employee endpoints on my router
- **File:** `adapters/http/api/my/routers.py`
- **What:** POST `/api/v1/my/report-incident` (all roles, create simplified incident), GET `/api/v1/my/incidents` (all roles, list own incidents). Add incident_repo dependency. Add event_bus for notifications.
- **Deps:** Tasks 5-6, 7
- **Acceptance:** Employee can report and list own incidents
- [x] Done

### Phase 4: Enrich Detail

#### Task 10: Enrich IncidentDetailDto.postmortem with typed PostMortemDto
- **File:** `src/incident_bc/incident/application/queries/get_incident_detail.py`
- **What:** Add PostMortemDto dataclass. Change IncidentDetailDto.postmortem from Optional[dict] to Optional[PostMortemDto]. Enrich with user name lookup for created_by. Update _detail_to_response in routers.py to map PostMortemDto → PostMortemResponse.
- **Acceptance:** Incident detail returns typed postmortem with creator name
- [x] Done

### Phase 5: Tests

#### Task 11: Unit tests — post-mortem and employee reporting handlers
- **Files:** `tests/unit/incident_bc/incident/application/commands/test_create_postmortem.py`, `tests/unit/incident_bc/incident/application/commands/test_report_incident_employee.py`
- **What:** Test create postmortem: happy path, incident not found, wrong status, duplicate. Test update postmortem: happy path, not found. Test report incident: happy path, default severity P3. Test list my incidents: returns restricted fields.
- **Acceptance:** All tests pass
- [x] Done

#### Task 12: Integration tests — post-mortem and employee reporting endpoints
- **File:** `tests/integration/test_incidents_endpoints.py`
- **What:** Test create postmortem (201), precondition wrong status (422), duplicate (409). Test get postmortem (200). Test update postmortem (200). Test employee report incident (201). Test employee list my incidents (200, restricted fields). Test postmortem appears in incident detail.
- **Acceptance:** All tests pass with real DB
- [x] Done

### Phase 6: Frontend

#### Task 13: Post-mortem section on incident detail page
- **File:** `web/app/src/pages/technician/IncidentDetail.tsx`
- **What:** Add PostMortem section visible when incident status is recovered/closed. Show existing post-mortem with root_cause, lessons_learned, corrective_actions, created_by_name, timestamps. Add create form (admin only) if no postmortem exists. Add inline edit capability (admin only) for existing postmortem. Update TypeScript types.
- **Acceptance:** Section renders, create/edit works, proper loading states
- [x] Done

#### Task 14: Employee report incident form + my incidents page
- **Files:** `web/app/src/pages/employee/ReportIncident.tsx` (NEW), `web/app/src/pages/employee/MyIncidents.tsx` (NEW), `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Report form: title, description, incident_type dropdown. My incidents: simple list with status badges. Add routes and sidebar entries under "My Activity".
- **Acceptance:** Employee can report and view incidents
- [x] Done

#### Task 15: i18n translations
- **File:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Translation keys for post-mortem section, employee reporting form, my incidents page, toast messages, timeline events.
- **Acceptance:** UI renders correctly in EN and ES
- [x] Done
