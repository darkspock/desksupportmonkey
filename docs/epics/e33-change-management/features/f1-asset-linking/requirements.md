# Feature: Asset Linking

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** F0
**Complexity:** S

## Scope

### Included

- ChangeAsset join table entity (change_request_id, asset_id, UniqueConstraint)
- Link assets command: POST /{change_id}/assets with list of asset_ids
- Unlink asset command: DELETE /{change_id}/assets/{asset_id}
- Cross-BC asset validation (verify asset exists via asset_repo)
- Affected assets displayed on change detail page (asset name, asset tag, brand/model)
- ChangeEvent entries for asset_linked / asset_unlinked
- Alembic migration for change_assets table

### Excluded (in other features)

- Change Request CRUD and state machine (F0)
- Post-Implementation Review (F2)
- Change dashboard (F3)
- Per-asset implementation status tracking (out of epic scope)

## User Value

When this feature is complete, admins and technicians can associate affected assets with a change request, providing traceability between a planned change and the specific endpoints impacted. This is essential for DORA compliance — auditors can verify which assets were affected by each change.

## Acceptance Criteria

- [ ] Can link one or more assets to a change request via POST /{change_id}/assets
- [ ] Can unlink an asset via DELETE /{change_id}/assets/{asset_id}
- [ ] Assets validated against asset_bc (404 if asset not found)
- [ ] Duplicate links are skipped (not error)
- [ ] ChangeEvent recorded for each link/unlink action
- [ ] Change detail page shows affected assets table (name, tag, brand/model)
- [ ] Linking allowed in any non-terminal state
- [ ] Unlinking allowed in DRAFT, PENDING_APPROVAL, SCHEDULED only
- [ ] i18n keys for affected assets section
- [ ] Unit tests for link/unlink commands
- [ ] Integration tests for link/unlink endpoints

## Technical Scope

### Entities (owned by this feature)

- **ChangeAsset** — join table (change_request_id + asset_id, unique constraint)

### Entities (used from dependencies)

- **ChangeRequest** (F0) — parent entity
- **ChangeEvent** (F0) — audit trail

### Key Components

- `src/change_bc/change_request/domain/entities.py` — add ChangeAsset dataclass
- `src/change_bc/change_request/infrastructure/models.py` — add ChangeAssetModel
- `src/change_bc/change_request/application/commands/link_assets.py`
- `src/change_bc/change_request/application/commands/unlink_asset.py`
- `adapters/http/api/changes/routers.py` — add link/unlink endpoints
- `adapters/http/api/changes/schemas.py` — add request/response schemas
- `alembic/versions/e33b1_*.py` — migration for change_assets table

## Notes

- Follows the exact pattern from vulnerability_bc (VulnerabilityAsset) and incident_bc (IncidentAsset)
- Cross-BC reference: asset_id is a string, no FK to assets table
- Asset details (name, tag, brand, model) fetched via cross-BC read at query time
