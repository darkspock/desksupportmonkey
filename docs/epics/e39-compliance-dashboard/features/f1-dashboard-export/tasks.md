# Implementation Tasks: Dashboard & Report Export (F1)

**Created:** 2026-02-24
**Total Tasks:** 4
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Dashboard Query | 1 | M |
| Celery - Report Task | 1 | M |
| Template - Report HTML | 1 | S |
| Notification - Event | 1 | S |

---

### TASK-001: Create GetComplianceDashboardQuery/Handler

- [x] `GetComplianceDashboardQuery(company_id, framework)` in `src/audit_bc/audit/application/queries/get_compliance_dashboard.py`
- [x] Handler computes per-framework summaries, identifies gap controls, returns `ComplianceDashboardDto`

### TASK-002: Create Celery task for PDF generation

- [x] `generate_compliance_report` in `core/tasks/compliance.py`
- [x] Fetches dashboard data, renders Jinja2 template, generates PDF via WeasyPrint
- [x] Uploads to MinIO and creates notification
- [x] Registered in `core/tasks/__init__.py`

### TASK-003: Create report HTML template

- [x] `templates/reports/compliance_report.html`
- [x] Summary cards, per-framework sections, gap analysis callout

### TASK-004: Add notification event

- [x] Add `COMPLIANCE_REPORT_READY` to `src/notification_bc/notification/domain/enums.py`
