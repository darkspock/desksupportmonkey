# Tasks: F20 - Operational Table UX Polish

**Feature:** Table Interaction and Dense List Clarity
**Date:** 2026-02-16

---

## Summary

Operational pages are table-heavy. Improve readability and action clarity for high-density list workflows without changing business behavior.

---

## Phase 1: Table Behavior Standards

### T1.1: Define table interaction rules
- Column priority per viewport
- Sticky headers where needed
- Right-aligned action column pattern
- Consistent empty/filter/no-results messaging

### T1.2: Filter/search consistency
- Standardize filter bar spacing and control sizes.
- Keep filter reset behavior predictable.

## Phase 2: Apply to Core Operational Tables

### T2.1: Admin and technician tables
- `UsersPage.tsx`
- `DepartmentsPage.tsx`
- `RequestQueuePage.tsx`
- `AssetListPage.tsx`
- `ReportsPage.tsx`
- `CompaniesPage.tsx`

### T2.2: Row action clarity
- Prefer icon-only actions with tooltips where density requires it.
- Apply confirmation for direct-change/destructive actions.

## Phase 3: Verification

### T3.1: Manual checks
- [ ] Tables remain usable on tablet/mobile (compact behavior defined)
- [ ] Row actions are discoverable and unambiguous
- [ ] Filter/search interactions are consistent across pages
- [ ] Empty and no-result states are clearly differentiated

