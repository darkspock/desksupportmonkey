# F1: PDF Generation + Celery Task

**Epic:** E6 - Report Generation
**Feature:** F1
**Status:** Pending
**Depends on:** F0
**Date:** 2026-02-16

---

## User Stories

### US-E6-003: Asset Inventory Report
**As an** admin, **I want** a PDF report of all assets in my company **so that** I can share inventory data with stakeholders.

### US-E6-004: Request Summary Report
**As an** admin, **I want** a PDF report summarizing service requests **so that** I can review operational performance.

### US-E6-005: Technician Performance Report
**As an** admin, **I want** a PDF report of technician performance metrics **so that** I can evaluate team efficiency.

---

## Acceptance Criteria

### Celery Task
- [ ] `generate_report` task fully implemented
- [ ] Updates report status: pending → processing → completed/failed
- [ ] Queries data using existing repository aggregate methods
- [ ] Renders Jinja2 HTML template with data
- [ ] Converts HTML to PDF with WeasyPrint
- [ ] Uploads PDF to MinIO at `reports/{company_id}/{report_id}.pdf`
- [ ] Updates report record with storage_key and completed_at
- [ ] On failure: updates status to failed, sets error_message
- [ ] Retries up to REPORT_MAX_RETRIES (3) on failure
- [ ] Respects CELERY_TASK_TIME_LIMIT (5 minutes)

### Asset Inventory Report
- [ ] Asset counts by status and type
- [ ] Full asset list: brand, model, serial_number, status, assigned_to, purchase_date, warranty_expiration
- [ ] Warranty expiration alerts (within 90 days)
- [ ] Company name in header

### Request Summary Report
- [ ] Request counts by status, type, priority
- [ ] Total open and resolved counts
- [ ] Average resolution time overall
- [ ] SLA breach count by priority
- [ ] Optional from_date/to_date filter
- [ ] Company name in header

### Technician Performance Report
- [ ] Average resolution time per technician
- [ ] Resolved count per technician
- [ ] Optional from_date/to_date filter
- [ ] Company name in header

---

## Dependencies

- F0 must be complete (Report entity, repository, Celery task skeleton)
- WeasyPrint installed
- Existing dashboard aggregate methods in repositories
- S3StorageService for upload
