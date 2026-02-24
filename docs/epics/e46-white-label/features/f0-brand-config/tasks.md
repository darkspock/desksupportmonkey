# Tasks: F0 — Brand Configuration Layer

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-24

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Create brand config module | S | FE |
| 2 | Replace hardcoded refs in Sidebar.tsx | S | FE |
| 3 | Replace hardcoded refs in Header.tsx | S | FE |
| 4 | Replace hardcoded refs in AuthShell.tsx | S | FE |
| 5 | Move brand strings out of i18n locales | S | FE |
| 6 | Make index.html title dynamic | S | FE |
| 7 | Use brand slug in localStorage keys | S | FE |
| 8 | Verify no hardcoded brand strings remain | S | FE |

## Detailed Tasks

### Phase 1: Configuration

#### Task 1: Create brand config module
- **Files:** `web/app/src/config/brand.ts`
- **What:** Create a single file that reads `import.meta.env.VITE_BRAND_*` variables and exports a typed `brand` object with defaults matching current "DeskSupportMonkey" identity:
  ```ts
  export const brand = {
    name: import.meta.env.VITE_BRAND_NAME ?? 'DeskSupportMonkey',
    shortName: import.meta.env.VITE_BRAND_SHORT_NAME ?? 'DS Monkey',
    slug: import.meta.env.VITE_BRAND_SLUG ?? 'dsm',
    tagline: import.meta.env.VITE_BRAND_TAGLINE ?? 'IT operations, service desk, and inventory in one place.',
    description: import.meta.env.VITE_BRAND_DESCRIPTION ?? 'Manage requests, assets, users, and reporting workflows...',
    logoPath: `/brands/${import.meta.env.VITE_BRAND_SLUG ?? 'dsm'}/logo.png`,
    faviconPath: `/brands/${import.meta.env.VITE_BRAND_SLUG ?? 'dsm'}/favicon.png`,
    loginImagePath: `/brands/${import.meta.env.VITE_BRAND_SLUG ?? 'dsm'}/brand-login.png`,
  }
  ```
- **Deps:** None
- **Acceptance:** Importing `brand` from this file returns correct values with defaults
- [x] Done

### Phase 2: Replace Hardcoded References

#### Task 2: Replace hardcoded refs in Sidebar.tsx
- **Files:** `web/app/src/components/layout/Sidebar.tsx`
- **What:** Import `brand` config and replace:
  - `src="/logo.png"` → `src={brand.logoPath}`
  - `alt="DeskSupportMonkey"` → `alt={brand.name}`
  - `"DS Monkey"` text → `brand.shortName`
- **Deps:** Task 1
- **Acceptance:** Sidebar shows brand name and logo from config
- [x] Done

#### Task 3: Replace hardcoded refs in Header.tsx
- **Files:** `web/app/src/components/layout/Header.tsx`
- **What:** Import `brand` config and replace `"DeskSupportMonkey"` with `brand.name`
- **Deps:** Task 1
- **Acceptance:** Mobile header shows configured brand name
- [x] Done

#### Task 4: Replace hardcoded refs in AuthShell.tsx
- **Files:** `web/app/src/components/auth/AuthShell.tsx`
- **What:** Import `brand` config and replace:
  - Logo `src` → `brand.loginImagePath`
  - `"DeskSupportMonkey"` text → `brand.name`
  - Alt text → `brand.name`
- **Deps:** Task 1
- **Acceptance:** Auth pages show configured brand identity
- [x] Done

#### Task 5: Move brand strings out of i18n locales
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Remove brand-specific keys (`auth.brand_tagline`, `auth.brand_subtitle`, `auth.brand_caption`, etc.) from locale files. Components that used these should read from `brand` config instead. Keep only role/feature translation strings in i18n.
- **Deps:** Task 1, Task 4
- **Acceptance:** Locale files contain no brand-specific strings; brand taglines come from config
- [x] Done

#### Task 6: Make index.html title dynamic
- **Files:** `web/app/index.html`, `web/app/vite.config.ts`
- **What:** Use `vite-plugin-html` or a simple Vite plugin to replace `<title>` with the value of `VITE_BRAND_NAME` at build time. Alternatively, set `document.title` in `main.tsx` from brand config.
- **Deps:** Task 1
- **Acceptance:** Built HTML has the correct brand name as page title
- [x] Done

#### Task 7: Use brand slug in localStorage keys
- **Files:** `web/app/src/lib/i18n.tsx`
- **What:** Replace hardcoded `'dsm.language'` localStorage key with `` `${brand.slug}.language` `` to avoid conflicts if two brands are served from the same domain.
- **Deps:** Task 1
- **Acceptance:** Language preference is stored under `{slug}.language` in localStorage
- [x] Done

### Phase 3: Validation

#### Task 8: Verify no hardcoded brand strings remain
- **Files:** All `web/app/src/**/*.{ts,tsx}`, `web/app/index.html`
- **What:** Search entire frontend source for "DeskSupportMonkey", "DS Monkey", "Desk Support Monkey" and confirm zero matches outside of `brand.ts` defaults and documentation files.
- **Deps:** Tasks 2-7
- **Acceptance:** `grep -r "DeskSupportMonkey\|DS Monkey" web/app/src/ --include="*.ts" --include="*.tsx"` returns only `config/brand.ts`
- [x] Done
