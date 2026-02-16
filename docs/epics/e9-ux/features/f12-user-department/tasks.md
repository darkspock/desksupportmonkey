# Tasks: F12 - User Department Assignment

**Feature:** User Department Assignment UI
**Date:** 2026-02-16

---

## Summary

Admins cannot assign users to departments from the UI. Backend `PATCH /api/v1/users/{id}/department` exists. Only frontend work needed.

---

## Phase 1: Frontend

### T1.1: Add department column and selector to UsersPage
- **File:** `web/app/src/pages/admin/UsersPage.tsx`
- Add "Department" column to the users table
- Show a dropdown with available departments (fetch from `GET /departments`)
- On change: `PATCH /api/v1/users/{id}/department` with `{ department_id }`
- Include an empty option to unassign from department (send `{ department_id: null }`)
- On success: invalidate users query
