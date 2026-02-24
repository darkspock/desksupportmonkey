# Feature F0: Incident Foundation

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 0
**Dependencies:** None
**Complexity:** L

## Scope

### Included
- New bounded context `incident_bc` with DDD + CQRS structure
- SecurityIncident entity (aggregate root) with full state machine
- IncidentTimeline entity (append-only event log)
- All domain enums: IncidentType, IncidentSeverity, IncidentStatus, TimelineEventType
- Repository interfaces + SQLAlchemy implementations
- ORM models for ALL E36 tables (security_incidents, incident_assets, incident_vendors, regulatory_reports, incident_timeline, post_mortems)
- Alembic migration creating all tables
- Core CRUD API endpoints: create, list (paginated/filterable), get detail, update
- Status change endpoint with state machine validation
- Severity change endpoint
- Assignment endpoint
- Close with mandatory `close_reason` for early closure
- Notifications: incident created, status changed, severity changed, assignment
- Frontend: "Security" section in sidebar navigation
- Frontend: incidents list page with filters (status, severity, type, date range)
- Frontend: incident detail page with timeline
- Frontend: create incident form
- i18n: EN/ES translations for all new UI

### Excluded (in other features)
- Regulatory reports and countdown timers (F1)
- Asset and vendor linking (F2)
- Post-mortem creation (F3)
- Employee simplified reporting (F3)
- Incident dashboard with analytics (F4)

## User Value

When this feature is complete, IT managers and technicians can:
- Create security incidents with mandatory classification (type, severity, detected_at)
- Track incidents through a 6-stage lifecycle (detected → triaged → contained → eradicated → recovered → closed)
- View a filterable list of all incidents
- See a complete audit trail (timeline) of every action taken on an incident
- Receive notifications for incident events
- Close incidents as false alarms with mandatory justification

## Acceptance Criteria

- [ ] New BC at `src/incident_bc/incident/` with domain, application, infrastructure layers
- [ ] SecurityIncident entity with factory method `create()` and state machine methods
- [ ] State transitions enforced: detected→triaged→contained→eradicated→recovered→closed + any→closed
- [ ] `close_reason` mandatory when closing from any state except recovered→closed
- [ ] IncidentTimeline records every state change, severity change, and assignment
- [ ] No delete endpoints — incidents are never deletable
- [ ] Alembic migration creates all 6 tables (security_incidents, incident_assets, incident_vendors, regulatory_reports, incident_timeline, post_mortems)
- [ ] POST `/api/v1/incidents` creates incident in `detected` status
- [ ] GET `/api/v1/incidents` returns paginated list with filters (status, severity, type, search, date range)
- [ ] GET `/api/v1/incidents/{id}` returns incident detail with timeline entries
- [ ] PUT `/api/v1/incidents/{id}` updates editable fields
- [ ] POST `/api/v1/incidents/{id}/status` changes status with validation
- [ ] POST `/api/v1/incidents/{id}/severity` changes severity
- [ ] POST `/api/v1/incidents/{id}/assign` assigns incident to user
- [ ] All endpoints require technician or admin role (assign is admin-only)
- [ ] Notifications sent for: creation, status change, severity change, assignment
- [ ] Frontend: "Security" section visible in sidebar for technician/admin roles
- [ ] Frontend: incidents list page with status, severity, type filters
- [ ] Frontend: incident detail page showing all fields + timeline
- [ ] Frontend: create incident modal/form
- [ ] i18n: all new strings in EN and ES
- [ ] Unit tests for all command/query handlers
- [ ] Integration tests for all API endpoints

## Technical Scope

### Entities (owned by this feature)
- `SecurityIncident` — aggregate root with state machine
- `IncidentTimeline` — append-only event log

### ORM Models (created by this feature, used by all)
- `SecurityIncidentModel` — maps to `security_incidents` table
- `IncidentTimelineModel` — maps to `incident_timeline` table
- `IncidentAssetModel` — maps to `incident_assets` table (table created, logic in F2)
- `IncidentVendorModel` — maps to `incident_vendors` table (table created, logic in F2)
- `RegulatoryReportModel` — maps to `regulatory_reports` table (table created, logic in F1)
- `PostMortemModel` — maps to `post_mortems` table (table created, logic in F3)

### Key Components
- `src/incident_bc/incident/domain/entities.py` — SecurityIncident, IncidentTimeline
- `src/incident_bc/incident/domain/enums.py` — IncidentType, IncidentSeverity, IncidentStatus, TimelineEventType
- `src/incident_bc/incident/domain/repository.py` — IncidentRepositoryInterface
- `src/incident_bc/incident/application/commands/` — create, update, change_status, change_severity, assign
- `src/incident_bc/incident/application/queries/` — list, get_detail
- `src/incident_bc/incident/application/services/` — IncidentEventFactory
- `src/incident_bc/incident/infrastructure/models.py` — all ORM models
- `src/incident_bc/incident/infrastructure/repository.py` — SQLAlchemy implementation
- `adapters/http/api/incidents/` — routers, schemas, dependencies
- `alembic/versions/xxx_create_incident_tables.py` — migration

## Notes

- The migration creates ALL tables for the entire epic (F0-F4) to avoid multiple migrations touching the same schema area.
- Notification integration reuses the existing `EventBus` + `NotificationSubscriber` pattern from `notification_bc`.
- New `EventType` enum values must be added to `src/notification_bc/notification/domain/enums.py`.
- New `IncidentEventFactory` follows the pattern of `RequestEventFactory`.
- Sidebar navigation adds a new "Security" top-level section (not under Management).
