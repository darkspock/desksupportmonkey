# Solution Design: Asset Linking

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-27
**Bounded Context:** `change_bc` (existing, extends F0)

## Summary

Add a ChangeAsset join entity to associate affected assets with change requests. Follows the IncidentAsset lightweight pattern (methods on main repository interface, simple dataclass) combined with VulnerabilityAsset's bulk-link command pattern. Cross-BC asset validation via `asset_bc` repository. Extends the existing detail query and frontend page with an affected assets section.

## Architecture Decision

- **Pattern:** Lightweight join — ChangeAsset dataclass in domain, methods added to existing `ChangeRequestRepositoryInterface` (same as IncidentAsset in `incident_bc`). No separate repository class needed for a simple join table.
- **Bulk link:** POST endpoint accepts `asset_ids: list[str]` (same as VulnerabilityAsset). Skips duplicates, validates all assets exist.
- **Cross-BC reference:** `asset_id` is a `String(26)`, no FK to assets table. Asset details (name, tag, brand, model) resolved at query time via `AssetRepository`.
- **Audit trail:** Two new `ChangeEventType` values (`ASSET_LINKED`, `ASSET_UNLINKED`). One event per link/unlink action with asset metadata.
- **Status guards:** Linking allowed in any non-terminal state. Unlinking restricted to DRAFT, PENDING_APPROVAL, SCHEDULED.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ChangeRequest entity | `src/change_bc/change_request/domain/entities.py` | Extend | Add ChangeAsset dataclass |
| ChangeEventType enum | `src/change_bc/change_request/domain/enums.py` | Extend | Add ASSET_LINKED, ASSET_UNLINKED |
| ChangeRequestRepositoryInterface | `src/change_bc/change_request/domain/repository.py` | Extend | Add 3 asset methods |
| ChangeRequestModel | `src/change_bc/change_request/infrastructure/models.py` | Extend | Add ChangeAssetModel |
| ChangeRequestRepository | `src/change_bc/change_request/infrastructure/repository.py` | Extend | Implement 3 asset methods |
| GetChangeRequestDetailQuery | `src/change_bc/change_request/application/queries/get_change_request_detail.py` | Extend | Add affected_assets to DTO |
| Changes router | `adapters/http/api/changes/routers.py` | Extend | Add 2 endpoints |
| Changes schemas | `adapters/http/api/changes/schemas.py` | Extend | Add request/response schemas |
| Changes dependencies | `adapters/http/api/changes/dependencies.py` | Extend | Add asset_repo dependency |
| IncidentAsset pattern | `src/incident_bc/incident/infrastructure/models.py` | Pattern reference | None — replicate for ChangeAsset |
| VulnerabilityAsset link command | `src/vulnerability_bc/vulnerability/application/commands/link_assets.py` | Pattern reference | None — replicate bulk link pattern |
| AssetRepository | `src/asset_bc/asset/infrastructure/repository.py` | Direct reuse | Cross-BC asset lookup |

## Implementation Plan

### 1. Domain Layer

#### 1.1 Entity — `src/change_bc/change_request/domain/entities.py` (add)

```python
@dataclass
class ChangeAsset:
    id: str
    change_request_id: str
    asset_id: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, change_request_id: str, asset_id: str) -> "ChangeAsset":
        return cls(
            id=str(ulid.new()),
            change_request_id=change_request_id,
            asset_id=asset_id,
        )
```

Simple dataclass — no status tracking, no business logic beyond factory. This is a pure association entity.

#### 1.2 Enums — `src/change_bc/change_request/domain/enums.py` (modify)

Add to `ChangeEventType`:
```python
ASSET_LINKED = "asset_linked"
ASSET_UNLINKED = "asset_unlinked"
```

#### 1.3 Exceptions — `src/change_bc/change_request/domain/exceptions.py` (modify)

Add:
```python
class AssetAlreadyLinkedError(Exception): ...
class AssetNotLinkedError(Exception): ...
class ChangeNotUnlinkableError(Exception):
    """Unlinking only allowed in DRAFT, PENDING_APPROVAL, SCHEDULED."""
    ...
```

#### 1.4 Repository Interface — `src/change_bc/change_request/domain/repository.py` (modify)

Add to `ChangeRequestRepositoryInterface`:
```python
# ChangeAsset
@abstractmethod
def save_change_asset(self, change_asset: ChangeAsset) -> None: ...

@abstractmethod
def delete_change_asset(self, change_request_id: str, asset_id: str) -> None: ...

@abstractmethod
def find_assets_by_change(self, change_request_id: str) -> list[ChangeAsset]: ...
```

### 2. Infrastructure Layer

#### 2.1 Model — `src/change_bc/change_request/infrastructure/models.py` (add)

```python
class ChangeAssetModel(ULIDMixin, Base):
    __tablename__ = "change_assets"

    change_request_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("change_requests.id"), nullable=False, index=True
    )
    asset_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("change_request_id", "asset_id", name="uq_change_assets_change_asset"),
        Index("ix_change_assets_asset_id", "asset_id"),
    )
```

Key points:
- FK to `change_requests.id` (same BC, referential integrity enforced)
- No FK to assets table (cross-BC reference, string only)
- UniqueConstraint prevents duplicate links
- Indexes on both FKs for query performance

#### 2.2 Repository — `src/change_bc/change_request/infrastructure/repository.py` (modify)

Add implementations:

```python
def save_change_asset(self, change_asset: ChangeAsset) -> None:
    model = ChangeAssetModel(
        id=change_asset.id,
        change_request_id=change_asset.change_request_id,
        asset_id=change_asset.asset_id,
    )
    self.session.add(model)
    self.session.flush()

def delete_change_asset(self, change_request_id: str, asset_id: str) -> None:
    self.session.query(ChangeAssetModel).filter(
        ChangeAssetModel.change_request_id == change_request_id,
        ChangeAssetModel.asset_id == asset_id,
    ).delete()
    self.session.flush()

def find_assets_by_change(self, change_request_id: str) -> list[ChangeAsset]:
    models = self.session.execute(
        select(ChangeAssetModel).where(
            ChangeAssetModel.change_request_id == change_request_id
        )
    ).scalars().all()
    return [
        ChangeAsset(
            id=m.id,
            change_request_id=m.change_request_id,
            asset_id=m.asset_id,
            created_at=m.created_at,
        )
        for m in models
    ]
```

#### 2.3 Migration — `alembic/versions/e33b1_create_change_assets_table.py`

```sql
CREATE TABLE change_assets (
    id VARCHAR(26) PRIMARY KEY,
    change_request_id VARCHAR(26) NOT NULL REFERENCES change_requests(id),
    asset_id VARCHAR(26) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_change_assets_change_asset UNIQUE (change_request_id, asset_id)
);

CREATE INDEX ix_change_assets_change_request_id ON change_assets (change_request_id);
CREATE INDEX ix_change_assets_asset_id ON change_assets (asset_id);
```

### 3. Application Layer

#### 3.1 Commands

**`commands/link_assets.py`** — Bulk link assets to a change request

```python
@dataclass
class LinkAssetsCommand(Command):
    change_id: str
    company_id: str
    asset_ids: list[str]
    actor_id: str

class LinkAssetsCommandHandler(CommandHandler[LinkAssetsCommand]):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
        asset_repo: AssetRepositoryInterface,
    ):
        self.change_repo = change_repo
        self.asset_repo = asset_repo

    def handle(self, command: LinkAssetsCommand) -> None:
        change = self.change_repo.find_by_id(command.change_id, command.company_id)
        if not change:
            raise ChangeNotFoundError(command.change_id)
        if change.status.is_terminal:
            raise InvalidStatusTransitionError(change.status, change.status)

        # Fetch existing links to skip duplicates
        existing = self.change_repo.find_assets_by_change(command.change_id)
        existing_ids = {ca.asset_id for ca in existing}

        linked = 0
        for asset_id in command.asset_ids:
            if asset_id in existing_ids:
                continue  # Skip duplicates silently
            # Validate asset exists in company
            asset = self.asset_repo.find_by_id(asset_id, command.company_id)
            if not asset:
                continue  # Skip invalid assets silently
            ca = ChangeAsset.create(
                change_request_id=command.change_id,
                asset_id=asset_id,
            )
            self.change_repo.save_change_asset(ca)
            linked += 1

        if linked > 0:
            event = ChangeEvent.create(
                change_request_id=command.change_id,
                event_type=ChangeEventType.ASSET_LINKED,
                description=f"{linked} asset(s) linked",
                actor_id=command.actor_id,
                metadata={"asset_ids": command.asset_ids, "linked": linked},
            )
            self.change_repo.save_event(event)
```

Key design choices:
- Duplicates silently skipped (not error) — per AC
- Invalid assets silently skipped — per vulnerability_bc pattern
- Single ChangeEvent for the batch operation (not per-asset)
- Cross-BC validation: `asset_repo.find_by_id()` from `asset_bc`

**`commands/unlink_asset.py`** — Unlink a single asset from a change request

```python
@dataclass
class UnlinkAssetCommand(Command):
    change_id: str
    company_id: str
    asset_id: str
    actor_id: str

class UnlinkAssetCommandHandler(CommandHandler[UnlinkAssetCommand]):
    def __init__(self, change_repo: ChangeRequestRepositoryInterface):
        self.change_repo = change_repo

    def handle(self, command: UnlinkAssetCommand) -> None:
        change = self.change_repo.find_by_id(command.change_id, command.company_id)
        if not change:
            raise ChangeNotFoundError(command.change_id)

        # Unlinking only in DRAFT, PENDING_APPROVAL, SCHEDULED
        allowed = {ChangeStatus.DRAFT, ChangeStatus.PENDING_APPROVAL, ChangeStatus.SCHEDULED}
        if change.status not in allowed:
            raise ChangeNotUnlinkableError(change.status.value)

        self.change_repo.delete_change_asset(command.change_id, command.asset_id)

        event = ChangeEvent.create(
            change_request_id=command.change_id,
            event_type=ChangeEventType.ASSET_UNLINKED,
            description="Asset unlinked",
            actor_id=command.actor_id,
            metadata={"asset_id": command.asset_id},
        )
        self.change_repo.save_event(event)
```

#### 3.2 Query Modifications

**`queries/get_change_request_detail.py`** — Extend with affected assets

Add DTO:
```python
@dataclass
class ChangeAssetDto:
    id: str
    asset_id: str
    asset_name: Optional[str]
    asset_tag: Optional[str]
    asset_brand: Optional[str]
    asset_model: Optional[str]
    created_at: Optional[datetime]
```

Extend `ChangeRequestDetailDto`:
```python
@dataclass
class ChangeRequestDetailDto:
    # ... all existing fields ...
    affected_assets: list[ChangeAssetDto]  # NEW
```

Extend `GetChangeRequestDetailQueryHandler.__init__`:
```python
def __init__(self, change_repo, user_name_resolver=None, asset_repo=None):
    self.change_repo = change_repo
    self.user_name_resolver = user_name_resolver
    self.asset_repo = asset_repo  # NEW — optional for backward compat
```

Extend `handle()`:
```python
# After fetching events, before building DTO:
affected_assets = []
if self.asset_repo:
    change_assets = self.change_repo.find_assets_by_change(query.change_id)
    if change_assets:
        asset_ids = [ca.asset_id for ca in change_assets]
        assets_map = {}
        for aid in asset_ids:
            a = self.asset_repo.find_by_id(aid, query.company_id)
            if a:
                assets_map[aid] = a
        affected_assets = [
            ChangeAssetDto(
                id=ca.id,
                asset_id=ca.asset_id,
                asset_name=assets_map[ca.asset_id].name if ca.asset_id in assets_map else None,
                asset_tag=assets_map[ca.asset_id].asset_tag if ca.asset_id in assets_map else None,
                asset_brand=assets_map[ca.asset_id].brand if ca.asset_id in assets_map else None,
                asset_model=assets_map[ca.asset_id].model if ca.asset_id in assets_map else None,
                created_at=ca.created_at,
            )
            for ca in change_assets
        ]
```

### 4. HTTP Layer

#### 4.1 Schemas — `adapters/http/api/changes/schemas.py` (modify)

Add:
```python
class LinkAssetsRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1)

class ChangeAssetResponse(BaseModel):
    id: str
    asset_id: str
    asset_name: Optional[str] = None
    asset_tag: Optional[str] = None
    asset_brand: Optional[str] = None
    asset_model: Optional[str] = None
    created_at: Optional[datetime] = None
```

Extend `ChangeRequestDetailResponse`:
```python
class ChangeRequestDetailResponse(BaseModel):
    # ... all existing fields ...
    affected_assets: list[ChangeAssetResponse] = []  # NEW
```

#### 4.2 Dependencies — `adapters/http/api/changes/dependencies.py` (modify)

Add:
```python
from src.asset_bc.asset.infrastructure.repository import AssetRepository

def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)
```

#### 4.3 Router — `adapters/http/api/changes/routers.py` (modify)

Add two endpoints:

```python
@router.post("/{change_id}/assets", status_code=status.HTTP_204_NO_CONTENT)
def link_assets(
    change_id: str,
    body: LinkAssetsRequest,
    current_user: User = Depends(require_roles(TECHNICIAN)),
    change_repo = Depends(get_change_repo),
    asset_repo = Depends(get_asset_repo),
    db: Session = Depends(get_db),
):
    handler = LinkAssetsCommandHandler(change_repo, asset_repo)
    try:
        handler.handle(LinkAssetsCommand(
            change_id=change_id,
            company_id=current_user.company_id,
            asset_ids=body.asset_ids,
            actor_id=current_user.id,
        ))
        db.commit()
    except ChangeNotFoundError:
        raise HTTPException(404, "Change request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(422, str(e))

@router.delete("/{change_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_asset(
    change_id: str,
    asset_id: str,
    current_user: User = Depends(require_roles(TECHNICIAN)),
    change_repo = Depends(get_change_repo),
    db: Session = Depends(get_db),
):
    handler = UnlinkAssetCommandHandler(change_repo)
    try:
        handler.handle(UnlinkAssetCommand(
            change_id=change_id,
            company_id=current_user.company_id,
            asset_id=asset_id,
            actor_id=current_user.id,
        ))
        db.commit()
    except ChangeNotFoundError:
        raise HTTPException(404, "Change request not found")
    except ChangeNotUnlinkableError as e:
        raise HTTPException(422, str(e))
```

Modify `_get_detail()` helper to pass `asset_repo` to the query handler:
```python
def _get_detail(change_id, company_id, change_repo, user_repo, asset_repo=None):
    handler = GetChangeRequestDetailQueryHandler(
        change_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        asset_repo=asset_repo,
    )
    # ... rest unchanged
```

Update `get_change_request` endpoint to inject `asset_repo`:
```python
@router.get("/{change_id}")
def get_change_request(
    change_id: str,
    current_user: User = Depends(require_roles(TECHNICIAN)),
    change_repo = Depends(get_change_repo),
    user_repo = Depends(get_user_repo),
    asset_repo = Depends(get_asset_repo),  # NEW
):
    result = _get_detail(change_id, current_user.company_id, change_repo, user_repo, asset_repo)
    # ... rest unchanged
```

### 5. Frontend

#### 5.1 TypeScript Types — `web/app/src/types/index.ts` (modify)

Add:
```typescript
export interface ChangeAsset {
  id: string;
  asset_id: string;
  asset_name: string | null;
  asset_tag: string | null;
  asset_brand: string | null;
  asset_model: string | null;
  created_at: string | null;
}
```

Extend `ChangeRequestDetail`:
```typescript
export interface ChangeRequestDetail {
  // ... all existing fields ...
  affected_assets: ChangeAsset[];
}
```

#### 5.2 ChangeDetailPage.tsx — `web/app/src/pages/admin/ChangeDetailPage.tsx` (modify)

Add an "Affected Assets" section after existing detail sections:

- **Section header:** "Affected Assets" with count badge
- **Table:** asset_name, asset_tag, brand/model, linked date, unlink button (trash icon)
- **"Link Assets" button:** Opens a modal/dropdown to search and select assets from the company
- **Unlink button:** Visible only in DRAFT/PENDING_APPROVAL/SCHEDULED states
- **Link button:** Visible in any non-terminal state
- **useMutation** for link/unlink with `queryClient.invalidateQueries(['change', id])`

Asset search in the link modal: reuse the existing asset search pattern from the codebase (GET /api/v1/assets with search param).

#### 5.3 i18n — `web/app/src/locales/en.ts` + `es.ts` (modify)

Add keys:
```typescript
// en.ts
'page.change_detail.affected_assets': 'Affected Assets',
'page.change_detail.link_assets': 'Link Assets',
'page.change_detail.unlink_asset': 'Unlink',
'page.change_detail.no_assets_linked': 'No assets linked to this change',
'page.change_detail.search_assets': 'Search assets...',
'page.change_detail.link_assets_title': 'Link Assets to Change',
'toast.assets_linked': 'Assets linked successfully',
'toast.asset_unlinked': 'Asset unlinked successfully',
'enum.change_event.asset_linked': 'Assets Linked',
'enum.change_event.asset_unlinked': 'Asset Unlinked',

// es.ts
'page.change_detail.affected_assets': 'Activos Afectados',
'page.change_detail.link_assets': 'Vincular Activos',
'page.change_detail.unlink_asset': 'Desvincular',
'page.change_detail.no_assets_linked': 'No hay activos vinculados a este cambio',
'page.change_detail.search_assets': 'Buscar activos...',
'page.change_detail.link_assets_title': 'Vincular Activos al Cambio',
'toast.assets_linked': 'Activos vinculados exitosamente',
'toast.asset_unlinked': 'Activo desvinculado exitosamente',
'enum.change_event.asset_linked': 'Activos Vinculados',
'enum.change_event.asset_unlinked': 'Activo Desvinculado',
```

### 6. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/change_bc/change_request/domain/entities.py` | Modify | Add ChangeAsset dataclass |
| `src/change_bc/change_request/domain/enums.py` | Modify | Add ASSET_LINKED, ASSET_UNLINKED to ChangeEventType |
| `src/change_bc/change_request/domain/exceptions.py` | Modify | Add AssetAlreadyLinkedError, AssetNotLinkedError, ChangeNotUnlinkableError |
| `src/change_bc/change_request/domain/repository.py` | Modify | Add 3 abstract methods |
| `src/change_bc/change_request/infrastructure/models.py` | Modify | Add ChangeAssetModel |
| `src/change_bc/change_request/infrastructure/repository.py` | Modify | Implement 3 asset methods |
| `src/change_bc/change_request/application/commands/link_assets.py` | New | LinkAssetsCommand + handler |
| `src/change_bc/change_request/application/commands/unlink_asset.py` | New | UnlinkAssetCommand + handler |
| `src/change_bc/change_request/application/queries/get_change_request_detail.py` | Modify | Add ChangeAssetDto, extend DetailDto + handler |
| `adapters/http/api/changes/schemas.py` | Modify | Add LinkAssetsRequest, ChangeAssetResponse, extend DetailResponse |
| `adapters/http/api/changes/dependencies.py` | Modify | Add get_asset_repo |
| `adapters/http/api/changes/routers.py` | Modify | Add 2 endpoints, extend _get_detail with asset_repo |
| `alembic/versions/e33b1_create_change_assets_table.py` | New | Migration |
| `web/app/src/types/index.ts` | Modify | Add ChangeAsset interface, extend ChangeRequestDetail |
| `web/app/src/pages/admin/ChangeDetailPage.tsx` | Modify | Add affected assets section |
| `web/app/src/locales/en.ts` | Modify | Add i18n keys |
| `web/app/src/locales/es.ts` | Modify | Add i18n keys |
| `tests/unit/change_bc/change_request/application/commands/test_link_assets.py` | New | Unit tests |
| `tests/unit/change_bc/change_request/application/commands/test_unlink_asset.py` | New | Unit tests |
| `tests/integration/test_change_request_endpoints.py` | Modify | Add link/unlink integration tests |

No `__init__.py` files needed — all directories already exist from F0.

## Database Schema

```sql
CREATE TABLE change_assets (
    id VARCHAR(26) PRIMARY KEY,
    change_request_id VARCHAR(26) NOT NULL REFERENCES change_requests(id),
    asset_id VARCHAR(26) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_change_assets_change_asset UNIQUE (change_request_id, asset_id)
);

CREATE INDEX ix_change_assets_change_request_id ON change_assets (change_request_id);
CREATE INDEX ix_change_assets_asset_id ON change_assets (asset_id);
```

## Testing Strategy

| Test Type | Scope | Files | Priority |
|-----------|-------|-------|----------|
| Unit | LinkAssetsCommand — link, skip duplicates, skip invalid, terminal guard | `tests/unit/change_bc/.../commands/test_link_assets.py` | High |
| Unit | UnlinkAssetCommand — unlink, status guard, not found | `tests/unit/change_bc/.../commands/test_unlink_asset.py` | High |
| Unit | GetChangeRequestDetail — affected_assets in response | `tests/unit/change_bc/.../queries/test_get_change_request_detail.py` | Medium (extend) |
| Integration | POST /{change_id}/assets — success, duplicates, terminal | `tests/integration/test_change_request_endpoints.py` | High |
| Integration | DELETE /{change_id}/assets/{asset_id} — success, status guard | `tests/integration/test_change_request_endpoints.py` | High |
| Integration | GET /{change_id} — affected_assets in detail response | `tests/integration/test_change_request_endpoints.py` | Medium |

## Implementation Order

1. Domain: Add ChangeEventType values (`enums.py`)
2. Domain: Add exceptions (`exceptions.py`)
3. Domain: Add ChangeAsset entity (`entities.py`)
4. Domain: Add repository methods (`repository.py`)
5. Infrastructure: Add ChangeAssetModel (`models.py`)
6. Infrastructure: Migration (`e33b1_*.py`)
7. Infrastructure: Implement repository methods (`repository.py`)
8. Application: LinkAssetsCommand (`commands/link_assets.py`)
9. Application: UnlinkAssetCommand (`commands/unlink_asset.py`)
10. Application: Extend detail query (`queries/get_change_request_detail.py`)
11. HTTP: Add schemas (`schemas.py`)
12. HTTP: Add dependency (`dependencies.py`)
13. HTTP: Add endpoints + extend _get_detail (`routers.py`)
14. Tests: Unit tests (link + unlink commands)
15. Tests: Integration tests (endpoints)
16. Frontend: TypeScript types
17. Frontend: Affected assets section on ChangeDetailPage
18. Frontend: i18n keys

## Open Technical Questions

None — all patterns are well-established in the codebase (IncidentAsset + VulnerabilityAsset).

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cross-BC asset lookup N+1 | Low | Slow detail page | Batch fetch asset_ids in single query if needed; acceptable for small asset counts per change |
| Migration dependency on F0 migration | Low | Migration order | F0 migration already applied; F1 migration depends on change_requests table existing |
