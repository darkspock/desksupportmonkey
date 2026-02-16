# Tasks: F14 - Company Edit UI

**Feature:** Company Edit UI
**Date:** 2026-02-16

---

## Summary

Super admins cannot edit company details from the UI. Backend `PUT /api/v1/companies/{id}` and `GET /api/v1/companies/{id}` exist. Only frontend work needed.

---

## Phase 1: Frontend

### T1.1: Add edit action to CompaniesPage
- **File:** `web/app/src/pages/superadmin/CompaniesPage.tsx`
- Add "Edit" button per company row
- On click: open modal with editable fields (name, email_domains)
- Pre-populate with current values (fetch `GET /companies/{id}` or use list data)
- On submit: `PUT /api/v1/companies/{id}`
- On success: invalidate companies query, close modal
