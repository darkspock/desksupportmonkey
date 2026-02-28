# Epic Slicing: E25 - Vendor & Supply Chain Risk

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-26
**Total Features:** 5

## Slicing Rationale

E25 extends the existing `procurement_bc/vendor` subdomain (E14) with contract management, risk assessments, dependency mapping, and compliance reporting. Since a working vendor CRUD + incident linking already exists, the features focus on NEW capabilities only.

Slicing follows **vertical slices by regulatory value**:
- **F0** extends the vendor entity and adds contracts — foundational data that everything else depends on
- **F1** adds risk assessments with scoring — the core NIS2/DORA requirement
- **F2** adds dependency mapping and concentration risk — DORA-specific ICT provider analysis
- **F3** adds the vendor detail page — unified frontend for all vendor risk data
- **F4** adds the supply chain dashboard, alerts, and export — compliance reporting layer

Each feature is independently deployable and delivers standalone regulatory value.

## Dependency Graph

```
Feature 0: Vendor Extensions & Contracts
    │
    ├── Feature 1: Risk Assessments
    │
    ├── Feature 2: Dependencies & Concentration Risk
    │
    ├── Feature 3: Vendor Detail Page (depends on F0, optionally F1+F2)
    │
    └── Feature 4: Dashboard, Alerts & Export (depends on F0+F1+F2)
```

F3 can start after F0 and incrementally add tabs as F1/F2 complete. F4 requires all data sources (F0+F1+F2) to be meaningful.

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Vendor Extensions & Contracts | None (extends E14) | Contract lifecycle tracking with state machine, document uploads, security clauses, auto-expiry, DORA Art. 28 documentation | L | Done |
| 1 | Risk Assessments | F0 | Structured vendor risk assessments with scoring questionnaire, auto-calculated risk level | M | Done |
| 2 | Dependencies & Concentration Risk | F0 | ICT dependency mapping, critical provider flagging, concentration risk detection | M | Done |
| 3 | Vendor Detail Page | F0 (F1, F2 optional) | Unified vendor risk profile with tabs for contracts, assessments, dependencies, incidents, risks | L | Done |
| 4 | Dashboard, Alerts & Export | F0, F1, F2 | Supply chain risk dashboard, contract renewal reminders, concentration alerts, PDF/CSV export | L | Done |

## Feature Details

### Feature 0: Vendor Extensions & Contracts
**Scope:**
- Extend Vendor entity: add `category`, `website`, `is_critical_ict`, `risk_level` fields
- Extend VendorModel + migration for new columns
- VendorContract entity, model, repository, and migration
- VendorContractDocument entity, model, repository (MinIO storage)
- Contract CRUD commands + queries (create, update, list, get, soft-delete)
- Contract document upload/download/soft-delete endpoints
- Contract HTTP endpoints under `/api/v1/vendors/:id/contracts`
- Contract status state machine: draft→active→expired/terminated with flexible reactivation
- Contract auto-expiry Celery daily task (active→expired when end_date < today)
- Security clauses JSON field with DORA Art. 28 checklist
- Update VendorListPage to show category and risk_level badges
- Unit tests for contract commands/queries
- Integration tests for contract + document endpoints
- i18n keys for contracts

### Feature 1: Risk Assessments
**Scope:**
- VendorRiskAssessment entity, model, repository, and migration
- Risk assessment create + list + get commands/queries
- Auto-calculated overall_risk_level from 5 questionnaire scores
- Cache latest risk_level on Vendor entity (with criticality escalation rule)
- HTTP endpoints under `/api/v1/vendors/:id/assessments`
- Soft delete for assessments
- Unit tests for assessment commands/queries
- Integration tests for assessment endpoints
- i18n keys for assessments

### Feature 2: Dependencies & Concentration Risk
**Scope:**
- VendorDependency entity, model, repository, and migration
- Dependency CRUD commands/queries (create, update, list, delete)
- HTTP endpoints under `/api/v1/vendors/:id/dependencies`
- Concentration risk query: compute percentage of critical dependencies per vendor
- GET `/api/v1/vendors/concentration-risk` endpoint
- Unit tests for dependency commands/queries + concentration calculation
- Integration tests for dependency and concentration endpoints
- i18n keys for dependencies

### Feature 3: Vendor Detail Page
**Scope:**
- New route: `/vendors/:id` with VendorDetailPage
- Tabbed layout: Overview, Contracts, Assessments, Dependencies, Incidents, Risks
- Overview tab: vendor info, risk level badge, latest assessment summary, active contracts count, dependency count
- Contracts tab: list with status badges, create/edit modal, security clauses checklist view
- Assessments tab: list of assessments, create assessment form with 5-score questionnaire
- Dependencies tab: list with criticality flag, add/edit/remove
- Incidents tab: linked incidents from incident_bc (read-only, cross-BC query)
- Risks tab: linked risks from risk_bc via RiskLinkType.VENDOR (read-only, cross-BC query)
- Risk profile endpoint: GET `/api/v1/vendors/:id/risk-profile` (includes linked risks)
- Update VendorListPage rows to link to detail page

### Feature 4: Dashboard, Alerts & Export
**Scope:**
- Supply chain dashboard endpoint: vendor count by risk level, expiring contracts, critical ICT providers, concentration risk summary
- GET `/api/v1/vendors/supply-chain-dashboard`
- Celery task: contract renewal reminders (60/30/7 days before expiry)
- Celery task: concentration risk periodic check with notification alerts
- Celery task: stale assessment detection (VENDOR_ASSESSMENT_OVERDUE)
- Notification events: CONTRACT_RENEWAL_REMINDER, CONCENTRATION_RISK_ALERT, VENDOR_ASSESSMENT_OVERDUE
- PDF/CSV export endpoint: POST `/api/v1/vendors/risk-export`
- Frontend: Supply chain dashboard page with cards and charts
- Route + sidebar entry for dashboard
- i18n keys for dashboard and alerts

## Recommended Order

1. **Feature 0: Vendor Extensions & Contracts** — Must be first. Extends the existing vendor entity with new fields and adds the contract sub-entity. All other features reference the extended vendor or its contracts.

2. **Feature 1: Risk Assessments** — Adds the core compliance capability. NIS2 Article 21(2)(d) requires risk evaluation of suppliers. This feature enables structured, auditable risk assessments with scoring.

3. **Feature 2: Dependencies & Concentration Risk** — Adds DORA-specific analysis. ICT dependency mapping and concentration risk detection satisfy DORA Article 28-29 requirements. Can be built in parallel with F1 if needed.

4. **Feature 3: Vendor Detail Page** — The frontend consolidation. Best built after F0-F2 so all tabs have data to show. Can start with only contracts tab (from F0) and add tabs incrementally.

5. **Feature 4: Dashboard, Alerts & Export** — The reporting and automation layer. Requires F0+F1+F2 data to populate the dashboard meaningfully. Export provides compliance evidence for auditors.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F3/F4 depend on F0-F2)
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered
- [x] Builds on existing foundation (E14 vendor CRUD, E36 incident linking)

## Risk Notes

- F0 modifies the existing Vendor entity/model — migration must be backward-compatible (all new columns nullable or with defaults).
- F1 risk scoring uses a simple average. May need weighting per category in future versions.
- F2 concentration risk threshold (40%) is hardcoded initially. Consider making it configurable per company.
- F3 is large (L complexity) because it consolidates 5 tabs with different data sources. Consider splitting frontend sub-tasks within F3.
- F4 Celery tasks must be idempotent — duplicate reminders should not be sent for the same contract/day.
- Cross-BC queries (incidents for a vendor) use the existing `VendorReader` port pattern from E36.
