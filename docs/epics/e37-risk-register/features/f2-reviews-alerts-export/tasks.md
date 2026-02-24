# Tasks: F2 — Reviews, Alerts & Export

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Notification enums: add risk event types | S | Domain |
| 2 | Target resolver: add risk review overdue resolver | S | Domain |
| 3 | Celery task: check_overdue_reviews | M | Infra |
| 4 | Celery beat schedule entry | S | Infra |
| 5 | CSV export endpoint (sync, no S3 needed) | M | HTTP |
| 6 | Unit tests: Celery task | S | Test |
| 7 | Frontend: export button on RiskListPage | S | FE |
| 8 | i18n: export translations | S | FE |

## Detailed Tasks

### Task 1: Notification enums
- **File:** `src/notification_bc/notification/domain/enums.py`
- **What:** Add RISK_REVIEW_OVERDUE to EventType enum.
- [x] Done

### Task 2: Target resolver
- **File:** `src/notification_bc/notification/application/services/target_resolver.py`
- **What:** Add resolver method for risk_review_overdue events. Target risk owner_id and company admins.
- [x] Done

### Task 3: Celery task: check_overdue_reviews
- **File:** `core/tasks/risks.py` (NEW)
- **What:** Task that iterates companies, calls find_overdue_reviews(), creates Notification for each overdue risk, records REVIEW_OVERDUE history entry to prevent duplicates.
- [x] Done

### Task 4: Celery beat schedule entry
- **File:** `core/celery.py`, `core/tasks/__init__.py`
- **What:** Add "check-risk-overdue-reviews" task every 6 hours. Import in __init__.py.
- [x] Done

### Task 5: CSV export endpoint
- **File:** `adapters/http/api/risks/routers.py`
- **What:** GET /api/v1/risks/export endpoint that generates CSV in memory and returns as StreamingResponse. No S3 needed for simple CSV.
- [x] Done

### Task 6: Unit test for Celery task
- **File:** `tests/unit/risk_bc/risk/test_tasks.py`
- **What:** Test check_overdue_reviews sends notifications and records history.
- [x] Done

### Task 7: Frontend export button
- **File:** `web/app/src/pages/technician/RiskListPage.tsx`
- **What:** Add "Export CSV" button next to "New Risk" button for admin users.
- [x] Done

### Task 8: i18n export translations
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** Add page.risks.export_csv key.
- [x] Done
