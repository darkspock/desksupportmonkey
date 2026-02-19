# Solution Design: F2 — Procurement Config

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `procurement_bc.budget`

## Summary

Per-company procurement configuration: enforcement mode, approval threshold, PO prefix, fiscal year start month, currency, auto-create assets toggle. Two API endpoints (GET + PUT), one frontend settings page. Follows the exact pattern of E11's assignment-ai config and E13's classification config.

## Architecture Decision

This is a singleton config per company, persisted via upsert command. The settings router goes under `/api/v1/settings/procurement` to match existing `/api/v1/settings/assignment-ai` and `/api/v1/settings/request-classification` conventions. Admin only.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| CompanyProcurementConfig entity + repo | `src/procurement_bc/budget/domain/` (F0) | Yes | None |
| Config model + repo | `src/procurement_bc/budget/infrastructure/` (F0) | Yes | None |
| AssignmentAISettings pattern | `adapters/http/api/settings/` | Template | None |
| AssignmentAISettingsPage | `web/app/src/pages/admin/AssignmentAISettingsPage.tsx` | Template | None |

## Implementation Plan

### 1. Application Layer

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| SaveProcurementConfigCommand | SaveProcurementConfigCommandHandler | Upsert procurement config |

```python
@dataclass
class SaveProcurementConfigCommand(Command):
    company_id: str
    enforcement_mode: str  # "warn" or "strict"
    approval_threshold_cents: int
    po_number_prefix: str
    fiscal_year_start_month: int
    currency: str
    auto_create_assets: bool
    performed_by: str = ""
```

Handler validates:
- `enforcement_mode` in ("warn", "strict")
- `approval_threshold_cents` >= 0
- `fiscal_year_start_month` in range 1-12
- `po_number_prefix` non-empty, max 10 chars
- `currency` is 3-character string

#### Queries

| Query | Handler | Description |
|-------|---------|-------------|
| GetProcurementConfigQuery | GetProcurementConfigQueryHandler | Get config or return defaults |

```python
@dataclass
class GetProcurementConfigQuery(Query):
    company_id: str
```

Returns config entity or a default config if none exists yet.

### 2. HTTP Layer

#### Endpoints

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| PUT | `/api/v1/settings/procurement` | admin | Save/update procurement config |
| GET | `/api/v1/settings/procurement` | admin | Get procurement config |

#### Schemas

```python
class ProcurementConfigUpdateRequest(BaseModel):
    enforcement_mode: str = Field(pattern="^(warn|strict)$")
    approval_threshold_cents: int = Field(ge=0)
    po_number_prefix: str = Field(min_length=1, max_length=10)
    fiscal_year_start_month: int = Field(ge=1, le=12)
    currency: str = Field(min_length=3, max_length=3)
    auto_create_assets: bool = False

class ProcurementConfigResponse(BaseModel):
    id: Optional[str]
    company_id: str
    enforcement_mode: str
    approval_threshold_cents: int
    po_number_prefix: str
    fiscal_year_start_month: int
    currency: str
    auto_create_assets: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

#### Dependencies

```python
def get_procurement_config_repo(db: Session = Depends(get_db)) -> CompanyProcurementConfigRepository:
    return CompanyProcurementConfigRepository(db)
```

### 3. Frontend

| Page | File | Description |
|------|------|-------------|
| ProcurementSettingsPage | `web/app/src/pages/admin/ProcurementSettingsPage.tsx` | Config form (follows AssignmentAISettingsPage pattern) |

Fields:
- Enforcement mode: dropdown (Warn / Strict)
- Approval threshold: number input (in whole currency units, convert to cents)
- PO number prefix: text input
- Fiscal year start month: dropdown (January-December)
- Currency: text input (ISO 4217)
- Auto-create assets on receipt: toggle

### 4. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `app.py` | Edit | Register procurement settings router |
| `web/app/src/router.tsx` | Edit | Add settings/procurement route |
| `web/app/src/components/layout/Sidebar.tsx` | Edit | Add "Procurement Settings" nav item |
| `web/app/src/types/index.ts` | Edit | Add CompanyProcurementConfig interface |
| `web/app/src/locales/en.ts` | Edit | Add ~15 keys |
| `web/app/src/locales/es.ts` | Edit | Add ~15 keys |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | SaveProcurementConfigCommandHandler (create + update) | High |
| Unit | GetProcurementConfigQueryHandler (exists + defaults) | High |
| Unit | Validation (invalid mode, threshold, month) | Medium |
| Integration | PUT + GET endpoints | High |
| Integration | Admin-only access | Medium |

~10 tests total (6 unit + 4 integration).

## Implementation Order

1. [ ] Application: SaveProcurementConfigCommand + handler
2. [ ] Application: GetProcurementConfigQuery + handler
3. [ ] HTTP: Schemas
4. [ ] HTTP: Dependencies
5. [ ] HTTP: Router
6. [ ] Config: Register router in app.py
7. [ ] Frontend: Types, page, router, sidebar, i18n
8. [ ] Tests: Unit tests
9. [ ] Tests: Integration tests
