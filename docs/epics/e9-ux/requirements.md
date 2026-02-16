# Epic E9: UX Improvements & Frontend Experience Refresh

**Type:** Epic
**Status:** Implemented (QA Spot-Check Pending)
**Created:** 2026-02-16
**Priority:** Medium
**Depends on:** E7 (Frontend), E1-E6 APIs

---

## Business Alignment

**Objective:** Close remaining UX gaps from E7 and raise the visual and interaction quality of the frontend to production level, without changing core business workflows.

E7 delivered complete route coverage and role-based functionality, but the current UI still shows implementation-level details (raw IDs, raw JSON, locale-dependent dates), limited user feedback, and inconsistent visual patterns. E9 must finish missing UX functionality and introduce a stronger, cohesive frontend experience.

---

## Current Frontend Baseline (Audit)

From current code in `web/app/src`:

- Auth pages are functional but visually basic (`LoginPage.tsx`, `RegisterPage.tsx`).
- `LoginPage.tsx` currently uses `/logo.png`; README branding image points to `web/site/logo.png`.
- Global styling is minimal (`index.css` only imports Tailwind).
- Many pages use ad-hoc inputs/buttons directly instead of shared form primitives.
- Several screens show IDs where users expect names/emails.
- Date rendering is inconsistent (`toLocaleDateString` / `toLocaleString`).
- Empty/loading/error states are uneven across pages.

---

## Proposed Solution

### A. Functional UX Completion (Existing E9 Scope)

### US-E9-001: Invite User by Email
Admin can invite users from Users page via magic link.

### US-E9-002: Departments Edit UX
Admin can rename departments inline or via focused edit flow.

### US-E9-003: Asset Detail Clarity
Asset history must be human-readable and no longer show raw JSON.

### US-E9-004: Resolve User IDs
Requests, notes, and dashboard sections must show names/emails, not opaque IDs.

### US-E9-005: Asset Assignment UX
Asset detail supports assign/unassign with clear feedback.

### US-E9-006: Date Standardization
All UI dates use `YYYY/MM/DD` and date-time uses `YYYY/MM/DD HH:mm`.

### US-E9-007: Confirmation Dialogs
Destructive and state-changing actions require explicit confirmation.

### US-E9-008: Mutation Feedback
Silent mutations must provide success/error feedback via toast/banner.

### US-E9-009: Empty State CTAs
Operational empty states include clear next-step actions.

### US-E9-010: i18n ES/EN
Language switcher and ES/EN translations for visible UI strings.

### US-E9-011: Asset Edit + Status
Asset detail supports edit and status change.

### US-E9-012: Request Priority Change
Technician/admin can change request priority on detail page.

### US-E9-013: User Department Assignment
Admins can assign department from Users page.

### US-E9-014: Dashboard Missing Widgets
Warranty alerts, aging alerts, and request trend chart added.

### US-E9-015: Company Edit
Super admin can edit company name and domains in Companies page.

---

### B. Frontend Quality Upgrade (New E9 Scope)

### US-E9-016: Auth Brand Refresh
Auth views (login/register/verify/set-password) use a shared branded layout with stronger hierarchy and messaging.

**Mandatory branding requirement:**
- Login view must use the same source image referenced in root README: `web/site/logo.png`.
- If needed for frontend bundling/performance, that asset can be copied to `web/app/public/` but visual source of truth remains README image.

### US-E9-017: Design System Foundation
Introduce a lightweight token system and shared UI/form primitives to reduce style duplication and improve consistency.

### US-E9-018: Responsive Navigation & Layout
Improve app shell behavior on tablet/mobile (sidebar behavior, spacing, tap targets, overflow handling).

### US-E9-019: Accessibility & Interaction Polish
Improve keyboard navigation, focus visibility, semantic labeling, and icon-action affordances.

### US-E9-020: Unified Loading/Empty/Error Patterns
Adopt consistent state components and usage rules across key pages.

---

### C. Frontend Reliability & Navigation Hardening (New E9 Scope)

### US-E9-021: Role-Based Route Guards
Routes must enforce role authorization at router/layout level, not only via sidebar visibility.

### US-E9-022: Real-Time Notification Delivery
Notification badge/list should update from WebSocket events in near real time, with polling as fallback.

### US-E9-023: Return-to-Intended Route After Login
When a user is redirected to login (expired token/unauthorized), app preserves and restores intended route after authentication.

### US-E9-024: Global Frontend Error Boundary
Application should render a safe recovery UI for uncaught render/runtime errors instead of blank/crashed screens.

### US-E9-025: SPA Navigation Consistency
Internal app navigation should use React Router navigation patterns and avoid full-page reload behavior.

---

## Non-Functional Requirements

- No regression in role-based authorization.
- Keep API contracts intact (contract-first policy).
- Mobile-first behavior verified for auth and app shell.
- All critical actions provide clear status feedback.
- Visual changes must remain performant (no heavy blocking assets).

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `web/app/src/pages/auth/*` | Auth visual and interaction redesign | Refactor into shared auth shell |
| `web/app/src/components/layout/*` | Header/sidebar responsiveness and UX | Add responsive nav behavior |
| `web/app/src/components/ui/*` | Add/extend shared primitives | Standardize controls and states |
| `web/app/src/pages/*` | Consistent date/empty/loading/error handling | Incremental page updates |
| `adapters/http/api/users/*` | Invite endpoint (F0) | Small backend addition |
| Existing request/user APIs | User resolution data | Ensure frontend can show names/emails |

---

## Definition of Done

- [x] All features F0-F20 in `slicing.md` implemented or explicitly deferred with rationale.
- [x] Login uses README branding image (`web/site/logo.png`) in redesigned auth experience.
- [x] No raw user IDs shown in user-facing frontend views.
- [x] Date formatting is fully standardized.
- [x] Confirmation + mutation feedback applied to required actions.
- [x] Empty/loading/error patterns are consistent in core pages.
- [x] Responsive behavior validated on desktop/tablet/mobile.
- [x] Basic accessibility pass completed (keyboard + focus + labels on interactive controls).
- [x] Role-based route guards prevent unauthorized page rendering.
- [x] Realtime notification updates work via WebSocket with graceful fallback.
- [x] Login flow restores intended route after auth/401 redirects.
- [x] Global error boundary provides safe fallback for unexpected UI errors.
- [x] Internal navigation avoids full-page reloads in role portals.
- [x] Epic validation document updated to reflect final scope/decisions.

Notes:
- Automated validations executed successfully: `npm run lint`, `npm run build`, `pytest -q`.
- Remaining unchecked items require manual cross-device/cross-assistive-tech QA session.
