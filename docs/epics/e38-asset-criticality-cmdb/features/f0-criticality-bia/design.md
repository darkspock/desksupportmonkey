# Solution Design: F0 — Criticality & BIA

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-26
**Bounded Context:** `asset_bc/asset` (extending existing)

## Summary

Extend the existing Asset entity with 7 new nullable fields for criticality classification (CRITICAL/HIGH/MEDIUM/LOW) and Business Impact Analysis (impact_score, RTO, RPO, justification, review tracking). Two new PATCH commands handle setting criticality and updating BIA data, each recording an AssetEvent for audit trail. The existing GetAsset/ListAssets queries and HTTP responses are updated to include the new fields. Frontend adds a criticality badge, BIA collapsible panel on detail page, and criticality column/filter on list page.

## Architecture Decision

**Approach:** Extend the existing `asset_bc/asset` subdomain rather than creating a new subdomain. The criticality and BIA fields are intrinsic properties of an Asset — they describe the asset itself, not a separate concept.

**Alternatives considered:**
- **Separate `cmdb_bc` bounded context**: Rejected. Criticality is an attribute of the asset, not a separate aggregate. Creating a new BC would require cross-BC reads for every asset display.
- **Separate entity (AssetClassification)**: Rejected. This would add unnecessary join complexity. The fields are simple, nullable columns on the existing asset — consistent with how `custom_fields_data` was added.

**Key decisions:**
- All 7 new columns are nullable → backward-compatible, no data migration needed
- Criticality defaults to `null` (unclassified), distinct from `LOW`
- BIA fields auto-set `bia_reviewed_at` and `bia_reviewed_by` on save
- Cannot set criticality on decommissioned assets (business rule)
- Two separate commands (SetCriticality, UpdateBia) rather than one combined command, following single-responsibility

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Asset entity | `src/asset_bc/asset/domain/entities.py` | Yes | Add 7 fields + `set_criticality()` + `update_bia()` methods |
| AssetStatus enum | `src/asset_bc/asset/domain/enums.py` | Yes | Add `AssetCriticality` enum in same file |
| Asset repository interface | `src/asset_bc/asset/domain/repository.py` | Yes | No changes needed (existing `save()` handles all fields) |
| AssetModel | `src/asset_bc/asset/infrastructure/models.py` | Yes | Add 7 mapped columns |
| AssetRepository (SQLAlchemy) | `src/asset_bc/asset/infrastructure/repository.py` | Yes | Update `save()` to persist new fields |
| AssetEvent entity | `src/asset_bc/asset/domain/entities.py` | Yes | No changes (event_type is a string, 2 new types: `criticality_set`, `bia_updated`) |
| UpdateAssetCommand pattern | `src/asset_bc/asset/application/commands/update_asset.py` | Reference pattern | New commands follow same structure |
| GetAssetQuery | `src/asset_bc/asset/application/queries/get_asset.py` | Yes | No changes needed (returns full Asset entity, new fields automatically included) |
| ListAssetsQuery | `src/asset_bc/asset/application/queries/list_assets.py` | Yes | Add `criticality` filter parameter |
| Asset router | `adapters/http/api/assets/routers.py` | Yes | Add 2 PATCH endpoints, update `_to_response()`, add criticality filter to list |
| AssetResponse schema | `adapters/http/api/assets/schemas.py` | Yes | Add 7 new fields |
| Asset TypeScript type | `web/app/src/types/index.ts` | Yes | Add 7 new fields |
| AssetDetailPage | `web/app/src/pages/technician/AssetDetailPage.tsx` | Yes | Add criticality badge + BIA section |
| AssetListPage | `web/app/src/pages/technician/AssetListPage.tsx` | Yes | Add criticality column + filter |
| Dependencies DI | `adapters/http/api/assets/dependencies.py` | Yes | No changes needed |

## Implementation Plan

### 1. Domain Layer

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| AssetCriticality | `src/asset_bc/asset/domain/enums.py` | CRITICAL, HIGH, MEDIUM, LOW |

```python
class AssetCriticality(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| Asset (extended) | `src/asset_bc/asset/domain/entities.py` | Add 7 nullable fields + 2 domain methods |

New fields on Asset dataclass:
```python
criticality: Optional[AssetCriticality] = None
impact_score: Optional[int] = None          # 1-10
rto_minutes: Optional[int] = None           # > 0
rpo_minutes: Optional[int] = None           # >= 0
bia_justification: Optional[str] = None
bia_reviewed_at: Optional[datetime] = None
bia_reviewed_by: Optional[str] = None
```

New domain methods:
```python
def set_criticality(self, criticality: Optional[AssetCriticality]) -> dict:
    """Set or clear criticality. Returns change dict for event recording."""
    if self.status == AssetStatus.DECOMMISSIONED:
        raise AssetDecommissionedError("Cannot set criticality on decommissioned asset")
    old = self.criticality
    self.criticality = criticality
    if old != criticality:
        return {"old": old.value if old else None, "new": criticality.value if criticality else None}
    return {}

def update_bia(self, impact_score: Optional[int], rto_minutes: Optional[int],
               rpo_minutes: Optional[int], justification: Optional[str],
               reviewed_by: str) -> dict:
    """Update BIA fields. Auto-sets reviewed_at/reviewed_by. Returns change dict."""
    if self.status == AssetStatus.DECOMMISSIONED:
        raise AssetDecommissionedError("Cannot update BIA on decommissioned asset")
    if impact_score is not None and (impact_score < 1 or impact_score > 10):
        raise ValueError("impact_score must be between 1 and 10")
    if rto_minutes is not None and rto_minutes <= 0:
        raise ValueError("rto_minutes must be greater than 0")
    if rpo_minutes is not None and rpo_minutes < 0:
        raise ValueError("rpo_minutes must be 0 or greater")
    changes = {}
    # ... track changes for each field ...
    self.bia_reviewed_at = datetime.utcnow()
    self.bia_reviewed_by = reviewed_by
    return changes
```

New exception:
```python
class AssetDecommissionedError(Exception):
    pass
```

#### Domain Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `criticality_set` | SetCriticalityCommand | `{old: str|null, new: str|null}` |
| `bia_updated` | UpdateBiaCommand | `{impact_score, rto_minutes, rpo_minutes, justification}` |

These are stored as AssetEvent records using the existing `AssetEvent.create()` factory — event_type is a string, no enum extension needed.

### 2. Application Layer

#### Commands

| Command | Handler | File | Description |
|---------|---------|------|-------------|
| SetCriticalityCommand | SetCriticalityCommandHandler | `src/asset_bc/asset/application/commands/set_criticality.py` | Sets or clears criticality on asset |
| UpdateBiaCommand | UpdateBiaCommandHandler | `src/asset_bc/asset/application/commands/update_bia.py` | Updates BIA fields on asset |

**SetCriticalityCommand:**
```python
@dataclass
class SetCriticalityCommand(Command):
    asset_id: str
    company_id: str
    criticality: Optional[str]  # None to clear
    performed_by: str
```

Handler pattern (same as UpdateAssetCommandHandler):
1. `find_by_id()` → raise AssetNotFoundError if None
2. Call `asset.set_criticality(AssetCriticality(criticality) if criticality else None)`
3. `save(asset)`
4. If changes → `save_event(AssetEvent.create(...))`

**UpdateBiaCommand:**
```python
@dataclass
class UpdateBiaCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    impact_score: Optional[int] = None
    rto_minutes: Optional[int] = None
    rpo_minutes: Optional[int] = None
    bia_justification: Optional[str] = None
```

Handler pattern:
1. `find_by_id()` → raise AssetNotFoundError if None
2. Call `asset.update_bia(...)` with `reviewed_by=command.performed_by`
3. `save(asset)`
4. If changes → `save_event(AssetEvent.create(...))`

#### Queries

| Query | Handler | File | Description |
|-------|---------|------|-------------|
| ListAssetsQuery (modified) | ListAssetsQueryHandler | `src/asset_bc/asset/application/queries/list_assets.py` | Add `criticality` filter param |

No new queries needed — GetAssetQuery already returns the full Asset entity which will include the new fields.

### 3. Infrastructure Layer

#### Models

| Model | File | Description |
|-------|------|-------------|
| AssetModel (extended) | `src/asset_bc/asset/infrastructure/models.py` | Add 7 nullable columns |

New columns:
```python
criticality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
impact_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
rto_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
rpo_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
bia_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
bia_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
bia_reviewed_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)
```

#### Repository

| Interface | Implementation | Table |
|-----------|----------------|-------|
| AssetRepositoryInterface | AssetRepository | `assets` (extended) |

Modifications to `AssetRepository.save()`:
- Add new fields to both update-existing and insert-new branches
- Add criticality field to entity hydration in `_to_entity()` (or equivalent)

Modifications to `AssetRepository.find_all()`:
- Add `criticality` filter parameter (WHERE clause on `criticality` column)

#### Migrations

| Migration | Description |
|-----------|-------------|
| `add_asset_criticality_bia_columns` | Add 7 nullable columns to `assets` table |

```sql
ALTER TABLE assets ADD COLUMN criticality VARCHAR(20);
ALTER TABLE assets ADD COLUMN impact_score INTEGER;
ALTER TABLE assets ADD COLUMN rto_minutes INTEGER;
ALTER TABLE assets ADD COLUMN rpo_minutes INTEGER;
ALTER TABLE assets ADD COLUMN bia_justification TEXT;
ALTER TABLE assets ADD COLUMN bia_reviewed_at TIMESTAMP;
ALTER TABLE assets ADD COLUMN bia_reviewed_by VARCHAR(26) REFERENCES users(id);
CREATE INDEX ix_assets_criticality ON assets (criticality) WHERE criticality IS NOT NULL;
```

### 4. HTTP Layer

#### Endpoints

| Method | Route | Description | Request Schema | Auth |
|--------|-------|-------------|---------------|------|
| PATCH | `/api/v1/assets/{id}/criticality` | Set/clear criticality | `SetCriticalityRequest` | technician+ |
| PATCH | `/api/v1/assets/{id}/bia` | Update BIA fields | `UpdateBiaRequest` | technician+ |

**Request Schemas:**

```python
class SetCriticalityRequest(BaseModel):
    criticality: Optional[str] = None  # null to clear

class UpdateBiaRequest(BaseModel):
    impact_score: Optional[int] = Field(None, ge=1, le=10)
    rto_minutes: Optional[int] = Field(None, gt=0)
    rpo_minutes: Optional[int] = Field(None, ge=0)
    bia_justification: Optional[str] = None
```

**Response Schema Updates:**

`AssetResponse` — add 7 new optional fields:
```python
criticality: Optional[str] = None
impact_score: Optional[int] = None
rto_minutes: Optional[int] = None
rpo_minutes: Optional[int] = None
bia_justification: Optional[str] = None
bia_reviewed_at: Optional[datetime] = None
bia_reviewed_by: Optional[str] = None
```

**Error mapping:**
| Exception | HTTP Status |
|-----------|-------------|
| AssetNotFoundError | 404 |
| AssetDecommissionedError | 422 |
| ValueError (validation) | 422 |

### 5. Frontend

#### TypeScript Types

`web/app/src/types/index.ts` — Asset interface:
```typescript
// Add to existing Asset interface:
criticality: string | null;
impact_score: number | null;
rto_minutes: number | null;
rpo_minutes: number | null;
bia_justification: string | null;
bia_reviewed_at: string | null;
bia_reviewed_by: string | null;
```

Add `AssetCriticality` type:
```typescript
export type AssetCriticality = 'critical' | 'high' | 'medium' | 'low';
```

#### Asset Detail Page

`web/app/src/pages/technician/AssetDetailPage.tsx`:
- **Criticality badge** next to asset name/status — color-coded (red=critical, orange=high, yellow=medium, green=low, gray=unclassified)
- **Set Criticality dropdown** (PATCH to `/api/v1/assets/{id}/criticality`)
- **BIA section** (collapsible panel):
  - Impact Score (1-10 input)
  - RTO (minutes input, display as human-readable e.g. "4 hours")
  - RPO (minutes input, display as human-readable)
  - Justification (textarea)
  - Last Reviewed (read-only, auto-set on save)
  - Save BIA button (PATCH to `/api/v1/assets/{id}/bia`)

#### Asset List Page

`web/app/src/pages/technician/AssetListPage.tsx`:
- **Criticality column** in table — shows color-coded badge
- **Criticality filter dropdown** in filters bar — options: All, Critical, High, Medium, Low, Unclassified

#### i18n

`web/app/src/locales/en.ts` / `es.ts` — new keys:
- `asset.criticality`, `asset.criticality_critical`, `asset.criticality_high`, `asset.criticality_medium`, `asset.criticality_low`, `asset.criticality_unclassified`
- `asset.bia_section`, `asset.impact_score`, `asset.rto`, `asset.rpo`, `asset.bia_justification`, `asset.bia_last_reviewed`, `asset.save_bia`
- `asset.set_criticality`

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/domain/enums.py` | Add enum | `AssetCriticality` |
| `src/asset_bc/asset/domain/entities.py` | Extend | 7 fields + 2 methods + 1 exception |
| `src/asset_bc/asset/infrastructure/models.py` | Extend | 7 columns on AssetModel |
| `src/asset_bc/asset/infrastructure/repository.py` | Extend | `save()` + `find_all()` + entity hydration |
| `src/asset_bc/asset/application/queries/list_assets.py` | Extend | Add `criticality` filter |
| `adapters/http/api/assets/routers.py` | Extend | 2 new endpoints + `_to_response()` + list filter |
| `adapters/http/api/assets/schemas.py` | Extend | 2 new request schemas + `AssetResponse` fields |
| `web/app/src/types/index.ts` | Extend | 7 fields + `AssetCriticality` type |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Extend | Criticality badge + BIA section |
| `web/app/src/pages/technician/AssetListPage.tsx` | Extend | Criticality column + filter |
| `web/app/src/locales/en.ts` | Extend | ~15 new keys |
| `web/app/src/locales/es.ts` | Extend | ~15 new keys |

#### New Files

| File | Description |
|------|-------------|
| `src/asset_bc/asset/application/commands/set_criticality.py` | SetCriticalityCommand + handler |
| `src/asset_bc/asset/application/commands/update_bia.py` | UpdateBiaCommand + handler |
| `alembic/versions/xxx_add_asset_criticality_bia_columns.py` | Migration |

#### Breaking Changes

None. All new columns are nullable, all new endpoints are additive, all response fields are optional.

## Database Schema

```sql
-- Migration: add_asset_criticality_bia_columns
ALTER TABLE assets ADD COLUMN criticality VARCHAR(20);
ALTER TABLE assets ADD COLUMN impact_score INTEGER;
ALTER TABLE assets ADD COLUMN rto_minutes INTEGER;
ALTER TABLE assets ADD COLUMN rpo_minutes INTEGER;
ALTER TABLE assets ADD COLUMN bia_justification TEXT;
ALTER TABLE assets ADD COLUMN bia_reviewed_at TIMESTAMP;
ALTER TABLE assets ADD COLUMN bia_reviewed_by VARCHAR(26) REFERENCES users(id);

-- Partial index for criticality filter (only non-null values)
CREATE INDEX ix_assets_criticality ON assets (criticality) WHERE criticality IS NOT NULL;
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Asset entity | Internal (same BC) | Extended with new fields |
| AssetEvent entity | Internal (same BC) | Used for audit trail (2 new event types) |
| Users table | FK reference | `bia_reviewed_by` references `users.id` |

## Testing Strategy

| Test Type | Scope | File | Priority |
|-----------|-------|------|----------|
| Unit | `set_criticality()` domain method | `tests/unit/asset_bc/asset/domain/test_entities.py` | High |
| Unit | `update_bia()` domain method + validation | `tests/unit/asset_bc/asset/domain/test_entities.py` | High |
| Unit | SetCriticalityCommandHandler | `tests/unit/asset_bc/asset/application/commands/test_set_criticality.py` | High |
| Unit | UpdateBiaCommandHandler | `tests/unit/asset_bc/asset/application/commands/test_update_bia.py` | High |
| Integration | PATCH `/assets/{id}/criticality` | `tests/integration/test_asset_endpoints.py` | High |
| Integration | PATCH `/assets/{id}/bia` | `tests/integration/test_asset_endpoints.py` | High |
| Integration | GET `/assets` with criticality filter | `tests/integration/test_asset_endpoints.py` | Medium |
| Integration | GET `/assets/{id}` includes new fields | `tests/integration/test_asset_endpoints.py` | Medium |

## Implementation Order

1. [ ] Domain: `AssetCriticality` enum in `enums.py`
2. [ ] Domain: `AssetDecommissionedError` exception + 7 fields + `set_criticality()` + `update_bia()` on Asset entity
3. [ ] Infrastructure: Alembic migration for 7 new columns
4. [ ] Infrastructure: `AssetModel` — add 7 columns
5. [ ] Infrastructure: `AssetRepository.save()` — persist new fields + entity hydration
6. [ ] Application: `SetCriticalityCommand` + handler
7. [ ] Application: `UpdateBiaCommand` + handler
8. [ ] Application: `ListAssetsQuery` — add criticality filter
9. [ ] HTTP: Request schemas (`SetCriticalityRequest`, `UpdateBiaRequest`)
10. [ ] HTTP: `AssetResponse` — add 7 fields
11. [ ] HTTP: 2 new PATCH endpoints in router + update `_to_response()`
12. [ ] Frontend: TypeScript Asset type update
13. [ ] Frontend: AssetDetailPage — criticality badge + BIA section
14. [ ] Frontend: AssetListPage — criticality column + filter
15. [ ] Frontend: i18n EN/ES
16. [ ] Tests: Unit tests (entity methods + command handlers)
17. [ ] Tests: Integration tests (endpoints)

## Open Technical Questions

None — all design decisions resolved during requirement validation.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration on large assets table | Low | Low | All columns nullable, no default values, partial index |
| Existing tests break due to new required fields | Low | Low | All fields are Optional with defaults — no test breakage |
