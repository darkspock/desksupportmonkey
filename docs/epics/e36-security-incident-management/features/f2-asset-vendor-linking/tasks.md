# Tasks: F2 — Asset & Vendor Linking

**Feature:** [requirements.md](requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Application: ports.py — AssetReader, VendorReader interfaces | S | App |
| 2 | Application: LinkAssetCommand + handler | S | App |
| 3 | Application: UnlinkAssetCommand + handler | S | App |
| 4 | Application: LinkVendorCommand + handler | S | App |
| 5 | Application: UnlinkVendorCommand + handler | S | App |
| 6 | Enrich GetIncidentDetailQueryHandler with asset/vendor names | M | App |
| 7 | HTTP: schemas (typed asset/vendor responses, link requests) | S | HTTP |
| 8 | HTTP: 4 link/unlink endpoints + port injection | M | HTTP |
| 9 | Unit tests: link/unlink command handlers | M | Test |
| 10 | Integration tests: link/unlink endpoints | M | Test |
| 11 | Frontend: affected assets + involved vendors sections | L | FE |
| 12 | i18n: EN/ES translations | S | FE |

## Detailed Tasks

### Phase 1: Application Layer

#### Task 1: Port interfaces
- **File:** `src/incident_bc/incident/application/ports.py` (NEW)
- **What:** Define `AssetReader` (ABC with `find_by_id(asset_id, company_id) -> Optional[Any]`, `find_all_by_company(company_id) -> list[Any]`) and `VendorReader` (ABC with `find_by_id(vendor_id, company_id) -> Optional[Any]`, `find_all(company_id) -> list[Any]`). Follow existing pattern from `asset_bc/asset/application/ports.py`.
- **Acceptance:** Abstract interfaces defined with proper typing
- [x] Done

#### Task 2: LinkAssetCommand + handler
- **File:** `src/incident_bc/incident/application/commands/link_asset.py`
- **What:** Command(incident_id, company_id, asset_id, impact_description?, actor_id). Handler: validates incident exists + not closed, calls repo.save_incident_asset(), creates timeline entry (ASSET_LINKED).
- **Deps:** Task 1
- **Acceptance:** Asset linked, timeline entry created, duplicate raises AssetAlreadyLinkedError
- [x] Done

#### Task 3: UnlinkAssetCommand + handler
- **File:** `src/incident_bc/incident/application/commands/unlink_asset.py`
- **What:** Command(incident_id, company_id, asset_id, actor_id). Handler: validates incident exists + not closed, calls repo.delete_incident_asset(), creates timeline entry (ASSET_UNLINKED).
- **Acceptance:** Asset unlinked, timeline entry created
- [x] Done

#### Task 4: LinkVendorCommand + handler
- **File:** `src/incident_bc/incident/application/commands/link_vendor.py`
- **What:** Command(incident_id, company_id, vendor_id, involvement_description?, actor_id). Handler: validates incident exists + not closed, calls repo.save_incident_vendor(), creates timeline entry (VENDOR_LINKED).
- **Acceptance:** Vendor linked, timeline entry created
- [x] Done

#### Task 5: UnlinkVendorCommand + handler
- **File:** `src/incident_bc/incident/application/commands/unlink_vendor.py`
- **What:** Command(incident_id, company_id, vendor_id, actor_id). Handler: validates incident exists + not closed, calls repo.delete_incident_vendor(), creates timeline entry (VENDOR_UNLINKED).
- **Acceptance:** Vendor unlinked, timeline entry created
- [x] Done

#### Task 6: Enrich incident detail with asset/vendor names
- **File:** `src/incident_bc/incident/application/queries/get_incident_detail.py`
- **What:** Inject AssetReader and VendorReader ports. After loading assets/vendors dicts from repo, look up each asset_id/vendor_id via ports to get name/type. Return IncidentAssetDto and IncidentVendorDto instead of raw dicts.
- **Deps:** Task 1
- **Acceptance:** Incident detail returns asset_name, asset_type, vendor_name for each linked item
- [x] Done

### Phase 2: HTTP Layer

#### Task 7: Schemas
- **File:** `adapters/http/api/incidents/schemas.py`
- **What:** Add `LinkAssetRequest(asset_id, impact_description?)`, `LinkVendorRequest(vendor_id, involvement_description?)`. Replace `assets: list[dict[str, Any]]` and `vendors: list[dict[str, Any]]` with typed `IncidentAssetResponse` and `IncidentVendorResponse` in IncidentDetailResponse.
- **Acceptance:** Typed schemas, proper validation
- [x] Done

#### Task 8: Link/unlink endpoints + port injection
- **File:** `adapters/http/api/incidents/routers.py`
- **What:** Add 4 endpoints: POST `/{id}/assets` (link), DELETE `/{id}/assets/{asset_id}` (unlink), POST `/{id}/vendors` (link), DELETE `/{id}/vendors/{vendor_id}` (unlink). All require technician+. Inject AssetReader/VendorReader ports (backed by asset_bc/procurement_bc repos). Update `_detail_to_response()` to map IncidentAssetDto/IncidentVendorDto fields.
- **Deps:** Tasks 2-6
- **Acceptance:** All endpoints work with proper error handling (409 duplicate, 404 not found, 422 closed)
- [x] Done

### Phase 3: Tests

#### Task 9: Unit tests — link/unlink commands
- **File:** `tests/unit/incident_bc/incident/application/commands/test_link_asset.py`, `tests/unit/incident_bc/incident/application/commands/test_link_vendor.py`
- **What:** Test happy path, incident not found, incident closed, duplicate link (for link commands). Test happy path, incident not found (for unlink commands).
- **Acceptance:** All tests pass
- [x] Done

#### Task 10: Integration tests — link/unlink endpoints
- **File:** `tests/integration/test_incidents_endpoints.py`
- **What:** Test link asset, unlink asset, link vendor, unlink vendor. Test duplicate link returns 409. Test timeline entries created. Test incident detail includes asset/vendor names.
- **Acceptance:** All tests pass with real DB
- [x] Done

### Phase 4: Frontend

#### Task 11: Affected assets + involved vendors sections
- **File:** `web/app/src/pages/technician/IncidentDetail.tsx`, `web/app/src/types/index.ts`
- **What:** Add "Affected Assets" section with linked assets list (name, type, impact desc, unlink button), asset search/selector to add new ones. Add "Involved Vendors" section similarly. Update TypeScript types. Mutations for link/unlink.
- **Acceptance:** Sections render, link/unlink works, proper loading states
- [x] Done

#### Task 12: i18n translations
- **File:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Translation keys for asset/vendor section titles, button labels, placeholders, toast messages.
- **Acceptance:** UI renders correctly in EN and ES
- [x] Done
