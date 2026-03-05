# Feature: Payout Requests

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 5
**Dependencies:** F4 (Commission Tracking — provides balance calculation)
**Complexity:** S

## Scope

### Included

- `ResellerPayout` entity (id, reseller_id, amount_cents, status, requested_at, processed_at, processed_by, payment_reference, notes)
- Payout request: reseller requests payout of current available balance (disabled if balance < min_payout_cents)
- Payout approval workflow: super admin reviews → approve/reject → mark as paid with payment reference
- Payout status lifecycle: `requested` → `approved` → `paid` | `requested` → `rejected`
- After rejection: reseller can immediately request again (no cooldown)
- When paid: mark associated confirmed commissions as `paid` to prevent double-counting
- Payout list: resellers see their payout history with status, amount, payment reference
- Dashboard update: pending payout status visible
- Super admin: list all payout requests, approve/reject/mark-paid

### Excluded (in other features)

- Reseller entity and auth → F1
- Client accounts → F2
- Referral links → F3
- Commission creation and balance calculation → F4
- Automatic payouts via Stripe Connect or PayPal (out of scope for entire epic)

## User Value

- Resellers can request a payout when their available balance reaches the minimum threshold
- Super admins can review, approve, and process payout requests with payment references
- Resellers can see their full payout history
- Rejected payouts don't lock funds — resellers can immediately retry

## Acceptance Criteria

- [ ] `reseller_payouts` table created with all fields
- [ ] `POST /reseller/payouts` creates a payout request with `status = requested` and `amount_cents = available_balance`
- [ ] Payout request disabled (400) if available balance < reseller's `min_payout_cents`
- [ ] Suspended reseller cannot request payouts (403)
- [ ] `GET /reseller/payouts` returns payout history with status, amount, payment reference
- [ ] Super admin can list all payout requests via `GET /admin/payouts`
- [ ] Super admin can approve a payout via `PATCH /admin/payouts/:id` (status → approved)
- [ ] Super admin can reject a payout via `PATCH /admin/payouts/:id` (status → rejected, with notes)
- [ ] Super admin can mark payout as paid via `PATCH /admin/payouts/:id` (status → paid, with payment_reference)
- [ ] When payout is marked as paid, associated confirmed commissions transition to `paid`
- [ ] After rejection, reseller can immediately request a new payout
- [ ] Dashboard shows pending payout status
- [ ] A payout request locks the current balance — new commissions confirmed after the request go toward the next payout
- [ ] Frontend: payout history page
- [ ] Frontend: "Request Payout" button (disabled when below threshold)
- [ ] Super admin frontend: payout management page with approve/reject/paid actions

## Technical Scope

### Entities (owned by this feature)

- `ResellerPayout` — payout request record

### Entities (used from dependencies)

- `Reseller` from F1 (min_payout_cents)
- `ResellerCommission` from F4 (balance calculation, mark as paid)

### Key Components

**Backend (`src/reseller_bc/`):**
- `payout/domain/entities.py` — ResellerPayout entity
- `payout/domain/enums.py` — PayoutStatus enum (requested, approved, paid, rejected)
- `payout/domain/repository.py` — ResellerPayoutRepository interface
- `payout/infrastructure/models.py` — ResellerPayoutModel
- `payout/infrastructure/repository.py` — ResellerPayoutRepository implementation
- `payout/application/commands/request_payout.py` — Creates payout request
- `payout/application/commands/process_payout.py` — Approve/reject/mark-paid (super admin)
- `payout/application/queries/list_payouts.py` — Payout list

**Adapters:**
- Update `adapters/http/api/reseller/routers.py` — Add payout endpoints
- Update `adapters/http/api/admin/reseller_routers.py` — Add payout management endpoints

**Frontend:**
- `web/app/src/pages/reseller/PayoutsPage.tsx` — Payout history + request button
- `web/app/src/pages/admin/resellers/PayoutManagementPage.tsx` — Super admin payout processing

**Migration:**
- Alembic migration for `reseller_payouts` table

## Notes

- Payout processing is manual — the super admin does the actual bank transfer externally and records the reference in the system. No Stripe Connect or PayPal integration in this epic.
- The "locks the current balance" rule means: when calculating a new payout amount, only count confirmed commissions not already associated with a pending/approved/paid payout. The simplest implementation: when marking a payout as paid, update the associated commissions to `paid` status. For balance calculation: `SUM(confirmed) - SUM(paid payouts) - SUM(clawbacks)`.
- Rejected payouts don't affect balance — the commissions remain `confirmed` and available for the next payout request.
