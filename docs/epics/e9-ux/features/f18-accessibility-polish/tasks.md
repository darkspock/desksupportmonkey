# Tasks: F18 - Accessibility Polish

**Feature:** Accessibility and Interaction Clarity
**Date:** 2026-02-16

---

## Summary

Improve accessibility baseline in key flows: keyboard navigation, focus states, icon-action discoverability, and semantic labeling.

---

## Phase 1: Focus and Keyboard

### T1.1: Standardize focus visibility
- Ensure all interactive controls have visible focus styles.
- Apply consistent focus ring token from F16.

### T1.2: Keyboard operability
- Verify modals, dropdowns, menus, and dialogs are keyboard operable.
- Ensure escape/close behavior is predictable.

## Phase 2: Labels and Tooltips

### T2.1: Icon-only actions
- Add visible tooltips for icon-only controls.
- Keep `aria-label` on icon-only buttons.

### T2.2: Semantic labels and structure
- Ensure form controls have explicit labels.
- Ensure headings follow clear hierarchy per screen.

## Phase 3: Color and Contrast

### T3.1: Contrast pass on critical UI
- Validate primary actions, badges, and text contrast on major pages.
- Fix low-contrast combinations introduced by visual refresh.

## Phase 4: Verification

### T4.1: Manual checks
- [ ] Keyboard-only navigation works on auth, tables, and detail pages
- [ ] Focus indicator is always visible
- [ ] Icon-only actions include tooltip and aria-label
- [ ] No critical contrast issues on default theme

