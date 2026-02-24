# Implementation Tasks: Frontend (F2)

**Created:** 2026-02-24
**Total Tasks:** 6
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Page - Dashboard | 1 | L |
| Component - Evidence Panel | 1 | M |
| Router | 1 | S |
| Sidebar | 1 | S |
| Types | 1 | S |
| i18n | 1 | S |

---

### TASK-001: Create ComplianceDashboardPage

- [x] `web/app/src/pages/admin/ComplianceDashboardPage.tsx`
- [x] Framework filter, stat cards, framework breakdown, gap analysis, assessment table, export

### TASK-002: Create ComplianceEvidencePanel

- [x] `web/app/src/components/compliance/ComplianceEvidencePanel.tsx`
- [x] Slide-over panel with evidence list, add/remove evidence

### TASK-003: Add route

- [x] Lazy import and route `/compliance/dashboard` in `web/app/src/router.tsx`

### TASK-004: Add sidebar entry

- [x] Add compliance dashboard nav item under Security section in `web/app/src/components/layout/Sidebar.tsx`

### TASK-005: Add TypeScript types

- [x] `ComplianceStatusType`, `EvidenceTypeValue`, `ControlAssessment`, `ComplianceEvidence`, `FrameworkSummary`, `ComplianceDashboard` in `web/app/src/types/index.ts`

### TASK-006: Add i18n translations

- [x] ~50 keys in `web/app/src/locales/en.ts`
- [x] ~50 keys in `web/app/src/locales/es.ts`
