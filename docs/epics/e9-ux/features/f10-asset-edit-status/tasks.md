# Tasks: F10 - Asset Edit & Status Change

**Feature:** Asset Edit & Status Change UI
**Date:** 2026-02-16

---

## Summary

The asset detail page is read-only. The backend already supports `PUT /api/v1/assets/{id}` (edit) and `PATCH /api/v1/assets/{id}/status` (change status). Only frontend work needed.

---

## Phase 1: Frontend

### T1.1: Add edit form to AssetDetailPage
- **File:** `web/app/src/pages/technician/AssetDetailPage.tsx`
- Add "Edit" button that opens an edit modal/form
- Editable fields: brand, model, purchase_date, warranty_expiration, notes
- On submit: `PUT /api/v1/assets/{id}`
- On success: invalidate asset query, close form

### T1.2: Add status change dropdown to AssetDetailPage
- **File:** `web/app/src/pages/technician/AssetDetailPage.tsx`
- Add status dropdown next to current status badge
- Options: in_stock, assigned, in_repair, decommissioned
- On change: `PATCH /api/v1/assets/{id}/status`
- On success: invalidate asset query
