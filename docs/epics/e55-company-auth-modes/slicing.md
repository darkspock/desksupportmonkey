# Epic Slicing: E55 — Company Login Slug, Multi-Company & Auth Mode

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Total Features:** 4
**Status:** Pending

## Slicing Rationale

E55 modifies two existing bounded contexts (`auth_bc`, `company_bc`) rather than creating a new one. The epic introduces three capabilities: company login slugs, multi-company user support via a membership registry, and configurable auth modes. The natural slices follow the build order: slug foundation → scoped auth with membership registry → company switcher → auth mode configuration.

Key decisions:
- **F1 is independently valuable** — adding `slug` to companies and creating a branded login page delivers value even without scoped auth. Users can visit `/login/acme-corp`, see company name, and still authenticate via existing unscoped endpoints.
- **F2 is the core** — creates the `CompanyUser` membership registry, rewrites all 5 auth flows to be company-scoped (two-step: identity → membership → copy-to-user-row), adds dual-writes to existing user commands, and includes the data migration that populates `company_users` from existing users. Everything after depends on this.
- **F3 depends on F2** — the company switcher API and UI need the membership registry and scoped auth to exist. Without F2, there's nothing to switch between.
- **F4 depends on F2** — auth mode configuration (`membership_only`) extends the lookup logic in F2's scoped auth. It also modifies the invite flow to support public-domain emails.

## Dependency Graph

```
F1 (Slug & Login Page)
 └── F2 (Scoped Auth & Membership Registry)
      ├── F3 (Company Switcher)         [parallel]
      └── F4 (Auth Mode Configuration)  [parallel]
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 1 | Slug & Login Page | None | Companies have branded login URLs; users see company name on login page | S | Done |
| 2 | Scoped Auth & Membership Registry | F1 | All auth flows are company-scoped; membership registry enables multi-company; dual-writes keep data consistent | L | Done |
| 3 | Company Switcher | F2 | Users with multiple memberships can switch companies without re-authenticating | S | Done |
| 4 | Auth Mode Configuration | F2 | Admins can switch to membership-only mode; contractors with public emails can be invited | M | Done |

## Recommended Order

1. **F1: Slug & Login Page** — must be first; adds slug to Company entity, migration, branded login page, slug resolve endpoint
2. **F2: Scoped Auth & Membership Registry** — highest complexity; creates CompanyUser entity, rewrites 5 auth flows, dual-writes, session invalidation, data migration
3. **F3: Company Switcher** — low effort after F2; adds 2 API endpoints + header dropdown UI (can be parallel with F4)
4. **F4: Auth Mode Configuration** — extends CompanyLookupService for membership_only mode; modifies invite flow for public domains; admin settings UI

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F1 → F2 → F3/F4)
- [x] Each feature independently deployable
- [x] Vertical slices (each includes backend domain + API + frontend UI)
- [x] Shared foundation identified (F1)
- [x] No overlapping scope (entity ownership is clear)
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F2 is the largest feature** — rewrites all 5 auth flows, creates CompanyUser entity + repository, adds dual-write to 4 existing user commands (change_role, deactivate, activate, assign_department), modifies create_company, modifies invite and import flows, adds MagicLink.company_id, includes data migration. Could be split further (auth flows vs dual-writes), but the dual-writes MUST land with the auth flows — if `company_users` exists but commands don't dual-write, the data goes stale immediately.
- **F2 modifies `get_current_user()` dependency** — the JWT company_id mismatch check is a one-line safety change, but it affects ALL 80+ endpoints. Must be tested carefully to avoid regressions (especially for SUPER_ADMIN with `company_id = NULL`).
- **F2 backward compatibility** — existing unscoped auth endpoints must continue working during transition. They resolve company from email domain as today, but return an error with company slugs if the email matches multiple companies. This is new behavior for a previously-working flow.
- **F4 modifies the invite flow** — in `membership_only` mode, the email domain validation that currently blocks public domains must be bypassed. This touches `adapters/http/api/users/routers.py` and the `import_users` command, both of which are heavily used.
