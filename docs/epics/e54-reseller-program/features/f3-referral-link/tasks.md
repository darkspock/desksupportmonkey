# Implementation Tasks: F3 — Referral Link

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 8
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain Layer | 0 | — (all reused from F1/F2) |
| Infrastructure Layer | 0 | — (all reused from F1/F2) |
| Application Layer | 1 | S |
| HTTP Layer | 3 | S each |
| Tests | 2 | S–M |
| Frontend | 2 | S each |

---

## Phase 1: Domain Layer

No tasks. All domain components already exist:
- `Reseller.referral_code` (F1)
- `ResellerClient.create()` with `source: ClientSource` (F2)
- `ClientSource.REFERRAL` enum value (F2)

## Phase 2: Infrastructure Layer

No tasks. All infrastructure already exists:
- `ResellerRepository.find_by_referral_code()` (F1)
- `ResellerClientRepository.find_by_company_id()` (F2)
- `ResellerClientRepository.save()` (F2)

---

## Phase 3: Application Layer

### TASK-001: Create `CreateReferralAttributionCommand` + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** None (all domain/infra components exist)

**Description:**
Create the command and handler that attributes a newly registered company to a reseller via referral code. The handler fails silently on all validation failures (invalid code, inactive reseller, already-attributed company).

**File:** `src/reseller_bc/client/application/commands/create_referral_attribution.py`

**Implementation:**
```python
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@dataclass
class CreateReferralAttributionCommand(Command):
    referral_code: str
    company_id: str


class CreateReferralAttributionCommandHandler(CommandHandler[CreateReferralAttributionCommand]):
    def __init__(
        self,
        reseller_repo: ResellerRepository,
        client_repo: ResellerClientRepository,
    ):
        self.reseller_repo = reseller_repo
        self.client_repo = client_repo

    def handle(self, command: CreateReferralAttributionCommand) -> None:
        # 1. Lookup reseller by referral code
        reseller = self.reseller_repo.find_by_referral_code(command.referral_code)
        if reseller is None:
            return  # Invalid code — fail silently

        # 2. Only active resellers get attribution
        if reseller.status != ResellerStatus.ACTIVE:
            return  # Inactive reseller — fail silently

        # 3. First-wins: don't re-attribute an already-linked company
        existing = self.client_repo.find_by_company_id(command.company_id)
        if existing is not None:
            return  # Already attributed — skip

        # 4. Create referral client record
        client = ResellerClient.create(
            reseller_id=reseller.id,
            company_id=command.company_id,
            source=ClientSource.REFERRAL,
            is_demo=False,
        )
        self.client_repo.save(client)
```

**Acceptance Criteria:**
- [ ] Inherits from `Command` / `CommandHandler`
- [ ] Command + Handler in the SAME file
- [ ] `handle()` returns `None` (CQRS)
- [ ] Finds reseller by referral code — returns silently if not found
- [ ] Checks `reseller.status == ACTIVE` — returns silently if not
- [ ] Checks `find_by_company_id` for first-wins — returns silently if already attributed
- [ ] Creates `ResellerClient` with `source=ClientSource.REFERRAL`, `is_demo=False`

---

## Phase 4: HTTP Layer

### TASK-002: Add `referral_code` to `RegisterCompanyRequest` Schema

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Add an optional `referral_code` field to the existing registration request schema. This is backward-compatible — existing calls without the field continue to work.

**File:** `adapters/http/api/registration/schemas.py`

**Change:**
```python
class RegisterCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    admin_email: EmailStr
    email_domains: list[str] = Field(min_length=1)
    referral_code: str | None = None  # NEW — optional referral attribution
```

**Acceptance Criteria:**
- [ ] `referral_code` field is `Optional[str]` with default `None`
- [ ] Existing request format still works without `referral_code`

---

### TASK-003: Add Reseller Repo Dependencies to Registration

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Add dependency provider functions for `ResellerRepository` and `ResellerClientRepository` in the registration dependencies module, so the registration router can instantiate the attribution handler.

**File:** `adapters/http/api/registration/dependencies.py`

**Add:**
```python
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository


def get_reseller_repo(db: Session = Depends(get_db)) -> ResellerRepository:
    return ResellerRepository(db)


def get_reseller_client_repo(db: Session = Depends(get_db)) -> ResellerClientRepository:
    return ResellerClientRepository(db)
```

**Acceptance Criteria:**
- [ ] `get_reseller_repo(db)` returns `ResellerRepository(db)`
- [ ] `get_reseller_client_repo(db)` returns `ResellerClientRepository(db)`
- [ ] Both use `Depends(get_db)` for session injection

---

### TASK-004: Update Registration Router for Referral Attribution

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-001, TASK-002, TASK-003

**Description:**
Modify the `register_company` endpoint to:
1. Pre-generate `company_id` and pass it to `CreateCompanyCommand(id=company_id, ...)`
2. After successful company creation, if `body.referral_code` is present, call `CreateReferralAttributionCommandHandler`
3. Wrap attribution in `try/except Exception` — log warning but never fail registration

**File:** `adapters/http/api/registration/routers.py`

**Changes:**
- Import `ulid`, `CreateReferralAttributionCommand`, `CreateReferralAttributionCommandHandler`, and the two new dependency functions
- Add `reseller_repo` and `reseller_client_repo` as `Depends(...)` params
- Pre-generate `company_id = str(ulid.new())` before `CreateCompanyCommand`
- Pass `id=company_id` to `CreateCompanyCommand`
- After company creation success, add referral attribution block:
```python
if body.referral_code:
    try:
        attribution_handler = CreateReferralAttributionCommandHandler(
            reseller_repo=reseller_repo,
            client_repo=reseller_client_repo,
        )
        attribution_handler.handle(
            CreateReferralAttributionCommand(
                referral_code=body.referral_code,
                company_id=company_id,
            )
        )
    except Exception:
        logger.warning(
            "Referral attribution failed for code=%s company=%s",
            body.referral_code, company_id, exc_info=True,
        )
```

**Acceptance Criteria:**
- [ ] Company ID pre-generated and passed to `CreateCompanyCommand.id`
- [ ] Attribution only attempted when `body.referral_code` is truthy
- [ ] Attribution handler instantiated with correct repos
- [ ] Attribution errors caught with `except Exception` — logged, never raised
- [ ] Existing error handling for company creation unchanged
- [ ] Return value unchanged (`{"data": {"message": ...}}`)

---

## Phase 5: Tests

### TASK-005: Unit Tests — `CreateReferralAttributionCommandHandler`

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create unit tests covering all handler behaviors using `MagicMock` for repos.

**File:** `tests/unit/reseller_bc/client/application/test_create_referral_attribution.py`

**Test Cases:**
1. **Valid referral code** → creates `ResellerClient` with `source=REFERRAL`, `is_demo=False`; `client_repo.save` called once
2. **Invalid referral code (no matching reseller)** → `find_by_referral_code` returns `None`; `client_repo.save` NOT called; no exception raised
3. **Reseller is suspended** → reseller returned with `status=SUSPENDED`; `client_repo.save` NOT called
4. **Reseller is deactivated** → reseller returned with `status=DEACTIVATED`; `client_repo.save` NOT called
5. **Company already attributed** → `find_by_company_id` returns existing `ResellerClient`; `client_repo.save` NOT called

**Pattern:**
```python
class TestCreateReferralAttribution:
    def setup_method(self):
        self.reseller_repo = MagicMock()
        self.client_repo = MagicMock()
        self.handler = CreateReferralAttributionCommandHandler(
            reseller_repo=self.reseller_repo,
            client_repo=self.client_repo,
        )
```

**Acceptance Criteria:**
- [ ] All 5 test cases implemented
- [ ] Uses `MagicMock` for both repos
- [ ] Verifies `save` is called (or not) in each scenario
- [ ] No exceptions raised in any test case

---

### TASK-006: Integration Tests — Registration with Referral Flow

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Create integration tests for `POST /api/v1/register` with the referral code parameter, verifying end-to-end attribution.

**File:** `tests/integration/test_registration_referral.py`

**Test Cases:**
1. **Register with valid referral code** → company created + `ResellerClient` record with `source=referral` found in DB
2. **Register with invalid referral code** → company created, no `ResellerClient` record, no error
3. **Register without referral code** → company created, no `ResellerClient` record (backward compat)
4. **Register with suspended reseller code** → company created, no `ResellerClient` record

**Fixtures Needed:**
- `reseller` fixture (active reseller with known referral_code)
- `suspended_reseller` fixture (suspended reseller)
- Use existing `client` fixture from `conftest.py`
- Stripe mock already provided by `conftest.py`

**Pattern:**
```python
@pytest.fixture()
def reseller(db_session):
    r = Reseller.create(email="ref@reseller.com", name="Ref Reseller", commission_pct=20, min_payout_cents=5000)
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r

class TestRegistrationReferral:
    def test_register_with_valid_referral(self, client, reseller, db_session):
        resp = client.post("/api/v1/register", json={
            "name": "Referred Corp",
            "admin_email": "admin@referredcorp.com",
            "email_domains": ["referredcorp.com"],
            "referral_code": reseller.referral_code,
        })
        assert resp.status_code == 201
        # Verify ResellerClient created
        rc = ResellerClientRepository(db_session).find_by_reseller_id(reseller.id)
        assert len(rc) == 1
        assert rc[0].source == ClientSource.REFERRAL
```

**Acceptance Criteria:**
- [ ] All 4 test cases implemented
- [ ] Tests use real DB (test fixtures from conftest.py)
- [ ] Verify `ResellerClient` records in DB (not just HTTP response)
- [ ] Backward compatibility confirmed (no referral_code → no attribution)

---

## Phase 6: Frontend

### TASK-007: Dashboard — Referral URL with Copy Button

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None (dashboard API already returns `referral_code`)

**Description:**
Update the reseller dashboard page to display the full referral URL (not just the raw code) and provide a copy-to-clipboard button.

**File:** `web/app/src/pages/reseller/ResellerDashboardPage.tsx`

**Changes:**
- Build full referral URL: `` `${window.location.origin}/auth/register?ref=${dashboard.referral_code}` ``
- Replace raw code display with a read-only input showing the full URL
- Add "Copy" button using `navigator.clipboard.writeText(referralUrl)`
- Show visual feedback (e.g., "Copied!" text) after successful copy

**Acceptance Criteria:**
- [ ] Full referral URL displayed (format: `https://{domain}/auth/register?ref={code}`)
- [ ] Copy button copies URL to clipboard
- [ ] Visual feedback on copy (brief "Copied!" indication)

---

### TASK-008: Registration Page — Cookie Handling + Referral Code in POST

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-002 (schema must accept `referral_code`)

**Description:**
Update the registration page to handle referral attribution:
1. On mount: read `ref` query param from URL; if present, set `dsm_ref` cookie (30-day expiry)
2. On submit: read referral code from URL param (priority) or `dsm_ref` cookie (fallback), include as `referral_code` in POST body

**File:** `web/app/src/pages/auth/RegisterPage.tsx`

**Changes:**
- Add `useEffect` to set `dsm_ref` cookie from URL `ref` param on mount
- Add `getReferralCode()` helper: URL param takes precedence over cookie
- Include `referral_code: getReferralCode()` in POST body (sends `null` if no referral)

**Implementation from design:**
```tsx
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const ref = params.get("ref");
  if (ref) {
    const expires = new Date();
    expires.setDate(expires.getDate() + 30);
    document.cookie = `dsm_ref=${ref}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
  }
}, []);

const getReferralCode = (): string | null => {
  const params = new URLSearchParams(window.location.search);
  const ref = params.get("ref");
  if (ref) return ref;
  const match = document.cookie.match(/(?:^|;\s*)dsm_ref=([^;]*)/);
  return match ? match[1] : null;
};
```

**Acceptance Criteria:**
- [ ] `dsm_ref` cookie set when `ref` URL param present (30-day expiry, `path=/`, `SameSite=Lax`)
- [ ] No cookie set when no `ref` param
- [ ] URL param takes precedence over cookie on submit
- [ ] `referral_code` included in POST body (null when no referral)
- [ ] Registration UX unchanged from prospect's perspective

---

## Dependency Graph

```
TASK-001 (Command+Handler) ─────────────────────┐
                                                 ├──→ TASK-004 (Router)──→ TASK-006 (Integration Tests)
TASK-002 (Schema) ──────────────────────────────┤
                                                 │
TASK-003 (Dependencies) ────────────────────────┘

TASK-001 ──→ TASK-005 (Unit Tests)

TASK-007 (Dashboard Frontend) ─── independent
TASK-008 (Registration Frontend) ── depends on TASK-002 (schema change)
```

## Execution Order

**Batch 1 (Parallel — no dependencies):**
- TASK-001: Create `CreateReferralAttributionCommand` + Handler
- TASK-002: Add `referral_code` to `RegisterCompanyRequest`
- TASK-003: Add reseller repo dependencies
- TASK-007: Dashboard referral URL + copy button

**Batch 2 (Depends on Batch 1):**
- TASK-004: Update registration router (depends on TASK-001, TASK-002, TASK-003)
- TASK-005: Unit tests (depends on TASK-001)
- TASK-008: Registration page cookie handling (depends on TASK-002)

**Batch 3 (Depends on Batch 2):**
- TASK-006: Integration tests (depends on TASK-004)

## Final Checklist

- [x] All 8 tasks completed
- [x] All unit tests passing (`make test`) — 5 referral attribution unit tests pass
- [x] All integration tests passing (`make test-integration`) — 4 registration referral integration tests pass
- [x] Existing registration tests still pass (backward compat) — 5 existing tests unaffected
- [ ] mypy passes (`make lint`)
- [x] No breaking changes to registration API
