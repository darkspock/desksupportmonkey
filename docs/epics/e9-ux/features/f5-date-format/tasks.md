# Tasks: F5 - Standardize Date Format

**Feature:** Standardize Date Format to YYYY/MM/DD
**Date:** 2026-02-16

---

## Summary

Per SCREEN_DESIGN_GUIDE: all visible dates must use `YYYY/MM/DD` format. Currently 11 instances across 7 files use `toLocaleDateString()` or `toLocaleString()` which produces locale-dependent formats.

**Approach:** Create a shared `formatDate` and `formatDateTime` utility, then replace all instances.

---

## Phase 1: Utility

### T1.1: Create date formatting utility
- **File:** `web/app/src/lib/date.ts` (NEW)
- `formatDate(date: string | Date): string` → `YYYY/MM/DD`
- `formatDateTime(date: string | Date): string` → `YYYY/MM/DD HH:mm`

## Phase 2: Replace all instances

### T2.1: Update all date displays
Files to update (date-only → `formatDate`):
- `pages/employee/MyRequestsPage.tsx` line 55
- `pages/technician/RequestQueuePage.tsx` line 82
- `pages/admin/DepartmentsPage.tsx` line 77

Files to update (date+time → `formatDateTime`):
- `pages/employee/NotificationsPage.tsx` line 62
- `pages/technician/AssetDetailPage.tsx` line 59
- `pages/technician/RequestDetailPage.tsx` lines 91, 117, 143
- `pages/admin/ReportsPage.tsx` lines 70, 71
