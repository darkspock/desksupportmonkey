# Feature: Account Creation

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F1 (Portal Foundation)
**Complexity:** L

## Scope

### Included

- `ResellerClient` entity (id, reseller_id, company_id, source, created_at)
- Demo account creation: pre-filled with seed data, Free plan, admin credentials shown once, auto-expiry after 14 days
- Normal account creation: empty company with admin user, reseller specifies company name + admin email + plan
- Client list: resellers see all their clients with plan and billing status
- Seed data refactor: `make seed` must accept a target `company_id` parameter (reusable for demo accounts)
- Demo account expiry: Celery beat task runs daily, suspends after 14 days, purges data after 44 days
- Super admin: view reseller's client list
- Dashboard update: client_count returns real data
- Database migration: `reseller_clients` table

### Excluded (in other features)

- Referral-based client creation (source=referral) → F3
- Commission tracking on client payments → F4
- Payout requests → F5

## User Value

- Resellers can create demo accounts pre-filled with realistic data to show prospects the product immediately
- Resellers can create normal client accounts with a company name and admin email
- Resellers can see a list of all their clients with current plan and status
- Demo accounts auto-expire, preventing abandoned demos from consuming resources

## Acceptance Criteria

- [ ] `reseller_clients` table created with all fields
- [ ] `POST /reseller/clients/demo` creates a company with seed data, Free plan, linked to reseller via ResellerClient (source=manual)
- [ ] Demo account creation returns admin credentials (shown once)
- [ ] Demo accounts are marked as demo in the client list
- [ ] `POST /reseller/clients/account` creates an empty company with admin user, linked to reseller
- [ ] Normal account admin receives standard onboarding (magic link)
- [ ] `GET /reseller/clients` returns reseller's clients with plan and billing status
- [ ] A company can only be linked to one reseller (first attribution wins)
- [ ] Dashboard `client_count` returns real count
- [ ] Seed data command refactored to accept target `company_id` parameter
- [ ] Celery beat task suspends demo accounts after 14 days
- [ ] Celery beat task purges demo account data after 44 days (14 + 30 retention)
- [ ] Suspended reseller cannot create new accounts (403)
- [ ] Super admin can see a reseller's client list via `GET /admin/resellers/:id/clients`
- [ ] Demo accounts do not generate commissions (they're on Free plan)
- [ ] Frontend: client list page with demo/normal distinction
- [ ] Frontend: demo account creation form
- [ ] Frontend: normal account creation form (company name, admin email, plan)

## Technical Scope

### Entities (owned by this feature)

- `ResellerClient` — link between reseller and company

### Entities (used from dependencies)

- `Reseller` from F1

### Key Components

**Backend (`src/reseller_bc/`):**
- `client/domain/entities.py` — ResellerClient entity
- `client/domain/enums.py` — ClientSource enum (manual, referral)
- `client/domain/repository.py` — ResellerClientRepository interface
- `client/infrastructure/models.py` — ResellerClientModel
- `client/infrastructure/repository.py` — ResellerClientRepository implementation
- `client/application/commands/create_demo_account.py` — Creates company + seed data + ResellerClient
- `client/application/commands/create_client_account.py` — Creates company + admin user + ResellerClient
- `client/application/queries/list_reseller_clients.py` — Client list with plan/billing info
- `client/application/tasks/demo_expiry_task.py` — Celery beat task for demo expiry

**Adapters:**
- Update `adapters/http/api/reseller/routers.py` — Add client creation and list endpoints

**Frontend:**
- `web/app/src/pages/reseller/ClientsPage.tsx` — Client list
- `web/app/src/pages/reseller/CreateDemoPage.tsx` — Demo creation form
- `web/app/src/pages/reseller/CreateAccountPage.tsx` — Normal account form

**Collateral (outside reseller_bc):**
- Seed data command: refactor to accept `company_id` parameter
- Company creation service: may need a lightweight variant callable from reseller_bc

**Migration:**
- Alembic migration for `reseller_clients` table

## Notes

- Demo account creation is the most complex part — it reuses the existing seed data logic but needs it to be parameterizable by `company_id`.
- The company creation flow called from reseller_bc should use the existing `create_company` command/service from `company_bc` via a port, not duplicate the logic.
- Demo expiry Celery task should be registered in the Celery beat schedule alongside existing periodic tasks.
