# Tasks: F6 - Confirmation Dialogs

**Feature:** Confirmation Dialogs for Destructive Actions
**Date:** 2026-02-16

---

## Summary

Per SCREEN_DESIGN_GUIDE: any action that performs `POST`/`PUT`/`DELETE` state changes must require confirmation. Currently 3 pages perform destructive actions without confirmation.

---

## Phase 1: Shared Component

### T1.1: Create ConfirmDialog component
- **File:** `web/app/src/components/ui/ConfirmDialog.tsx` (NEW)
- Simple modal with title, message, Confirm and Cancel buttons
- Confirm button should be red/destructive styled for delete actions
- Props: `open`, `title`, `message`, `onConfirm`, `onCancel`, `confirmLabel`

## Phase 2: Apply to pages

### T2.1: DepartmentsPage - confirm delete
- **File:** `pages/admin/DepartmentsPage.tsx` line 79
- Wrap `deleteDept.mutate(d.id)` with confirmation dialog

### T2.2: UsersPage - confirm deactivate
- **File:** `pages/admin/UsersPage.tsx` line 89
- Wrap deactivate action with confirmation (activate can proceed without)

### T2.3: CompaniesPage - confirm status change to suspended/deactivated
- **File:** `pages/superadmin/CompaniesPage.tsx` line 105
- Wrap destructive status changes with confirmation
