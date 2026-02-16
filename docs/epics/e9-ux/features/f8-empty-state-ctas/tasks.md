# Tasks: F8 - Empty State CTAs

**Feature:** Empty State Call-to-Actions
**Date:** 2026-02-16

---

## Summary

Per SCREEN_DESIGN_GUIDE: empty states should include a CTA so users know what to do next.

---

## Phase 1: Frontend

### T1.1: MyEquipmentPage empty state CTA
- **File:** `web/app/src/pages/employee/MyEquipmentPage.tsx` line 25
- Current: "No equipment assigned to you."
- Add: Link to "Request Equipment" (navigate to `/my/requests/new`)
