# Tasks: F0 - Billing Domain Foundation

**Epic:** [slicing.md](../../slicing.md)
**Date:** 2026-02-22

---

## Phase 1: Domain Layer

### T1.1: Create billing enums
- [x] **File:** `src/company_bc/company/domain/billing_enums.py` (NEW)
- `PlanTier(str, Enum)`: `FREE = "free"`, `PREMIUM = "premium"`, `ENTERPRISE = "enterprise"`, `OPEN_SOURCE = "open_source"`
- `BillingStatus(str, Enum)`: `ACTIVE = "active"`, `GRACE_PERIOD = "grace_period"`, `SUSPENDED = "suspended"`, `OVER_LIMIT = "over_limit"`

### T1.2: Extend Company entity with billing fields
- [x] **File:** `src/company_bc/company/domain/entities.py` (MODIFY)
- Add fields:
  - `plan: PlanTier` (default: `PlanTier.FREE`)
  - `billing_status: BillingStatus` (default: `BillingStatus.ACTIVE`)
  - `stripe_customer_id: Optional[str]` (default: None)
  - `stripe_subscription_id: Optional[str]` (default: None)
  - `grace_period_started_at: Optional[datetime]` (default: None)
  - `current_period_end: Optional[datetime]` (default: None)
  - `pending_downgrade_plan: Optional[PlanTier]` (default: None)
  - `complimentary: bool` (default: False)
- Add domain methods:
  - `set_billing_status(status: BillingStatus) -> None`
  - `apply_plan_change(plan: PlanTier, subscription_id: str, period_end: datetime) -> None`
  - `enter_grace_period() -> None` — sets `billing_status = GRACE_PERIOD`, records `grace_period_started_at = now()`
  - `restore_billing() -> None` — sets `billing_status = ACTIVE`, clears `grace_period_started_at`
  - `grant_complimentary(plan: PlanTier) -> None` — sets `complimentary = True`, `plan = plan`, `billing_status = ACTIVE`
  - `revoke_complimentary() -> None` — sets `complimentary = False`, `plan = FREE`, `billing_status = OVER_LIMIT`

### T1.3: Create PlanGate service
- [x] **File:** `src/company_bc/company/domain/plan_gate.py` (NEW)
- Constants: `PLAN_FEATURES: dict[PlanTier, set[str]]`
  - `FREE`: `{"core", "assets", "requests", "dashboard", "magic_link", "password_login"}`
  - `PREMIUM`: all FREE + `{"reports", "oauth_login", "api_keys", "ai_classification", "appointments", "shipments", "maintenance", "procurement"}`
  - `ENTERPRISE`: all PREMIUM + `{"mcp_server", "sso", "audit_trail", "custom_fields", "automations", "sla", "knowledge_base", "onboarding"}`
  - `OPEN_SOURCE`: all features
- Constants: `PLAN_USER_LIMITS: dict[PlanTier, Optional[int]]`
  - `FREE`: 5, `PREMIUM`: 25, `ENTERPRISE`: None, `OPEN_SOURCE`: None
- Constants: `PLAN_ASSET_LIMITS: dict[PlanTier, Optional[int]]`
  - `FREE`: 50, `PREMIUM`: 500, `ENTERPRISE`: None, `OPEN_SOURCE`: None
- Static methods:
  - `is_feature_available(plan, billing_status, complimentary, open_source_mode, feature) -> bool`
    - Returns True if `open_source_mode=True` or `complimentary=True` or feature in PLAN_FEATURES[plan]
    - Returns False if `billing_status == SUSPENDED` for write features
  - `is_write_allowed(billing_status, open_source_mode) -> bool`
    - Returns False if `billing_status` is `SUSPENDED` or `OVER_LIMIT` (and not `open_source_mode`)
  - `get_user_limit(plan) -> Optional[int]`
  - `get_asset_limit(plan) -> Optional[int]`

---

## Phase 2: Infrastructure Layer

### T2.1: Extend CompanyModel with billing columns
- [x] **File:** `src/company_bc/company/infrastructure/models.py` (MODIFY)
- Add columns using SQLAlchemy 2.0 `Mapped` style:
  - `plan: Mapped[str] = mapped_column(String(20), nullable=False, server_default="free")`
  - `billing_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")`
  - `stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)`
  - `stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)`
  - `grace_period_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)`
  - `current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)`
  - `pending_downgrade_plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)`
  - `complimentary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")`
- Update `_to_entity()` / mapper to include new billing fields

### T2.2: Create ProcessedStripeEventModel
- [x] **File:** `src/company_bc/company/infrastructure/models.py` (MODIFY — same file)
- New model `ProcessedStripeEventModel(Base)`:
  - `__tablename__ = "processed_stripe_events"`
  - `id: Mapped[str] = mapped_column(String(255), primary_key=True)` — Stripe event ID
  - `processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())`

### T2.3: Update models_registry.py
- [x] **File:** `core/models_registry.py` (MODIFY)
- Add import for `ProcessedStripeEventModel`

### T2.4: Extend CompanyRepository with billing methods
- [x] **File:** `src/company_bc/company/infrastructure/repository.py` (MODIFY)
- Add:
  - `find_by_stripe_customer_id(customer_id: str) -> Optional[Company]`
  - `mark_stripe_event_processed(event_id: str) -> None` — INSERT INTO processed_stripe_events
  - `is_stripe_event_processed(event_id: str) -> bool` — SELECT EXISTS
- Update `save()` to persist new billing fields

### T2.5: Update CompanyRepositoryInterface
- [x] **File:** `src/company_bc/company/domain/repository.py` (MODIFY)
- Add abstract methods: `find_by_stripe_customer_id`, `mark_stripe_event_processed`, `is_stripe_event_processed`

---

## Phase 3: Migration

### T3.1: Create Alembic migration
- [x] Run: `alembic revision --autogenerate -m "add_billing_fields_to_companies_and_processed_stripe_events"`
- Verify migration adds:
  - 8 new columns to `companies` (all nullable or server-defaulted — non-breaking)
  - New `processed_stripe_events` table with `id` (PK) and `processed_at`
- Test upgrade + downgrade

---

## Phase 4: Configuration

### T4.1: Add billing config to core/config.py
- [x] **File:** `core/config.py` (MODIFY)
- Add:
  - `STRIPE_SECRET_KEY: str = ""`
  - `STRIPE_PUBLISHABLE_KEY: str = ""`
  - `STRIPE_WEBHOOK_SECRET: str = ""`
  - `STRIPE_PRICE_PREMIUM: str = ""`
  - `STRIPE_PRICE_ENTERPRISE: str = ""`
  - `OPEN_SOURCE_MODE: bool = False`

### T4.2: Update .env.example
- [x] **File:** `.env.example` (MODIFY)
- Add all 6 new env vars with placeholder values

---

## Phase 5: Tests

### T5.1: Unit tests — PlanGate service
- [x] **File:** `tests/unit/company_bc/company/domain/test_plan_gate.py` (NEW)
- Test `is_feature_available`: open_source bypass, complimentary bypass, free/premium/enterprise limits, suspended blocks writes
- Test `is_write_allowed`: active → True, grace_period → True, suspended → False, over_limit → False, open_source bypass
- Test `get_user_limit` / `get_asset_limit`: correct values per plan

### T5.2: Unit tests — Company entity billing methods
- [x] **File:** `tests/unit/company_bc/company/domain/test_company_billing.py` (NEW)
- Test `enter_grace_period`, `restore_billing`, `apply_plan_change`, `grant_complimentary`, `revoke_complimentary`

---

## Phase 6: Verification

### T6.1: Run linter
- [x] `make lint` — mypy + flake8 pass

### T6.2: Run unit tests
- [x] `make test` — all tests pass

### T6.3: Run migration
- [x] `alembic upgrade head` + downgrade/upgrade cycle — reversible

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.3 | 2 new | 1 modified (entity) |
| 2. Infrastructure | T2.1-T2.5 | — | 3 modified (models, repo, repo interface, registry) |
| 3. Migration | T3.1 | 1 migration | — |
| 4. Configuration | T4.1-T4.2 | — | 2 modified (config, .env.example) |
| 5. Tests | T5.1-T5.2 | 2 new | — |
| 6. Verification | T6.1-T6.3 | — | — |
