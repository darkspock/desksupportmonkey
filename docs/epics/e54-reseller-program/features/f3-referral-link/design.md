# Solution Design: F3 — Referral Link

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `reseller_bc` (primary) + collateral in `registration` adapter

## Summary

Add referral link attribution to the self-service registration flow. When a prospect registers a company using a URL that contains a reseller's referral code (e.g., `?ref=abc12345`), the system automatically creates a `ResellerClient` record attributing that company to the reseller. The reseller dashboard is updated to display the full referral URL with a copy-to-clipboard button. The frontend registration page handles cookie-based attribution (30-day `dsm_ref` cookie) so the referral persists even if the prospect doesn't register immediately.

## Architecture Decision

**Approach: Separate attribution command, orchestrated by the registration router.**

The referral attribution is a concern of the `reseller_bc`, not the `company_bc`. To keep bounded contexts clean:

- `CreateCompanyCommand` stays unchanged (the company BC doesn't know about resellers)
- A new `CreateReferralAttributionCommand` in `reseller_bc` handles the attribution logic
- The registration router orchestrates both: first creates the company, then (if a referral code is provided) calls the attribution handler
- Attribution failures are silently caught — they must never block registration

**Why not put attribution inside `CreateCompanyCommandHandler`?**
- Violates BC boundaries (company BC shouldn't import from reseller BC)
- Makes registration dependent on reseller infrastructure
- The router is already an orchestration layer — it's allowed to coordinate across BCs

**Why pre-generate company_id in the router?**
- `CreateCompanyCommand` already has an optional `id` field
- Pre-generating the ID allows the router to pass it to both the company creation handler and the attribution handler, without needing a return value from the command (which would violate CQRS)

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `Reseller.referral_code` field | `src/reseller_bc/reseller/domain/entities.py` | Yes | None — already auto-generated (8-char alphanumeric) |
| `ResellerRepository.find_by_referral_code()` | `src/reseller_bc/reseller/infrastructure/repository.py` | Yes | None — already exists |
| `ResellerClient.create()` with `source` param | `src/reseller_bc/client/domain/entities.py` | Yes | None — already accepts `ClientSource.REFERRAL` |
| `ClientSource.REFERRAL` enum value | `src/reseller_bc/client/domain/enums.py` | Yes | None — already exists |
| `ResellerClientRepository.find_by_company_id()` | `src/reseller_bc/client/infrastructure/repository.py` | Yes | None — already exists (for first-wins check) |
| `ResellerClientRepository.save()` | `src/reseller_bc/client/infrastructure/repository.py` | Yes | None |
| `ResellerDashboardDto.referral_code` | `src/reseller_bc/reseller/application/dtos.py` | Yes | None — already exposed on dashboard |
| `ResellerDashboardResponse.referral_code` | `adapters/http/api/reseller/schemas.py` | Yes | None — already in response schema |
| `CreateCompanyCommand.id` (optional) | `src/company_bc/company/application/commands/create_company.py` | Yes | None — already supports pre-generated ID |
| Registration router | `adapters/http/api/registration/routers.py` | Modify | Add referral code handling after company creation |
| Registration schema | `adapters/http/api/registration/schemas.py` | Modify | Add optional `referral_code` field |
| Registration dependencies | `adapters/http/api/registration/dependencies.py` | Modify | Add reseller repo dependencies |
| Reseller dashboard page | `web/app/src/pages/reseller/ResellerDashboardPage.tsx` | Modify | Add full URL display + copy button |
| Registration page | `web/app/src/pages/auth/RegisterPage.tsx` | Modify | Handle `ref` param + `dsm_ref` cookie |

## Implementation Plan

### 1. Domain Layer

No new entities, value objects, enums, or domain events needed. All domain components already exist from F1 and F2.

### 2. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| `CreateReferralAttributionCommand` | `CreateReferralAttributionCommandHandler` | `src/reseller_bc/client/application/commands/create_referral_attribution.py` | Attributes a newly registered company to a reseller via referral code |

**`CreateReferralAttributionCommand`:**

```python
@dataclass
class CreateReferralAttributionCommand(Command):
    referral_code: str
    company_id: str
```

**`CreateReferralAttributionCommandHandler`:**

```python
class CreateReferralAttributionCommandHandler(CommandHandler[CreateReferralAttributionCommand]):
    def __init__(
        self,
        reseller_repo: ResellerRepositoryInterface,
        client_repo: ResellerClientRepositoryInterface,
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

**Key behaviors:**
- Fails silently on invalid code, inactive reseller, or already-attributed company
- Returns `None` (CQRS compliance)
- No exceptions raised — all validation results in silent no-ops

### 3. Infrastructure Layer

No new models, repositories, or migrations needed. All infrastructure already exists from F1 and F2.

### 4. HTTP Layer

#### Schema Changes

**`adapters/http/api/registration/schemas.py`** — Add optional referral_code:

```python
class RegisterCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    admin_email: EmailStr
    email_domains: list[str] = Field(min_length=1)
    referral_code: str | None = None  # NEW — optional referral attribution
```

#### Dependency Changes

**`adapters/http/api/registration/dependencies.py`** — Add reseller repo factories:

```python
def get_reseller_repo(db: Session = Depends(get_db)) -> ResellerRepository:
    return ResellerRepository(db)

def get_reseller_client_repo(db: Session = Depends(get_db)) -> ResellerClientRepository:
    return ResellerClientRepository(db)
```

#### Router Changes

**`adapters/http/api/registration/routers.py`** — Orchestrate referral attribution:

```python
@router.post("", status_code=status.HTTP_201_CREATED)
def register_company(
    body: RegisterCompanyRequest,
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    # ... existing deps ...
    reseller_repo: ResellerRepository = Depends(get_reseller_repo),
    reseller_client_repo: ResellerClientRepository = Depends(get_reseller_client_repo),
):
    # Pre-generate company ID so we can use it for attribution
    company_id = str(ulid.new())

    handler = CreateCompanyCommandHandler(...)
    cmd = CreateCompanyCommand(
        id=company_id,  # Pass pre-generated ID
        name=body.name,
        email_domains=body.email_domains,
        admin_email=body.admin_email,
    )
    try:
        handler.handle(cmd)
    except ...:
        # existing error handling
        ...

    # Referral attribution (after successful company creation)
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

    return {"data": {"message": "Company registered. Check your email for the magic link."}}
```

### 5. Frontend Changes

#### Reseller Dashboard — Referral Link Section

**`web/app/src/pages/reseller/ResellerDashboardPage.tsx`:**

Replace the raw `referral_code` display with a full referral URL and copy-to-clipboard button:

```tsx
// Build full referral URL
const referralUrl = `${window.location.origin}/auth/register?ref=${dashboard.referral_code}`;

// UI: Input showing full URL + Copy button
<div className="flex items-center gap-2">
  <input
    type="text"
    readOnly
    value={referralUrl}
    className="flex-1 bg-gray-50 border rounded px-3 py-2 text-sm font-mono"
  />
  <button onClick={() => navigator.clipboard.writeText(referralUrl)}>
    Copy
  </button>
</div>
```

#### Registration Page — Referral Cookie Handling

**`web/app/src/pages/auth/RegisterPage.tsx`:**

On mount:
1. Read `ref` query parameter from URL
2. If present, set `dsm_ref` cookie with 30-day expiry
3. On form submit, read `ref` from URL params or `dsm_ref` cookie, include as `referral_code` in the POST body

```tsx
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const ref = params.get("ref");
  if (ref) {
    // Set cookie with 30-day expiry
    const expires = new Date();
    expires.setDate(expires.getDate() + 30);
    document.cookie = `dsm_ref=${ref}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
  }
}, []);

// In submit handler:
const getReferralCode = (): string | null => {
  // URL param takes precedence
  const params = new URLSearchParams(window.location.search);
  const ref = params.get("ref");
  if (ref) return ref;
  // Fall back to cookie
  const match = document.cookie.match(/(?:^|;\s*)dsm_ref=([^;]*)/);
  return match ? match[1] : null;
};

// POST body:
const payload = {
  name: companyName,
  admin_email: adminEmail,
  email_domains: domains,
  referral_code: getReferralCode(),  // null if no referral
};
```

### 6. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `adapters/http/api/registration/schemas.py` | Modify | Add optional `referral_code` field |
| `adapters/http/api/registration/routers.py` | Modify | Pre-generate company_id, call attribution handler after company creation |
| `adapters/http/api/registration/dependencies.py` | Modify | Add `get_reseller_repo` and `get_reseller_client_repo` |
| `web/app/src/pages/reseller/ResellerDashboardPage.tsx` | Modify | Full referral URL + copy button |
| `web/app/src/pages/auth/RegisterPage.tsx` | Modify | Cookie handling + referral_code in POST body |

#### Breaking Changes

None. The `referral_code` field is optional in the request schema. Existing registration flow works identically without it.

## Data Flow

```
Prospect clicks referral link
  → Frontend loads /auth/register?ref=abc12345
  → Sets dsm_ref cookie (30-day expiry)
  → Prospect fills out registration form
  → Frontend reads ref param / dsm_ref cookie
  → POST /api/v1/register { name, admin_email, email_domains, referral_code: "abc12345" }

Registration Router:
  1. Pre-generate company_id
  2. CreateCompanyCommand(id=company_id, name, email_domains, admin_email)
     → Creates company, admin user, magic link, seeds data
  3. If referral_code present:
     CreateReferralAttributionCommand(referral_code, company_id)
       → find_by_referral_code("abc12345") → Reseller entity
       → Check reseller.status == ACTIVE
       → find_by_company_id(company_id) → None (first-wins check)
       → ResellerClient.create(reseller_id, company_id, source=REFERRAL)
       → save()
  4. Return success message

Reseller Dashboard:
  → GET /api/v1/reseller/dashboard already returns referral_code
  → Frontend formats as full URL: {origin}/auth/register?ref={code}
  → Copy button copies URL to clipboard
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F1 (Portal Foundation) | Feature | `Reseller` entity with `referral_code` field |
| F2 (Account Creation) | Feature | `ResellerClient` entity, `ClientSource` enum, `ResellerClientRepository` |
| Registration flow | Existing | `POST /api/v1/register` endpoint and `CreateCompanyCommand` |

## Testing Strategy

| Test Type | Scope | File | Priority |
|-----------|-------|------|----------|
| Unit | `CreateReferralAttributionCommandHandler` — valid code, invalid code, inactive reseller, first-wins | `tests/unit/reseller_bc/client/application/test_create_referral_attribution.py` | High |
| Integration | `POST /api/v1/register` with referral_code — successful attribution, invalid code ignored, inactive reseller ignored | `tests/integration/test_registration_referral.py` | High |
| Integration | Existing registration tests pass without referral_code (backward compat) | `tests/integration/test_registration_endpoints.py` (existing) | High |

### Unit Test Cases for `CreateReferralAttributionCommandHandler`:
1. Valid referral code → creates `ResellerClient` with `source=REFERRAL`
2. Invalid referral code (no matching reseller) → no-op, no exception
3. Reseller is suspended → no-op
4. Reseller is deactivated → no-op
5. Company already attributed to a reseller → no-op (first-wins)

### Integration Test Cases:
1. Register with valid referral_code → company created + ResellerClient record created with `source=referral`
2. Register with invalid referral_code → company created, no ResellerClient (no error)
3. Register without referral_code → company created, no ResellerClient (backward compat)
4. Register with referral_code of suspended reseller → company created, no ResellerClient

## Implementation Order

1. [ ] Application: `CreateReferralAttributionCommand` + handler
2. [ ] HTTP: Add `referral_code` to `RegisterCompanyRequest` schema
3. [ ] HTTP: Add reseller repo dependencies to registration
4. [ ] HTTP: Update registration router to orchestrate attribution
5. [ ] Unit tests: `CreateReferralAttributionCommandHandler`
6. [ ] Integration tests: Registration with referral flow
7. [ ] Frontend: Dashboard referral URL + copy button
8. [ ] Frontend: Registration page cookie handling + referral_code in POST

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Attribution fails and blocks registration | Low | High | try/except with logging — attribution errors never propagate |
| Cookie blocked by browser privacy settings | Medium | Low | URL param also works as direct fallback; cookie is for delayed registration only |
| Race condition: two registrations with same company name, one with referral | Very Low | Low | Company name uniqueness check runs first; attribution only runs on success |

## Open Technical Questions

None — all infrastructure already exists. Implementation is straightforward.
