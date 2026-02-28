# Feature F0: Criticality & BIA

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 0
**Dependencies:** None (extends existing asset_bc)
**Complexity:** M

## Scope

### Included
- AssetCriticality enum (CRITICAL, HIGH, MEDIUM, LOW)
- 7 new nullable fields on Asset entity: criticality, impact_score, rto_minutes, rpo_minutes, bia_justification, bia_reviewed_at, bia_reviewed_by
- Database migration: add columns to `assets` table
- SetCriticalityCommand + handler (with AssetEvent `criticality_set`)
- UpdateBiaCommand + handler (with AssetEvent `bia_updated`)
- Update existing GetAssetQuery/ListAssetsQuery to return new fields
- ListAssetsQuery: add criticality filter parameter
- HTTP: new endpoints PATCH `/api/v1/assets/{id}/criticality` and PATCH `/api/v1/assets/{id}/bia`
- Update AssetResponse schema with new fields
- Frontend: criticality badge on asset detail page
- Frontend: BIA section (collapsible panel) on asset detail page
- Frontend: criticality column + filter on asset list page
- Update TypeScript Asset type with new fields
- Unit tests for commands and domain logic
- Integration tests for new endpoints
- i18n EN/ES for criticality levels and BIA labels

### Excluded (in other features)
- CI Relationships (F1)
- Impact propagation and dependency graph (F2)
- CMDB Dashboard (F2)
- Affected assets on requests (F3)
- SLA escalation (F3)

## User Value

When this feature is complete:
- Admins and technicians can classify any asset by criticality level (Critical/High/Medium/Low)
- Admins can record Business Impact Analysis data (impact score, RTO, RPO, justification) per asset
- Asset detail page shows a criticality badge and BIA summary
- Asset list can be filtered by criticality level for compliance audits
- All changes are recorded in asset event history (audit trail)

## Acceptance Criteria

- [ ] Asset criticality field (CRITICAL/HIGH/MEDIUM/LOW) settable via PATCH endpoint
- [ ] Criticality can be cleared (set to null/unclassified)
- [ ] Cannot set criticality on decommissioned assets (422)
- [ ] BIA fields (impact_score 1-10, rto_minutes > 0, rpo_minutes >= 0, justification) recordable via PATCH endpoint
- [ ] BIA saves auto-set bia_reviewed_at and bia_reviewed_by
- [ ] Validation: impact_score out of range → 422, rto_minutes <= 0 → 422
- [ ] AssetEvent `criticality_set` recorded with old/new values
- [ ] AssetEvent `bia_updated` recorded with all BIA fields
- [ ] Asset list filterable by criticality
- [ ] Asset detail page shows criticality badge (color-coded)
- [ ] Asset detail page shows BIA section (impact score, RTO, RPO, justification, last reviewed)
- [ ] Migration adds nullable columns (backward-compatible)
- [ ] Unit tests for SetCriticalityCommand and UpdateBiaCommand
- [ ] Integration tests for both endpoints
- [ ] i18n EN/ES translations
- [ ] TypeScript Asset type updated

## Technical Scope

### Entities (owned by this feature)
- Asset entity — EXTENDED with 7 new fields
- AssetCriticality enum — NEW

### Entities (used from dependencies)
- AssetEvent — existing, 2 new event type strings

### Key Components
- `src/asset_bc/asset/domain/enums.py` — add AssetCriticality
- `src/asset_bc/asset/domain/entities.py` — add fields + set_criticality() + update_bia() methods
- `src/asset_bc/asset/infrastructure/models.py` — add mapped columns
- `alembic/versions/` — migration for new columns
- `src/asset_bc/asset/application/commands/set_criticality.py` — NEW
- `src/asset_bc/asset/application/commands/update_bia.py` — NEW
- `adapters/http/api/assets/routers.py` — add 2 PATCH endpoints
- `adapters/http/api/assets/schemas.py` — update response, add request schemas
- `web/app/src/pages/technician/AssetDetailPage.tsx` — criticality badge + BIA section
- `web/app/src/pages/technician/AssetListPage.tsx` — criticality column + filter
- `web/app/src/types/index.ts` — update Asset type

## Notes

- All new columns are nullable — no impact on existing assets.
- Criticality defaults to null (unclassified). This is intentional: it distinguishes "not yet assessed" from "Low".
- BIA review tracking (reviewed_at/reviewed_by) is passive — no Celery reminders. The CMDB dashboard (F2) will show overdue reviews.
