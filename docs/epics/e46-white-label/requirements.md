# Requirements: E46 - White Label & Multi-Brand Deployment

**Epic:** E46
**Date:** 2026-02-24
**Priority:** High
**Depends on:** E0, E7, E9

---

## Problem Statement

The platform currently has a single hardcoded brand identity ("DeskSupportMonkey") embedded across the frontend — in HTML titles, logos, sidebar text, auth pages, CSS color tokens, and i18n strings. This makes it impossible to deploy the same codebase under a different brand name, logo, or visual identity without manually editing source files.

The business needs to deploy multiple instances of the application — each with its own name, logo, color scheme, and database, all built from the same codebase and deployed to different folders or servers. The number of brands is unbounded; the system must make adding a new brand as simple as creating an env file and an asset folder.

## Goals

1. Extract all brand-specific values (name, short name, logo, favicon, colors, taglines) into a centralized configuration layer driven by environment variables at build time
2. Support building multiple branded versions of the frontend from the same source code with a single command
3. Each deployment gets its own `.env` file pointing to a different database, brand config, and deployment folder
4. Zero hardcoded brand references remain in source code — all branding flows through configuration
5. Keep the solution simple: no runtime brand switching, no multi-tenant branding — one build = one brand

## User Stories

### US-1: Build-time Brand Configuration

**As a** DevOps engineer,
**I want to** build the frontend with different brand values by changing environment variables,
**So that** I can produce distinct branded builds from the same source code.

**Acceptance Criteria:**
- [ ] A brand configuration file (`web/app/src/config/brand.ts`) reads brand values from Vite env vars (`import.meta.env.VITE_*`)
- [ ] All brand values have sensible defaults (current "DeskSupportMonkey" identity) so builds work without any env vars set
- [ ] The following values are configurable via env vars:
  - `VITE_BRAND_NAME` — Full brand name (e.g., "DeskSupportMonkey", "IT Service Pro")
  - `VITE_BRAND_SHORT_NAME` — Sidebar short name (e.g., "DS Monkey", "ISP")
  - `VITE_BRAND_SLUG` — URL-safe lowercase identifier (e.g., "dsm", "isp")
  - `VITE_BRAND_TAGLINE` — Auth page tagline
  - `VITE_BRAND_DESCRIPTION` — Auth page description
- [ ] Brand config is a simple TypeScript object exported from one file, not a context/provider
- [ ] Build fails with a clear error if `VITE_BRAND_SLUG` is set but `web/app/public/brands/{slug}/` folder does not exist or is missing required files (`logo.png`)

### US-2: Brand-specific Assets (Logo & Favicon)

**As a** deployer,
**I want to** provide different logos and favicons per brand,
**So that** each deployment has its own visual identity.

**Acceptance Criteria:**
- [ ] Brand assets are organized in folders: `web/app/public/brands/{slug}/logo.png` and `favicon.png`
- [ ] A default brand folder exists: `web/app/public/brands/dsm/` with the current logo
- [ ] `VITE_BRAND_SLUG` determines which brand folder is used for asset paths
- [ ] `index.html` favicon path is dynamically set at build time or uses a generic path that gets resolved
- [ ] Sidebar, Header, and AuthShell reference the brand config for logo path instead of hardcoded `/logo.png`

### US-3: Brand-specific Color Theme

**As a** deployer,
**I want to** customize the color palette per brand,
**So that** each deployment looks distinct.

**Acceptance Criteria:**
- [ ] Primary color tokens (`--primary`, `--sidebar`, `--sidebar-primary`) can be overridden via CSS custom properties or env vars
- [ ] A mechanism exists to load a brand-specific CSS override file (e.g., `brands/{slug}/theme.css`) or inject CSS vars from config
- [ ] Default theme remains the current blue palette if no overrides are specified
- [ ] At minimum, the following colors are brand-customizable: primary, sidebar background (`--sidebar`), sidebar foreground (`--sidebar-foreground`), sidebar accent (`--sidebar-accent`), sidebar border (`--sidebar-border`), sidebar primary (`--sidebar-primary`)

### US-4: Remove All Hardcoded Brand References

**As a** developer,
**I want** zero hardcoded brand strings in the source code,
**So that** all branding is driven by configuration.

**Acceptance Criteria:**
- [ ] `index.html` — title reads from build-time config or uses a template variable
- [ ] `Sidebar.tsx` — logo `src`, `alt` text, and "DS Monkey" text use brand config
- [ ] `Header.tsx` — mobile app name uses brand config
- [ ] `AuthShell.tsx` — logo, brand name text, and alt text use brand config
- [ ] `locales/en.ts` and `locales/es.ts` — brand-specific taglines moved to brand config (i18n keeps only role/feature translations)
- [ ] No string "DeskSupportMonkey" or "DS Monkey" remains hardcoded in any `.tsx`, `.ts`, or `.html` file (except documentation)

### US-5: Per-Brand Build Script

**As a** DevOps engineer,
**I want** a simple command to build for a specific brand,
**So that** I can produce and deploy branded builds easily.

**Acceptance Criteria:**
- [ ] Brand-specific `.env` files exist: `.env.dsm`, `.env.formal` (or similar naming convention)
- [ ] Each brand env file includes `VITE_BRAND_*` variables plus `DATABASE_URL` and any backend-specific config
- [ ] A Makefile target or script builds for a specific brand: `make build-brand BRAND=dsm`
- [ ] The build output goes to a configurable directory (e.g., `dist/dsm/`, `dist/formal/`)
- [ ] The backend can also be started with a brand-specific env file: `make start BRAND=dsm`

### US-6: Brand-aware Email Templates

**As a** deployer,
**I want** outbound emails (magic links, notifications) to show the configured brand name,
**So that** users see consistent branding across the entire experience.

**Acceptance Criteria:**
- [ ] Email subject lines use the brand name instead of hardcoded "DeskSupportMonkey"
- [ ] Email body/templates reference the brand name and logo from backend env vars
- [ ] Backend env var `BRAND_NAME` (non-Vite, for Python) controls the brand name in emails
- [ ] Default value is "DeskSupportMonkey" for backward compatibility

### US-7: Brand-aware PDF Report Templates

**As a** deployer,
**I want** PDF reports to show the configured brand name and logo in headers/footers,
**So that** generated documents match the deployment's brand identity.

**Acceptance Criteria:**
- [ ] Jinja2 report templates in `templates/` use a brand name variable instead of hardcoded text
- [ ] Report header/footer logo is configurable via backend env var (`BRAND_LOGO_PATH` or similar)
- [ ] Default values produce current behavior (DeskSupportMonkey branding)

### US-8: Backend Database Isolation

**As a** deployer,
**I want** each brand deployment to use a separate database,
**So that** data is fully isolated between brands.

**Acceptance Criteria:**
- [ ] `DATABASE_URL` in the brand-specific `.env` file points to a different database per brand
- [ ] No code changes required in the backend — existing `.env` mechanism already supports this
- [ ] Documentation explains how to set up a new brand with its own database
- [ ] Migration commands (`make db-upgrade`) respect the active `.env` file

## Technical Constraints

- **Build-time only**: Brand selection happens at build time via env vars, not at runtime. No brand switching in the browser.
- **Same codebase**: No forks, no branches per brand. One codebase, multiple builds.
- **Backward compatible**: Building without any `VITE_BRAND_*` vars produces the current "DeskSupportMonkey" build exactly as before.
- **Vite native**: Use Vite's built-in `import.meta.env` system — no custom webpack plugins or build tooling.
- **Minimal footprint**: One config file, one brand assets folder. No brand context providers, no runtime brand detection.

## Out of Scope

- Runtime brand switching or dynamic theming
- Per-tenant branding within a single deployment (already handled by `company_name`)
- Backend API response changes — API payloads remain brand-agnostic
- Landing page / marketing site (`web/site/`) — separate concern
- Brand-specific feature flags or functionality differences
- Logo generation or design tooling
