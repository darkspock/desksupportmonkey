# Tasks: F3 — Compliance Dashboard & Reports

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Application: GetSlaDashboardQuery + handler | S | App |
| 2 | HTTP: SLA dashboard endpoint | S | HTTP |
| 3 | Pydantic schemas for dashboard response | S | HTTP |
| 4 | Add SLA_COMPLIANCE report type to enum | S | Domain |
| 5 | Report data collector: collect_sla_compliance | M | Task |
| 6 | HTML template: sla_compliance report | M | Task |
| 7 | Register report in generate_report task | S | Task |
| 8 | Unit tests: GetSlaDashboardQuery | M | Test |
| 9 | Unit tests: report data collector | S | Test |
| 10 | Frontend: SlaDashboardPage with metrics, tables, trend chart | L | FE |
| 11 | Frontend: route + sidebar entry for SLA dashboard | S | FE |
| 12 | i18n: SLA dashboard translations EN/ES | S | FE |

## Detailed Tasks

### Task 1: GetSlaDashboardQuery + handler
- **File:** `src/sla_bc/sla/application/queries/get_dashboard.py`
- **What:** Query accepts company_id, from_date, to_date, bucket. Handler calls compliance_stats, compliance_by_priority, compliance_by_type, breach_trend from SlaRepository. Returns SlaDashboardDto.
- [x] Done

### Task 2: HTTP SLA dashboard endpoint
- **File:** `adapters/http/api/sla/routers.py`
- **What:** GET /api/v1/sla/dashboard with query params from_date, to_date, bucket (default "week"). Admin only.
- [x] Done

### Task 3: Pydantic schemas for dashboard response
- **File:** `adapters/http/api/sla/schemas.py`
- **What:** SlaDashboardResponse with overall stats, by_priority list, by_type list, breach_trend list.
- [x] Done

### Task 4: Add SLA_COMPLIANCE report type
- **File:** `src/report_bc/report/domain/enums.py`
- **What:** Add SLA_COMPLIANCE = "sla_compliance" to ReportType enum.
- [x] Done

### Task 5: Report data collector
- **File:** `core/tasks/report_data.py`
- **What:** collect_sla_compliance(company_id, params, session) — uses SlaRepository dashboard methods to build report data dict.
- [x] Done

### Task 6: HTML template for SLA compliance report
- **File:** `templates/reports/sla_compliance.html`
- **What:** Jinja2 template rendering compliance metrics, by-priority table, by-type table, top breached requests.
- [x] Done

### Task 7: Register in generate_report task
- **File:** `core/tasks/reports.py`
- **What:** Add sla_compliance to DATA_COLLECTORS and TEMPLATE_MAP dicts.
- [x] Done

### Task 8: Unit tests — GetSlaDashboardQuery
- **File:** `tests/unit/sla_bc/sla/application/queries/test_get_dashboard.py`
- **What:** Test dashboard query returns correct DTOs from repository data.
- [x] Done

### Task 9: Unit tests — report data collector
- **File:** `tests/unit/sla_bc/sla/test_report_data.py`
- **What:** Test collect_sla_compliance returns expected data structure.
- [x] Done

### Task 10: Frontend: SlaDashboardPage
- **File:** `web/app/src/pages/admin/SlaDashboardPage.tsx`
- **What:** Compliance metrics cards, by-priority table, by-type table, breach trend chart (using date range picker).
- [x] Done

### Task 11: Route + sidebar entry
- **Files:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Add /sla/dashboard route (admin+super_admin), sidebar entry under Management section.
- [x] Done

### Task 12: i18n translations EN/ES
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** Add page.sla_dashboard.* keys for dashboard page.
- [x] Done
