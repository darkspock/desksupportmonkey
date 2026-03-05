# Architecture Review Report — Reseller Self-Registration + Password Auth

**Files Reviewed:** 20+
**Date:** 2026-03-04
**Status:** WARNINGS

---

## Summary

| Category | Status | Violations |
|----------|--------|------------|
| Layer Dependencies | WARNINGS | 2 (medium — pre-existing pattern) |
| CQRS Compliance | PASS | 0 |
| DDD Patterns | PASS | 0 |
| BC Boundaries | PASS | 0 |
| Anti-Patterns | WARNINGS | 3 (medium/low) |

---

## Scope

This review covers the new files and modifications for the "Reseller Self-Registration + Password Auth" feature (E54). It distinguishes between **new violations** introduced by this feature and **pre-existing patterns** carried over from the existing reseller BC codebase.

---

## 1. Layer Dependency Analysis

### Domain Layer — `src/reseller_bc/reseller/domain/`

| File | Status | Notes |
|------|--------|-------|
| `enums.py` | PASS | Pure enum, zero external dependencies |
| `entities.py` | PASS | Domain-only imports (enums, exceptions). Factory `create()` with validation. Business methods (`approve()`, `set_password_hash()`, `set_reset_token()`, etc.) encapsulate state transitions correctly |
| `exceptions.py` | PASS | Self-contained, no imports. 3 new exceptions: `ResellerPendingApprovalException`, `ResellerInvalidPasswordException`, `ResellerInvalidResetTokenException` |
| `repository.py` | PASS | Abstract interface only. Added `find_by_reset_token()` method returning domain entity |

**Verdict:** Domain layer is clean. No cross-layer violations.

---

### Application Layer — `src/reseller_bc/reseller/application/commands/`

| File | Inherits Command? | Inherits CommandHandler? | Method `handle()`? | Returns None? | Same file? | Status |
|------|---|---|---|---|---|---|
| `register_reseller.py` | Yes | Yes | Yes | Yes | Yes | PASS |
| `approve_reseller.py` | Yes | Yes | Yes | Yes | Yes | PASS |
| `reject_reseller.py` | Yes | Yes | Yes | Yes | Yes | PASS |
| `change_password.py` | Yes | Yes | Yes | Yes | Yes | PASS |
| `forgot_password.py` | Yes | Yes | Yes | Yes | Yes | PASS |
| `reset_password.py` | Yes | Yes | Yes | Yes | Yes | PASS |
| `password_login.py` | N/A (Service) | N/A | N/A | Returns `str` | N/A | See note |

**Note on `password_login.py`:** This is a `ResellerPasswordLoginService` (not a Command/Handler pair). It returns a JWT token string. This is **acceptable** — login is a read+verify operation that produces a token, which doesn't fit the Command (void return) pattern. The existing `reseller_oauth_login.py` follows the same service pattern. This is consistent with how auth flows work across the codebase.

#### Medium: Celery tasks imported directly inside command handlers

**Files:** `register_reseller.py:55`, `approve_reseller.py:42`, `reject_reseller.py:37`, `forgot_password.py:36`

```python
# Inside handle() method:
from core.tasks.reseller_emails import send_reseller_registration_confirmation
send_reseller_registration_confirmation.delay(...)
```

**Rule concern:** Application layer importing from `core/tasks/` (infrastructure-adjacent).

**Mitigating factors:**
- This is a **pre-existing pattern** used across the codebase (`notification_bc/email_subscriber.py:108`, `incident_bc/generate_report.py:61`, `report_bc/request_report.py:32`)
- Deferred import (inside `handle()`) reduces coupling at module level
- Celery `.delay()` is fire-and-forget async — no return value consumed

**Severity:** Medium (pre-existing pattern). Not a new violation introduced by this feature.

**Recommendation for future:** Extract an `EmailNotificationPort` interface in the domain, inject implementations via DI. Low priority since the pattern is established and stable.

#### Medium: `core.config.settings` accessed directly in handlers

**Files:** `approve_reseller.py:3` (import), `forgot_password.py` (import)

```python
from core.config import settings
login_url = f"{settings.FRONTEND_URL}/reseller/login"
```

**Concern:** Direct dependency on configuration singleton.

**Mitigating factors:** Same pattern used across codebase. `settings` is a simple Pydantic `BaseSettings` instance — not a service or repository.

**Severity:** Medium (pre-existing pattern).

**Recommendation:** Inject URL-building as a dependency or config parameter in future refactoring.

---

### Infrastructure Layer — `src/reseller_bc/reseller/infrastructure/`

| File | Status | Notes |
|------|--------|-------|
| `models.py` | PASS | SQLAlchemy 2.0 style (`Mapped[]`, `mapped_column()`). 3 new columns: `password_hash`, `reset_token`, `reset_token_expires_at` — all nullable, correct types |
| `repository.py` | PASS | Implements `ResellerRepositoryInterface`. `save()` and `_to_entity()` correctly map new fields. `find_by_reset_token()` properly implemented. Returns domain entities |

**Verdict:** Infrastructure layer is clean.

---

### HTTP Layer — `adapters/http/api/`

| File | Status | Notes |
|------|--------|-------|
| `reseller/schemas.py` | PASS | Simple Pydantic models. No `field_validator`, no `ConfigDict`. Proper validation constraints |
| `reseller/routers.py` | PASS (new endpoints) | See detailed analysis below |
| `admin/reseller_routers.py` | WARNINGS | See detailed analysis below |

---

## 2. CQRS Compliance

### Commands

| Command | Inherits? | Returns None? | Handler in same file? | Status |
|---------|-----------|---------------|----------------------|--------|
| `RegisterResellerCommand` | Yes | Yes | Yes | PASS |
| `ApproveResellerCommand` | Yes | Yes | Yes | PASS |
| `RejectResellerCommand` | Yes | Yes | Yes | PASS |
| `ChangeResellerPasswordCommand` | Yes | Yes | Yes | PASS |
| `ForgotResellerPasswordCommand` | Yes | Yes | Yes | PASS |
| `ResetResellerPasswordCommand` | Yes | Yes | Yes | PASS |

All commands properly use `@dataclass` decorator, inherit from `Command`, and their handlers inherit from `CommandHandler[T]` with `handle() -> None`.

---

## 3. DDD Pattern Compliance

### Entity: `Reseller`

| Check | Status | Notes |
|-------|--------|-------|
| Factory method `create()` | PASS | Accepts optional `status`, `password_hash`, `company_name` params. Validates inputs |
| State changes via methods | PASS | `approve()` checks PENDING status, sets ACTIVE. `set_password_hash()`, `set_reset_token()`, `clear_reset_token()` properly encapsulate mutations |
| Business rules in entity | PASS | `approve()` raises `ResellerPendingApprovalException` if not PENDING. `has_password` property |
| Domain exceptions | PASS | Custom exceptions for each business rule violation |

### Repository Interface

| Check | Status | Notes |
|-------|--------|-------|
| Interface in Domain | PASS | `ResellerRepositoryInterface(ABC)` |
| Implementation in Infrastructure | PASS | `ResellerRepository` implements interface |
| Returns entities | PASS | All methods return `Reseller` or `Optional[Reseller]` |
| New method `find_by_reset_token` | PASS | Properly defined in interface, implemented in infrastructure |

---

## 4. Bounded Context Boundaries

| Check | Status | Notes |
|-------|--------|-------|
| No cross-BC repository access | PASS | All new commands only use `ResellerRepositoryInterface` |
| No entity leakage | PASS | `Reseller` entity stays within `reseller_bc` |
| `PasswordService` and `JWTService` from `core/` | PASS | These are shared infrastructure services, not BC-specific |

---

## 5. HTTP Layer — Detailed Analysis of New Endpoints

### `POST /api/v1/reseller/auth/register` (routers.py:111-138)

**Exception handling:**
| Exception | Caught? | HTTP Status | Correct? |
|-----------|---------|-------------|----------|
| `ResellerAlreadyExistsException` | Yes | 409 | Yes |
| `ResellerInvalidPasswordException` | Yes | 422 | Yes |

**Verdict:** PASS — all handler exceptions properly caught.

### `POST /api/v1/reseller/auth/login` (routers.py:141-169)

**Exception handling:**
| Exception | Caught? | HTTP Status | Correct? |
|-----------|---------|-------------|----------|
| `ResellerNotRegisteredException` | Yes | 401 | Yes |
| `ResellerInvalidPasswordException` | Yes | 401 | Yes |
| `ResellerPendingApprovalException` | Yes | 403 | Yes |
| `ResellerDeactivatedException` | Yes | 401 | Yes |

**Verdict:** PASS — all service exceptions properly caught. Error messages don't leak internals.

### `POST /api/v1/reseller/auth/forgot-password` (routers.py:172-186)

**Exception handling:** No try/catch needed — handler intentionally never raises (silent on unknown email to prevent email enumeration).

**Verdict:** PASS — correct by design.

### `POST /api/v1/reseller/auth/reset-password` (routers.py:189-213)

**Exception handling:**
| Exception | Caught? | HTTP Status | Correct? |
|-----------|---------|-------------|----------|
| `ResellerInvalidResetTokenException` | Yes | 400 | Yes |
| `ResellerInvalidPasswordException` | Yes | 422 | Yes |

**Verdict:** PASS — all handler exceptions properly caught.

### `POST /api/v1/reseller/change-password` (routers.py:216-243)

**Exception handling:**
| Exception | Caught? | HTTP Status | Correct? |
|-----------|---------|-------------|----------|
| `ResellerNotFoundException` | Yes | 404 | Yes |
| `ResellerInvalidPasswordException` | Yes | 400 | Yes |

**Verdict:** PASS — all handler exceptions properly caught.

### `POST /api/v1/admin/resellers/{id}/approve` (admin_routers.py:194-220)

**Exception handling:**
| Exception | Caught? | HTTP Status | Correct? |
|-----------|---------|-------------|----------|
| `ResellerNotFoundException` | Yes | 404 | Yes |
| `ResellerPendingApprovalException` | Yes | 422 | Yes |
| `ReferralCodeCollisionException` | Yes | 500 | See note |

**Note:** `ReferralCodeCollisionException` mapped to 500 is **debatable** — it's a transient infrastructure issue (all generated codes collided), not a user error. 500 is arguably correct since it indicates a server-side problem. However, 409 (Conflict) or 503 (Service Unavailable/retry) might be more appropriate.

**Severity:** Low. Edge case that should rarely/never happen in practice.

### `POST /api/v1/admin/resellers/{id}/reject` (admin_routers.py:223-240+)

**Exception handling:**
| Exception | Caught? | HTTP Status | Correct? |
|-----------|---------|-------------|----------|
| `ResellerNotFoundException` | Yes | 404 | Yes |
| `ResellerPendingApprovalException` | Yes | 422 | Yes |

**Verdict:** PASS.

---

## 6. Anti-Patterns Detected

### Medium (Pre-existing): Direct Repository Instantiation in Routers

**Location:** All new endpoints in `routers.py` and `admin/reseller_routers.py`

```python
repo = ResellerRepository(db)
handler = RegisterResellerCommandHandler(repo=repo, password_service=PasswordService())
```

**Concern:** Architecture docs recommend dependency injection via container + Command/Query Bus.

**Mitigating factors:** This is the **established pattern** across the entire reseller BC (lines 50, 85, 97, 112 of `admin_routers.py` all pre-date this feature). The reseller BC was built without a DI container, unlike older BCs. All new endpoints follow the same pattern.

**Severity:** Medium (pre-existing). Not a regression.

**Recommendation:** When refactoring the reseller BC, introduce a DI container. This is a cross-cutting improvement, not specific to this feature.

### Low: `PasswordService` imported as module-level vs injected

**Location:** `password_login.py`, `change_password.py`, `reset_password.py` — `PasswordService` is injected via `__init__()`.

**Verdict:** PASS — this is actually the correct approach. Handlers receive `PasswordService` as a constructor parameter, which is proper DI.

### Low: `company_name` field hardcoded in `Reseller.create()`

**Location:** `entities.py` — `commission_pct=20` and `min_payout_cents=5000` are hardcoded in `register_reseller.py:45-46`.

**Concern:** Default commission/payout values should arguably come from configuration.

**Severity:** Low. These are business defaults for self-registered resellers and are intentional (per plan spec).

---

## 7. Email Templates & Celery Tasks

### `core/tasks/reseller_emails.py`

| Check | Status |
|-------|--------|
| Proper retry logic | PASS (max_retries=3, retry_backoff=True) |
| Consistent with existing patterns | PASS (matches `core/tasks/email_notifications.py`) |
| Uses template rendering | PASS |
| Error handling with logging | PASS |
| Registered in `core/tasks/__init__.py` | PASS |

---

## 8. OAuth Guard Modification

### `reseller_oauth_login.py` — PENDING status check

**Change:** Added `ResellerPendingApprovalException` check before `ResellerDeactivatedException` check.

```python
if reseller.status == ResellerStatus.PENDING:
    raise ResellerPendingApprovalException()
```

**Verdict:** PASS — correct ordering (check PENDING before DEACTIVATED), proper domain exception.

---

## Recommendations

### Must Fix (Blocking)

None. No critical architectural violations detected.

### Should Fix (Non-Blocking)

1. **`ReferralCodeCollisionException` status code** (admin_routers.py:214): Consider changing from 500 to 409 or 503 for better semantics.

### Consider (Future Improvements)

1. **DI Container for Reseller BC:** The entire reseller BC uses direct repository instantiation in routers. When the BC stabilizes, introduce a proper DI container.

2. **Email notification port:** Extract Celery task dispatching behind a domain interface (`EmailNotificationPort`). This would make command handlers fully testable without `@patch` on task modules.

3. **Configuration injection:** Replace direct `settings.FRONTEND_URL` access in handlers with injected config values.

---

## Architecture Diagram

```
                       ┌─────────────────────────────────────┐
                       │         HTTP Layer (Routers)         │
                       │   adapters/http/api/reseller/        │
                       │   adapters/http/api/admin/           │
                       │                                       │
                       │  - Parses requests (Pydantic schemas) │
                       │  - Catches domain exceptions → HTTP   │
                       │  - Uses Mappers for DTO → Response    │
                       └──────────┬────────────────────────────┘
                                  │ instantiates handlers directly
                                  │ (no DI container — pre-existing)
                       ┌──────────▼────────────────────────────┐
                       │       Application Layer (Commands)     │
                       │   register, approve, reject,           │
                       │   change_pw, forgot_pw, reset_pw,      │
                       │   password_login (service)             │
                       │                                        │
                       │  ✅ Inherit Command/CommandHandler      │
                       │  ✅ Return None                         │
                       │  ✅ Use repository interface            │
                       │  ⚠️ Import Celery tasks directly       │
                       └──────────┬─────────────────────────────┘
                                  │ depends on
                       ┌──────────▼─────────────────────────────┐
                       │         Domain Layer                    │
                       │   entities.py, enums.py,               │
                       │   exceptions.py, repository.py         │
                       │                                        │
                       │  ✅ Zero external dependencies          │
                       │  ✅ Factory methods with validation     │
                       │  ✅ Business rules in entity methods    │
                       │  ✅ Abstract repository interface       │
                       └────────────────────────────────────────┘
                                  ▲ implements
                       ┌──────────┴─────────────────────────────┐
                       │       Infrastructure Layer              │
                       │   models.py (SQLAlchemy 2.0)           │
                       │   repository.py (implements interface)  │
                       │                                        │
                       │  ✅ Mapped[] columns                    │
                       │  ✅ Entity ↔ Model mapping              │
                       │  ✅ find_by_reset_token() implemented   │
                       └────────────────────────────────────────┘
```

---

## References

- `ai_docs/architecture/architecture.md` — DDD and Hexagonal overview
- `ai_docs/architecture/critical-rules.md` — Critical rules (esp. Rule #0, #1, #4)
- `ai_docs/architecture/application-layer.md` — CQRS patterns
- `ai_docs/architecture/http-layer.md` — HTTP layer patterns
