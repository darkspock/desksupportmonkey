# Solution Design: F1 — Company List Enrichment

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Bounded Context:** `company_bc`

---

## Summary

Additive changes only — no new entities, no migrations, no breaking changes. Extend the existing list query, repository, DTO, HTTP schema, and frontend to expose usage counts, trial info, and plan data already stored in the database.

---

## Architecture Decision

**Batch counts via correlated subqueries** — avoid N+1 by fetching user and asset counts for all listed companies in the same SQL query using subqueries in the SELECT clause. SQLAlchemy supports this cleanly with `scalar_subquery()`.

**Plan price constants in `plan_gate.py`** — co-located with other plan constants (user limits, asset limits, feature flags). Single source of truth for all plan-related data.

---

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `ListCompaniesQuery` | `src/company_bc/company/application/queries/list_companies.py` | Yes | Add `in_trial`, `plan` filter params |
| `ListCompaniesQueryHandler` | same file | Yes | Add batch count fetch, trial computation |
| `CompanyListItemDto` | same file | Yes | Add `user_count`, `asset_count`, `trial_days_remaining`, `plan`, `billing_status` |
| `CompanyRepository.find_all()` | `src/company_bc/company/infrastructure/repository.py` | Yes | Add filter params + batch count subquery |
| `CompanyResponse` schema | `adapters/http/api/companies/schemas.py` | Yes | Add new fields |
| `GetCompanyBillingQueryHandler` | `src/company_bc/company/application/queries/billing/get_company_billing.py` | Yes | Add trial fields to DTO |
| `CompanyBillingResponse` schema | `adapters/http/api/companies/schemas.py` | Yes | Add trial fields |
| `plan_gate.py` | `src/company_bc/company/domain/plan_gate.py` | Yes | Add price constants |
| `CompaniesPage.tsx` | `web/app/src/pages/superadmin/CompaniesPage.tsx` | Yes | Add columns + filters |
| `CompanyBillingModal.tsx` | `web/app/src/pages/superadmin/CompanyBillingModal.tsx` | Yes | Add trial section |
| `types/index.ts` | `web/app/src/types/index.ts` | Yes | Add new Company fields |

---

## Implementation Plan

### 1. Domain Layer — No changes

`Company` entity already has all needed fields. No new enums or value objects needed.

---

### 2. Application Layer

#### `src/company_bc/company/domain/plan_gate.py` — Add price constants

```python
# Add alongside PLAN_USER_LIMITS and PLAN_ASSET_LIMITS:
PLAN_PRICE_CENTS: dict[PlanTier, int] = {
    PlanTier.FREE: 0,
    PlanTier.PREMIUM: 4900,       # $49/month
    PlanTier.ENTERPRISE: 14900,   # $149/month
    PlanTier.OPEN_SOURCE: 0,
}
```

#### `src/company_bc/company/application/queries/list_companies.py` — Extend

```python
@dataclass
class CompanyListItemDto:
    id: str
    name: str
    status: str
    email_domains: list[str]
    is_active: bool
    plan: str
    billing_status: str
    user_count: int
    asset_count: int
    trial_days_remaining: Optional[int]   # null = not in trial
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class ListCompaniesQuery(Query):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    in_trial: Optional[bool] = None    # NEW: True = only trial companies
    plan: Optional[str] = None          # NEW: filter by plan tier

class ListCompaniesQueryHandler(QueryHandler[ListCompaniesQuery, tuple[list[CompanyListItemDto], int]]):
    def handle(self, query: ListCompaniesQuery) -> tuple[list[CompanyListItemDto], int]:
        rows, total = self.company_repo.find_all_with_counts(
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            in_trial=query.in_trial,
            plan=query.plan,
        )
        now = datetime.now(timezone.utc)
        result = []
        for company, user_count, asset_count in rows:
            trial_days_remaining: Optional[int] = None
            if company.trial_ends_at:
                trial_end = company.trial_ends_at
                if trial_end.tzinfo is None:
                    trial_end = trial_end.replace(tzinfo=timezone.utc)
                if trial_end > now:
                    trial_days_remaining = max(0, (trial_end - now).days)
            result.append(CompanyListItemDto(
                id=company.id,
                name=company.name,
                status=company.status.value,
                email_domains=company.email_domains,
                is_active=company.is_active,
                plan=company.plan.value,
                billing_status=company.billing_status.value,
                user_count=user_count,
                asset_count=asset_count,
                trial_days_remaining=trial_days_remaining,
                created_at=company.created_at,
                updated_at=company.updated_at,
            ))
        return result, total
```

#### `src/company_bc/company/application/queries/billing/get_company_billing.py` — Extend DTO

```python
@dataclass
class CompanyBillingDto:
    # ... existing fields ...
    trial_days_remaining: Optional[int]   # NEW
    trial_ends_at: Optional[datetime]      # NEW
```

Handler update — add after `company = self.company_repo.find_by_id(...)`:
```python
trial_days_remaining: Optional[int] = None
if company.trial_ends_at:
    trial_end = company.trial_ends_at
    if trial_end.tzinfo is None:
        trial_end = trial_end.replace(tzinfo=timezone.utc)
    remaining = (trial_end - datetime.now(timezone.utc)).days
    trial_days_remaining = max(0, remaining) if trial_end > datetime.now(timezone.utc) else None
```

---

### 3. Infrastructure Layer

#### `src/company_bc/company/infrastructure/repository.py` — Add `find_all_with_counts`

New method replaces `find_all` for the list query. Uses correlated subqueries:

```python
def find_all_with_counts(
    self,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    in_trial: Optional[bool] = None,
    plan: Optional[str] = None,
) -> tuple[list[tuple[Company, int, int]], int]:
    from src.auth_bc.user.infrastructure.models import UserModel
    from src.asset_bc.asset.infrastructure.models import AssetModel

    # Correlated subqueries for counts
    user_count_sq = (
        select(func.count())
        .where(UserModel.company_id == CompanyModel.id)
        .where(UserModel.is_active == True)
        .correlate(CompanyModel)
        .scalar_subquery()
    )
    asset_count_sq = (
        select(func.count())
        .where(AssetModel.company_id == CompanyModel.id)
        .where(AssetModel.status != "decommissioned")
        .correlate(CompanyModel)
        .scalar_subquery()
    )

    stmt = select(CompanyModel, user_count_sq.label("user_count"), asset_count_sq.label("asset_count"))

    # Filters
    if search:
        stmt = stmt.where(CompanyModel.name.ilike(f"%{search}%"))
    if in_trial is True:
        stmt = stmt.where(CompanyModel.trial_ends_at > func.now())
    if plan:
        stmt = stmt.where(CompanyModel.plan == plan)

    total = self._session.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = stmt.order_by(CompanyModel.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    rows = self._session.execute(stmt).all()
    result = [
        (self._to_entity(row.CompanyModel), row.user_count, row.asset_count)
        for row in rows
    ]
    return result, total or 0
```

---

### 4. HTTP Layer

#### `adapters/http/api/companies/schemas.py` — Extend schemas

```python
class CompanyResponse(BaseModel):
    id: str
    name: str
    status: str
    email_domains: list[str]
    is_active: bool
    plan: str                                    # NEW
    billing_status: str                          # NEW
    user_count: int                              # NEW (moved from CompanyDetailResponse)
    asset_count: int                             # NEW
    trial_days_remaining: Optional[int] = None  # NEW
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CompanyBillingResponse(BaseModel):
    # ... existing fields ...
    trial_days_remaining: Optional[int] = None  # NEW
    trial_ends_at: Optional[datetime] = None     # NEW
```

#### `adapters/http/api/companies/routers.py` — Add filter params

```python
@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    in_trial: Optional[bool] = Query(None),   # NEW
    plan: Optional[str] = Query(None),          # NEW
    ...
):
    handler = ListCompaniesQueryHandler(company_repo=company_repo)
    companies, total = handler.handle(
        ListCompaniesQuery(page=page, page_size=page_size, search=search, in_trial=in_trial, plan=plan)
    )
```

Update `_to_response()` helper to map all new DTO fields.

---

### 5. Frontend

#### `web/app/src/types/index.ts`

```typescript
export interface Company {
  id: string;
  name: string;
  status: CompanyStatus;
  email_domains: string[];
  is_active: boolean;
  plan: string;                          // NEW
  billing_status: string;                // NEW
  user_count: number;                    // NEW
  asset_count: number;                   // NEW
  trial_days_remaining: number | null;   // NEW
  created_at: string;
  updated_at?: string;
}
```

#### `web/app/src/pages/superadmin/CompaniesPage.tsx`

**New table columns:** Users (numeric), Assets (numeric)
**Trial badge:** pill next to company name when `trial_days_remaining !== null`
**New filter row:**
```tsx
<select value={planFilter} onChange={...}>
  <option value="">All plans</option>
  <option value="free">Free</option>
  <option value="premium">Premium</option>
  <option value="enterprise">Enterprise</option>
  <option value="open_source">Open Source</option>
</select>
<label>
  <input type="checkbox" checked={inTrialFilter} onChange={...} />
  In trial only
</label>
```

#### `web/app/src/pages/superadmin/CompanyBillingModal.tsx`

Add trial section at the top of the modal when `billing.trial_days_remaining !== null`:
```tsx
{billing.trial_days_remaining !== null && (
  <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm dark:border-blue-800 dark:bg-blue-900/20">
    <p className="font-medium text-blue-800 dark:text-blue-300">
      {t('page.companies.billing.in_trial')}
    </p>
    <p className="text-blue-700 dark:text-blue-400">
      {billing.trial_days_remaining} {t('page.companies.billing.days_remaining')}
      {billing.trial_ends_at && ` · ${t('page.companies.billing.expires')} ${formatDate(billing.trial_ends_at)}`}
    </p>
  </div>
)}
```

---

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/company_bc/company/domain/plan_gate.py` | Additive | Add `PLAN_PRICE_CENTS` dict |
| `src/company_bc/company/application/queries/list_companies.py` | Extend | New DTO fields + filter params |
| `src/company_bc/company/application/queries/billing/get_company_billing.py` | Extend | Add trial fields to DTO |
| `src/company_bc/company/infrastructure/repository.py` | Additive | New `find_all_with_counts()` method |
| `adapters/http/api/companies/schemas.py` | Extend | New response fields |
| `adapters/http/api/companies/routers.py` | Extend | New query params, updated handler call |
| `web/app/src/types/index.ts` | Extend | New Company fields |
| `web/app/src/pages/superadmin/CompaniesPage.tsx` | Extend | New columns + filters |
| `web/app/src/pages/superadmin/CompanyBillingModal.tsx` | Extend | Trial section |
| `web/app/src/locales/en.ts` + `es.ts` | Additive | New i18n keys |

**Breaking changes:** None — all response changes are additive.

---

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | `ListCompaniesQueryHandler` — trial computation, dto fields | High |
| Unit | `GetCompanyBillingQueryHandler` — trial fields in DTO | High |
| Integration | `GET /companies` — counts, trial badge, filters | High |
| Integration | `GET /companies/{id}/billing` — trial fields present | Medium |

---

## Implementation Order

1. `plan_gate.py` — add `PLAN_PRICE_CENTS`
2. `list_companies.py` — extend DTO + query + handler
3. `repository.py` — add `find_all_with_counts()`
4. `get_company_billing.py` — extend DTO + handler
5. `schemas.py` — extend HTTP schemas
6. `routers.py` — wire new params
7. Unit tests
8. Integration tests
9. Frontend: types → CompaniesPage → CompanyBillingModal → i18n
