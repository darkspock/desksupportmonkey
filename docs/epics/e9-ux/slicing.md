# Slicing: E9 - UX Improvements & Frontend Experience Refresh

**Epic:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-02-16

---

## Features

| # | Feature | Description | Depends | Status |
|---|---------|-------------|---------|--------|
| F0 | Invite User by Email | Admin can invite users via email from the Users page, sending a magic link | - | Implemented |
| F1 | Departments CRUD UX | Add edit (rename) functionality to Departments page; backend already supports PUT | - | Implemented |
| F2 | Asset Detail Page Polish | Format event history data properly instead of raw JSON; improve overall layout | - | Implemented |
| F3 | Resolve User IDs to Names | Show user names/emails instead of raw IDs in requests, dashboard, and notes | - | Implemented |
| F4 | Asset Assignment UI | Add assign/unassign user buttons on asset detail page; backend endpoints already exist | - | Implemented |
| F5 | Standardize Date Format | Replace all toLocaleDateString/toLocaleString with YYYY/MM/DD format across 7 files (11 instances) | - | Implemented |
| F6 | Confirmation Dialogs | Add confirmation dialogs for destructive actions: department delete, user deactivate, company status change | - | Implemented |
| F7 | Mutation Feedback | Add success/error toast notifications for mutations that lack feedback (notifications mark-read, user toggle, company status, department delete) | - | Implemented |
| F8 | Empty State CTAs | Add call-to-action on MyEquipmentPage empty state (e.g., link to request equipment) | - | Implemented |
| F9 | i18n: Spanish & English | Add multi-language support (ES/EN) with language selector in header top-right | - | Implemented |
| F10 | Asset Edit & Status Change | Add edit button and status change dropdown on asset detail page; backend PUT and PATCH /status exist | - | Implemented |
| F11 | Request Priority Change | Add priority change dropdown on request detail page; backend PATCH /priority exists | - | Implemented |
| F12 | User Department Assignment | Add department assignment dropdown on Users page; backend PATCH /department exists | - | Implemented |
| F13 | Dashboard: Missing Alerts & Trend | Add warranty alerts, aging alerts, and request trend chart to dashboard; backend endpoints exist | - | Implemented |
| F14 | Company Edit UI | Add edit company name/domains on Companies page; backend PUT exists | - | Implemented |
| F15 | Auth Brand Refresh | Redesign auth screens and use README brand image (`web/site/logo.png`) as login visual anchor | F16 | Implemented |
| F16 | Design System Foundation | Add tokenized base styles and shared form/action primitives to remove ad-hoc page styling | - | Implemented |
| F17 | Responsive App Shell | Improve sidebar/header/mobile behavior and spacing across breakpoints | F16 | Implemented |
| F18 | Accessibility Polish | Improve keyboard/focus/labels/tooltips for interactive controls and icon actions | F16, F17 | Implemented |
| F19 | Unified State UX | Standardize loading/empty/error and mutation feedback patterns in core pages | F16 | Implemented |
| F20 | Operational Table UX Polish | Improve dense list usability (filters/actions consistency, clarity, row affordances) | F16, F19 | Implemented |
| F21 | Role-Based Route Guards | Enforce authorization at routing/layout level so users cannot access unauthorized pages by URL | - | Implemented |
| F22 | Real-Time Notifications Hardening | Wire WebSocket notifications to unread badge/list updates with polling fallback | F19 | Implemented |
| F23 | Auth Return Route | Preserve intended route on auth redirect and restore after successful login | F21 | Implemented |
| F24 | Global Error Boundary | Add router/app-level error boundary with recovery UI and safe reset action | F19 | Implemented |
| F25 | SPA Navigation Consistency | Replace internal `window.location` navigations with React Router navigation patterns | F16, F21 | Implemented |

## Dependency Graph

```
F16 (design system foundation)
 ├── F15 (auth brand refresh)
 ├── F17 (responsive app shell)
 │    └── F18 (accessibility polish)
 ├── F19 (unified state UX)
 │    ├── F20 (operational table UX polish)
 │    ├── F22 (realtime notifications hardening)
 │    └── F24 (global error boundary)
 │
 └── Existing E9 feature stream:
F0 (invite user)
F1 (departments CRUD UX)
F2 (asset detail polish)
F3 (resolve user IDs to names)
F4 (asset assignment UI)        ── depends on F3 for user display
F5 (date format)
F6 (confirmation dialogs)
F7 (mutation feedback)
F8 (empty state CTAs)
F9 (i18n ES/EN)
F10 (asset edit & status)       ── depends on F2 for detail page polish
F11 (request priority change)
F12 (user department assignment)
F13 (dashboard alerts & trend)
F14 (company edit)

F21 (role-based route guards)
 ├── F23 (auth return route)
 └── F25 (spa navigation consistency)
```

All features are independent unless noted. F4 benefits from F3, F10 benefits from F2. New quality features F15-F20 establish a stronger UX baseline before broad page-level polish.

---

## Implementation Phases

1. **Foundation**
- F16 Design System Foundation
- F15 Auth Brand Refresh
- F17 Responsive App Shell

2. **Interaction Quality**
- F18 Accessibility Polish
- F19 Unified State UX
- F20 Operational Table UX Polish

3. **Reliability & Navigation**
- F21 Role-Based Route Guards
- F23 Auth Return Route
- F22 Real-Time Notifications Hardening
- F24 Global Error Boundary
- F25 SPA Navigation Consistency

4. **Functional UX Completion**
- F0 through F14

---

## Notes

- EPIC09 now combines two tracks:
- EPIC09 now combines three tracks:
  - Existing functional UX gaps (F0-F14)
  - Frontend quality uplift (F15-F20)
  - Reliability and navigation hardening (F21-F25)
- Implementation has been completed for F0-F25.
- F9 is implemented with an in-repo i18n provider (`web/app/src/lib/i18n.tsx`) and EN/ES dictionaries, preserving the same product behavior originally requested.
- Automated validation used during execution: `npm run lint`, `npm run build`, `pytest -q` (passing).
