# Tasks: F25 - SPA Navigation Consistency

**Feature:** Router-First Internal Navigation
**Date:** 2026-02-16

---

## Summary

Some internal flows still navigate with `window.location`, causing full-page reload behavior and breaking SPA UX consistency.

---

## Phase 1: Audit and Standards

### T1.1: Audit non-router navigation usage
- Find all `window.location` internal navigations in frontend.
- Classify internal vs external/intentional full reload.

### T1.2: Define navigation standard
- Internal app routes: `Link`, `NavLink`, `useNavigate`.
- External URLs: explicit full navigation allowed.

## Phase 2: Refactor

### T2.1: Replace internal full reload patterns
- Start with known cases:
  - `web/app/src/pages/employee/MyRequestsPage.tsx`
- Replace with router navigation while preserving behavior.

### T2.2: Re-test route transitions
- Ensure query state and page transitions remain correct.

## Phase 3: Verification

### T3.1: Manual checks
- [x] Internal page transitions do not trigger full reload
- [x] Browser back/forward works correctly after navigation
- [x] No regression in deep-linkable pages

