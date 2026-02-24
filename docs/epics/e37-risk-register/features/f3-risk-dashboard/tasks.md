# Tasks: F3 — Risk Dashboard

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Application: GetRiskDashboardQuery + handler | S | App |
| 2 | HTTP: Dashboard schema + endpoint | S | HTTP |
| 3 | Frontend: RiskDashboardPage with heat map | M | FE |
| 4 | Frontend: route + sidebar entry | S | FE |
| 5 | i18n: dashboard translations EN/ES | S | FE |

## Detailed Tasks

### Task 1: Dashboard query
- **File:** `src/risk_bc/risk/application/queries/get_dashboard.py`
- **What:** GetRiskDashboardQuery(company_id) + handler using repo.get_dashboard_stats(). Returns RiskDashboardDto.
- [x] Done

### Task 2: HTTP endpoint + schema
- **Files:** `adapters/http/api/risks/schemas.py`, `adapters/http/api/risks/routers.py`
- **What:** RiskDashboardResponse schema. GET /api/v1/risks/dashboard endpoint (technician+).
- [x] Done

### Task 3: RiskDashboardPage
- **File:** `web/app/src/pages/technician/RiskDashboardPage.tsx` (NEW)
- **What:** Summary stat cards (total, open, mitigated, accepted, overdue). By-level and by-category breakdown. 5x5 heat map with color-coded cells. Recent risks list with badges.
- [x] Done

### Task 4: Routes + sidebar
- **Files:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Route /risks/dashboard (technician+). Sidebar entry under Security with grid icon.
- [x] Done

### Task 5: i18n translations
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** All page.risk_dashboard.* keys and nav.risk_dashboard.
- [x] Done
