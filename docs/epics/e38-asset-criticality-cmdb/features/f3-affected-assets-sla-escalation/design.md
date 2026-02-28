# Solution Design: F3 — Affected Assets & SLA Escalation

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-26
**Bounded Context:** `request_bc` (affected assets command), `sla_bc` (escalation logic), `asset_bc` (batch lookup), `company_bc` (escalation config)

## Summary

Technicians can mark which of the requester's assigned assets are affected by a service request. The affected asset IDs are stored in the request's existing `data` JSON field (`data.affected_asset_ids: string[]`). The SLA query handler reads these IDs, fetches the highest criticality among affected assets, and applies read-time priority escalation — looking up SLA policy by a higher effective priority without modifying the request's actual priority. A company-level setting controls whether escalation is active.

## Architecture Decision

**Approach chosen:** Read-time escalation in the SLA query handler.

This was chosen over alternatives because:
- **No migration needed** for affected assets — uses existing `data` JSON field on `ServiceRequest`, consistent with how `auto_assignment` metadata is already stored there.
- **Read-time escalation** avoids modifying `request.priority` (which would trigger cascading events, audit logs, and confuse reporting). The SLA query simply resolves a different policy tier at read time.
- **Company config follows existing pattern** — separate entity in `company_bc/sla_escalation_config/` following the `assignment_config` and `nav_config` patterns (each config gets its own subdomain with entity, repository, model).
- **Batch asset lookup** — new `find_by_ids()` method on AssetRepositoryInterface avoids N+1 queries.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ServiceRequest.data JSON field | `src/request_bc/request/domain/entities.py` | Yes | No changes — already supports arbitrary dict |
| RequestRepository | `src/request_bc/request/infrastructure/repository.py` | Yes | No changes — already persists `data` field |
| Request PATCH pattern | `adapters/http/api/requests/routers.py` | Pattern | Add new PATCH endpoint for affected assets |
| GetRequestSlaStatusQuery | `src/sla_bc/sla/application/queries/get_request_sla.py` | Modify | Add escalation logic, new DTO fields |
| SlaRepositoryInterface.find_policy_for_request | `src/sla_bc/sla/domain/repository.py` | Yes | No changes — already accepts priority string |
| AssetRepositoryInterface | `src/asset_bc/asset/domain/repository.py` | Extend | Add `find_by_ids()` method |
| AssetRepository (infra) | `src/asset_bc/asset/infrastructure/repository.py` | Extend | Implement `find_by_ids()` |
| find_by_assigned_to | `src/asset_bc/asset/domain/repository.py` | Yes | Used to show requester's assets |
| Company config pattern | `src/company_bc/nav_config/` | Pattern | Follow for sla_escalation_config |
| RequestPriority enum | `src/request_bc/request/domain/enums.py` | Yes | No changes |
| AssetCriticality enum | `src/asset_bc/asset/domain/enums.py` | Yes | No changes |

## Implementation Plan

### 1. Domain Layer

#### New Entity: SLA Escalation Config

| Entity | File Path | Description |
|--------|-----------|-------------|
| CompanySlaEscalationConfig | `src/company_bc/sla_escalation_config/domain/entities.py` | Company-level on/off toggle for criticality-based SLA escalation |

```python
@dataclass
class CompanySlaEscalationConfig:
    id: str
    company_id: str
    enabled: bool  # default: True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id: str, enabled: bool = True) -> "CompanySlaEscalationConfig":
        return cls(id=str(ulid.new()), company_id=company_id, enabled=enabled)
```

#### Repository Interface: SLA Escalation Config

| Interface | File Path | Methods |
|-----------|-----------|---------|
| SlaEscalationConfigRepositoryInterface | `src/company_bc/sla_escalation_config/domain/repository.py` | `save()`, `find_by_company()` |

#### Extended Interface: AssetRepository

| Method | File Path | Description |
|--------|-----------|-------------|
| `find_by_ids(asset_ids, company_id)` | `src/asset_bc/asset/domain/repository.py` | Batch fetch assets by ID list (single `WHERE id IN (...)` query) |

#### Escalation Logic (Pure Function)

A pure helper function for priority escalation, placed in the SLA query file alongside the handler:

```python
PRIORITY_ESCALATION_MAP = {
    "low": "medium",
    "medium": "high",
    "high": "urgent",
    "urgent": "urgent",  # already max
}

def compute_effective_priority(
    request_priority: str,
    affected_asset_criticalities: list[str],
) -> tuple[str, bool]:
    """Returns (effective_priority, escalated)."""
    if not affected_asset_criticalities:
        return request_priority, False

    max_criticality = _highest_criticality(affected_asset_criticalities)

    if max_criticality == "critical":
        escalated_priority = PRIORITY_ESCALATION_MAP.get(request_priority, request_priority)
        if escalated_priority != request_priority:
            return escalated_priority, True
    elif max_criticality == "high" and request_priority == "low":
        return "medium", True

    return request_priority, False


def _highest_criticality(criticalities: list[str]) -> str:
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return max(criticalities, key=lambda c: order.get(c, 0))
```

### 2. Infrastructure Layer

#### Model: SLA Escalation Config

| Model | File Path | Table |
|-------|-----------|-------|
| SlaEscalationConfigModel | `src/company_bc/sla_escalation_config/infrastructure/models.py` | `company_sla_escalation_configs` |

```python
class SlaEscalationConfigModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_sla_escalation_configs"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    __table_args__ = (UniqueConstraint("company_id", name="uq_sla_escalation_config_company"),)
```

#### Repository Implementation: SLA Escalation Config

| Implementation | File Path |
|---------------|-----------|
| SlaEscalationConfigRepository | `src/company_bc/sla_escalation_config/infrastructure/repository.py` |

Standard save (upsert) and find_by_company pattern.

#### Migration

| Migration | Description |
|-----------|-------------|
| `e38c1_create_sla_escalation_config_table.py` | Creates `company_sla_escalation_configs` table. Revises: `e38b1` |

#### AssetRepository Extension

Add `find_by_ids` to `src/asset_bc/asset/infrastructure/repository.py`:

```python
def find_by_ids(self, asset_ids: list[str], company_id: str) -> list[Asset]:
    if not asset_ids:
        return []
    stmt = select(AssetModel).where(
        AssetModel.company_id == company_id,
        AssetModel.id.in_(asset_ids),
    )
    models = self.session.execute(stmt).scalars().all()
    return [self._to_entity(m) for m in models]
```

### 3. Application Layer

#### Commands

| Command | Handler | File | Description |
|---------|---------|------|-------------|
| SetAffectedAssetsCommand | SetAffectedAssetsCommandHandler | `src/request_bc/request/application/commands/set_affected_assets.py` | Validates asset IDs belong to company, saves to request.data |

**SetAffectedAssetsCommand:**
```python
@dataclass
class SetAffectedAssetsCommand(Command):
    request_id: str
    company_id: str
    asset_ids: list[str]
    performed_by: str
```

**Handler logic:**
1. Fetch request by ID — raise `RequestNotFoundError` if not found
2. Validate all `asset_ids` exist in the company (use `find_by_ids`) — raise `AssetNotFoundError` for any missing
3. Set `request.data["affected_asset_ids"] = asset_ids` (merge into existing data dict)
4. Save request
5. Record `RequestEvent` with type `affected_assets_updated`

**Domain exceptions:**
- `RequestNotFoundError` — request does not exist
- `AssetNotFoundError` — one or more asset IDs not found in company

#### Commands: Save SLA Escalation Config

| Command | Handler | File | Description |
|---------|---------|------|-------------|
| SaveSlaEscalationConfigCommand | SaveSlaEscalationConfigCommandHandler | `src/company_bc/sla_escalation_config/application/commands/save_config.py` | Upserts escalation config |

```python
@dataclass
class SaveSlaEscalationConfigCommand(Command):
    company_id: str
    enabled: bool
    performed_by: str
```

#### Queries: Get SLA Escalation Config

| Query | Handler | File | Description |
|-------|---------|------|-------------|
| GetSlaEscalationConfigQuery | GetSlaEscalationConfigQueryHandler | `src/company_bc/sla_escalation_config/application/queries/get_config.py` | Returns config or default (enabled=True) |

```python
@dataclass
class SlaEscalationConfigDto:
    enabled: bool
```

Returns `SlaEscalationConfigDto(enabled=True)` when no config exists (default behavior).

#### Queries: Get Requester Assets

| Query | Handler | File | Description |
|-------|---------|------|-------------|
| GetRequesterAssetsQuery | GetRequesterAssetsQueryHandler | `src/request_bc/request/application/queries/get_requester_assets.py` | Returns assets assigned to the requester |

```python
@dataclass
class GetRequesterAssetsQuery(Query):
    request_id: str
    company_id: str

@dataclass
class RequesterAssetDto:
    id: str
    brand: str
    model: str
    serial_number: str
    type: str
    criticality: Optional[str]
    status: str
    is_affected: bool  # True if asset_id is in request.data.affected_asset_ids
```

**Handler logic:**
1. Fetch request — return empty list if not found
2. Get `created_by` (requester user ID) from request
3. Use `asset_repo.find_by_assigned_to(created_by, company_id)` to get requester's assets
4. Read `request.data.get("affected_asset_ids", [])` for current affected IDs
5. Map to DTOs with `is_affected` flag

#### Modified Query: GetRequestSlaStatus

Modify `src/sla_bc/sla/application/queries/get_request_sla.py`:

**New constructor dependencies:**
- `asset_repo: AssetRepositoryInterface` — to fetch affected asset criticalities
- `escalation_config_repo: SlaEscalationConfigRepositoryInterface` — to check if escalation is enabled

**New DTO fields on SlaStatusDto:**
```python
escalated: bool = False
effective_priority: Optional[str] = None
original_priority: Optional[str] = None
```

**Modified handle() logic:**
1. Existing: fetch request, determine priority
2. NEW: if escalation enabled for company:
   a. Read `request.data.get("affected_asset_ids", [])`
   b. Fetch affected assets via `asset_repo.find_by_ids()`
   c. Extract criticalities
   d. Call `compute_effective_priority(request.priority.value, criticalities)`
   e. If escalated, use `effective_priority` for policy lookup instead of `request.priority.value`
3. Existing: fetch policy, calculate elapsed/remaining, return DTO with new fields

### 4. HTTP Layer

#### Endpoints

| Method | Route | Handler | Request Schema | Response |
|--------|-------|---------|---------------|----------|
| PATCH | `/api/v1/requests/{id}/affected-assets` | SetAffectedAssetsCommandHandler | `SetAffectedAssetsRequest` | RequestResponse (existing) |
| GET | `/api/v1/requests/{id}/requester-assets` | GetRequesterAssetsQueryHandler | — | `list[RequesterAssetResponse]` |
| GET | `/api/v1/settings/sla-escalation` | GetSlaEscalationConfigQueryHandler | — | `SlaEscalationConfigResponse` |
| PUT | `/api/v1/settings/sla-escalation` | SaveSlaEscalationConfigCommandHandler | `SaveSlaEscalationConfigRequest` | `SlaEscalationConfigResponse` |

#### Request/Response Schemas

**In `adapters/http/api/requests/schemas.py`:**
```python
class SetAffectedAssetsRequest(BaseModel):
    asset_ids: list[str]

class RequesterAssetResponse(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    type: str
    criticality: Optional[str] = None
    status: str
    is_affected: bool
```

**In `adapters/http/api/settings/sla_escalation_schemas.py`:**
```python
class SaveSlaEscalationConfigRequest(BaseModel):
    enabled: bool

class SlaEscalationConfigResponse(BaseModel):
    enabled: bool
```

#### Modified SLA Response

**In `adapters/http/api/sla/schemas.py`:**
Add to SlaStatusResponse:
```python
escalated: bool = False
effective_priority: Optional[str] = None
original_priority: Optional[str] = None
```

#### Endpoint Details

**PATCH `/api/v1/requests/{id}/affected-assets`** — added to `adapters/http/api/requests/routers.py`:
- Auth: `require_role(UserRole.TECHNICIAN)`
- Catches: `RequestNotFoundError` → 404, `AssetNotFoundError` → 404
- Records `RequestEvent` "affected_assets_updated"
- Returns refreshed request with updated data field

**GET `/api/v1/requests/{id}/requester-assets`** — added to `adapters/http/api/requests/routers.py`:
- Auth: `require_role(UserRole.TECHNICIAN)`
- Returns list of requester's assigned assets with `is_affected` flag

**GET/PUT `/api/v1/settings/sla-escalation`** — new router `adapters/http/api/settings/sla_escalation_router.py`:
- Auth: `require_role(UserRole.ADMIN)`
- Follows `nav_config_router.py` pattern

#### Dependencies

**In `adapters/http/api/settings/sla_escalation_dependencies.py`:**
```python
def get_sla_escalation_config_repo(db: Session = Depends(get_db)):
    return SlaEscalationConfigRepository(db)
```

#### Router Registration

- Mount `sla_escalation_router` in `adapters/http/api/settings/routers.py` (or `app.py`)
- SLA query endpoint already exists — just modify its handler

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/domain/repository.py` | Add method | `find_by_ids(asset_ids, company_id) -> list[Asset]` |
| `src/asset_bc/asset/infrastructure/repository.py` | Implement | `find_by_ids` with `WHERE id IN (...)` |
| `src/sla_bc/sla/application/queries/get_request_sla.py` | Modify | Add escalation logic, new constructor deps, new DTO fields |
| `adapters/http/api/requests/routers.py` | Add endpoints | PATCH affected-assets, GET requester-assets |
| `adapters/http/api/requests/schemas.py` | Add schemas | SetAffectedAssetsRequest, RequesterAssetResponse |
| `adapters/http/api/sla/schemas.py` | Add fields | escalated, effective_priority, original_priority |
| `adapters/http/api/sla/routers.py` | Update DI | Pass asset_repo and escalation_config_repo to SLA handler |
| `app.py` | Register | sla_escalation_router |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Add section | Affected Assets UI |
| `web/app/src/types/index.ts` | Add types | RequesterAsset, SlaEscalationConfig |
| `web/app/src/locales/en.ts` | Add keys | Affected assets, escalation labels |
| `web/app/src/locales/es.ts` | Add keys | Spanish translations |

#### Breaking Changes

None. All changes are additive:
- New DTO fields have defaults (`escalated=False`, `effective_priority=None`)
- New endpoints don't affect existing ones
- SLA query handler gains optional dependencies — existing callers unaffected if defaults provided
- `find_by_ids` is a new method on the interface

## Database Schema

```sql
CREATE TABLE company_sla_escalation_configs (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_sla_escalation_config_company UNIQUE (company_id)
);

CREATE INDEX ix_sla_escalation_config_company ON company_sla_escalation_configs(company_id);
```

No migration needed for affected asset IDs — stored in existing `requests.data` JSONB column.

## Escalation Rules

```
Input: request_priority + max_criticality_of_affected_assets
Output: effective_priority + escalated flag

CRITICAL asset:
  LOW     → MEDIUM   (escalated=True)
  MEDIUM  → HIGH     (escalated=True)
  HIGH    → URGENT   (escalated=True)
  URGENT  → URGENT   (escalated=False, already max)

HIGH asset:
  LOW     → MEDIUM   (escalated=True)
  MEDIUM  → MEDIUM   (escalated=False)
  HIGH    → HIGH     (escalated=False)
  URGENT  → URGENT   (escalated=False)

MEDIUM/LOW asset:
  No escalation (escalated=False)

No affected assets:
  No escalation (escalated=False)
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F0: Criticality fields | Data | Asset.criticality must exist for escalation lookup |
| E19: SLA Management | Existing | SlaPolicy and get_request_sla query exist |
| ServiceRequest.data | Existing | JSON field for storing affected_asset_ids |
| Company config pattern | Pattern | nav_config / assignment_config pattern for new config entity |

## Testing Strategy

| Test Type | Scope | File | Priority |
|-----------|-------|------|----------|
| Unit | Escalation logic (all priority x criticality combos) | `tests/unit/sla_bc/sla/application/queries/test_sla_escalation.py` | High |
| Unit | SetAffectedAssetsCommandHandler | `tests/unit/request_bc/request/application/commands/test_set_affected_assets.py` | High |
| Unit | GetRequesterAssetsQueryHandler | `tests/unit/request_bc/request/application/queries/test_get_requester_assets.py` | Medium |
| Unit | SaveSlaEscalationConfigCommandHandler | `tests/unit/company_bc/sla_escalation_config/test_commands.py` | Medium |
| Unit | GetSlaEscalationConfigQueryHandler | `tests/unit/company_bc/sla_escalation_config/test_queries.py` | Medium |
| Integration | PATCH affected-assets endpoint | `tests/integration/test_affected_assets_endpoints.py` | High |
| Integration | SLA with escalation | `tests/integration/test_sla_escalation_endpoints.py` | High |
| Integration | SLA escalation config endpoints | `tests/integration/test_sla_escalation_config_endpoints.py` | Medium |

## Implementation Order

1. Domain: SlaEscalationConfig entity + repository interface
2. Domain: Add `find_by_ids()` to AssetRepositoryInterface
3. Infrastructure: SlaEscalationConfigModel + repository implementation
4. Infrastructure: Migration for `company_sla_escalation_configs`
5. Infrastructure: Implement `find_by_ids()` in AssetRepository
6. Application: SaveSlaEscalationConfigCommand + handler
7. Application: GetSlaEscalationConfigQuery + handler
8. Application: SetAffectedAssetsCommand + handler
9. Application: GetRequesterAssetsQuery + handler
10. Application: Modify GetRequestSlaStatusQuery with escalation logic
11. HTTP: SLA escalation config router + schemas + dependencies
12. HTTP: Request router — PATCH affected-assets + GET requester-assets
13. HTTP: Modify SLA response schema with escalation fields
14. HTTP: Update SLA router DI for new handler dependencies
15. HTTP: Register routers in app.py
16. Tests: Unit tests (escalation logic, commands, queries)
17. Tests: Integration tests (endpoints)
18. Frontend: Affected Assets section on RequestDetailPage
19. Frontend: SLA escalation indicator
20. Frontend: i18n EN/ES

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cross-BC read (asset_bc from sla_bc query) | Certain | Low | Read-only cross-BC query — acceptable per architecture (no cross-BC writes) |
| N+1 on asset criticality lookup | Medium | Medium | Batch `find_by_ids()` with single `WHERE IN` query |
| SLA handler constructor change | Low | Low | Add new deps as optional with defaults to maintain backward compat |
| Large affected_asset_ids list | Low | Low | Frontend limits selection to requester's assigned assets (typically < 20) |
