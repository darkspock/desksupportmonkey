# Tasks: F2 - Notification + Download Integration

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-16

---

## Phase 1: EventType + TargetResolver Updates

### Task 1.1: Add REPORT_READY to EventType enum
**File:** `src/notification_bc/notification/domain/enums.py`
- Add `REPORT_READY = "report.ready"`

### Task 1.2: Add report.ready targeting to TargetResolver
**File:** `src/notification_bc/notification/application/services/target_resolver.py`
- Add `_resolve_report_ready` method
- Returns `[payload["requested_by"]]` — only the requester
- Register in resolve() dispatch

---

## Phase 2: Notification in Celery Task

### Task 2.1: Add notification creation to generate_report task
**File:** `core/tasks/reports.py`
- After successful completion (status: completed):
  - Create Notification entity with event_type=REPORT_READY
  - Save via NotificationRepository
  - Title: "Report ready"
  - Body: "{type} report is ready for download"
  - Data: {"report_id": report_id}
  - User: report.requested_by

---

## Phase 3: Download Endpoint

### Task 3.1: Add download endpoint to reports router
**File:** `adapters/http/api/reports/routers.py`
- `GET /api/v1/reports/{id}/download`
- Load report by id + company_id
- 404 if not found
- 409 if status != completed
- Generate signed URL via S3StorageService.get_signed_url()
- Return {"data": {"download_url": url}}

### Task 3.2: Add DownloadResponse schema
**File:** `adapters/http/api/reports/schemas.py`
- DownloadResponse with download_url field

---

## Phase 4: Tests

### Task 4.1: Unit tests for notification creation
**File:** `tests/unit/core/tasks/test_reports.py` (APPEND)
- Test notification created on successful report generation
- Test notification has correct event_type, title, body
- Test notification targets requested_by user

### Task 4.2: Unit tests for download endpoint
**File:** `tests/unit/report_bc/test_endpoints.py` (APPEND)
- Test download returns signed URL for completed report
- Test download returns 404 for not found
- Test download returns 409 for pending report
- Test download returns 409 for failed report
- Test requires admin role

### Task 4.3: Unit tests for TargetResolver update
**File:** `tests/unit/notification_bc/notification/application/services/test_target_resolver.py` (APPEND)
- Test report.ready targets only requested_by user

---

## Phase 5: Verify

- Run `python -m pytest tests/ -v` — all tests pass
- Full E6 verification:
  - POST /reports creates record, dispatches task
  - Celery worker generates PDF
  - Report status transitions correctly
  - Notification created on completion
  - GET /reports/{id}/download returns signed URL
  - Signed URL is valid and PDF downloadable
