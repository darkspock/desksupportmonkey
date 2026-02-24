# Feature F2: Asset & Vendor Linking

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F0 (Incident Foundation)
**Complexity:** S

## Scope

### Included
- IncidentAsset link entity and repository logic
- IncidentVendor link entity and repository logic
- Link/unlink API endpoints for assets and vendors
- Timeline entries for all link/unlink operations (asset_linked, asset_unlinked, vendor_linked, vendor_unlinked)
- Cross-BC read queries to fetch asset/vendor details for display
- Incident detail response enriched with linked assets and vendors
- Frontend: "Affected Assets" section on incident detail page with asset search/selector
- Frontend: "Involved Vendors" section on incident detail page with vendor selector
- i18n: EN/ES for asset/vendor linking UI

### Excluded (in other features)
- Incident CRUD and lifecycle (F0)
- Regulatory reports (F1)
- Post-mortem (F3)
- Dashboard (F4)

## User Value

When this feature is complete, IT managers can:
- Link affected assets (devices, servers, workstations) to a security incident
- Link involved vendors (third-party suppliers) to a security incident
- See exactly which assets and vendors are impacted by each incident
- Unlink incorrectly added assets/vendors with full audit trail

## Acceptance Criteria

- [ ] POST `/api/v1/incidents/{id}/assets` links one or more assets to an incident
- [ ] DELETE `/api/v1/incidents/{id}/assets/{asset_id}` unlinks an asset
- [ ] POST `/api/v1/incidents/{id}/vendors` links a vendor to an incident
- [ ] DELETE `/api/v1/incidents/{id}/vendors/{vendor_id}` unlinks a vendor
- [ ] Each link/unlink creates a timeline entry (asset_linked, asset_unlinked, vendor_linked, vendor_unlinked)
- [ ] Impact description can be provided when linking an asset
- [ ] Involvement description can be provided when linking a vendor
- [ ] GET `/api/v1/incidents/{id}` response includes linked assets (with name, type) and vendors (with name)
- [ ] Asset data fetched via cross-BC read from `asset_bc`
- [ ] Vendor data fetched via cross-BC read from `procurement_bc`
- [ ] All endpoints require technician or admin role
- [ ] Frontend: asset search/selector component on incident detail
- [ ] Frontend: vendor selector component on incident detail
- [ ] Frontend: display linked assets and vendors with unlink option
- [ ] i18n: all new strings in EN and ES
- [ ] Unit tests for link/unlink commands
- [ ] Integration tests for all link/unlink endpoints

## Technical Scope

### Entities (owned by this feature)
- `IncidentAsset` — link table entity
- `IncidentVendor` — link table entity

### Entities (used from dependencies)
- `SecurityIncident` from F0
- `IncidentTimeline` from F0
- `Asset` from `asset_bc` (read-only cross-BC)
- `Vendor` from `procurement_bc` (read-only cross-BC)

### Key Components
- `src/incident_bc/incident/application/commands/link_asset.py`
- `src/incident_bc/incident/application/commands/unlink_asset.py`
- `src/incident_bc/incident/application/commands/link_vendor.py`
- `src/incident_bc/incident/application/commands/unlink_vendor.py`
- `src/incident_bc/incident/application/ports.py` — AssetReader, VendorReader interfaces
- `adapters/http/api/incidents/routers.py` — add asset/vendor endpoints

## Notes

- Cross-BC reads follow the project pattern: define port interfaces in `incident_bc`, implement in infrastructure using direct repository access to `asset_bc` and `procurement_bc` tables.
- Tables (`incident_assets`, `incident_vendors`) are already created by F0 migration.
- Timeline entries for unlink operations were added per resolved decision #5.
