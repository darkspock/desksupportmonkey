# Tasks: F19 - Unified State UX

**Feature:** Consistent Loading, Empty, Error, and Feedback States
**Date:** 2026-02-16

---

## Summary

State handling is currently inconsistent across pages. Define and apply shared patterns so users always understand what is happening and what to do next.

---

## Phase 1: Shared State Components

### T1.1: Add reusable state components
- **Folder:** `web/app/src/components/ui/`
- Add `EmptyState`, `ErrorState`, and optional `Skeleton` helpers.
- Keep APIs simple and composable.

### T1.2: Feedback standardization
- Reuse or create toast/inline feedback approach from F7.
- Define default success/error message style rules.

## Phase 2: Page Adoption

### T2.1: Apply to high-traffic pages
- `DashboardPage.tsx`
- `UsersPage.tsx`
- `DepartmentsPage.tsx`
- `RequestQueuePage.tsx`
- `NotificationsPage.tsx`
- `MyEquipmentPage.tsx`

### T2.2: Empty-state CTA quality
- Ensure empty states include a relevant next action (or explicit reason when no action is possible).

## Phase 3: Verification

### T3.1: Manual checks
- [ ] Loading state appears on every async screen
- [ ] Empty state includes clear message and CTA where relevant
- [ ] Errors are visible and actionable
- [ ] Mutation outcomes are never silent

