# Feature: Commission Tracking

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 4
**Dependencies:** F2 (Account Creation — owns ResellerClient entity)
**Complexity:** M

## Scope

### Included

- `ResellerCommission` entity (id, reseller_id, reseller_client_id, company_id, payment_amount_cents, commission_pct, commission_amount_cents, stripe_invoice_id, period_start, period_end, status, created_at)
- Commission creation on `invoice.payment_succeeded` Stripe webhook: check if paying company has a ResellerClient → calculate commission → create ResellerCommission record
- Commission calculation: `payment_amount_cents * commission_pct / 100`, rounded down
- Commission status lifecycle: `pending` → `confirmed` (after 30 days) → `paid` (after payout in F5)
- Refund clawback: on `charge.refunded` webhook, set commission to `clawed_back`; if already paid, create negative commission record
- Celery beat task: daily commission confirmation (pending → confirmed after 30 days)
- Commission list: resellers see all commissions with client, amount, rate, earned, status
- Available balance calculation: sum of confirmed commissions − paid payouts − clawbacks
- Dashboard update: real commission totals and available balance
- Super admin: view all commissions, view commissions per reseller

### Excluded (in other features)

- Reseller entity and auth → F1
- ResellerClient entity and account creation → F2
- Referral attribution → F3
- Payout requests and approval → F5

## User Value

- Commissions are automatically calculated when reseller clients make payments — no manual tracking needed
- Resellers can see every commission with full details (client, amount, rate, status)
- 30-day chargeback protection prevents premature payouts
- Refund clawbacks keep the financial model honest — if a client gets a refund, the commission is reversed
- Dashboard shows real financial data (total earned, available balance)

## Acceptance Criteria

- [ ] `reseller_commissions` table created with all fields
- [ ] On `invoice.payment_succeeded`: if company has ResellerClient, commission created with reseller's current `commission_pct`
- [ ] Commission amount = `payment_amount_cents * commission_pct / 100` (rounded down)
- [ ] Commission status starts as `pending`
- [ ] Celery beat task runs daily, transitions commissions from `pending` to `confirmed` where `created_at < now - 30 days`
- [ ] On `charge.refunded`: matching commission set to `clawed_back` regardless of current status
- [ ] On `charge.refunded` for already-paid commission: negative-amount commission record created
- [ ] `GET /reseller/commissions` returns paginated commission list with client name, payment, rate, earned, status
- [ ] Available balance = sum(confirmed commission amounts) − sum(paid payout amounts) − sum(clawback amounts)
- [ ] Dashboard shows total commissions earned and available balance
- [ ] Demo account payments (Free plan) do not generate commissions
- [ ] Super admin can view all commissions via `GET /admin/resellers/:id/commissions`
- [ ] Suspended reseller still sees commissions (read-only)
- [ ] Frontend: commissions page with filterable/sortable list
- [ ] Frontend: clawed-back commissions clearly marked

## Technical Scope

### Entities (owned by this feature)

- `ResellerCommission` — commission record per client payment

### Entities (used from dependencies)

- `Reseller` from F1 (commission_pct)
- `ResellerClient` from F2 (links commission to client)

### Key Components

**Backend (`src/reseller_bc/`):**
- `commission/domain/entities.py` — ResellerCommission entity
- `commission/domain/enums.py` — CommissionStatus enum (pending, confirmed, paid, clawed_back)
- `commission/domain/repository.py` — ResellerCommissionRepository interface
- `commission/infrastructure/models.py` — ResellerCommissionModel
- `commission/infrastructure/repository.py` — ResellerCommissionRepository implementation
- `commission/application/commands/create_commission.py` — Creates commission from payment event
- `commission/application/commands/clawback_commission.py` — Handles refund clawback
- `commission/application/queries/list_commissions.py` — Commission list with filters
- `commission/application/queries/get_available_balance.py` — Balance calculation
- `commission/application/tasks/confirm_commissions_task.py` — Celery beat daily confirmation

**Collateral (outside reseller_bc):**
- Stripe webhook dispatcher: add handler for `invoice.payment_succeeded` → check ResellerClient → create commission
- Stripe webhook dispatcher: add handler for `charge.refunded` → find commission by stripe_invoice_id → clawback

**Frontend:**
- `web/app/src/pages/reseller/CommissionsPage.tsx` — Commission list
- Update `web/app/src/pages/reseller/DashboardPage.tsx` — Real commission/balance data

**Migration:**
- Alembic migration for `reseller_commissions` table

## Notes

- The Stripe webhook integration is the most critical part. The `StripeWebhookDispatcher` (from E43) already handles `invoice.payment_succeeded`. This feature adds a hook that checks if the paying company has a `ResellerClient` record and creates a commission if so.
- The `charge.refunded` webhook may not be handled yet in the codebase. Need to verify and add a new handler if missing.
- The balance calculation must account for: confirmed commissions (positive), paid payouts from F5 (negative), and clawback records (negative). Until F5 is deployed, paid payouts = 0, so balance = confirmed commissions − clawbacks.
