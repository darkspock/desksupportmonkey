# E9: UX Improvements - Feature Slicing

**Date:** 2026-02-16

---

## Features

| # | Feature | Description | Depends | Status |
|---|---------|-------------|---------|--------|
| F0 | Invite User by Email | Admin can invite users via email from the Users page, sending a magic link | - | Pending |
| F1 | Departments CRUD UX | Add edit (rename) functionality to Departments page; backend already supports PUT | - | Pending |
| F2 | Asset Detail Page Polish | Format event history data properly instead of raw JSON; improve overall layout | - | Pending |
| F3 | Resolve User IDs to Names | Show user names/emails instead of raw IDs in requests, dashboard, and notes | - | Pending |
| F4 | Asset Assignment UI | Add assign/unassign user buttons on asset detail page; backend endpoints already exist | - | Pending |
| F5 | Standardize Date Format | Replace all toLocaleDateString/toLocaleString with YYYY/MM/DD format across 7 files (11 instances) | - | Pending |
| F6 | Confirmation Dialogs | Add confirmation dialogs for destructive actions: department delete, user deactivate, company status change | - | Pending |
| F7 | Mutation Feedback | Add success/error toast notifications for mutations that lack feedback (notifications mark-read, user toggle, company status, department delete) | - | Pending |
| F8 | Empty State CTAs | Add call-to-action on MyEquipmentPage empty state (e.g., link to request equipment) | - | Pending |
| F9 | i18n: Spanish & English | Add multi-language support (ES/EN) with react-i18next; language selector in header top-right | - | Pending |
| F10 | Asset Edit & Status Change | Add edit button and status change dropdown on asset detail page; backend PUT and PATCH /status exist | - | Pending |
| F11 | Request Priority Change | Add priority change dropdown on request detail page; backend PATCH /priority exists | - | Pending |
| F12 | User Department Assignment | Add department assignment dropdown on Users page; backend PATCH /department exists | - | Pending |
| F13 | Dashboard: Missing Alerts & Trend | Add warranty alerts, aging alerts, and request trend chart to dashboard; backend endpoints exist | - | Pending |
| F14 | Company Edit UI | Add edit company name/domains on Companies page; backend PUT exists | - | Pending |

## Dependency Graph

```
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
```

All features are independent unless noted. F4 benefits from F3, F10 benefits from F2.
