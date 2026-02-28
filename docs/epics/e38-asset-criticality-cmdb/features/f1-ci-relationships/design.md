# Solution Design: F1 — CI Relationships

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-26
**Bounded Context:** `asset_bc/asset`

## Summary

Add a `CIRelationship` entity to the existing `asset_bc/asset` subdomain that models typed, directional dependency links between assets. Full CRUD via HTTP endpoints nested under `/api/v1/assets/{id}/relationships`, with constraint enforcement (no self-reference, no duplicates, same company, no decommissioned targets). Frontend adds a "Dependencies" tab to the asset detail page.

## Architecture Decision

**Extend existing `asset_bc/asset` subdomain** rather than creating a new subdomain. Rationale:
- CIRelationship is a supporting entity within the asset domain — it links assets to assets
- It reuses the existing `AssetRepository` for asset lookups (validation) and `AssetEvent` for audit trail
- The existing router, schemas, and dependency injection patterns in `adapters/http/api/assets/` can be extended or a sub-router added
- This follows the same pattern as `AssetLocation` — a secondary entity within the asset subdomain

**Separate repository interface and implementation** for CIRelationship (not mixed into AssetRepository). Rationale:
- CIRelationship has its own table and independent CRUD lifecycle
- Keeps single responsibility — AssetRepository already has 18+ methods
- The CI relationship repository is injected separately into handlers that need it

**Sub-router for relationship endpoints** (`relationship_router.py`) mounted under the assets prefix. Rationale:
- Keeps `routers.py` from growing too large
- Relationship endpoints are nested under `/api/v1/assets/{asset_id}/relationships` — a natural sub-resource

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Asset entity | `src/asset_bc/asset/domain/entities.py` | Yes — read for validation | None |
| AssetEvent entity | `src/asset_bc/asset/domain/entities.py` | Yes — 2 new event type strings | None (event_type is free-form string) |
| AssetStatus enum | `src/asset_bc/asset/domain/enums.py` | Yes — check decommissioned | None |
| AssetRepositoryInterface | `src/asset_bc/asset/domain/repository.py` | Yes — `find_by_id()` for validation | None |
| AssetRepository | `src/asset_bc/asset/infrastructure/repository.py` | Yes — `find_by_id()`, `save_event()` | None |
| AssetModel | `src/asset_bc/asset/infrastructure/models.py` | Yes — FK target | None |
| Assets router | `adapters/http/api/assets/routers.py` | Yes — mount sub-router | Add `include_router()` for relationship_router |
| Assets schemas | `adapters/http/api/assets/schemas.py` | Yes — pattern reference | None |
| Assets dependencies | `adapters/http/api/assets/dependencies.py` | Yes — pattern, add CI repo dep | Add `get_ci_relationship_repo()` |
| ULIDMixin, TimestampMixin | `src/asset_bc/asset/infrastructure/models.py` | Yes — for new model | None |
| Framework Command/Query | `src/framework/application/` | Yes — base classes | None |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| CIRelationship | `src/asset_bc/asset/domain/entities.py` | New dataclass — id, company_id, source_asset_id, target_asset_id, relationship_type (CIRelationshipType), description (Optional[str]), created_at, created_by. Factory `create()` with ULID generation. |

```python
@dataclass
class CIRelationship:
    id: str
    company_id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: CIRelationshipType
    description: Optional[str]
    created_at: datetime
    created_by: str

    @classmethod
    def create(cls, company_id, source_asset_id, target_asset_id,
               relationship_type, created_by, description=None) -> "CIRelationship":
        return cls(
            id=generate_ulid(),
            company_id=company_id,
            source_asset_id=source_asset_id,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            description=description,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )

    def update_description(self, description: Optional[str]) -> dict:
        old = self.description
        self.description = description
        if old != description:
            return {"description": {"old": old, "new": description}}
        return {}
```

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| CIRelationshipType | `src/asset_bc/asset/domain/enums.py` | `RUNS_ON`, `DEPENDS_ON`, `CONNECTED_TO`, `PART_OF`, `BACKS_UP` |

```python
class CIRelationshipType(str, Enum):
    RUNS_ON = "runs_on"
    DEPENDS_ON = "depends_on"
    CONNECTED_TO = "connected_to"
    PART_OF = "part_of"
    BACKS_UP = "backs_up"
```

#### Repository Interface

| Interface | File Path | Description |
|-----------|-----------|-------------|
| CIRelationshipRepositoryInterface | `src/asset_bc/asset/domain/repository.py` | Abstract class with save, find_by_id, find_by_asset, find_duplicate, delete |

Methods:
- `save(relationship: CIRelationship) -> CIRelationship` — upsert
- `find_by_id(relationship_id: str, company_id: str) -> Optional[CIRelationship]`
- `find_by_asset(asset_id: str, company_id: str) -> list[CIRelationship]` — all relationships where asset is source OR target
- `find_duplicate(source_asset_id: str, target_asset_id: str, relationship_type: str, company_id: str) -> Optional[CIRelationship]` — for uniqueness check
- `delete(relationship_id: str) -> None` — hard delete

#### Domain Exceptions

New exceptions in `src/asset_bc/asset/domain/exceptions.py` (new file, or add to entities.py following existing pattern):

| Exception | When Raised |
|-----------|-------------|
| `CIRelationshipNotFoundError` | Relationship ID not found |
| `SelfReferenceError` | source_asset_id == target_asset_id |
| `DuplicateRelationshipError` | Same source+target+type already exists |
| `CrossCompanyRelationshipError` | Source and target belong to different companies |
| `DecommissionedTargetError` | Target asset has status=decommissioned |

These follow the existing pattern of `AssetNotFoundError`, `AssetDecommissionedError`, etc. defined alongside command handlers.

### 2. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| CreateCIRelationshipCommand | CreateCIRelationshipCommandHandler | `src/asset_bc/asset/application/commands/create_ci_relationship.py` | Validate constraints, create entity, save, record AssetEvent |
| UpdateCIRelationshipCommand | UpdateCIRelationshipCommandHandler | `src/asset_bc/asset/application/commands/update_ci_relationship.py` | Find relationship, update description, save |
| DeleteCIRelationshipCommand | DeleteCIRelationshipCommandHandler | `src/asset_bc/asset/application/commands/delete_ci_relationship.py` | Find relationship, delete, record AssetEvent |

**CreateCIRelationshipCommand fields:**
- `company_id: str`
- `source_asset_id: str`
- `target_asset_id: str`
- `relationship_type: str`
- `description: Optional[str]`
- `performed_by: str`

**Handler logic:**
1. Validate source != target (SelfReferenceError)
2. Load source asset via `asset_repo.find_by_id(source_asset_id, company_id)` — raise AssetNotFoundError if None
3. Load target asset via `asset_repo.find_by_id(target_asset_id, company_id)` — raise AssetNotFoundError if None (also validates same company)
4. Check target not decommissioned (DecommissionedTargetError)
5. Check no duplicate via `ci_repo.find_duplicate(...)` (DuplicateRelationshipError)
6. Create CIRelationship entity
7. Save via `ci_repo.save(relationship)`
8. Record AssetEvent on source: `ci_relationship_created` with data `{relationship_id, target_asset_id, relationship_type}`
9. Return None (CQRS)

**UpdateCIRelationshipCommand fields:**
- `relationship_id: str`
- `company_id: str`
- `description: Optional[str]`
- `performed_by: str`

**Handler logic:**
1. Load relationship — raise CIRelationshipNotFoundError if None
2. Call `relationship.update_description(command.description)`
3. Save if changes occurred

**DeleteCIRelationshipCommand fields:**
- `relationship_id: str`
- `company_id: str`
- `source_asset_id: str`
- `performed_by: str`

**Handler logic:**
1. Load relationship — raise CIRelationshipNotFoundError if None
2. Delete via `ci_repo.delete(relationship.id)`
3. Record AssetEvent on source: `ci_relationship_deleted` with data `{relationship_id, target_asset_id, relationship_type}`

#### Queries

| Query | Handler | File Path | Return Type | Description |
|-------|---------|-----------|-------------|-------------|
| ListCIRelationshipsQuery | ListCIRelationshipsQueryHandler | `src/asset_bc/asset/application/queries/list_ci_relationships.py` | `list[CIRelationship]` | Return all relationships for an asset (both directions) |

**Query fields:**
- `asset_id: str`
- `company_id: str`

**Handler logic:**
1. Return `ci_repo.find_by_asset(asset_id, company_id)`

### 3. Infrastructure Layer

#### Model

| Model | File Path | Table |
|-------|-----------|-------|
| CIRelationshipModel | `src/asset_bc/asset/infrastructure/models.py` | `ci_relationships` |

```python
class CIRelationshipModel(Base, ULIDMixin, TimestampMixin):
    __tablename__ = "ci_relationships"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    source_asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    target_asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str] = mapped_column(String(26))

    __table_args__ = (
        UniqueConstraint("source_asset_id", "target_asset_id", "relationship_type",
                         name="uq_ci_rel_source_target_type"),
    )
```

#### Repository Implementation

| Interface | Implementation | File Path |
|-----------|----------------|-----------|
| CIRelationshipRepositoryInterface | CIRelationshipRepository | `src/asset_bc/asset/infrastructure/ci_relationship_repository.py` |

Separate file to keep AssetRepository focused. Methods:
- `save()` — upsert pattern (check existing, update or create)
- `find_by_id()` — single lookup with company_id filter
- `find_by_asset()` — WHERE source_asset_id = X OR target_asset_id = X, filtered by company_id
- `find_duplicate()` — WHERE source + target + type match
- `delete()` — session.delete() for hard delete

Static `_to_entity()` and `_to_model()` conversion methods.

#### Migration

| Migration | Description |
|-----------|-------------|
| `create_ci_relationships_table` | Create `ci_relationships` table with FKs, indexes, unique constraint |

```sql
CREATE TABLE ci_relationships (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    source_asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    target_asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    relationship_type VARCHAR(20) NOT NULL,
    description VARCHAR(500),
    created_by VARCHAR(26) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (source_asset_id, target_asset_id, relationship_type)
);

CREATE INDEX ix_ci_relationships_company_id ON ci_relationships(company_id);
CREATE INDEX ix_ci_relationships_source ON ci_relationships(source_asset_id);
CREATE INDEX ix_ci_relationships_target ON ci_relationships(target_asset_id);
```

### 4. HTTP Layer

#### Endpoints

| Method | Route | Description | Request Schema | Response Schema |
|--------|-------|-------------|---------------|-----------------|
| POST | `/api/v1/assets/{asset_id}/relationships` | Create relationship | `CreateCIRelationshipRequest` | `CIRelationshipResponse` (201) |
| GET | `/api/v1/assets/{asset_id}/relationships` | List relationships | — | `list[CIRelationshipResponse]` |
| PATCH | `/api/v1/assets/{asset_id}/relationships/{relationship_id}` | Update description | `UpdateCIRelationshipRequest` | `CIRelationshipResponse` |
| DELETE | `/api/v1/assets/{asset_id}/relationships/{relationship_id}` | Delete relationship | — | 204 No Content |

#### Router File

New file: `adapters/http/api/assets/relationship_router.py`

Mounted into the main assets router via `router.include_router(relationship_router, prefix="/{asset_id}/relationships", tags=["asset-relationships"])`.

#### Schemas

Added to `adapters/http/api/assets/schemas.py`:

```python
class CreateCIRelationshipRequest(BaseModel):
    target_asset_id: str = Field(..., min_length=1, max_length=26)
    relationship_type: str = Field(...)  # validated against CIRelationshipType values
    description: Optional[str] = Field(None, max_length=500)

class UpdateCIRelationshipRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=500)

class CIRelationshipResponse(BaseModel):
    id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    description: Optional[str]
    created_at: str
    created_by: str
    # Enriched fields for display:
    target_asset_name: Optional[str] = None  # "{brand} {model}"
    target_asset_serial: Optional[str] = None
    target_asset_type: Optional[str] = None
    target_asset_criticality: Optional[str] = None
    target_asset_status: Optional[str] = None
    source_asset_name: Optional[str] = None
    source_asset_serial: Optional[str] = None
    source_asset_type: Optional[str] = None
    source_asset_criticality: Optional[str] = None
    source_asset_status: Optional[str] = None
```

#### Dependencies

Add to `adapters/http/api/assets/dependencies.py`:

```python
def get_ci_relationship_repo(db: Session = Depends(get_db)) -> CIRelationshipRepository:
    return CIRelationshipRepository(db)
```

#### Error Mapping

| Domain Exception | HTTP Status | Detail |
|-----------------|-------------|--------|
| AssetNotFoundError | 404 | "Asset not found" |
| CIRelationshipNotFoundError | 404 | "Relationship not found" |
| SelfReferenceError | 422 | "Cannot create relationship to self" |
| DuplicateRelationshipError | 409 | "Relationship already exists" |
| CrossCompanyRelationshipError | 422 | "Assets must belong to same company" |
| DecommissionedTargetError | 422 | "Cannot create relationship to decommissioned asset" |

### 5. Frontend

#### AssetDetailPage — Dependencies Tab

File: `web/app/src/pages/technician/AssetDetailPage.tsx`

Add a "Dependencies" tab (alongside existing tabs). Content:
- Two sections: **"Depends On"** (where this asset is source) and **"Depended On By"** (where this asset is target)
- Each row shows: relationship type icon/label, linked asset name (brand + model), serial number, criticality badge, description, actions (edit/delete)
- "Add Relationship" button opens modal
- Delete with confirmation dialog

#### Add Relationship Modal

New component or inline in AssetDetailPage:
- Type dropdown: 5 relationship types with display labels
- Asset search: searchable dropdown/combobox querying `/api/v1/assets?search=...` (existing endpoint)
- Description: optional text field (max 500 chars)
- Submit: POST to `/api/v1/assets/{asset_id}/relationships`

#### i18n

Add to `web/app/src/locales/en.ts` and `es.ts`:
- Relationship type labels: "Runs on", "Depends on", "Connected to", "Part of", "Backs up"
- Section headers: "Dependencies", "Depends On", "Depended On By"
- Actions: "Add Relationship", "Edit Description", "Delete Relationship"
- Confirmation: "Are you sure you want to delete this relationship?"
- Errors: constraint violation messages

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/domain/entities.py` | Add | CIRelationship dataclass |
| `src/asset_bc/asset/domain/enums.py` | Add | CIRelationshipType enum |
| `src/asset_bc/asset/domain/repository.py` | Add | CIRelationshipRepositoryInterface abstract class |
| `src/asset_bc/asset/infrastructure/models.py` | Add | CIRelationshipModel |
| `adapters/http/api/assets/routers.py` | Modify | Mount relationship_router |
| `adapters/http/api/assets/schemas.py` | Add | Relationship request/response schemas |
| `adapters/http/api/assets/dependencies.py` | Add | `get_ci_relationship_repo()` |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Modify | Add Dependencies tab |
| `web/app/src/locales/en.ts` | Add | i18n keys for relationships |
| `web/app/src/locales/es.ts` | Add | i18n keys for relationships |
| `web/app/src/types/index.ts` | Add | CIRelationship TypeScript type |

#### New Files

| File | Description |
|------|-------------|
| `src/asset_bc/asset/infrastructure/ci_relationship_repository.py` | Repository implementation |
| `src/asset_bc/asset/application/commands/create_ci_relationship.py` | Command + handler |
| `src/asset_bc/asset/application/commands/update_ci_relationship.py` | Command + handler |
| `src/asset_bc/asset/application/commands/delete_ci_relationship.py` | Command + handler |
| `src/asset_bc/asset/application/queries/list_ci_relationships.py` | Query + handler |
| `adapters/http/api/assets/relationship_router.py` | HTTP sub-router |
| `alembic/versions/xxx_create_ci_relationships_table.py` | Migration |
| `tests/unit/asset_bc/asset/domain/test_ci_relationship.py` | Domain entity tests |
| `tests/unit/asset_bc/asset/application/commands/test_create_ci_relationship.py` | Command tests |
| `tests/unit/asset_bc/asset/application/commands/test_update_ci_relationship.py` | Command tests |
| `tests/unit/asset_bc/asset/application/commands/test_delete_ci_relationship.py` | Command tests |
| `tests/unit/asset_bc/asset/application/queries/test_list_ci_relationships.py` | Query tests |
| `tests/integration/test_ci_relationship_endpoints.py` | Integration tests |

#### Breaking Changes

None. This is purely additive — new table, new entity, new endpoints. No existing data or APIs are modified.

## Database Schema

```sql
CREATE TABLE ci_relationships (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    source_asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    target_asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    relationship_type VARCHAR(20) NOT NULL,
    description VARCHAR(500),
    created_by VARCHAR(26) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ci_rel_source_target_type UNIQUE (source_asset_id, target_asset_id, relationship_type)
);

CREATE INDEX ix_ci_relationships_company_id ON ci_relationships(company_id);
CREATE INDEX ix_ci_relationships_source ON ci_relationships(source_asset_id);
CREATE INDEX ix_ci_relationships_target ON ci_relationships(target_asset_id);
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F0 (Criticality & BIA) | Data | Criticality badges displayed on related assets |
| Asset entity | Read | Validate asset exists, check status, get display data |
| AssetEvent | Write | Audit trail for create/delete |
| AssetRepository | Read | `find_by_id()` for validation, `save_event()` for audit |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | CIRelationship entity create + update_description | High | `test_ci_relationship.py` |
| Unit | CreateCIRelationshipCommandHandler — all 5 constraints | High | `test_create_ci_relationship.py` |
| Unit | UpdateCIRelationshipCommandHandler — happy + not found | High | `test_update_ci_relationship.py` |
| Unit | DeleteCIRelationshipCommandHandler — happy + not found + event | High | `test_delete_ci_relationship.py` |
| Unit | ListCIRelationshipsQueryHandler — returns both directions | Medium | `test_list_ci_relationships.py` |
| Integration | POST /relationships — all constraints, happy path | High | `test_ci_relationship_endpoints.py` |
| Integration | GET /relationships — returns enriched data | High | `test_ci_relationship_endpoints.py` |
| Integration | PATCH /relationships/{id} — update description | Medium | `test_ci_relationship_endpoints.py` |
| Integration | DELETE /relationships/{id} — hard delete + event | High | `test_ci_relationship_endpoints.py` |

## Implementation Order

1. Domain: CIRelationshipType enum
2. Domain: CIRelationship entity
3. Domain: CIRelationshipRepositoryInterface
4. Infrastructure: CIRelationshipModel
5. Infrastructure: Migration
6. Infrastructure: CIRelationshipRepository
7. Application: CreateCIRelationshipCommand + handler
8. Application: UpdateCIRelationshipCommand + handler
9. Application: DeleteCIRelationshipCommand + handler
10. Application: ListCIRelationshipsQuery + handler
11. HTTP: Schemas (request/response)
12. HTTP: Dependencies
13. HTTP: relationship_router.py
14. HTTP: Mount in routers.py
15. Tests: Unit tests (domain + commands + queries)
16. Tests: Integration tests
17. Frontend: TypeScript types
18. Frontend: Dependencies tab + Add modal
19. Frontend: i18n EN/ES
20. Verification: TypeScript check + test suites

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large number of relationships per asset slows GET | Low | Medium | Index on source/target columns; flat listing (no recursion) |
| Orphan relationships when asset deleted | Low | Low | Assets use soft-delete (decommissioned); relationships preserved per AC |
| Concurrent duplicate creation | Low | Low | Unique DB constraint catches race conditions |
