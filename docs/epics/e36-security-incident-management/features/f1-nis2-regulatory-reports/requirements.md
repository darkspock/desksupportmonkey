# Feature F1: NIS2 Regulatory Reports

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** F0 (Incident Foundation)
**Complexity:** L

## Scope

### Included
- RegulatoryReport entity with state machine (pending → generated → submitted)
- Auto-creation of 3 regulatory reports on incident creation (24h, 72h, 30d deadlines)
- Countdown timer data included in incident detail API response
- PDF report generation using existing Celery + WeasyPrint + S3 infrastructure
- Report download endpoint (signed S3 URL)
- Report regeneration (replaces previous PDF, logs in timeline)
- Mark as submitted workflow
- Celery beat periodic task for deadline monitoring
- Escalation notifications at 75% and 90% of elapsed time
- Critical alert when deadline passes without submission
- Frontend: regulatory reports section on incident detail page
- Frontend: countdown timers for each deadline
- Frontend: generate/regenerate/download/submit buttons
- i18n: EN/ES for regulatory report UI

### Excluded (in other features)
- Incident CRUD and lifecycle (F0)
- Asset/vendor linking (F2)
- Post-mortem (F3)
- Dashboard (F4)

## User Value

When this feature is complete, IT managers can:
- See NIS2 countdown timers (24h, 72h, 30d) from the moment an incident is detected
- Generate pre-filled regulatory PDF reports with one click
- Regenerate reports when incident data changes
- Download PDFs for CSIRT submission
- Mark reports as submitted for compliance tracking
- Receive automatic escalation alerts before deadlines expire

## Acceptance Criteria

- [ ] RegulatoryReport entity with state machine (pending → generated → submitted)
- [ ] When incident is created, 3 RegulatoryReport records auto-created with calculated deadlines
- [ ] Deadlines calculated from `detected_at`: +24h, +72h, +30d
- [ ] GET `/api/v1/incidents/{id}` response includes regulatory reports with deadline countdowns
- [ ] GET `/api/v1/incidents/{id}/reports` lists all regulatory reports for an incident
- [ ] POST `/api/v1/incidents/{id}/reports/{report_id}/generate` generates PDF via Celery task
- [ ] POST `/api/v1/incidents/{id}/reports/{report_id}/submit` marks report as submitted
- [ ] GET `/api/v1/incidents/{id}/reports/{report_id}/download` returns signed S3 download URL
- [ ] Reports can be regenerated after initial generation (new PDF replaces old)
- [ ] Each generation/regeneration creates a timeline entry (report_generated / report_regenerated)
- [ ] Submission creates a timeline entry (report_submitted)
- [ ] Celery beat task runs every 15 minutes to check deadlines
- [ ] Warning notification sent at 75% of elapsed time
- [ ] Urgent notification sent at 90% of elapsed time
- [ ] Critical alert when deadline passes without submission
- [ ] PDF contains: incident details, severity, status, timeline, affected assets (if any), current status
- [ ] Generate/submit endpoints require admin role
- [ ] Frontend: countdown timers (hours/minutes remaining) visible on incident detail
- [ ] Frontend: generate, regenerate, download, submit buttons with proper states
- [ ] i18n: all new strings in EN and ES
- [ ] Unit tests for report generation command, deadline check logic
- [ ] Integration tests for all report endpoints

## Technical Scope

### Entities (owned by this feature)
- `RegulatoryReport` — with deadline calculation and state machine

### Entities (used from dependencies)
- `SecurityIncident` from F0
- `IncidentTimeline` from F0

### Key Components
- `src/incident_bc/incident/domain/entities.py` — add RegulatoryReport entity
- `src/incident_bc/incident/domain/enums.py` — add ReportType, ReportStatus enums
- Modify `CreateIncidentCommandHandler` to auto-create 3 reports
- `src/incident_bc/incident/application/commands/generate_report.py`
- `src/incident_bc/incident/application/commands/submit_report.py`
- `src/incident_bc/incident/application/queries/list_reports.py`
- `core/tasks/incidents.py` — Celery task for deadline monitoring
- `templates/reports/incident_report.html` — Jinja2 template for PDF
- `adapters/http/api/incidents/routers.py` — add report endpoints
- `core/celery.py` — add beat schedule entry

## Notes

- Reuse the exact same PDF generation pattern from `report_bc`: Celery task → Jinja2 → WeasyPrint → S3.
- The Celery beat task should check ALL pending/generated reports across all companies.
- Escalation notifications use the existing `EventBus` pattern with new `EventType` values.
- PDF template should be clean and professional — it will be submitted to government authorities (CSIRT).
