# Feature F2: Stripe Invoice History

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F1, E43 (Stripe client exists, `stripe_customer_id` stored on Company)
**Complexity:** M

---

## Scope

### Included

- New endpoint `GET /api/v1/companies/{id}/invoices` — fetches invoice list from Stripe API
- New `list_invoices()` method on `StripeClient`
- New query `GetCompanyInvoicesQuery` + handler
- Frontend: Invoices tab in `CompanyBillingModal`
- Open Source mode: returns empty list, no Stripe API call
- No Stripe customer: returns empty list

### Excluded

- Creating or voiding invoices (Stripe-managed)
- Invoice PDF generation (link to Stripe-hosted PDF)
- Caching invoice data locally

---

## User Value

Super admin can verify payment history for any company — see when they last paid, how much, and whether any invoices are open or failed — without leaving the platform.

---

## Acceptance Criteria

- [ ] `GET /api/v1/companies/{id}/invoices` returns list of invoices for the company
- [ ] Each invoice includes: date, period (start/end), amount, currency, status, invoice URL, PDF URL
- [ ] Returns empty list `[]` if company has no `stripe_customer_id`
- [ ] Returns empty list `[]` in `OPEN_SOURCE_MODE`
- [ ] Returns `503` if Stripe API is unavailable
- [ ] Returns `404` if company does not exist
- [ ] Returns `403` for non-super-admin
- [ ] Optional query param `?limit=N` (default 20, max 100)
- [ ] Frontend billing modal shows Invoices tab next to billing info
- [ ] Invoice table shows date, amount, status badge, PDF/view links
- [ ] Empty state shown when no invoices
- [ ] Error state shown when Stripe unavailable

---

## Technical Scope

### Entities (used from dependencies)

- `Company` — `stripe_customer_id`
- `StripeClient` — extend with `list_invoices()`

### Key Components

**Backend:**
- `StripeClient.list_invoices(customer_id, limit)` in `core/stripe_client.py`
- `GetCompanyInvoicesQuery(company_id, limit)` + `GetCompanyInvoicesQueryHandler`
- `InvoiceDto` dataclass
- `GET /api/v1/companies/{id}/invoices` endpoint in `adapters/http/api/companies/routers.py`
- `InvoiceResponse` schema in `adapters/http/api/companies/schemas.py`

**Frontend:**
- `CompanyBillingModal.tsx` — add Invoices tab with table

---

## Notes

Invoices are fetched live from Stripe on every request. No local storage needed — Stripe is the system of record for payment history.
