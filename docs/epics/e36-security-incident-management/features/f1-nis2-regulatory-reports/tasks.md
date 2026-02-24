# Tasks: F1 — NIS2 Regulatory Reports

**Feature:** [requirements.md](requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: RegulatoryReport entity + state machine | M | Domain |
| 2 | Domain: repository interface additions | S | Domain |
| 3 | Modify CreateIncidentCommandHandler to auto-create 3 reports | M | App |
| 4 | Application: GenerateReportCommand + handler | M | App |
| 5 | Application: SubmitReportCommand + handler | S | App |
| 6 | Application: ListReportsQuery + handler (with countdown) | M | App |
| 7 | Application: deadline escalation event methods | S | App |
| 8 | Infrastructure: repository — save_report, update_report, deadline query | M | Infra |
| 9 | Celery: generate_incident_report task (PDF) | L | Infra |
| 10 | Celery: check_regulatory_deadlines beat task | M | Infra |
| 11 | Celery: beat schedule entry + task imports | S | Infra |
| 12 | PDF: Jinja2 template for incident reports (3 types) | M | Infra |
| 13 | HTTP: schemas (report-specific request/response) | S | HTTP |
| 14 | HTTP: report endpoints (list, generate, submit, download) | M | HTTP |
| 15 | Enrich ReportResponse with countdown fields | S | HTTP |
| 16 | Unit tests: RegulatoryReport entity | S | Test |
| 17 | Unit tests: GenerateReport + SubmitReport command handlers | M | Test |
| 18 | Unit tests: ListReportsQuery handler | S | Test |
| 19 | Unit tests: deadline check logic | M | Test |
| 20 | Integration tests: report endpoints | L | Test |
| 21 | Frontend: regulatory reports section on incident detail | L | FE |
| 22 | Frontend: countdown timers component | M | FE |
| 23 | i18n: EN/ES translations for regulatory reports | S | FE |

## Detailed Tasks

### Phase 1: Domain Layer

#### Task 1: RegulatoryReport entity + state machine
- **File:** `src/incident_bc/incident/domain/entities.py`
- **What:** Add RegulatoryReport dataclass with `create_for_incident()` factory (creates 3 reports with deadlines), `mark_generated(file_path)`, `mark_submitted()` methods. State machine: pending → generated → submitted. generated → generated allowed (regeneration).
- **Acceptance:** Deadline calculation correct (24h, 72h, 30d from detected_at), state transitions validated, regeneration allowed
- [x] Done

#### Task 2: Repository interface additions
- **File:** `src/incident_bc/incident/domain/repository.py`
- **What:** Add `save_report(report: RegulatoryReport)`, `update_report(report: RegulatoryReport)`, `find_pending_reports_approaching_deadline() -> list[tuple[dict, SecurityIncident]]` abstract methods. Update `save_reports_batch` to accept `list[RegulatoryReport]`.
- **Acceptance:** All new methods defined with proper typing
- [x] Done

### Phase 2: Application Layer

#### Task 3: Modify CreateIncidentCommandHandler
- **File:** `src/incident_bc/incident/application/commands/create_incident.py`
- **What:** After creating incident + timeline, call `RegulatoryReport.create_for_incident()` and `repo.save_reports_batch()` to auto-create 3 regulatory reports.
- **Acceptance:** Creating an incident now also creates 3 reports with correct deadlines
- [x] Done

#### Task 4: GenerateReportCommand + handler
- **File:** `src/incident_bc/incident/application/commands/generate_report.py`
- **What:** Command(incident_id, report_id, company_id, actor_id). Handler validates incident exists + report exists, dispatches Celery task for PDF generation, creates timeline entry (report_generated or report_regenerated based on current status).
- **Deps:** Tasks 1, 2
- **Acceptance:** Command dispatches Celery task, timeline entry created
- [x] Done

#### Task 5: SubmitReportCommand + handler
- **File:** `src/incident_bc/incident/application/commands/submit_report.py`
- **What:** Command(incident_id, report_id, company_id, actor_id). Handler validates report is generated (not pending), calls mark_submitted(), saves, creates timeline entry.
- **Deps:** Tasks 1, 2
- **Acceptance:** Only generated reports can be submitted, timeline entry created
- [x] Done

#### Task 6: ListReportsQuery + handler
- **File:** `src/incident_bc/incident/application/queries/list_reports.py`
- **What:** Query(incident_id, company_id). Handler returns list[ReportDto] with computed `time_remaining_seconds` and `elapsed_percentage` fields. ReportDto extended with these 2 computed fields.
- **Acceptance:** Reports returned with countdown data, elapsed percentage computed correctly
- [x] Done

#### Task 7: Deadline escalation event methods
- **File:** `src/incident_bc/incident/application/services/incident_event_factory.py`
- **What:** Add `deadline_warning(incident, report_type, percentage)` and `deadline_passed(incident, report_type)` static methods.
- **Collateral:** `src/notification_bc/notification/domain/enums.py` — add INCIDENT_DEADLINE_WARNING, INCIDENT_DEADLINE_URGENT, INCIDENT_DEADLINE_PASSED event types
- **Acceptance:** Events created with correct payload and event_type
- [x] Done

### Phase 3: Infrastructure Layer

#### Task 8: Repository implementation additions
- **File:** `src/incident_bc/incident/infrastructure/repository.py`
- **What:** Implement `save_report()` (single RegulatoryReport entity), `update_report()` (updates status, file_path, generated_at, submitted_at), `find_pending_reports_approaching_deadline()` (returns unsubmitted reports with joined incident data). Update `save_reports_batch()` to accept RegulatoryReport entities.
- **Acceptance:** All methods work, deadline query returns correct data
- [x] Done

#### Task 9: Celery task — generate_incident_report
- **File:** `core/tasks/incidents.py`
- **What:** Celery task that: loads incident + report from DB, collects data (timeline, incident details), renders Jinja2 template per report_type, converts to PDF via WeasyPrint, uploads to S3, updates report with file_path + generated_at + status=generated.
- **Deps:** Tasks 8, 12
- **Acceptance:** PDF generated and uploaded to S3, report status updated
- [x] Done

#### Task 10: Celery task — check_regulatory_deadlines
- **File:** `core/tasks/incidents.py` (same file)
- **What:** Beat task that: queries all unsubmitted reports, computes elapsed percentage, sends warning at 75%, urgent at 90%, critical alert when deadline passed. Only sends each notification level once per report (tracked via metadata or a simple flag).
- **Deps:** Tasks 7, 8
- **Acceptance:** Notifications sent at correct thresholds, no duplicate alerts
- [x] Done

#### Task 11: Beat schedule + task imports
- **File:** `core/celery.py`, `core/tasks/__init__.py`
- **What:** Add beat_schedule entry for `check-regulatory-deadlines` (every 15 min). Add task imports in `__init__.py`.
- **Acceptance:** Beat schedule registered, tasks importable
- [x] Done

#### Task 12: PDF Jinja2 template
- **File:** `templates/reports/incident_report.html`
- **What:** Single template that adapts to report_type. Extends base.html. Shows: incident details (title, severity, status, type, detected_at), timeline of events, attack vector, data breach scope. For early_warning: minimal, just facts. For detailed: full timeline + analysis. For final: everything + resolution summary.
- **Acceptance:** Clean, professional PDF suitable for CSIRT submission
- [x] Done

### Phase 4: HTTP Layer

#### Task 13: Schemas additions
- **File:** `adapters/http/api/incidents/schemas.py`
- **What:** Add `time_remaining_seconds` and `elapsed_percentage` to ReportResponse.
- **Acceptance:** Fields present in response
- [x] Done

#### Task 14: Report endpoints
- **File:** `adapters/http/api/incidents/routers.py`
- **What:** Add 4 endpoints: GET `/{id}/reports` (list), POST `/{id}/reports/{report_id}/generate` (admin), POST `/{id}/reports/{report_id}/submit` (admin), GET `/{id}/reports/{report_id}/download` (admin). Download returns signed S3 URL redirect or JSON with URL.
- **Deps:** Tasks 4, 5, 6
- **Acceptance:** All endpoints work with proper role auth and error handling
- [x] Done

#### Task 15: Enrich response with countdown
- **File:** `adapters/http/api/incidents/routers.py`
- **What:** Update `_detail_to_response()` to include `time_remaining_seconds` and `elapsed_percentage` in report DTOs. Use `ListReportsQuery` for enriched data or compute inline.
- **Acceptance:** Incident detail API returns reports with countdown data
- [x] Done

### Phase 5: Tests

#### Task 16: Unit tests — RegulatoryReport entity
- **File:** `tests/unit/incident_bc/incident/domain/test_regulatory_report.py`
- **What:** Test create_for_incident (3 reports, correct deadlines), mark_generated, mark_submitted, invalid transitions (submit ungenerated)
- **Acceptance:** All tests pass, state machine fully covered
- [x] Done

#### Task 17: Unit tests — command handlers
- **File:** `tests/unit/incident_bc/incident/application/commands/test_generate_report.py`, `tests/unit/incident_bc/incident/application/commands/test_submit_report.py`
- **What:** Test GenerateReportCommandHandler (happy path, report not found, incident not found), SubmitReportCommandHandler (happy path, not generated error)
- **Acceptance:** All tests pass
- [x] Done

#### Task 18: Unit tests — ListReportsQuery
- **File:** `tests/unit/incident_bc/incident/application/queries/test_list_reports.py`
- **What:** Test handler returns reports with computed countdown fields
- **Acceptance:** All tests pass
- [x] Done

#### Task 19: Unit tests — deadline check logic
- **File:** `tests/unit/incident_bc/incident/application/test_check_deadlines.py`
- **What:** Test threshold calculations (75%, 90%, 100%), notification dispatch logic
- **Acceptance:** All tests pass
- [x] Done

#### Task 20: Integration tests — report endpoints
- **File:** `tests/integration/test_incidents_endpoints.py`
- **What:** Test GET reports list, POST generate (triggers task mock), POST submit (status change), GET download (signed URL), role authorization (admin required for generate/submit/download)
- **Acceptance:** All tests pass with real DB
- [x] Done

### Phase 6: Frontend

#### Task 21: Regulatory reports section
- **File:** `web/app/src/pages/technician/IncidentDetail.tsx`
- **What:** Add regulatory reports section below timeline. Shows 3 report cards (Early Warning 24h, Detailed 72h, Final 30d) with status badge, deadline, countdown timer, and action buttons (generate/regenerate/download/submit). Admin-only actions.
- **Acceptance:** Section renders, buttons work, proper loading states
- [x] Done

#### Task 22: Countdown timer component
- **File:** `web/app/src/pages/technician/IncidentDetail.tsx` (inline or separate)
- **What:** Live countdown component that shows remaining time (Xd Xh Xm) or "OVERDUE" with color coding (green > 25% remaining, yellow < 25%, red < 10%, critical/overdue)
- **Acceptance:** Timer updates live, color coding correct
- [x] Done

#### Task 23: i18n translations
- **File:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Translation keys for: report type labels, report status labels, button labels (generate, regenerate, download, submit), countdown labels, section title
- **Acceptance:** UI renders correctly in EN and ES
- [x] Done
