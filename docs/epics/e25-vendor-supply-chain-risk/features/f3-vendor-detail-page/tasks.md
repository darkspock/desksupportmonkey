# Tasks: F3 — Vendor Detail Page

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-26

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Application: GetVendorRiskProfileQuery + handler (aggregated view) | M | App |
| 2 | Application: Cross-BC ports — incidents by vendor, risks by vendor | M | App |
| 3 | HTTP: risk profile schemas | S | HTTP |
| 4 | HTTP: risk profile endpoint | S | HTTP |
| 5 | Unit tests: risk profile query handler | M | Test |
| 6 | Integration tests: risk profile endpoint | M | Test |
| 7 | Frontend: VendorDetailPage — Overview tab | M | FE |
| 8 | Frontend: VendorDetailPage — Contracts tab | L | FE |
| 9 | Frontend: VendorDetailPage — Assessments tab | M | FE |
| 10 | Frontend: VendorDetailPage — Dependencies tab | M | FE |
| 11 | Frontend: VendorDetailPage — Incidents tab | S | FE |
| 12 | Frontend: VendorDetailPage — Risks tab | S | FE |
| 13 | Frontend: Routes + update VendorListPage links | S | FE |
| 14 | Frontend: i18n EN/ES translations for vendor detail | M | FE |

## Detailed Tasks

### Phase 1: Application

#### Task 1: GetVendorRiskProfileQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/get_vendor_risk_profile.py` (new)
- **What:** `GetVendorRiskProfileQuery(vendor_id, company_id)`. Handler aggregates: vendor details (with extended fields), latest assessment (if any), active contracts count + list, dependency count + critical count, incident count (via port), linked risk count (via port). Returns `VendorRiskProfileDto`.
- **Deps:** F0 tasks 4-5, F1 task 4, F2 task 4
- **Acceptance:** Returns comprehensive risk profile with all data sources
- [x] Done

#### Task 2: Cross-BC ports — incidents by vendor, risks by vendor
- **Files:**
  - `src/procurement_bc/vendor/application/ports.py` (new)
  - Implement ports at router level using incident_bc and risk_bc repos
- **What:**
  - `IncidentByVendorReader` port: `find_by_vendor(vendor_id, company_id, page, page_size)` → list of incident summaries (id, title, severity, status, created_at)
  - `RiskByVendorReader` port: `find_by_vendor(vendor_id, company_id)` → list of risk summaries (id, title, risk_level, status)
  - Ports satisfied at HTTP router level by injecting incident_bc and risk_bc repositories
- **Acceptance:** Ports defined, implementations return correct cross-BC data
- [x] Done

### Phase 2: HTTP

#### Task 3: Risk profile schemas
- **File:** `adapters/http/api/vendors/risk_profile_schemas.py` (new)
- **What:** `VendorRiskProfileResponse` (vendor info + latest assessment + contract summary + dependency summary + incident count + risk count). `VendorIncidentSummaryResponse`, `VendorRiskSummaryResponse` for sub-lists.
- **Deps:** Tasks 1-2
- **Acceptance:** All schemas defined
- [x] Done

#### Task 4: Risk profile endpoint
- **File:** `adapters/http/api/vendors/risk_profile_router.py` (new) or extend contract_router
- **What:** GET `/api/v1/vendors/:id/risk-profile`. Technician+ auth. Injects cross-BC ports. Returns aggregated profile.
- **Deps:** Task 3
- **Acceptance:** Endpoint returns complete risk profile
- [x] Done

### Phase 3: Tests

#### Task 5: Unit tests — risk profile query handler
- **File:** `tests/unit/procurement_bc/vendor/application/queries/test_risk_profile_query.py` (new)
- **What:** Test GetVendorRiskProfileQueryHandler: vendor with all data, vendor with no assessments/contracts, vendor not found. Mock all repos + ports.
- **Acceptance:** All scenarios covered
- [x] Done

#### Task 6: Integration tests — risk profile endpoint
- **File:** `tests/integration/test_vendor_risk_profile_endpoints.py` (new)
- **What:** Create vendor + contract + assessment + dependency → GET risk-profile returns all. Empty vendor → returns zeros. Auth: employee=403. Not found=404.
- **Acceptance:** Full profile endpoint tested
- [x] Done

### Phase 4: Frontend

#### Task 7: VendorDetailPage — Overview tab
- **File:** `web/app/src/pages/admin/VendorDetailPage.tsx` (new)
- **What:** Tab layout with 6 tabs. Overview tab shows: vendor name/info card, risk level badge (color-coded), is_critical_ict flag, latest assessment summary (5 scores as bar/radar chart or simple list), quick stats (active contracts, dependencies, critical dependencies, linked incidents, linked risks). Back button to vendor list.
- **Acceptance:** Overview renders with all data from risk-profile endpoint
- [x] Done

#### Task 8: VendorDetailPage — Contracts tab
- **File:** `web/app/src/pages/admin/VendorDetailPage.tsx` (extend)
- **What:** Contracts list table with status badges (draft=gray, active=green, expired=orange, terminated=red). Create/edit contract modal with all fields including security clauses checklist (toggle switches for each clause). Document upload area per contract (drag & drop or click). Document list with download/delete. Status change button (dropdown with valid transitions).
- **Acceptance:** Full contract CRUD including documents and status changes
- [x] Done

#### Task 9: VendorDetailPage — Assessments tab
- **File:** `web/app/src/pages/admin/VendorDetailPage.tsx` (extend)
- **What:** Assessment history list (ordered by date desc, latest highlighted). Create assessment form with 5 sliders or number inputs (1-5 scale), justification textarea, next review date picker. Shows calculated risk level preview before submit.
- **Acceptance:** Assessment create form works, list displays history
- [x] Done

#### Task 10: VendorDetailPage — Dependencies tab
- **File:** `web/app/src/pages/admin/VendorDetailPage.tsx` (extend)
- **What:** Dependencies list with business function badge, is_critical flag (red shield icon), service description. Add/edit dependency modal with business function dropdown, criticality toggle, description field. Delete confirmation.
- **Acceptance:** Full dependency CRUD working
- [x] Done

#### Task 11: VendorDetailPage — Incidents tab
- **File:** `web/app/src/pages/admin/VendorDetailPage.tsx` (extend)
- **What:** Read-only table of incidents linked to this vendor (from cross-BC query). Columns: title, severity badge, status badge, date. Link to incident detail page.
- **Acceptance:** Incidents display correctly, links work
- [x] Done

#### Task 12: VendorDetailPage — Risks tab
- **File:** `web/app/src/pages/admin/VendorDetailPage.tsx` (extend)
- **What:** Read-only table of risks linked to this vendor (from risk_bc via RiskLinkType.VENDOR). Columns: title, risk_level badge, status badge. Link to risk detail page.
- **Acceptance:** Linked risks display correctly
- [x] Done

#### Task 13: Routes + update VendorListPage links
- **Files:** `web/app/src/router.tsx`, `web/app/src/pages/admin/VendorListPage.tsx`
- **What:** Add route `/vendors/:id` pointing to VendorDetailPage. Update VendorListPage vendor name column to be a `<Link>` to detail page.
- **Acceptance:** Navigation works between list and detail
- [x] Done

#### Task 14: i18n EN/ES translations
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Vendor detail page keys: tab names (overview, contracts, assessments, dependencies, incidents, risks), section titles, labels, empty states, button labels.
- **Acceptance:** All strings translated EN + ES
- [x] Done
