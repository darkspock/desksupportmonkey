# F2: Notification + Download Integration

**Epic:** E6 - Report Generation
**Feature:** F2
**Status:** Pending
**Depends on:** F1
**Date:** 2026-02-16

---

## User Stories

### US-E6-002: Report Download (partial)
**As an** admin, **I want** to download completed reports **so that** I can share PDFs with stakeholders.

### US-E6-006: Report Ready Notification
**As an** admin, **I want** to be notified when a report is ready **so that** I don't need to poll the status endpoint.

---

## Acceptance Criteria

### Download Endpoint (`GET /api/v1/reports/{id}/download`)
- [ ] Returns signed S3 URL for completed reports
- [ ] Signed URL expires after S3_SIGNED_URL_EXPIRY (default 1 hour)
- [ ] Returns 404 if report not found or wrong company
- [ ] Returns 409 if report status is pending, processing, or failed
- [ ] Admin+ role only
- [ ] Scoped by company_id

### Report Ready Notification
- [ ] Add `REPORT_READY` to EventType enum
- [ ] When Celery task completes, create notification for requested_by user
- [ ] Notification title: "Report ready"
- [ ] Notification body: "{report_type} report is ready for download"
- [ ] Notification data includes report_id
- [ ] Notification created directly in Celery task (separate process, no EventBus)
- [ ] Add report.ready targeting in TargetResolver (for future use)

---

## Dependencies

- F1 must be complete (reports can be generated)
- S3StorageService.get_signed_url() exists
- NotificationRepository exists for creating notifications
- EventType enum exists for adding REPORT_READY
