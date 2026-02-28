# Feature F1: CI Relationships

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** F0 (criticality fields on Asset, needed for criticality badges in dependency views)
**Complexity:** M

## Scope

### Included
- CIRelationship entity (id, company_id, source_asset_id, target_asset_id, relationship_type, description, created_at, created_by)
- CIRelationshipType enum (RUNS_ON, DEPENDS_ON, CONNECTED_TO, PART_OF, BACKS_UP)
- CIRelationship repository interface + SQLAlchemy implementation
- Database migration: create `ci_relationships` table with FK and unique constraints
- CreateCIRelationshipCommand + handler (with AssetEvent `ci_relationship_created`)
- UpdateCIRelationshipCommand + handler (edit description only)
- DeleteCIRelationshipCommand + handler (hard delete, with AssetEvent `ci_relationship_deleted`)
- ListCIRelationshipsQuery + handler (list relationships for an asset, both directions)
- HTTP endpoints under `/api/v1/assets/{id}/relationships`: POST, GET, PATCH `/{rel_id}`, DELETE `/{rel_id}`
- Constraint enforcement: no self-reference, no duplicates, same company, no decommissioned targets
- Frontend: "Dependencies" tab on asset detail page showing upstream/downstream relationships
- Frontend: "Add Relationship" modal with type dropdown, asset search, description field
- Frontend: edit description inline, delete with confirmation
- Unit tests for all commands/queries and constraint validation
- Integration tests for relationship endpoints
- i18n EN/ES for relationship types and UI labels

### Excluded (in other features)
- Recursive impact propagation traversal (F2)
- Impact radius calculation (F2)
- CMDB dashboard (F2)
- SLA escalation (F3)

## User Value

When this feature is complete:
- Technicians and admins can create typed, directional relationships between assets (e.g., "App Server depends_on Database Server")
- Dependencies tab on asset detail shows all upstream dependencies and downstream dependents with criticality badges
- Relationship descriptions can be edited after creation
- All constraint violations are caught (self-reference, duplicates, cross-company, decommissioned targets)
- Relationship creation/deletion is audited via AssetEvent

## Acceptance Criteria

- [ ] CIRelationship CRUD: create, list, update description, delete (hard)
- [ ] 5 relationship types: runs_on, depends_on, connected_to, part_of, backs_up
- [ ] No self-referencing allowed (source == target → 422)
- [ ] No duplicate relationships (same source + target + type → 409)
- [ ] Both assets must belong to same company (cross-company → 422)
- [ ] Cannot create relationship to decommissioned asset (→ 422)
- [ ] Existing relationships preserved when asset is decommissioned
- [ ] AssetEvent `ci_relationship_created` recorded on source asset
- [ ] AssetEvent `ci_relationship_deleted` recorded on source asset
- [ ] Dependencies tab shows upstream (this asset depends on) and downstream (depends on this asset)
- [ ] Each relationship row shows: type icon/label, target asset name/serial, criticality badge, description
- [ ] Add Relationship modal: type dropdown, asset search, optional description
- [ ] Edit description via inline edit or modal
- [ ] Delete with confirmation dialog
- [ ] Migration creates `ci_relationships` table with indexes and unique constraint
- [ ] Unit tests for commands, queries, constraint validation
- [ ] Integration tests for all relationship endpoints
- [ ] i18n EN/ES translations

## Technical Scope

### Entities (owned by this feature)
- CIRelationship entity — NEW
- CIRelationshipType enum — NEW
- CIRelationshipRepositoryInterface — NEW
- CIRelationshipRepository (SQLAlchemy) — NEW
- CIRelationshipModel — NEW

### Entities (used from dependencies)
- Asset entity (F0) — read-only, for validation and criticality badge display
- AssetEvent — existing, 2 new event type strings

### Key Components
- `src/asset_bc/asset/domain/entities.py` — add CIRelationship dataclass
- `src/asset_bc/asset/domain/enums.py` — add CIRelationshipType
- `src/asset_bc/asset/domain/repository.py` — add CIRelationship repository interface (or separate file)
- `src/asset_bc/asset/infrastructure/models.py` — add CIRelationshipModel
- `src/asset_bc/asset/infrastructure/repository.py` — add CIRelationship repository implementation
- `alembic/versions/` — migration for `ci_relationships` table
- `src/asset_bc/asset/application/commands/create_ci_relationship.py` — NEW
- `src/asset_bc/asset/application/commands/update_ci_relationship.py` — NEW
- `src/asset_bc/asset/application/commands/delete_ci_relationship.py` — NEW
- `src/asset_bc/asset/application/queries/list_ci_relationships.py` — NEW
- `adapters/http/api/assets/routers.py` — add relationship endpoints (or separate relationship_router.py)
- `adapters/http/api/assets/schemas.py` — add relationship request/response schemas
- `web/app/src/pages/technician/AssetDetailPage.tsx` — add Dependencies tab

## Notes

- The Dependencies tab on asset detail page shows two tables: "Depends On" (this asset is source) and "Depended On By" (this asset is target). Each table lists the related asset with its type, name, serial number, criticality badge, and relationship description.
- The dependency listing at this stage is flat (direct relationships only, depth=1). Recursive traversal comes in F2.
- Relationship types are displayed with icons or labels: runs_on → "Runs on", depends_on → "Depends on", etc.
