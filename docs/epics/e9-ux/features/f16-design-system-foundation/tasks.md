# Tasks: F16 - Design System Foundation

**Feature:** Shared Visual Tokens and UI Primitives
**Date:** 2026-02-16

---

## Summary

Current frontend styling is mostly page-local Tailwind classes, with minimal global foundation. Add a lightweight design system layer to improve consistency and speed up UX work in all E9 features.

---

## Phase 1: Tokens

### T1.1: Add global design tokens
- **File:** `web/app/src/index.css`
- Define semantic tokens for:
  - color roles (surface, text, border, accent, success, warning, danger)
  - spacing scale references
  - radius and elevation
  - focus ring style

### T1.2: Add typography baseline
- Define heading/body/label sizes and weights via reusable utility classes or CSS variables.
- Ensure readability on dense tables and forms.

## Phase 2: Primitive Components

### T2.1: Add shared action/form primitives
- **Folder:** `web/app/src/components/ui/`
- Add or standardize `Button`, `Input`, `Select`, `Textarea`, `FormField` wrappers.
- Include visual states: default, hover, focus, disabled, error.

### T2.2: Align existing components with tokens
- Update `Card`, `Table`, `Badge`, `Loading`, `Pagination` styles to use tokenized semantics.

## Phase 3: Apply to Key Pages

### T3.1: Replace ad-hoc control styles in core pages
- `LoginPage.tsx`
- `UsersPage.tsx`
- `DepartmentsPage.tsx`
- `RequestQueuePage.tsx`
- `AssetDetailPage.tsx`

## Phase 4: Verification

### T4.1: Manual checks
- [ ] Core controls have consistent look/behavior
- [ ] Error and focus states are visible and consistent
- [ ] No page uses obsolete one-off control styles in critical paths

