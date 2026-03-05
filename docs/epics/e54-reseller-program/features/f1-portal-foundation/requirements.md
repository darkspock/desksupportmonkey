# Feature: Portal Foundation

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** None
**Complexity:** M

## Scope

### Included

- `Reseller` entity with all fields (id, email, name, google_id, microsoft_id, avatar_url, company_name, tax_id, commission_pct, min_payout_cents, referral_code, status, timestamps)
- Reseller OAuth authentication (Google + Microsoft only, JWT with `type: reseller` claim)
- Reseller auth middleware (separate from main user auth)
- Reseller portal shell: login page, dashboard (basic — client count, commission totals, balance as placeholders until F4), profile edit
- Super admin: create reseller, edit reseller settings, list resellers with client count/earnings
- Referral code auto-generation on reseller creation
- Reseller status management (active, suspended, deactivated)
- Frontend: `/reseller/login`, `/reseller/dashboard`, `/reseller/profile`, `ResellerAuthProvider` context
- Super admin frontend: reseller management pages under admin section
- Database migration: `resellers` table

### Excluded (in other features)

- `ResellerClient` entity and client account creation → F2
- Demo account creation and seed data refactor → F2
- Referral link attribution on registration → F3
- `ResellerCommission` entity and Stripe webhook integration → F4
- `ResellerPayout` entity and payout flow → F5
- Commission/balance data in dashboard (shows placeholders/zeros until F4) → F4

## User Value

- Super admins can onboard new resellers by creating their records
- Resellers can log in with Google/Microsoft, see their (initially empty) dashboard, and edit their company name and tax ID
- Super admins can view all resellers, change commission rates, payout thresholds, and status

## Acceptance Criteria

- [ ] `resellers` table created with all fields from domain model
- [ ] Reseller OAuth login with Google works (shared OAuth app credentials)
- [ ] Reseller OAuth login with Microsoft works (shared OAuth app credentials)
- [ ] Unregistered email shows "Not registered as a reseller" message
- [ ] Reseller JWT has `type: reseller` claim, distinct from user JWT
- [ ] Reseller JWT cannot be used to access regular user endpoints
- [ ] Regular user JWT cannot be used to access reseller endpoints
- [ ] Reseller dashboard loads and shows basic structure (zeros for clients/commissions)
- [ ] Reseller can edit own `company_name` and `tax_id` only
- [ ] Reseller cannot edit `commission_pct`, `min_payout_cents`, or `status`
- [ ] Super admin can create a reseller (email, name, commission_pct, min_payout_cents)
- [ ] Super admin can edit reseller settings (commission_pct, min_payout_cents, status)
- [ ] Super admin can list all resellers
- [ ] Referral code auto-generated on reseller creation (unique, URL-safe)
- [ ] Suspended reseller can log in and view data but gets 403 on write operations
- [ ] Deactivated reseller cannot log in (401)
- [ ] Frontend: `/reseller/login` page with Google/Microsoft buttons
- [ ] Frontend: `/reseller/dashboard` page with portal shell and navigation
- [ ] Frontend: `ResellerAuthProvider` context separate from main `AuthContext`

## Technical Scope

### Entities (owned by this feature)

- `Reseller` — full entity with all fields

### Entities (used from dependencies)

- None (this is the foundation)

### Key Components

**Backend (`src/reseller_bc/`):**
- `reseller/domain/entities.py` — Reseller entity
- `reseller/domain/enums.py` — ResellerStatus enum
- `reseller/domain/repository.py` — ResellerRepository interface
- `reseller/infrastructure/models.py` — ResellerModel (SQLAlchemy)
- `reseller/infrastructure/repository.py` — ResellerRepository implementation
- `reseller/application/commands/` — CreateReseller, UpdateReseller, UpdateResellerProfile
- `reseller/application/queries/` — GetReseller, ListResellers, GetResellerDashboard
- `reseller/application/services/reseller_auth_service.py` — OAuth login for resellers

**Adapters:**
- `adapters/http/api/reseller/routers.py` — Reseller portal endpoints
- `adapters/http/api/reseller/dependencies.py` — `get_current_reseller()` dependency
- `adapters/http/api/reseller/schemas.py` — Request/response schemas
- `adapters/http/api/admin/reseller_routers.py` — Super admin reseller management

**Frontend:**
- `web/app/src/pages/reseller/` — Login, Dashboard, Profile pages
- `web/app/src/contexts/ResellerAuthContext.tsx` — Reseller auth provider
- `web/app/src/pages/admin/resellers/` — Super admin reseller pages

**Migration:**
- Alembic migration for `resellers` table

## Notes

- The dashboard endpoint returns a structure with placeholder zeros for client_count, total_commissions, available_balance, pending_payout. These fields get real data as F2/F4/F5 are deployed.
- OAuth callback URLs must handle both user and reseller flows. The callback distinguishes by a state parameter or separate callback paths.
- The reseller portal is part of the same React app but with a completely separate route tree under `/reseller/*` and its own auth context (`ResellerAuthProvider`).
