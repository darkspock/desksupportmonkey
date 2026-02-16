# Tasks: F21 - Role-Based Route Guards

**Feature:** Role Authorization at Route Level
**Date:** 2026-02-16

---

## Summary

Current app shell blocks unauthenticated users but does not enforce role access per route. Add centralized role guards to prevent unauthorized page rendering via direct URL access.

---

## Phase 1: Guard Architecture

### T1.1: Define route-guard strategy
- Choose implementation pattern:
  - guarded route wrapper component, or
  - route metadata + centralized guard check.
- Ensure role rules are defined in one place (avoid duplication across pages).

### T1.2: Add role maps for route groups
- Employee-only routes
- Technician+ routes
- Admin+ routes
- Super-admin-only routes

## Phase 2: Apply Guards

### T2.1: Enforce guards in router/layout
- **Files:** `web/app/src/router.tsx`, `web/app/src/components/layout/AppLayout.tsx`
- Unauthorized access should redirect to safe destination (default dashboard/home by role or generic unauthorized page).

### T2.2: Keep sidebar visibility aligned
- Ensure nav visibility and route guard rules remain consistent.

## Phase 3: Verification

### T3.1: Manual checks
- [ ] Employee cannot open admin/super-admin URLs directly
- [ ] Technician cannot open super-admin URLs directly
- [ ] Admin cannot open super-admin URLs directly
- [ ] Authorized roles access expected routes without regression

