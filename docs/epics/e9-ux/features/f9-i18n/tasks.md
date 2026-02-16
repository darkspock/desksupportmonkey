# Tasks: F9 - i18n: Spanish & English

**Feature:** Multi-language support (ES/EN)
**Date:** 2026-02-16

---

## Summary

Add internationalization to the frontend with Spanish and English support. Users can switch language via a selector in the header (top-right). Language preference is persisted in localStorage.

**Implementation:** In-repo i18n provider (`web/app/src/lib/i18n.tsx`) and EN/ES dictionaries in `web/app/src/locales/*`.

---

## Phase 1: Setup

### T1.1: Configure i18n provider
- **File:** `web/app/src/lib/i18n.tsx` (NEW)
- Configure provider with:
  - Default language: `en`
  - Fallback dictionary: `en`
  - Browser language detection
  - localStorage persistence

### T1.2: Create translation files
- **File:** `web/app/src/locales/en.ts` (NEW)
- **File:** `web/app/src/locales/es.ts` (NEW)
- Extract all user-facing strings from all pages and components
- Organize by namespace/section: `auth`, `sidebar`, `equipment`, `requests`, `assets`, `admin`, `common`

## Phase 2: Language Selector

### T2.1: Add language selector to Header
- **File:** `web/app/src/components/layout/Header.tsx`
- Add a dropdown/toggle (ES/EN) in the top-right area
- On change: switch language via i18n context
- Show current language flag or abbreviation

## Phase 3: Apply translations

### T3.1: Auth pages
- `LoginPage.tsx`, `RegisterPage.tsx`, `VerifyPage.tsx`, `SetPasswordPage.tsx`

### T3.2: Layout components
- `Sidebar.tsx` (nav labels), `Header.tsx`

### T3.3: Employee pages
- `MyEquipmentPage.tsx`, `MyRequestsPage.tsx`, `NewRequestPage.tsx`, `NotificationsPage.tsx`

### T3.4: Technician pages
- `RequestQueuePage.tsx`, `RequestDetailPage.tsx`, `AssetListPage.tsx`, `AssetDetailPage.tsx`, `AssetFormPage.tsx`, `AssetImportPage.tsx`

### T3.5: Admin pages
- `DashboardPage.tsx`, `UsersPage.tsx`, `DepartmentsPage.tsx`, `ReportsPage.tsx`

### T3.6: Super admin pages
- `CompaniesPage.tsx`

### T3.7: Shared UI components
- `Badge.tsx`, `Loading.tsx`, `Pagination.tsx`, empty states, error messages

## Phase 4: Verification

### T4.1: Manual E2E test
- [ ] App loads in browser's language (or default EN)
- [ ] Language selector switches all visible text
- [ ] Language preference persists across page reloads
- [ ] All pages display correctly in both ES and EN
- [ ] No untranslated strings visible
- [ ] StatusBadge values display translated labels
