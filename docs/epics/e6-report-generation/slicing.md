# Slicing: E6 - Report Generation

**Epic:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-02-16

---

## Feature Breakdown

| Feature | Description | User Stories | Complexity |
|---|---|---|---|
| **F0** | Report Model + API Endpoints | US-E6-001, US-E6-002 | Medium |
| **F1** | PDF Generation + Celery Task | US-E6-003, US-E6-004, US-E6-005, US-E6-006 | High |
| **F2** | Notification + Download Integration | US-E6-002 (download), US-E6-006 | Low-Medium |

---

## F0: Report Model + API Endpoints

**Scope:** Report entity, repository, migration, API endpoints for creating, listing, and viewing reports.

**Why F0:** The Report entity and persistence must exist before the Celery task can update report status. The API endpoints let admins request reports and check status. The Celery task dispatch is wired here but the actual generation logic comes in F1.

**Includes:**
- Report entity (dataclass) + ReportType/ReportStatus enums
- ReportRepositoryInterface + ReportRepository
- ReportModel (SQLAlchemy, ULIDMixin + TimestampMixin)
- Alembic migration for reports table
- RequestReport command (creates record, dispatches Celery task)
- ListReports query (paginated, company-scoped)
- GetReport query
- Router with 3 endpoints: POST /reports, GET /reports, GET /reports/{id}
- Response schemas
- Install weasyprint dependency
- models_registry.py update

**Endpoints:**
- `POST /api/v1/reports` — request report generation (202 Accepted)
- `GET /api/v1/reports` — list reports for company
- `GET /api/v1/reports/{id}` — get report detail

---

## F1: PDF Generation + Celery Task

**Scope:** Celery task implementation, Jinja2 HTML templates, WeasyPrint PDF conversion, S3 upload, report status updates.

**Why F1:** This is the core of E6 — the async pipeline that actually generates PDFs. Depends on F0 for the report record to exist and the task dispatch mechanism.

**Depends on:** F0 (Report entity, repository, task dispatch)

**Includes:**
- Celery task: `core/tasks/reports.py` — `generate_report` task
- Data collector functions (query aggregates from repositories)
- 3 Jinja2 HTML templates (base + asset_inventory + request_summary + technician_performance)
- WeasyPrint HTML→PDF conversion
- S3 upload of generated PDF
- Report status lifecycle: pending → processing → completed/failed
- Retry logic (max 3 retries)
- Extract SLA thresholds to shared constants
- Add `find_all_by_company()` to AssetRepository for unpaginated asset list

---

## F2: Notification + Download Integration

**Scope:** Report ready notification, download endpoint with signed URL.

**Why F2:** Notification requires the report to be generated (F1). The download endpoint generates a signed S3 URL for the completed report.

**Depends on:** F1 (reports must be generatable)

**Includes:**
- Add `REPORT_READY` to EventType enum
- Add report.ready targeting in TargetResolver (→ requested_by user only)
- Create notification directly in Celery task (separate process, no EventBus)
- `GET /api/v1/reports/{id}/download` endpoint — returns signed URL
- 409 response if report not completed
- Unit tests for notification creation and download endpoint

---

## Dependency Graph

```
F0: Report Model + API Endpoints
 │
 └── F1: PDF Generation + Celery Task
      │
      └── F2: Notification + Download Integration
```

Strictly sequential: F0 creates the model and API, F1 builds the generation pipeline, F2 adds notifications and download.

---

## Implementation Order

1. **F0** — Report entity, repository, migration, API endpoints, weasyprint dep
2. **F1** — Celery task, templates, PDF generation, S3 upload
3. **F2** — Report ready notification, download endpoint

---

## Migration Strategy

**Single migration in F0:** Create the `reports` table with all columns. No additional migrations for F1-F2.
