# Referral Program Patterns Analysis

## Key Files Explored
1. `adapters/http/api/registration/routers.py` - Registration endpoint with referral attribution
2. `adapters/http/api/reseller/routers.py` - Reseller endpoints
3. `adapters/http/api/reseller/schemas.py` - Response schemas
4. `adapters/http/api/reseller/mappers.py` - DTOs to response mappers
5. `core/celery.py` - Beat scheduler configuration
6. `core/tasks/__init__.py` - Task registration pattern
7. `core/tasks/commission.py` - Commission transition task
8. `core/tasks/reseller.py` - Demo expiry task
9. `core/tasks/reseller_emails.py` - Email tasks with retries

## Referral Attribution Flow (Existing Pattern)

### Registration Endpoint
- Location: `POST /api/v1/register` (lines 52-116 in registration/routers.py)
- Flow:
  1. Creates company via `CreateCompanyCommand`
  2. After success, checks for `body.referral_code` (optional field)
  3. If present, creates `CreateReferralAttributionCommand`
  4. Uses `CreateReferralAttributionCommandHandler` to handle attribution
  5. **Silently fails** if code invalid or reseller inactive (no error raised)

### Referral Attribution Command
- Location: `src/reseller_bc/client/application/commands/create_referral_attribution.py`
- Handler logic (lines 30-57):
  1. Lookup reseller by referral code (early exit if not found)
  2. Only attribute if reseller is ACTIVE (silent skip if not)
  3. Prevent duplicate attribution (first-wins) via `find_by_company_id`
  4. Create `ResellerClient` with `source=ClientSource.REFERRAL`
  5. Logs attribution success

- Error handling: All errors silently suppressed (no exceptions raised)

## Reseller Entities & Data Structures

### Reseller Entity
- Location: `src/reseller_bc/reseller/domain/entities.py`
- Key fields:
  - `id, email, name, status` (ResellerStatus enum: ACTIVE, SUSPENDED, DEACTIVATED, PENDING)
  - `referral_code` (auto-generated 8-char alphanumeric string)
  - `commission_pct, min_payout_cents` (configurable)
  - `google_id, microsoft_id` (for OAuth linking)
  - `password_hash, reset_token` (for password auth)

- Key methods:
  - `create()` - factory method with validation
  - `update_settings()` - bulk update for admin
  - `suspend(), activate(), deactivate()` - status transitions
  - `approve()` - explicit status check before activation

### ResellerClient Entity
- Location: `src/reseller_bc/client/domain/entities.py`
- Key fields:
  - `id, reseller_id, company_id`
  - `source: ClientSource` (enum: MANUAL, REFERRAL)
  - `is_demo: bool` (default False)
  - `demo_expires_at` (set to now + 14 days if is_demo=True)
  - `created_at`

- Factory method `create()`:
  ```python
  @classmethod
  def create(cls, reseller_id, company_id, source, is_demo=False, id=None):
      now = datetime.utcnow()
      return cls(
          id=id or str(ulid.new()),
          demo_expires_at=now + timedelta(days=14) if is_demo else None,
          ...
      )
  ```

- DB constraint: `company_id` is UNIQUE (one company per reseller)

### ResellerCommission Entity
- Location: `src/reseller_bc/commission/domain/entities.py`
- Key fields:
  - `id, reseller_id, reseller_client_id, company_id`
  - `payment_amount_cents, commission_pct, commission_amount_cents` (auto-calculated)
  - `stripe_invoice_id` (for audit trail)
  - `period_start, period_end` (for reporting)
  - `status: CommissionStatus` (PENDING, CONFIRMED, CLAWED_BACK, PAID)

- Methods:
  - `create()` - factory auto-calculates commission_amount
  - `create_clawback()` - creates negative commission for refunds
  - `confirm()` - transition from PENDING to CONFIRMED
  - `clawback()` - mark as CLAWED_BACK
  - `mark_as_paid()` - transition to PAID

## Celery Task Patterns

### Task Registration
- Location: `core/celery.py` (lines 39-111)
- Pattern:
  - Beat schedule defined in `celery_app.conf.beat_schedule` dict
  - Each task has a name, schedule (crontab), and kwargs
  - All tasks registered via `celery_app.autodiscover_tasks(["core.tasks"])`

- Existing tasks:
  - `cleanup-magic-links`: daily at midnight
  - `send-appointment-reminders`: every 15 minutes
  - `generate-recurring-maintenance`: daily at 02:00 UTC
  - **`expire-demo-accounts`**: daily at 03:00 UTC (exists in reseller.py)
  - **`confirm-commissions`**: daily at 04:00 UTC (exists in commission.py)

### Task Implementation Pattern
- Location: Examples in `core/tasks/commission.py` and `core/tasks/reseller.py`

**commission.py** (lines 9-34):
```python
@celery_app.task(name="core.tasks.commission.confirm_commissions")
def confirm_commissions() -> dict:
    session = SessionLocal()
    try:
        repo = ResellerCommissionRepository(session)
        cutoff = datetime.utcnow() - timedelta(days=30)
        pending = repo.find_pending_before(before=cutoff)
        confirmed_count = 0
        for commission in pending:
            commission.confirm()
            repo.save(commission)
            confirmed_count += 1
        session.commit()
        logger.info("Commission confirmation: confirmed=%d", confirmed_count)
        return {"confirmed": confirmed_count}
    except Exception as e:
        session.rollback()
        logger.error("Commission confirmation failed: %s", str(e))
        raise
    finally:
        session.close()
```

**reseller.py** (lines 9-54):
```python
@celery_app.task(name="core.tasks.reseller.expire_demo_accounts")
def expire_demo_accounts() -> dict:
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        client_repo = ResellerClientRepository(session)
        company_repo = CompanyRepository(session)
        
        # Phase 1: Suspend active demos past expiry (14 days)
        expired = client_repo.find_expired_demos(before=now)
        suspended_count = 0
        for client in expired:
            company = company_repo.find_by_id(client.company_id)
            if company and company.status == CompanyStatus.ACTIVE:
                company.change_status(CompanyStatus.SUSPENDED)
                company_repo.save(company)
                suspended_count += 1
        
        # Phase 2: Deactivate after 44 days total
        ...session.commit()
        return {"suspended": suspended_count, "deactivated": deactivated_count}
    except Exception as e:
        session.rollback()
        logger.error("Demo expiry task failed: %s", str(e))
        raise
    finally:
        session.close()
```

### Email Task Pattern
- Location: `core/tasks/reseller_emails.py`
- All tasks have retry configuration:
  ```python
  @celery_app.task(
      name="core.tasks.reseller_emails.send_reseller_registration_confirmation",
      bind=True,
      max_retries=3,
      default_retry_delay=30,  # 30 seconds
      retry_backoff=True,
      retry_backoff_max=600,   # 10 minutes max
  )
  def send_reseller_registration_confirmation(self, to_email: str, name: str):
      try:
          template = _jinja_env.get_template("reseller_registration_confirmation.html")
          html = template.render(name=name)
          subject = f"[{settings.BRAND_NAME}] We received your reseller application"
          email_service = get_email_service()
          email_service.send(to_email, subject, html)
          logger.info("Reseller registration confirmation sent to %s", to_email)
      except Exception as exc:
          logger.error("Failed to send reseller registration confirmation...")
          raise self.retry(exc=exc)
  ```

- Template dir: `templates/email/` (relative to project root)
- Global Jinja2 variables: `brand_name`, `frontend_url` (from settings)

## DI/IoC Pattern

### FastAPI Dependencies
- Location: `adapters/http/api/registration/dependencies.py`
- Simple factory functions using `Depends(get_db)`:
  ```python
  def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
      return CompanyRepository(db)
  ```

### Command/Query Bus Pattern
- Location: `src/framework/application/command_bus.py` and `query_bus.py`
- Convention-based handler discovery:
  - Command: `MyCommand` → handler `MyCommandHandler` → provider method `my_command_handler()`
  - Query: `MyQuery` → handler `MyQueryHandler` → provider method `my_query_handler()`
  - Container parameter required for resolving handler providers

### Handler Execution
- Commands return `None` (CQRS pattern)
- Handlers can have optional `get_pending_events()` method
- Bus caches handler lookups

## Status Transitions

### ResellerStatus
- PENDING → ACTIVE (via `approve()` with explicit check)
- ACTIVE → SUSPENDED (via `suspend()`)
- SUSPENDED → ACTIVE (via `activate()`)
- ACTIVE/SUSPENDED → DEACTIVATED (via `deactivate()`)
- PENDING state only valid at creation

### CompanyStatus (in reseller.py line 13)
- ACTIVE → SUSPENDED (demo expiry at 14 days)
- SUSPENDED → DEACTIVATED (demo purge at 44 days total)

## Referral Logic Features

### Silent Failures
- Invalid referral code: no error, no attribution (line 34 in create_referral_attribution.py)
- Inactive reseller: no error, no attribution (lines 37-38)
- Already attributed company: no error, no update (lines 41-43)

### Atomic Attribution
- Uses single `ResellerClient.create()` call with factory method
- Single `repo.save()` to persist
- No partial updates

### Logging
- Info level for success: "Referral attribution: company=%s -> reseller=%s"
- Warning level for registration failure (lines 111-114 in registration/routers.py)

## Testing Patterns

### Test Location
- Integration: `tests/integration/test_registration_referral.py`
- Unit: `tests/unit/reseller_bc/client/application/test_create_referral_attribution.py`

### Integration Test Fixtures
```python
@pytest.fixture()
def reseller(db_session):
    r = Reseller.create(...)
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r
```

### Test Cases
1. Valid referral with active reseller → attribution created
2. Invalid code → company created, no attribution
3. No referral code → company created, no attribution
4. Suspended reseller code → company created, no attribution

## Mapper Pattern

### Location
- `adapters/http/api/reseller/mappers.py`

### Pattern
```python
class ResellerMapper:
    @staticmethod
    def dto_to_response(dto: ResellerDto) -> ResellerResponse:
        return ResellerResponse(
            id=dto.id,
            email=dto.email,
            ...
            created_at=dto.created_at.isoformat() if dto.created_at else "",
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )
```

- Handles type conversions (datetime → ISO string)
- Handles optional fields with fallback values

## Summary of Key Patterns

1. **Referral Attribution**: Silent on error, first-wins duplicate prevention
2. **Celery Tasks**: Session-based, explicit rollback on error, always close session
3. **Email Tasks**: Retry with exponential backoff, Jinja2 templates
4. **Entities**: Factory methods with validation, status transition methods
5. **DI**: FastAPI Depends for DB, repositories for DB access
6. **Commands**: Return None, use exceptions for errors
7. **Mappers**: Isolate DTO-to-Response conversion, handle datetime serialization
8. **Testing**: Fixtures for setup, db_session flush to ensure IDs before assertions
