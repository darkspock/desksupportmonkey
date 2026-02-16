# Tasks: F1 - Departments CRUD UX

**Feature:** Departments CRUD UX Improvements
**Date:** 2026-02-16

---

## Summary

The Departments page (`/departments`) currently supports Create and Delete but is missing Edit (rename) functionality. The backend already has a `PUT /api/v1/departments/{id}` endpoint. Only frontend work is needed.

---

## Phase 1: Frontend

### T1.1: Add inline edit to DepartmentsPage
- **File:** `web/app/src/pages/admin/DepartmentsPage.tsx`
- Add an "Edit" button next to Delete in the Actions column
- On click: toggle the department name to an editable input field (inline edit)
- On submit: `PUT /api/v1/departments/{id}` with new name
- On success: invalidate departments query, show success feedback
- On cancel: revert to display mode
- Handle errors (e.g., duplicate name → 409)

## Phase 2: Verification

### T2.1: Manual E2E test
- [x] Admin clicks "Edit" on a department
- [x] Name field becomes editable
- [x] Admin changes name and submits
- [x] Department name updates in the list
- [x] Duplicate name shows error message
- [x] Cancel reverts without changes
