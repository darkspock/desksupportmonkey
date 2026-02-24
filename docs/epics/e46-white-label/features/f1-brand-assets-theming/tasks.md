# Tasks: F1 — Brand Assets & Theming

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-24

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Organize brand asset folders | S | FE |
| 2 | Create brand theme CSS override mechanism | S | FE |
| 3 | Update favicon to use brand path | S | FE |

## Detailed Tasks

### Phase 1: Asset Organization

#### Task 1: Organize brand asset folders
- **Files:** `web/app/public/brands/dsm/`
- **What:** Create the default brand folder structure:
  ```
  web/app/public/brands/
  └── dsm/
      ├── logo.png        (move from public/logo.png)
      ├── favicon.png      (copy from logo.png or create)
      ├── brand-login.png  (move from public/brand-login.png)
      └── theme.css        (empty or default — no overrides needed)
  ```
  Keep original `public/logo.png` and `public/brand-login.png` temporarily for backward compatibility, then remove once all references are updated.
- **Deps:** F0 complete
- **Acceptance:** Brand assets load correctly from `/brands/dsm/` path
- [x] Done

### Phase 2: Color Theming

#### Task 2: Create brand theme CSS override mechanism
- **Files:** `web/app/src/index.css`, `web/app/public/brands/dsm/theme.css`
- **What:** Add a mechanism to load a brand-specific CSS file that overrides the default CSS custom properties. Options (pick simplest):
  - **Option A (recommended):** In `main.tsx`, dynamically import `/brands/${brand.slug}/theme.css` as a link tag
  - **Option B:** Use Vite env vars for color values (`VITE_COLOR_PRIMARY`, etc.) and inject them as CSS vars in `index.css`

  The brand `theme.css` can override:
  ```css
  :root {
    --primary: oklch(0.35 0.15 160);
    --sidebar: oklch(0.12 0.01 160);
    --sidebar-foreground: oklch(0.95 0 0);
    --sidebar-primary: oklch(0.45 0.15 160);
    --sidebar-accent: oklch(0.18 0.02 160);
    --sidebar-border: oklch(0.25 0.02 160);
  }
  ```
  This gives full control over the sidebar appearance: background, text color, active item highlight, hover accent, and border separators.
  Default brand (`dsm`) has an empty `theme.css` (no overrides).
- **Deps:** Task 1
- **Acceptance:** Adding color overrides in `theme.css` changes the app's color scheme without touching source code
- [x] Done

#### Task 3: Update favicon to use brand path
- **Files:** `web/app/index.html` or `web/app/src/main.tsx`
- **What:** Set the favicon dynamically to `brand.faviconPath`. Either:
  - Replace the favicon link in `index.html` at build time via Vite plugin
  - Or set it programmatically in `main.tsx`: `document.querySelector('link[rel="icon"]')?.setAttribute('href', brand.faviconPath)`
- **Deps:** Task 1
- **Acceptance:** Each brand build shows its own favicon in the browser tab
- [x] Done
