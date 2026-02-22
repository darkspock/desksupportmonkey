# Tasks: F1 - Stripe Customer Bootstrap

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F0](../f0-billing-foundation/tasks.md)
**Date:** 2026-02-22

---

## Phase 1: Stripe Client

### T1.1: Create StripeClient
- [ ] **File:** `core/stripe_client.py` (NEW)
- Define `StripeUnavailableError(Exception)` and `InvalidStripeSignatureError(Exception)`
- Class `StripeClient`:
  - Constructor: `__init__(self, secret_key: str, open_source_mode: bool = False)`
  - `create_customer(name: str, email: str, metadata: dict) -> str`
    - If `open_source_mode=True`: return `""` (no-op)
    - Calls `stripe.Customer.create(name=name, email=email, metadata=metadata)`
    - On `stripe.error.StripeError`: raise `StripeUnavailableError`
    - Returns `customer.id`
  - `cancel_subscription(subscription_id: str) -> None`
    - If `open_source_mode=True`: return (no-op)
    - Calls `stripe.Subscription.cancel(subscription_id)`
    - On `stripe.error.StripeError`: raise `StripeUnavailableError`
- Add `stripe` to backend dependencies: `uv add stripe`

### T1.2: Wire StripeClient into dependency injection
- [ ] **File:** `adapters/http/dependencies.py` (MODIFY — or wherever DI factories live)
- Add `get_stripe_client() -> StripeClient` factory reading `settings.STRIPE_SECRET_KEY` and `settings.OPEN_SOURCE_MODE`

---

## Phase 2: Application Layer

### T2.1: Extend CreateCompanyCommandHandler
- [ ] **File:** `src/company_bc/company/application/commands/create_company.py` (MODIFY)
- Add `stripe_client: StripeClient` as a dependency
- After saving company:
  1. Call `stripe_client.create_customer(name=company.name, email=command.admin_email or "", metadata={"company_id": company.id})`
  2. Set `company.stripe_customer_id = customer_id`
  3. Save company again
- If `StripeUnavailableError` raised: propagate (do NOT catch here — router handles it)
- When `OPEN_SOURCE_MODE=True`: `create_customer()` returns `""` — save that value

---

## Phase 3: HTTP Layer

### T3.1: Map StripeUnavailableError → HTTP 503 in companies router
- [ ] **File:** `adapters/http/api/companies/routers.py` (MODIFY)
- In `POST /api/v1/companies` handler, catch `StripeUnavailableError`:
  ```python
  raise HTTPException(status_code=503, detail="stripe_unavailable")
  ```

---

## Phase 4: Tests

### T4.1: Unit tests — StripeClient
- [ ] **File:** `tests/unit/core/test_stripe_client.py` (NEW)
- Test `create_customer` success — returns customer ID
- Test `create_customer` with `open_source_mode=True` — returns `""` without calling Stripe SDK
- Test `create_customer` on `stripe.error.StripeError` — raises `StripeUnavailableError`
- Test `cancel_subscription` with `open_source_mode=True` — no-op, no exception

### T4.2: Unit tests — CreateCompanyCommandHandler (billing extension)
- [ ] **File:** `tests/unit/company_bc/company/application/commands/test_create_company.py` (MODIFY)
- Test: `stripe_customer_id` persisted on company after successful creation
- Test: `StripeUnavailableError` from Stripe propagates out of handler

### T4.3: Integration test — registration with Stripe
- [ ] **File:** `tests/integration/test_companies_endpoints.py` (MODIFY)
- Test: `POST /api/v1/companies` with mocked `StripeClient` — response 201, `stripe_customer_id` saved in DB
- Test: `POST /api/v1/companies` when Stripe raises `StripeUnavailableError` — response 503

---

## Phase 5: Verification

### T5.1: Run linter
- [ ] `make lint` — no errors

### T5.2: Run all tests
- [ ] `make test` + `make test-integration`

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Stripe Client | T1.1-T1.2 | 1 new | 1 modified (dependencies) |
| 2. Application | T2.1 | — | 1 modified (create_company handler) |
| 3. HTTP | T3.1 | — | 1 modified (companies router) |
| 4. Tests | T4.1-T4.3 | 1 new | 2 modified |
| 5. Verification | T5.1-T5.2 | — | — |
