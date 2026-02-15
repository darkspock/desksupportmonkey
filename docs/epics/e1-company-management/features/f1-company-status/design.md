# Design: F1 - Company Status + Auth Integration

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F1 adds status transition logic to the Company entity (domain layer) and integrates company status checking into two auth touchpoints: magic link verification and JWT-based request authentication.

```
MODIFIED FILES:
src/company_bc/company/domain/entities.py      # Add transition logic
src/company_bc/company/domain/enums.py         # Add VALID_TRANSITIONS
src/company_bc/company/application/commands/   # New: update_company_status.py
src/company_bc/company/infrastructure/repository.py  # Add update_status method
adapters/http/api/companies/routers.py         # Add PATCH /status endpoint
adapters/http/api/companies/schemas.py         # Add status request schema
adapters/http/api/auth/dependencies.py         # Add company status check
src/auth_bc/magic_link/application/commands/verify_magic_link.py  # Add company status check
```

---

## Domain Layer Changes

### CompanyStatus Enum (extend)

Add valid transitions map:

```python
VALID_TRANSITIONS = {
    CompanyStatus.ACTIVE: [CompanyStatus.SUSPENDED, CompanyStatus.DEACTIVATED],
    CompanyStatus.SUSPENDED: [CompanyStatus.ACTIVE, CompanyStatus.DEACTIVATED],
    CompanyStatus.DEACTIVATED: [],  # terminal state
}
```

### Company Entity (extend)

Add `change_status()` method:

```python
def change_status(self, new_status: CompanyStatus) -> None:
    if new_status == self.status:
        raise InvalidStatusTransitionError(f"Company is already {self.status.value}")
    if new_status not in VALID_TRANSITIONS[self.status]:
        raise InvalidStatusTransitionError(
            f"Cannot transition from '{self.status.value}' to '{new_status.value}'"
        )
    self.status = new_status
    self.is_active = (new_status == CompanyStatus.ACTIVE)
```

---

## Application Layer

### UpdateCompanyStatusCommand

```python
@dataclass
class UpdateCompanyStatusCommand:
    company_id: str
    new_status: str  # validated to CompanyStatus in handler

class UpdateCompanyStatusCommandHandler:
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: UpdateCompanyStatusCommand) -> Company:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError()

        new_status = CompanyStatus(command.new_status)
        company.change_status(new_status)  # raises InvalidStatusTransitionError
        self.company_repo.save(company)
        return company
```

---

## Auth Integration

### Change 1: get_current_user dependency

In `adapters/http/api/auth/dependencies.py`, after loading the user and checking `is_active`, add company status check:

```python
# After user is_active check, before set_tenant:
if user.company_id:
    from src.company_bc.company.infrastructure.repository import CompanyRepository
    company_repo = CompanyRepository(db)
    company = company_repo.find_by_id(user.company_id)
    if company and company.status != CompanyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company access is currently restricted",
        )
```

Note: Super admins with `company_id = None` skip this check.

### Change 2: VerifyMagicLinkCommand

In `src/auth_bc/magic_link/application/commands/verify_magic_link.py`, the company status is already handled by `CompanyLookupService` which only returns company_id for active companies (via the `is_active` filter). However, to provide a distinct error message ("Company access is currently restricted" vs "Only corporate email addresses are allowed"), we need to:

1. Split the lookup: first find domain match (any status), then check if active
2. Or: add a method to CompanyLookupService that returns company status info

**Decision:** Extend `CompanyLookupService` with a new method:

```python
def find_company_by_email_domain(self, email: str) -> Optional[tuple[str, bool]]:
    """Returns (company_id, is_active) or None if domain not found."""
```

Then in VerifyMagicLinkCommand:
```python
result = self.company_lookup.find_company_by_email_domain(email)
if result is None:
    raise InvalidEmailDomainError()  # domain not found
company_id, is_active = result
if not is_active:
    raise CompanyRestrictedError()  # domain found but company not active
```

Similarly update `CreateMagicLinkCommand`.

---

## HTTP Layer Changes

### New Schema

```python
class UpdateCompanyStatusRequest(BaseModel):
    status: str  # validated against CompanyStatus values
```

### New Endpoint

```python
@router.patch("/api/v1/companies/{company_id}/status")
def update_company_status(
    company_id: str,
    body: UpdateCompanyStatusRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ...
```

Maps:
- `CompanyNotFoundError` → 404
- `InvalidStatusTransitionError` → 409

---

## Migration

No migration needed — `status` column was added in F0.

---

## Decisions

1. **Company status check on every request** (via get_current_user): This is simpler and more secure than token invalidation. Small performance cost (one extra query) is acceptable since the company can be cached in tenant context or fetched alongside the user.

2. **Distinct error for restricted company**: Users see "Company access is currently restricted" (not "domain not found") when their company is suspended — provides clearer feedback.

3. **Super admins are exempt** from company status checks: They either have `company_id = None` or should always be able to access the system.
