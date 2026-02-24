# Tasks: F3 — Build & Deploy Tooling

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-24

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Create brand-specific env files | S | Config |
| 2 | Add `.env.*` to .gitignore | S | Config |
| 3 | Add Makefile targets for branded builds | S | Tooling |
| 4 | Add documentation for creating a new brand | S | Docs |

## Detailed Tasks

### Phase 1: Environment Files

#### Task 1: Create brand-specific env files
- **Files:** `.env.dsm.example`, `.env.formal.example` (examples, not actual secrets)
- **What:** Create example env files for each brand deployment. Each includes:
  ```env
  # Brand identity (frontend — build-time)
  VITE_BRAND_NAME=DeskSupportMonkey
  VITE_BRAND_SHORT_NAME=DS Monkey
  VITE_BRAND_SLUG=dsm
  VITE_BRAND_TAGLINE=IT operations, service desk, and inventory in one place.
  VITE_BRAND_DESCRIPTION=Manage requests, assets, users, and reporting workflows...

  # Brand identity (backend — runtime)
  BRAND_NAME=DeskSupportMonkey

  # Database (unique per brand)
  DATABASE_URL=postgresql://postgres:postgres@localhost:5444/dsm_db

  # All other backend config (same as .env.example)
  ...
  ```
  The second brand (`.env.formal.example`) uses a different `DATABASE_URL`, `BRAND_NAME`, `VITE_BRAND_SLUG`, etc.
- **Deps:** F0, F1, F2
- **Acceptance:** Each env file has distinct brand values (frontend + backend) and database URL
- [x] Done

#### Task 2: Add `.env.*` to .gitignore
- **Files:** `.gitignore`
- **What:** Add `.env.*` pattern to `.gitignore` to prevent accidental commit of brand-specific env files containing secrets (`DATABASE_URL`, API keys). Only `.env.*.example` files should be committed.
  ```gitignore
  .env
  .env.*
  !.env.example
  !.env.*.example
  ```
- **Deps:** None
- **Acceptance:** `git status` does not show `.env.dsm` or `.env.formal` as untracked
- [x] Done

### Phase 2: Build Automation

#### Task 3: Add Makefile targets for branded builds
- **Files:** `Makefile`
- **What:** Add targets that use brand-specific env files:
  ```makefile
  # Build frontend for a specific brand
  # Usage: make build-brand BRAND=dsm
  build-brand:
  	cd web/app && env $$(cat ../../.env.$(BRAND) | grep VITE_ | xargs) npm run build -- --outDir ../../dist/$(BRAND)

  # Start backend with a brand-specific env
  # Usage: make start-brand BRAND=dsm
  start-brand:
  	env $$(cat .env.$(BRAND) | xargs) uv run uvicorn app:app --host 0.0.0.0 --port 8001 --reload

  # Apply migrations for a specific brand's database
  # Usage: make db-upgrade-brand BRAND=dsm
  db-upgrade-brand:
  	env $$(cat .env.$(BRAND) | xargs) uv run alembic upgrade head
  ```
- **Deps:** Task 1
- **Acceptance:** `make build-brand BRAND=dsm` produces a complete build in `dist/dsm/`; `make build-brand BRAND=formal` produces a build in `dist/formal/` with different branding
- [x] Done

### Phase 3: Documentation

#### Task 4: Add documentation for creating a new brand
- **Files:** `docs/epics/e46-white-label/guide.md`
- **What:** Write a concise guide covering:
  1. Copy `.env.dsm.example` to `.env.{newbrand}`
  2. Update `VITE_BRAND_*`, `BRAND_NAME`, and `DATABASE_URL`
  3. Create asset folder: `web/app/public/brands/{slug}/` with logo.png, favicon.png, brand-login.png
  4. Optionally add `theme.css` for color overrides
  5. Create the database: `createdb {newbrand}_db`
  6. Run migrations: `make db-upgrade-brand BRAND={newbrand}`
  7. Seed data: `make seed-brand BRAND={newbrand}` (if applicable)
  8. Build frontend: `make build-brand BRAND={newbrand}`
  9. Start backend: `make start-brand BRAND={newbrand}`
  10. Deploy the `dist/{slug}/` folder to the target server
- **Deps:** Tasks 1-3
- **Acceptance:** A developer can follow the guide to create and deploy a new brand from scratch
- [x] Done
