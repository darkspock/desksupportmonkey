# Tasks: F24 - Global Error Boundary

**Feature:** Frontend Runtime Resilience
**Date:** 2026-02-16

---

## Summary

Unexpected runtime/render errors currently risk breaking the whole UI experience. Add a global error boundary strategy with safe fallback and recovery actions.

---

## Phase 1: Boundary Strategy

### T1.1: Define boundary scope
- Router-level fallback for route render errors.
- Optional component-level boundaries for high-risk areas (charts/details).

### T1.2: Define fallback UX
- User-friendly message
- Retry/back-home action
- Optional diagnostics reference for support/dev

## Phase 2: Implementation

### T2.1: Add global boundary wiring
- **Files:** `web/app/src/router.tsx`, top-level app wrapper if needed.
- Use `errorElement` or equivalent boundary component pattern.

### T2.2: Add reusable error fallback component
- **File:** `web/app/src/components/ui/ErrorState.tsx` (or dedicated boundary UI component).

## Phase 3: Verification

### T3.1: Manual checks
- [x] Forced render error shows fallback instead of blank/crash
- [x] User can recover via retry or navigation action
- [x] Boundary does not break auth/session behavior

