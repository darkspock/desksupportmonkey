# Tasks: F4 - Asset Assignment UI

**Feature:** Asset Assignment UI
**Date:** 2026-02-16

---

## Summary

There is no way to assign/unassign an asset to a user from the frontend. The backend already has `PATCH /api/v1/assets/{id}/assign` and `PATCH /api/v1/assets/{id}/unassign` endpoints. Only frontend work is needed.

---

## Phase 1: Frontend

### T1.1: Add assign/unassign controls to AssetDetailPage
- **File:** `web/app/src/pages/technician/AssetDetailPage.tsx`
- If asset is unassigned: show a user selector (dropdown or search input) + "Assign" button
  - Fetch company users via `GET /api/v1/users` to populate the selector
  - On submit: `PATCH /api/v1/assets/{id}/assign` with `{ user_id: "..." }`
- If asset is assigned: show "Unassign" button
  - On click: `PATCH /api/v1/assets/{id}/unassign`
- On success: invalidate asset query to refresh detail
- Show assigned user's email/name instead of raw ID (depends on F3 or resolve inline)

## Phase 2: Verification

### T2.1: Manual E2E test
- [ ] Technician opens asset detail page
- [ ] Unassigned asset shows user selector + Assign button
- [ ] Selecting a user and clicking Assign works
- [ ] Assigned asset shows user info + Unassign button
- [ ] Clicking Unassign works
- [ ] Event history updates after assign/unassign
