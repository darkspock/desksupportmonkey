# Tasks: F0 — Incident Foundation

**Feature:** [requirements.md](requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: enums | S | Domain |
| 2 | Domain: SecurityIncident entity + state machine | M | Domain |
| 3 | Domain: IncidentTimeline entity | S | Domain |
| 4 | Domain: exceptions | S | Domain |
| 5 | Domain: repository interface | M | Domain |
| 6 | Infrastructure: ORM models (all 6 tables) | M | Infra |
| 7 | Infrastructure: Alembic migration | M | Infra |
| 8 | Infrastructure: repository implementation | L | Infra |
| 9 | Application: CreateIncidentCommand + handler | M | App |
| 10 | Application: UpdateIncidentCommand + handler | S | App |
| 11 | Application: ChangeStatusCommand + handler | M | App |
| 12 | Application: ChangeSeverityCommand + handler | S | App |
| 13 | Application: AssignIncidentCommand + handler | S | App |
| 14 | Application: ListIncidentsQuery + handler | M | App |
| 15 | Application: GetIncidentDetailQuery + handler | M | App |
| 16 | Application: IncidentEventFactory + notification integration | M | App |
| 17 | HTTP: schemas (requests + responses) | M | HTTP |
| 18 | HTTP: dependencies | S | HTTP |
| 19 | HTTP: routers (all F0 endpoints) | L | HTTP |
| 20 | HTTP: register router in main app | S | HTTP |
| 21 | Unit tests: domain entities + state machine | M | Test |
| 22 | Unit tests: command handlers | M | Test |
| 23 | Unit tests: query handlers | M | Test |
| 24 | Integration tests: all F0 endpoints | L | Test |
| 25 | Frontend: sidebar Security section + routes | M | FE |
| 26 | Frontend: incidents list page | L | FE |
| 27 | Frontend: incident detail page + timeline | L | FE |
| 28 | Frontend: create incident form | M | FE |
| 29 | i18n: EN/ES translations | S | FE |

## Detailed Tasks

### Phase 1: Domain Layer

#### Task 1: Domain enums
- **File:** `src/incident_bc/__init__.py`, `src/incident_bc/incident/__init__.py`, `src/incident_bc/incident/domain/__init__.py`, `src/incident_bc/incident/domain/enums.py`
- **What:** Create directory structure + IncidentType, IncidentSeverity, IncidentStatus, TimelineEventType enums
- **Acceptance:** All enums importable, values match design doc
- [x] Done

#### Task 2: SecurityIncident entity + state machine
- **File:** `src/incident_bc/incident/domain/entities.py`
- **What:** SecurityIncident dataclass with create() factory, change_status() with VALID_STATUS_TRANSITIONS, change_severity(), assign_to(), update_details(). close_reason mandatory for early closure.
- **Acceptance:** State machine validates all transitions, close_reason enforced, closed incidents reject modifications
- [x] Done

#### Task 3: IncidentTimeline entity
- **File:** `src/incident_bc/incident/domain/entities.py` (same file)
- **What:** IncidentTimeline dataclass with create() factory method
- **Acceptance:** Entity creates with ULID, all fields populated
- [x] Done

#### Task 4: Domain exceptions
- **File:** `src/incident_bc/incident/domain/exceptions.py`
- **What:** All domain exceptions: IncidentNotFoundError, InvalidStatusTransitionError, CloseReasonRequiredError, IncidentClosedError, ReportNotFoundError, ReportNotGeneratedError, PostMortemAlreadyExistsError, PostMortemNotFoundError, IncidentNotClosableForPostMortemError, AssetAlreadyLinkedError, AssetNotLinkedError, VendorAlreadyLinkedError, VendorNotLinkedError
- **Acceptance:** All exceptions importable
- [x] Done

#### Task 5: Repository interface
- **File:** `src/incident_bc/incident/domain/repository.py`
- **What:** IncidentRepositoryInterface(ABC) with all abstract methods per design doc
- **Acceptance:** All methods defined, proper typing
- [x] Done

### Phase 2: Infrastructure Layer

#### Task 6: ORM models
- **File:** `src/incident_bc/incident/infrastructure/__init__.py`, `src/incident_bc/incident/infrastructure/models.py`
- **What:** SecurityIncidentModel, IncidentTimelineModel, IncidentAssetModel, IncidentVendorModel, RegulatoryReportModel, PostMortemModel. All use Mapped[] annotations, ULIDMixin, TimestampMixin. Proper indexes and constraints.
- **Acceptance:** All models follow SQLAlchemy 2.0 style, indexes match design
- [x] Done

#### Task 7: Alembic migration
- **File:** `alembic/versions/xxx_create_incident_tables.py`
- **What:** Create all 6 tables with indexes, FKs, unique constraints
- **Acceptance:** `make db-upgrade` succeeds, all tables created
- [x] Done

#### Task 8: Repository implementation
- **File:** `src/incident_bc/incident/infrastructure/repository.py`
- **What:** IncidentRepository implementing all interface methods. Entity↔model conversion with _to_entity/_to_model helpers.
- **Acceptance:** All CRUD operations work, proper tenant isolation (company_id filtering)
- [x] Done

### Phase 3: Application Layer

#### Task 9: CreateIncidentCommand
- **File:** `src/incident_bc/incident/application/__init__.py`, `src/incident_bc/incident/application/commands/__init__.py`, `src/incident_bc/incident/application/commands/create_incident.py`
- **What:** Command + Handler. Creates SecurityIncident via factory, saves to repo, creates timeline entry "Incident created", publishes incident.created event.
- **Deps:** Tasks 1-5, 8
- **Acceptance:** Incident created in detected status, timeline entry added, notification sent
- [x] Done

#### Task 10: UpdateIncidentCommand
- **File:** `src/incident_bc/incident/application/commands/update_incident.py`
- **What:** Command + Handler. Updates editable fields (title, description, attack_vector, data_breach_scope). Rejects if closed.
- **Acceptance:** Fields updated, timeline entry created, closed incidents rejected
- [x] Done

#### Task 11: ChangeStatusCommand
- **File:** `src/incident_bc/incident/application/commands/change_status.py`
- **What:** Command + Handler. Validates transition via state machine, enforces close_reason, sets closed_at, publishes status_changed event.
- **Acceptance:** Valid transitions succeed, invalid rejected, close_reason enforced for early closure
- [x] Done

#### Task 12: ChangeSeverityCommand
- **File:** `src/incident_bc/incident/application/commands/change_severity.py`
- **What:** Command + Handler. Updates severity, creates timeline entry, publishes severity_changed event.
- **Acceptance:** Severity updated, timeline logged, notification sent
- [x] Done

#### Task 13: AssignIncidentCommand
- **File:** `src/incident_bc/incident/application/commands/assign_incident.py`
- **What:** Command + Handler. Sets assigned_to, creates timeline entry, publishes assigned event.
- **Acceptance:** Assignment updated, timeline logged, notification sent to assigned user
- [x] Done

#### Task 14: ListIncidentsQuery
- **File:** `src/incident_bc/incident/application/queries/__init__.py`, `src/incident_bc/incident/application/queries/list_incidents.py`
- **What:** Query + Handler + IncidentListDto. Paginated list with filters (status, severity, type, search, date range). Returns tuple[list[IncidentListDto], int].
- **Acceptance:** Pagination works, all filters work, tenant isolated
- [x] Done

#### Task 15: GetIncidentDetailQuery
- **File:** `src/incident_bc/incident/application/queries/get_incident_detail.py`
- **What:** Query + Handler + IncidentDetailDto + TimelineEntryDto. Returns full incident with timeline. Resolves user names for reported_by, assigned_to, timeline actors.
- **Acceptance:** All fields populated, timeline sorted by created_at desc, user names resolved
- [x] Done

#### Task 16: IncidentEventFactory + notification integration
- **File:** `src/incident_bc/incident/application/services/__init__.py`, `src/incident_bc/incident/application/services/incident_event_factory.py`
- **Collateral:** `src/notification_bc/notification/domain/enums.py` (add event types), `src/notification_bc/notification/application/services/target_resolver.py` (add routing)
- **What:** IncidentEventFactory with static methods for each event type. Add EventType values to notification BC. Add target resolution rules.
- **Acceptance:** Events published, notifications delivered to correct users
- [x] Done

### Phase 4: HTTP Layer

#### Task 17: Schemas
- **File:** `adapters/http/api/incidents/__init__.py`, `adapters/http/api/incidents/schemas.py`
- **What:** All request/response Pydantic models per design doc
- **Acceptance:** Validation works, all fields present
- [x] Done

#### Task 18: Dependencies
- **File:** `adapters/http/api/incidents/dependencies.py`
- **What:** get_incident_repo(), get_user_repo() dependency providers
- **Acceptance:** Dependencies injectable in router functions
- [x] Done

#### Task 19: Routers (F0 endpoints)
- **File:** `adapters/http/api/incidents/routers.py`
- **What:** POST /incidents, GET /incidents, GET /incidents/{id}, PUT /incidents/{id}, POST /incidents/{id}/status, POST /incidents/{id}/severity, POST /incidents/{id}/assign. All with proper role authorization, error handling.
- **Acceptance:** All endpoints work, domain exceptions caught, proper HTTP status codes
- [x] Done

#### Task 20: Register router
- **File:** `adapters/http/main.py` (or app.py)
- **What:** Include incidents router in main application
- **Acceptance:** Router accessible at /api/v1/incidents
- [x] Done

### Phase 5: Tests

#### Task 21: Unit tests — domain entities
- **File:** `tests/unit/incident_bc/__init__.py`, `tests/unit/incident_bc/incident/__init__.py`, `tests/unit/incident_bc/incident/domain/__init__.py`, `tests/unit/incident_bc/incident/domain/test_security_incident.py`
- **What:** Test create(), all state transitions (valid + invalid), close_reason enforcement, closed incident rejection
- **Acceptance:** All tests pass, full state machine coverage
- [x] Done

#### Task 22: Unit tests — command handlers
- **File:** `tests/unit/incident_bc/incident/application/commands/test_*.py`
- **What:** Test each command handler with mocked repos
- **Acceptance:** All handlers tested, edge cases covered
- [x] Done

#### Task 23: Unit tests — query handlers
- **File:** `tests/unit/incident_bc/incident/application/queries/test_*.py`
- **What:** Test list and detail query handlers
- **Acceptance:** All queries tested, pagination, filters
- [x] Done

#### Task 24: Integration tests
- **File:** `tests/integration/test_incidents_endpoints.py`
- **What:** Full HTTP tests for all F0 endpoints. Test CRUD, state machine, authorization.
- **Acceptance:** All tests pass with real DB
- [x] Done

### Phase 6: Frontend

#### Task 25: Sidebar + routes
- **File:** `web/app/src/components/layout/Sidebar.tsx`, `web/app/src/router.tsx`
- **What:** Add "Security" section to sidebar with Incidents link. Add React Router routes for list, detail, and create.
- **Acceptance:** Nav visible for technician/admin, routes work
- [x] Done

#### Task 26: Incidents list page
- **File:** `web/app/src/pages/technician/IncidentsList.tsx`
- **What:** Paginated table with status/severity/type/search filters. Severity and status badges. Link to detail.
- **Acceptance:** List loads, filters work, pagination works
- [x] Done

#### Task 27: Incident detail page + timeline
- **File:** `web/app/src/pages/technician/IncidentDetail.tsx`
- **What:** Full detail view with all fields. Timeline section showing chronological events. Status transition buttons. Severity change. Assignment.
- **Acceptance:** All fields displayed, timeline renders, status buttons work
- [x] Done

#### Task 28: Create incident form
- **File:** `web/app/src/pages/technician/CreateIncidentPage.tsx`
- **What:** Form with title, description, incident_type, severity, detected_at (mandatory). Optional: attack_vector, data_breach_scope.
- **Acceptance:** Validation works, creates incident, redirects to detail
- [x] Done

#### Task 29: i18n translations
- **File:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** All new translation keys for incidents section
- **Acceptance:** UI renders correctly in both EN and ES
- [x] Done
