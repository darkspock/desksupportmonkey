# Tasks: F17 - Responsive App Shell

**Feature:** Layout and Navigation Responsiveness
**Date:** 2026-02-16

---

## Summary

Current app shell works on desktop but needs stronger behavior for tablet/mobile navigation, spacing, and overflow handling.

---

## Phase 1: AppLayout Structure

### T1.1: Add responsive shell behavior
- **File:** `web/app/src/components/layout/AppLayout.tsx`
- Desktop: persistent sidebar
- Tablet/mobile: collapsible drawer/sidebar
- Ensure content area handles horizontal overflow gracefully

### T1.2: Add mobile nav toggle behavior
- **Files:** `Header.tsx`, `Sidebar.tsx`, `AppLayout.tsx`
- Add trigger button for sidebar drawer on small screens
- Add overlay and close interactions

## Phase 2: Sidebar and Header Polish

### T2.1: Improve sidebar density and active states
- Keep role-based visibility logic
- Improve active item contrast and touch target size

### T2.2: Header adaptability
- Ensure notification/user menu interactions remain usable on narrow widths
- Prevent clipping/overlap with long emails

## Phase 3: Verification

### T3.1: Manual responsive checks
- [x] No layout breaks at common widths (320, 768, 1024, 1440)
- [x] Navigation can be operated with one hand on mobile
- [x] Main content remains readable without horizontal scroll in normal flows
- [x] Role-based nav visibility remains correct

