# Tasks: F4 — Dashboard, Alerts & Export

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-26

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Application: SupplyChainDashboardQuery + handler | M | App |
| 2 | Application: Celery task — contract renewal reminders | M | App |
| 3 | Application: Celery task — concentration risk periodic check | M | App |
| 4 | Application: Celery task — stale assessment detection | S | App |
| 5 | Application: VendorRiskExportCommand + handler | M | App |
| 6 | Notification: Add new event types | S | App |
| 7 | HTTP: dashboard + export schemas | S | HTTP |
| 8 | HTTP: dashboard + export endpoints | M | HTTP |
| 9 | HTTP: Register in app.py + Celery beat schedule | S | HTTP |
| 10 | Unit tests: dashboard query handler | M | Test |
| 11 | Unit tests: Celery tasks | M | Test |
| 12 | Unit tests: export command handler | S | Test |
| 13 | Integration tests: dashboard + export endpoints | M | Test |
| 14 | Frontend: SupplyChainDashboardPage | L | FE |
| 15 | Frontend: Route + sidebar entry | S | FE |
| 16 | Frontend: i18n EN/ES translations | S | FE |

## Detailed Tasks

### Phase 1: Application

#### Task 1: SupplyChainDashboardQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/supply_chain_dashboard.py` (new)
- **What:** `SupplyChainDashboardQuery(company_id)`. Handler aggregates:
  - Total vendors, active vendors
  - Vendors by risk_level (low/medium/high/critical counts)
  - Contracts expiring in next 30/60/90 days
  - Critical ICT providers count
  - Concentration risk summary (vendors above 40% threshold)
  - Vendors with stale assessments count (next_review_date < today)
  - Returns `SupplyChainDashboardDto`
- **Deps:** F0-F2 repos
- **Acceptance:** Returns correct aggregated data
- [x] Done

#### Task 2: Celery task — contract renewal reminders
- **File:** `core/tasks/vendor_contracts.py` (extend from F0 task 17)
- **What:** `send_contract_renewal_reminders` task. Runs daily. Finds contracts with renewal_date in 60, 30, or 7 days. For each, creates `CONTRACT_RENEWAL_REMINDER` notification for company admins. Must be idempotent — track last_reminder_sent or check if reminder already exists for this contract+date combo.
- **Deps:** F0 task 4, Task 6
- **Acceptance:** Reminders sent at 60/30/7 days, no duplicates
- [x] Done

#### Task 3: Celery task — concentration risk periodic check
- **File:** `core/tasks/vendor_contracts.py` (extend)
- **What:** `check_concentration_risk` task. Runs daily. For each company, compute concentration risk. If any vendor exceeds 40%, create `CONCENTRATION_RISK_ALERT` notification for company admins. Idempotent — don't re-alert if situation unchanged since last check.
- **Deps:** F2 task 9, Task 6
- **Acceptance:** Alerts sent when threshold exceeded, no spam
- [x] Done

#### Task 4: Celery task — stale assessment detection
- **File:** `core/tasks/vendor_contracts.py` (extend)
- **What:** `check_stale_assessments` task. Runs daily. Finds vendors whose latest assessment's next_review_date < today. Creates `VENDOR_ASSESSMENT_OVERDUE` notification for company admins. Idempotent.
- **Deps:** F1 task 4, Task 6
- **Acceptance:** Alerts sent for stale assessments, no duplicates
- [x] Done

#### Task 5: VendorRiskExportCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/export_vendor_risk.py` (new)
- **What:** `ExportVendorRiskCommand(company_id, format: pdf|csv, requested_by)`. Handler: fetch all vendors with risk data (assessments, contracts, dependencies), generate PDF (WeasyPrint) or CSV. Store in MinIO via report_bc infrastructure. Return download URL.
  - PDF includes: vendor list with risk levels, contract summary per vendor, latest assessment scores, dependency map, concentration risk table.
  - CSV includes: flat table of vendors with all risk fields.
- **Deps:** All F0-F2 repos + report_bc storage
- **Acceptance:** PDF and CSV generated with correct data, stored in MinIO
- [x] Done

#### Task 6: Notification — add new event types
- **File:** `src/notification_bc/notification/domain/enums.py` (extend)
- **What:** Add: `CONTRACT_RENEWAL_REMINDER = "vendor.contract_renewal_reminder"`, `CONCENTRATION_RISK_ALERT = "vendor.concentration_risk_alert"`, `VENDOR_ASSESSMENT_OVERDUE = "vendor.assessment_overdue"`.
- **File:** `src/notification_bc/notification/application/services/event_factory.py` (extend)
- **What:** Add notification title/body templates for the 3 new event types.
- **Acceptance:** Event types registered, templates defined
- [x] Done

### Phase 2: HTTP

#### Task 7: Dashboard + export schemas
- **File:** `adapters/http/api/vendors/dashboard_schemas.py` (new)
- **What:** `SupplyChainDashboardResponse` (vendor counts by risk level, expiring contracts, critical ICT count, concentration risk items, stale assessment count). `ExportVendorRiskRequest` (format: pdf|csv). `ExportVendorRiskResponse` (download_url).
- **Deps:** Tasks 1, 5
- **Acceptance:** All schemas defined
- [x] Done

#### Task 8: Dashboard + export endpoints
- **File:** `adapters/http/api/vendors/dashboard_router.py` (new)
- **What:** GET `/api/v1/vendors/supply-chain-dashboard` (technician+). POST `/api/v1/vendors/risk-export` (admin). Note: these routes must be registered BEFORE the `/:id` wildcard routes to avoid path conflicts.
- **Deps:** Task 7
- **Acceptance:** Both endpoints working with correct auth
- [x] Done

#### Task 9: Register in app.py + Celery beat schedule
- **Files:** `app.py` (extend), `core/celery.py` (extend beat_schedule)
- **What:** Register dashboard_router. Add beat entries:
  - `check-contract-renewals`: daily at 06:00 UTC
  - `check-concentration-risk`: daily at 07:00 UTC
  - `check-stale-assessments`: daily at 07:30 UTC
  - `expire-vendor-contracts`: daily at 01:00 UTC (from F0 task 17)
- **Deps:** Tasks 2-4, 8
- **Acceptance:** All routers and tasks registered
- [x] Done

### Phase 3: Tests

#### Task 10: Unit tests — dashboard query handler
- **File:** `tests/unit/procurement_bc/vendor/application/queries/test_dashboard_query.py` (new)
- **What:** Test SupplyChainDashboardQueryHandler: company with various vendors/contracts/assessments/dependencies. Empty company. Mock all repos.
- **Acceptance:** Aggregation logic correct
- [x] Done

#### Task 11: Unit tests — Celery tasks
- **File:** `tests/unit/procurement_bc/vendor/application/test_celery_tasks.py` (new)
- **What:** Test renewal reminder task: contract at 60/30/7 days creates notification, contract at 61 days doesn't. Test concentration risk task: vendor above 40% triggers alert. Test stale assessment task: overdue assessment triggers alert. Test idempotency: running twice doesn't duplicate notifications.
- **Acceptance:** All task logic tested
- [x] Done

#### Task 12: Unit tests — export command handler
- **File:** `tests/unit/procurement_bc/vendor/application/commands/test_export_command.py` (new)
- **What:** Test ExportVendorRiskCommandHandler: PDF generation called, CSV generation called, file stored in MinIO. Mock repos + storage.
- **Acceptance:** Export logic tested
- [x] Done

#### Task 13: Integration tests — dashboard + export endpoints
- **File:** `tests/integration/test_vendor_dashboard_endpoints.py` (new)
- **What:** GET dashboard (200, correct counts after seeding data). POST export (201, returns URL). Auth: employee=403, technician dashboard=200, admin export=200. Empty company returns zeros.
- **Acceptance:** All endpoints tested with real DB
- [x] Done

### Phase 4: Frontend

#### Task 14: SupplyChainDashboardPage
- **File:** `web/app/src/pages/admin/SupplyChainDashboardPage.tsx` (new)
- **What:**
  - Summary cards: total vendors, critical ICT providers, stale assessments, expiring contracts (next 30 days)
  - Risk distribution chart: vendors by risk_level (bar or donut chart using recharts)
  - Concentration risk table: vendors with percentage of critical dependencies, flagged rows above 40%
  - Expiring contracts table: contracts expiring in next 90 days with vendor name, title, end_date, days remaining
  - Export button (PDF/CSV dropdown) → triggers POST export → opens download URL
- **Acceptance:** Dashboard renders with all sections, export works
- [x] Done

#### Task 15: Route + sidebar entry
- **Files:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Add route `/vendors/supply-chain`. Sidebar entry under Vendors/Procurement section: "Supply Chain Risk" with appropriate icon. Visible to technician+.
- **Acceptance:** Navigation works, sidebar shows entry
- [x] Done

#### Task 16: i18n EN/ES translations
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Dashboard page keys: page title, card labels, chart labels, table headers, export buttons, concentration risk labels, empty states.
- **Acceptance:** All strings translated EN + ES
- [x] Done
