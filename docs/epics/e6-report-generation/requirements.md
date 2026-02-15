# Epic E6: Report Generation

**Type:** Epic
**Status:** Pending Validation
**Created:** 2026-02-16
**Priority:** Medium
**Depends on:** E2 (Asset Inventory), E3 (Service Requests), E5 (Admin Dashboard)

---

## Business Alignment

**Objective:** Allow admins to generate PDF reports on demand, processed asynchronously via Celery, stored in MinIO (S3-compatible), and downloadable via signed URLs — so they can share operational data with stakeholders who don't have platform access.

E5 delivered real-time dashboard metrics via API. But admins need exportable, shareable reports: a PDF they can email to management, attach to a quarterly review, or archive. E6 delivers the async report pipeline that converts dashboard data into formatted PDFs.

---

## Problem Statement

### Current Situation
E5 provides dashboard API endpoints for metrics and alerts. But:
- No way to export dashboard data as a document
- No PDF generation capability
- No async task pipeline for long-running operations
- Celery infrastructure exists (cleanup tasks) but no report tasks
- MinIO/S3 storage exists but no report files stored yet
- No report tracking (status, download URL, history)

### What E6 Delivers
An async report generation pipeline that provides:
- Report request API (admin triggers generation)
- Celery task for async PDF generation (Jinja2 + WeasyPrint)
- Upload to MinIO with signed download URLs (1h expiry)
- Report record tracking (pending → completed/failed)
- Three report types: asset inventory, request summary, technician performance
- Notification when report is ready (via existing event bus)
- Report history with re-download capability

---

## Proposed Solution

### US-E6-001: Request Report Generation
**As an** admin
**I want** to request a report by type
**So that** I can generate a PDF of operational data

**Acceptance Criteria:**
- [ ] `POST /api/v1/reports` accepts report type and optional parameters
- [ ] Report types: `asset_inventory`, `request_summary`, `technician_performance`
- [ ] Creates a Report record with status `pending`
- [ ] Dispatches a Celery task for async generation
- [ ] Returns report id and status immediately (202 Accepted)
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E6-002: Report Status and Download
**As an** admin
**I want** to check report status and download completed reports
**So that** I can retrieve generated PDFs

**Acceptance Criteria:**
- [ ] `GET /api/v1/reports` lists all reports for the company (paginated)
- [ ] `GET /api/v1/reports/{id}` returns report detail with status
- [ ] `GET /api/v1/reports/{id}/download` returns signed URL for completed reports
- [ ] Signed URL expires after 1 hour (configurable via S3_SIGNED_URL_EXPIRY)
- [ ] Returns 404 for non-existent or other company's reports
- [ ] Returns 409 if report is still pending or failed
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E6-003: Asset Inventory Report
**As an** admin
**I want** a PDF report of all assets in my company
**So that** I can share inventory data with stakeholders

**Acceptance Criteria:**
- [ ] Includes asset counts by status and type (from E5 queries)
- [ ] Includes full asset list with: brand, model, serial_number, status, assigned_to, purchase_date, warranty_expiration
- [ ] Includes warranty expiration alerts (assets expiring within 90 days)
- [ ] Formatted as a professional PDF with company header
- [ ] Uploaded to MinIO at `reports/{company_id}/{report_id}.pdf`

### US-E6-004: Request Summary Report
**As an** admin
**I want** a PDF report summarizing service requests
**So that** I can review operational performance

**Acceptance Criteria:**
- [ ] Includes request counts by status, type, priority (from E5 queries)
- [ ] Includes overall average resolution time
- [ ] Includes request volume trend (last 30 days by day)
- [ ] Includes SLA breach summary (count of breached requests by priority)
- [ ] Optional date range filter (from_date, to_date in report parameters)
- [ ] Formatted as a professional PDF with company header

### US-E6-005: Technician Performance Report
**As an** admin
**I want** a PDF report of technician performance metrics
**So that** I can evaluate team efficiency

**Acceptance Criteria:**
- [ ] Includes average resolution time per technician
- [ ] Includes resolved request count per technician
- [ ] Includes currently assigned open requests per technician
- [ ] Optional date range filter
- [ ] Formatted as a professional PDF with company header

### US-E6-006: Report Ready Notification
**As an** admin
**I want** to be notified when a report is ready
**So that** I don't need to poll the status endpoint

**Acceptance Criteria:**
- [ ] When report generation completes, publish a domain event
- [ ] New event type: `report.ready`
- [ ] Notification includes report id, type, and title
- [ ] Delivered via existing notification + WebSocket system
- [ ] Only sent to the user who requested the report

---

## Entities

### Report
New domain entity:
```
Report:
  id: str (ULID)
  company_id: str
  requested_by: str (user_id)
  type: str (asset_inventory | request_summary | technician_performance)
  status: str (pending | processing | completed | failed)
  parameters: dict (optional filters like from_date, to_date)
  storage_key: str | None (S3 object key when completed)
  error_message: str | None (failure reason)
  created_at: datetime
  completed_at: datetime | None
```

---

## Use Cases

### UC-E6-001: Admin Generates Report
**Actor:** Admin
**Preconditions:** Logged in with admin+ role

**Main Flow:**
1. Admin selects report type and optional parameters
2. System creates Report record (status: pending)
3. System dispatches Celery task
4. System returns 202 with report id
5. Celery worker picks up task
6. Worker queries data, generates HTML, converts to PDF
7. Worker uploads PDF to MinIO
8. Worker updates Report record (status: completed, storage_key set)
9. Worker publishes report.ready event
10. Admin receives notification
11. Admin downloads report via signed URL

### UC-E6-002: Report Generation Fails
**Actor:** System
**Preconditions:** Celery task is processing

**Main Flow:**
1. PDF generation or upload fails
2. Worker updates Report record (status: failed, error_message set)
3. If retries remaining, Celery retries the task
4. After max retries, report stays failed
5. Admin can see failed status and error message

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `app.py` | Register reports router | Update router includes |
| `core/tasks/` | New report generation task | Add `reports.py` task module |
| `core/celery.py` | Already routes core.tasks.* to reports queue | None |
| `core/storage.py` | Already has upload + signed URL | None |
| `core/config.py` | Already has ReportSettings | None |
| `notification_bc/enums.py` | Add REPORT_READY event type | Update enum |
| `notification_bc/target_resolver.py` | Add report.ready targeting | Update resolver |
| New migration | reports table | Alembic migration |

---

## Bounded Context

E6 creates a new bounded context `report_bc` for the Report entity and its lifecycle. The Celery task lives in `core/tasks/` (infrastructure concern, not domain) and queries across bounded contexts (asset_bc, request_bc) for data aggregation.

```
src/report_bc/report/
├── domain/
│   ├── __init__.py
│   ├── entities.py          # Report dataclass
│   ├── enums.py             # ReportType, ReportStatus
│   └── repository.py        # ReportRepositoryInterface
├── application/
│   ├── __init__.py
│   ├── commands/
│   │   ├── __init__.py
│   │   └── request_report.py   # Create report + dispatch task
│   └── queries/
│       ├── __init__.py
│       ├── list_reports.py
│       └── get_report.py
└── infrastructure/
    ├── __init__.py
    ├── models.py            # ReportModel
    └── repository.py        # ReportRepository

core/tasks/
├── reports.py               # Celery task: generate_report

adapters/http/api/reports/
├── __init__.py
├── routers.py               # Report endpoints
└── schemas.py               # Request/response schemas

templates/reports/
├── base.html                # Base PDF template
├── asset_inventory.html     # Asset report template
├── request_summary.html     # Request report template
└── technician_performance.html  # Technician report template
```

---

## Technical Decisions

### 1. WeasyPrint for PDF Generation
Jinja2 renders HTML templates, WeasyPrint converts to PDF. This gives full CSS control over layout. WeasyPrint is a Python library that doesn't require external binaries like wkhtmltopdf.

### 2. Celery for Async Processing
PDF generation can take seconds — too long for a synchronous HTTP response. Celery tasks process reports in the background. The existing Celery + Redis setup routes `core.tasks.*` to the "reports" queue.

### 3. Report Entity in New Bounded Context
Reports have their own lifecycle (pending → processing → completed/failed), distinct from assets or requests. A separate `report_bc` keeps concerns clean.

### 4. S3 Key Format
Reports stored at `reports/{company_id}/{report_id}.pdf`. This makes it easy to list or clean up reports per company.

### 5. Max 3 Retries
Celery task retries up to `REPORT_MAX_RETRIES` (default 3) on failure. After max retries, the report is marked as `failed` with the error message.

### 6. Signed URL for Download
Reports are not publicly accessible. The download endpoint generates a pre-signed S3 URL (1h expiry) that the client uses to download the PDF directly from MinIO.

---

## Definition of Done

- [ ] Report entity with status lifecycle (pending → processing → completed/failed)
- [ ] Report table migration
- [ ] POST endpoint to request report generation (202 Accepted)
- [ ] GET endpoints for list, detail, download
- [ ] Celery task for async PDF generation
- [ ] Three HTML→PDF templates (asset inventory, request summary, technician performance)
- [ ] Upload to MinIO with signed URL download
- [ ] Report.ready notification via event bus
- [ ] Max 3 retries on failure
- [ ] All endpoints admin+ only, scoped by company_id
- [ ] Unit tests for report entity, commands, queries
- [ ] Unit tests for report endpoints
- [ ] Unit tests for Celery task logic

---

## Open Questions

1. **Email delivery of reports?** **Recommend:** Not in v1. Admin downloads via signed URL. Email delivery is a future enhancement.
2. **Report retention/cleanup?** **Recommend:** REPORT_RETENTION_DAYS setting exists (365 days). Add cleanup Celery beat task later.
3. **CSV export alongside PDF?** **Recommend:** Not in v1. PDF only. CSV can be added as a second format later.
4. **Concurrent report limit?** **Recommend:** Not in v1. Allow unlimited concurrent reports. Rate limiting can be added later.
5. **Report caching?** **Recommend:** No. Each report is a snapshot at request time. Previous reports are accessible via history.
