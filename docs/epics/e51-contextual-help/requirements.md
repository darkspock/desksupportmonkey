# E51 — Contextual Help System

## Problem

The app has 40+ pages but no in-app help. Users need contextual guidance explaining what each page does and how to use it.

## Solution

A floating help button (bottom-right) opens a slide-in panel with page-specific content and a support contact (support@dsmcontrol.com). Content changes dynamically based on the current route.

## Requirements

1. **Floating help button** — visible on all authenticated pages, bottom-right corner
2. **Slide-in panel** — opens on click with page-specific help text
3. **Route-aware content** — help text changes when navigating between pages
4. **Support contact** — panel includes mailto link to support@dsmcontrol.com
5. **Bottom padding** — all pages have extra bottom padding so content scrolls past the button
6. **Close interactions** — panel closes on X button, click outside, or ESC key
7. **i18n** — all text available in English and Spanish

## Non-functional

- No backend changes required (frontend-only feature)
- Help content stored as i18n translation keys
- Z-index layering: button z-[80], panel z-[85], below modals at z-[90]
