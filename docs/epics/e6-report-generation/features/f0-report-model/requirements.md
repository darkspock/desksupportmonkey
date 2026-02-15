# F0: Report Model + API Endpoints

**Epic:** E6 - Report Generation
**Feature:** F0
**Status:** Pending
**Date:** 2026-02-16

---

## User Stories

### US-E6-001: Request Report Generation
**As an** admin, **I want** to request a report by type **so that** I can generate a PDF of operational data.

### US-E6-002: Report Status (partial)
**As an** admin, **I want** to check report status **so that** I know when a report is ready.

---

## Acceptance Criteria

### Create Report (`POST /api/v1/reports`)
- [ ] Accepts: type (asset_inventory | request_summary | technician_performance), optional parameters (from_date, to_date)
- [ ] Creates Report record with status `pending`
- [ ] Dispatches Celery task `core.tasks.reports.generate_report`
- [ ] Returns 202 Accepted with report id and status
- [ ] Admin+ role only
- [ ] Scoped by company_id

### List Reports (`GET /api/v1/reports`)
- [ ] Returns paginated list of reports for the company
- [ ] Each item: id, type, status, created_at, completed_at
- [ ] Sorted by created_at desc (newest first)
- [ ] Admin+ role only
- [ ] Scoped by company_id

### Get Report (`GET /api/v1/reports/{id}`)
- [ ] Returns report detail: id, type, status, parameters, created_at, completed_at, error_message
- [ ] Returns 404 if not found or wrong company
- [ ] Admin+ role only
- [ ] Scoped by company_id

---

## Dependencies

- WeasyPrint must be installed (for F1, but install now)
- Celery task module exists (skeleton, actual generation in F1)
- models_registry.py must include ReportModel
