# Tasks: F7 - Mutation Feedback

**Feature:** Toast Notifications for Mutations
**Date:** 2026-02-16

---

## Summary

Per SCREEN_DESIGN_GUIDE: users must always know loading, success, or failure state. Several mutations complete silently without feedback.

---

## Phase 1: Toast System

### T1.1: Add toast notification system
- **File:** `web/app/src/components/ui/Toast.tsx` (NEW) or use a lightweight library
- Simple toast component: success (green), error (red)
- Auto-dismiss after 3 seconds
- Stackable if multiple toasts

## Phase 2: Add feedback to silent mutations

### T2.1: NotificationsPage - mark all read
- **File:** `pages/employee/NotificationsPage.tsx` line 42-43
- Add success toast on markAllRead

### T2.2: UsersPage - toggle active
- **File:** `pages/admin/UsersPage.tsx` line 43-46
- Add success/error toast on toggleActive

### T2.3: CompaniesPage - change status
- **File:** `pages/superadmin/CompaniesPage.tsx` line 46-49
- Add success/error toast on changeStatus

### T2.4: DepartmentsPage - delete
- **File:** `pages/admin/DepartmentsPage.tsx` line 38-41
- Add success/error toast on deleteDept
