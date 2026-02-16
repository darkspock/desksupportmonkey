# Tasks: F15 - Auth Brand Refresh

**Feature:** Auth Experience Redesign + Branding Alignment
**Date:** 2026-02-16

---

## Summary

Auth pages are functional but visually basic and inconsistent. Introduce a shared auth shell and redesign login/register/verify/set-password for stronger hierarchy and trust.

Mandatory requirement: use the same image source referenced by root README (`web/site/logo.png`) as the login visual anchor.

---

## Phase 1: Asset and Layout Foundation

### T1.1: Define branded auth visual source
- Confirm `web/site/logo.png` as source of truth.
- Expose it to frontend runtime via public asset copy or equivalent bundling-safe strategy.
- Document chosen approach in this feature PR.

### T1.2: Create reusable AuthShell
- **File:** `web/app/src/components/auth/AuthShell.tsx` (NEW)
- 2-panel layout (desktop): brand visual + form content
- 1-column stacked layout (mobile)
- Shared spacing, typography, and content width constraints

## Phase 2: Page Refactor

### T2.1: Redesign LoginPage
- **File:** `web/app/src/pages/auth/LoginPage.tsx`
- Use `AuthShell`
- Keep both login modes (magic link/password)
- Improve input hierarchy, helper text, and error clarity
- Use README brand image as prominent visual element

### T2.2: Redesign Register/Verify/SetPassword pages
- **Files:** `RegisterPage.tsx`, `VerifyPage.tsx`, `SetPasswordPage.tsx`
- Move to shared shell and consistent action hierarchy
- Align success/error blocks and CTA placement

## Phase 3: Verification

### T3.1: Manual checks
- [ ] Auth pages render correctly on desktop/tablet/mobile
- [ ] Login displays branded image from README source (`web/site/logo.png`)
- [ ] Magic link and password flows still work
- [ ] Register and password setup flows remain functional
- [ ] No auth route regression (`/auth/*`)

