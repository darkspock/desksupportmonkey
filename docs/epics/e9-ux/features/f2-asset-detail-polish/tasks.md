# Tasks: F2 - Asset Detail Page Polish

**Feature:** Asset Detail Page Polish
**Date:** 2026-02-16

---

## Summary

The Asset Detail page (`/assets/:id`) displays event history data as raw `JSON.stringify` output, which is hard to read. The event data should be formatted into human-readable text based on event type (e.g., "Assigned to John Doe", "Status changed from available to in_use").

---

## Phase 1: Frontend

### T1.1: Format event data in AssetDetailPage
- **File:** `web/app/src/pages/technician/AssetDetailPage.tsx`
- Replace `JSON.stringify(e.data)` with a formatter function
- Map event types to human-readable descriptions:
  - `created` → "Asset created"
  - `assigned` → "Assigned to {user}"
  - `unassigned` → "Unassigned from {user}"
  - `status_changed` → "Status: {old} → {new}"
  - `updated` → show changed fields
- Fallback to formatted key-value display for unknown event types

## Phase 2: Verification

### T2.1: Manual E2E test
- [x] Navigate to an asset detail page
- [x] Event history shows human-readable descriptions instead of raw JSON
- [x] All event types render correctly
- [x] Unknown event types show graceful fallback
