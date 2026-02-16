# Tasks: F11 - Request Priority Change

**Feature:** Request Priority Change UI
**Date:** 2026-02-16

---

## Summary

Technicians cannot change request priority from the UI. Backend `PATCH /api/v1/requests/{id}/priority` exists. Only frontend work needed.

---

## Phase 1: Frontend

### T1.1: Add priority dropdown to RequestDetailPage
- **File:** `web/app/src/pages/technician/RequestDetailPage.tsx`
- Add priority dropdown next to the priority badge (tech/admin only)
- Options: low, medium, high, urgent
- On change: `PATCH /api/v1/requests/{id}/priority`
- On success: invalidate request query
