# Tasks: F23 - Auth Return Route

**Feature:** Preserve and Restore Intended Route After Authentication
**Date:** 2026-02-16

---

## Summary

When users are redirected to login due to missing/expired session, app should remember the target route and return there after successful authentication.

---

## Phase 1: Redirect Contract

### T1.1: Define return-route mechanism
- Store intended route in query param or location state (or both).
- Ensure mechanism works for:
  - direct protected URL access while logged out
  - session expiration (`401`) while navigating.

## Phase 2: Implement Flow

### T2.1: Capture intended route on guard redirect
- **Files:** route guard/app layout/auth handling files.
- On auth redirect, include return target.

### T2.2: Consume return route on login success
- **File:** `web/app/src/pages/auth/LoginPage.tsx`
- After successful login, navigate to intended route if present; fallback to default role landing.

### T2.3: Update API 401 behavior
- **File:** `web/app/src/lib/api.ts`
- Preserve current route before redirecting to login.

## Phase 3: Verification

### T3.1: Manual checks
- [x] Logged-out user opening protected route returns there after login
- [x] 401 during active session sends user to login and then back to intended route
- [x] Invalid/unsafe return routes are rejected safely (fallback used)

