# Feature F3: Affected Assets & SLA Escalation

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F0 (criticality field on Asset, needed for SLA escalation lookup)
**Complexity:** M

## Scope

### Included
- "Affected Assets" section on request detail page: shows requester's assigned assets, technician can check/uncheck to mark as affected
- Save affected asset IDs in request's `data.affected_asset_ids: string[]` JSON field (no migration needed)
- Backend: PATCH `/api/v1/requests/{id}/affected-assets` endpoint to save affected asset IDs
- Backend: query to fetch requester's assigned assets for display
- Criticality-based SLA escalation in get_request_sla query:
  - Read `data.affected_asset_ids` from request
  - Fetch criticality for each affected asset
  - If any asset has criticality=CRITICAL, escalate effective priority by one level
  - If any asset has criticality=HIGH and request priority=LOW, escalate to MEDIUM
  - Escalation is read-time only — request priority field unchanged
  - SLA response includes `escalated: bool` and `effective_priority` fields
- Company setting: `sla_criticality_escalation_enabled` (default: true)
- Frontend: affected assets section with checkboxes, asset name/type/criticality badge
- Frontend: SLA status display shows "Escalated" indicator when active
- Unit tests for SLA escalation logic (all priority combinations)
- Integration tests for affected assets endpoint and SLA with escalation
- i18n EN/ES for affected assets and escalation labels

### Excluded (in other features)
- Criticality/BIA fields on Asset (F0)
- CI Relationships (F1)
- Impact propagation and CMDB dashboard (F2)

## User Value

When this feature is complete:
- Technicians can mark which of the requester's assets are affected by a service request
- Affected assets appear as badges/links on the request detail page for context
- SLA targets automatically escalate when a critical asset is involved — ensuring faster response for critical infrastructure issues
- Admins can disable SLA escalation per company if not desired

## Acceptance Criteria

- [ ] Request detail page shows "Affected Assets" section for technicians
- [ ] Section lists requester's assigned assets with name, type, serial, criticality badge
- [ ] Technician can check/uncheck assets as affected
- [ ] Affected asset IDs stored in request `data.affected_asset_ids`
- [ ] If requester has no assigned assets → section shows "No assets assigned to requester"
- [ ] PATCH `/api/v1/requests/{id}/affected-assets` saves the asset ID list (technician+ role)
- [ ] SLA escalation: Critical asset → effective priority escalates one level (Low→Medium, Medium→High, High→Critical)
- [ ] SLA escalation: High asset + Low priority → escalate to Medium
- [ ] SLA escalation: does NOT escalate if already at highest priority
- [ ] SLA response includes `escalated: bool` and `effective_priority: str`
- [ ] Company setting `sla_criticality_escalation_enabled` controls whether escalation is active
- [ ] Escalation is read-time only — request.priority field is NOT modified
- [ ] Frontend: SLA status shows "Escalated" indicator when escalation is active
- [ ] Unit tests for escalation logic (all priority × criticality combinations)
- [ ] Integration tests for affected assets endpoint
- [ ] Integration tests for SLA with escalation
- [ ] i18n EN/ES translations

## Technical Scope

### Entities (owned by this feature)
- No new entities — uses existing ServiceRequest.data JSON and Asset.criticality (F0)

### Entities (used from dependencies)
- Asset entity with criticality field (F0)
- ServiceRequest entity (existing, data JSON field)
- SlaPolicy entity (existing, E19)

### Key Components
- `adapters/http/api/requests/routers.py` — add PATCH `/{id}/affected-assets`
- `adapters/http/api/requests/schemas.py` — add SetAffectedAssetsRequest schema
- `src/sla_bc/sla/application/queries/get_request_sla.py` — modify handler to check affected_asset_ids and apply escalation
- `src/asset_bc/asset/domain/repository.py` — add method to fetch criticality for multiple asset IDs (batch)
- `web/app/src/pages/technician/RequestDetailPage.tsx` — add Affected Assets section
- `web/app/src/locales/en.ts` / `es.ts` — i18n keys

## Notes

- The `data` JSON field on ServiceRequest already exists and is used for other purpose-specific data. Adding `affected_asset_ids` is consistent with this pattern.
- SLA escalation does NOT create a new SLA policy — it adjusts which existing policy/priority tier is used for target lookup. Example: if a request is priority=Medium but linked to a Critical asset, the system looks up the High priority SLA targets instead.
- The batch criticality lookup should use a single query (`WHERE id IN (...)`) to avoid N+1 issues.
- Company setting can be stored in the company's settings JSON (existing pattern from other features like assignment AI settings).
