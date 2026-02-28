# Epic E25: Vendor & Supply Chain Risk

**Date:** 2026-02-26
**Priority:** Medium
**Status:** Pending
**Bounded Context:** `procurement_bc` (extends existing `vendor` subdomain)

## Business Alignment

**Objective:** Extend the existing vendor management system with contract lifecycle tracking, third-party risk assessments, supply chain security scoring, ICT dependency mapping, and concentration risk monitoring — satisfying NIS2 Article 21(2)(d) supply chain security requirements and DORA Chapter V Article 28 third-party ICT risk management obligations.

**KPI Targets:**
- 100% of active vendors have a current risk assessment (not older than review cadence)
- 100% of critical ICT vendors have documented contracts with security clauses
- Concentration risk alerts triggered when any single vendor exceeds 40% of critical service dependencies
- Mean time to vendor risk assessment < 5 business days
- Vendor contract renewal reminders sent 60/30/7 days before expiry

**Evidence:**
- NIS2 Article 21(2)(d): "supply chain security, including security-related aspects concerning the relationships between each entity and its direct suppliers or service providers"
- DORA Article 28: "ICT third-party risk management" — requires documented contractual arrangements, risk assessments, exit strategies, and concentration risk monitoring for critical ICT providers

## Problem Statement

**Current situation:** The platform has a functional vendor directory (E14) with basic CRUD and incident-vendor linking (E36), but lacks the structured risk management capabilities required by NIS2/DORA. Vendors exist as contacts only — no contracts, no risk scoring, no dependency mapping.

| Pain Point | Impact | Regulatory Gap |
|-----------|--------|----------------|
| No vendor contracts tracked | Renewal dates missed, no SLA visibility | DORA Art. 28(2) requires documented contractual arrangements |
| No risk assessment per vendor | Cannot classify vendor risk levels | NIS2 Art. 21(2)(d) requires supply chain risk evaluation |
| No ICT dependency mapping | Unknown which vendors support critical services | DORA Art. 28(4) requires identification of critical ICT providers |
| No concentration risk monitoring | Over-reliance on single vendor goes undetected | DORA Art. 29 addresses concentration risk |
| No contract compliance tracking | Security clauses not verified | DORA Art. 28(5) requires specific contractual provisions |
| No vendor performance metrics | Cannot measure vendor SLA adherence | Operational risk from underperforming vendors |

**Who is affected:**
- **Admins/Procurement Managers:** Need to manage contracts, assess vendor risk, monitor dependencies
- **Technicians:** Need visibility into vendor risk when linking vendors to incidents
- **Management/Auditors:** Need supply chain risk reports for NIS2/DORA compliance evidence

## Existing Foundation

E25 builds on top of what already exists:

| Component | Status | Source |
|-----------|--------|--------|
| Vendor CRUD (create, list, get, update, activate/deactivate) | Done | E14 |
| Vendor domain entity (name, email, phone, address, notes) | Done | E14 |
| Incident-vendor linking | Done | E36 |
| Risk-vendor association type (enum exists in risk_bc) | Partial | E37 |
| Vendor frontend (list page, inline modal CRUD) | Done | E14 |
| Vendor integration tests | Done | E14 |

## Proposed Solution

Extend the `procurement_bc/vendor` subdomain with new entities and capabilities:

### 1. Vendor Contracts
Track contract lifecycle per vendor: start/end dates, renewal dates, contract type (service, supply, licensing, SaaS), value, auto-renewal flag, security clauses checklist, and attached documents (stored in MinIO).

### 2. Vendor Risk Assessments
Structured questionnaire-based assessment per vendor covering: data handling practices, security certifications (ISO 27001, SOC2), incident response capability, business continuity, subcontractor management. Produces a risk score (Low/Medium/High/Critical) with justification.

### 3. Supply Chain Security Scoring
Vendor risk level is the `overall_risk_level` from the latest risk assessment, with an automatic escalation rule: if a vendor is flagged as critical ICT provider (`is_critical_ict = true`) and has no active contract with security clauses, the risk level is escalated to `critical` regardless of the assessment score. The cached `risk_level` on the Vendor entity is updated when a new assessment is created or when the critical ICT flag changes.

### 4. ICT Dependency Mapping
Map which vendors provide services to which business functions/asset types. Flag vendors as "critical ICT provider" when they support essential services. Enables concentration risk analysis.

### 5. Concentration Risk Alerts
Automated detection when a single vendor provides >40% of critical ICT services. Celery periodic check with notification alerts.

### 6. Vendor Performance Tracking
Track vendor SLA metrics: response time, resolution time, uptime (for SaaS vendors). Derived from linked incidents and contract SLAs.

### User Stories

**US1:** As an admin, I can create a contract for a vendor with type, dates, value, and renewal terms, so contract lifecycle is tracked centrally.

**US2:** As an admin, I can record security clauses in a vendor contract (data processing, breach notification, audit rights, exit strategy), so DORA Article 28 contractual requirements are documented.

**US3:** As an admin, I can conduct a risk assessment for a vendor using a structured questionnaire, so third-party risk is evaluated consistently.

**US4:** As an admin, I can view the computed supply chain security score for each vendor, so I can prioritize risk mitigation for high-risk vendors.

**US5:** As an admin, I can map vendor dependencies to business functions and asset types, so I understand which critical services depend on which vendors.

**US6:** As an admin, I can flag a vendor as a "critical ICT provider," so DORA-required oversight applies to those vendors.

**US7:** As an admin, I receive alerts when concentration risk is detected (single vendor >40% of critical dependencies), so I can plan diversification.

**US8:** As an admin, I can view vendor performance metrics (incident count, avg resolution time), so I can evaluate vendor effectiveness.

**US9:** As an admin, I receive renewal reminders 60/30/7 days before a contract expires, so renewals are not missed.

**US10:** As an admin, I can view a vendor detail page showing contracts, risk assessments, linked incidents, dependencies, linked risks, and performance metrics in one place, so I have a complete vendor risk profile.

**US11:** As an admin, I can export vendor risk data (assessments, contracts, dependencies) as PDF/CSV, so I can provide evidence to auditors.

**US12:** As an admin, I can upload and download documents attached to a vendor contract, so contract files are centrally stored.

**US13:** As an admin, I receive alerts when a vendor's latest risk assessment is older than the configured review cadence, so stale assessments are detected.

## Entities & States

### VendorContract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| vendor_id | ULID | Yes | FK to vendor |
| company_id | ULID | Yes | Tenant isolation |
| contract_type | Enum | Yes | service, supply, licensing, saas |
| title | String(200) | Yes | Contract title/reference |
| start_date | Date | Yes | Contract start |
| end_date | Date | No | Contract end (null = indefinite) |
| renewal_date | Date | No | Next renewal deadline |
| auto_renewal | Bool | No | Whether contract auto-renews |
| annual_value | Decimal | No | Annual contract value |
| currency | String(3) | No | ISO 4217 currency code |
| security_clauses | JSON | No | Checklist of DORA Art. 28 clauses |
| notes | Text | No | Additional notes |
| status | Enum | Yes | draft, active, expired, terminated |
| is_deleted | Bool | Yes | Soft delete flag (default false) |
| created_at | DateTime | Yes | Auto-set |
| updated_at | DateTime | Yes | Auto-updated |

**Contract Status State Machine:**

```
draft → active → expired (auto via Celery when end_date < today)
  │        │         │
  │        │         └── active (renewal/reactivation)
  │        │
  │        └── terminated
  │               │
  │               └── draft (renegotiation)
  │
  └── terminated (cancel before activation)
```

Valid transitions:
- draft → active (contract signed/approved)
- draft → terminated (cancelled before activation)
- active → expired (automatic via Celery daily task when `end_date < today`)
- active → terminated (early termination)
- expired → active (contract renewed/reactivated)
- terminated → draft (renegotiation — new terms being drafted)

Side effects:
- active → expired: Celery daily task auto-transitions; notification sent to admins
- Any status change: `updated_at` auto-updated

**Security Clauses JSON structure:**
```json
{
  "data_processing_agreement": true,
  "breach_notification_clause": true,
  "audit_rights": false,
  "exit_strategy": true,
  "subcontractor_oversight": false,
  "data_location_restrictions": true,
  "business_continuity_plan": false
}
```

### VendorContractDocument

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| contract_id | ULID | Yes | FK to vendor_contract |
| company_id | ULID | Yes | Tenant isolation |
| filename | String(255) | Yes | Original filename |
| content_type | String(100) | Yes | MIME type |
| size_bytes | Int | Yes | File size |
| storage_key | String(500) | Yes | MinIO object key |
| uploaded_by | ULID | Yes | User who uploaded |
| is_deleted | Bool | Yes | Soft delete flag (default false) |
| created_at | DateTime | Yes | Auto-set |

### VendorRiskAssessment

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| vendor_id | ULID | Yes | FK to vendor |
| company_id | ULID | Yes | Tenant isolation |
| assessed_by | ULID | Yes | User who conducted assessment |
| assessment_date | Date | Yes | When assessment was done |
| next_review_date | Date | No | When to reassess |
| data_handling_score | Int(1-5) | Yes | Data handling practices |
| security_certs_score | Int(1-5) | Yes | Security certifications |
| incident_response_score | Int(1-5) | Yes | Incident response capability |
| business_continuity_score | Int(1-5) | Yes | Business continuity planning |
| subcontractor_score | Int(1-5) | Yes | Subcontractor management |
| overall_risk_level | Enum | Yes | Auto-calculated: low, medium, high, critical |
| justification | Text | No | Assessment justification/notes |
| is_deleted | Bool | Yes | Soft delete flag (default false) |
| created_at | DateTime | Yes | Auto-set |

**Risk Level Calculation:**
- Average of 5 scores → 1.0-2.0 = Low, 2.1-3.0 = Medium, 3.1-4.0 = High, 4.1-5.0 = Critical
- Inverse: higher scores = worse risk (1 = excellent, 5 = poor)

### VendorDependency

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| vendor_id | ULID | Yes | FK to vendor |
| company_id | ULID | Yes | Tenant isolation |
| service_description | String(300) | Yes | What service the vendor provides |
| business_function | Enum | Yes | it_operations, security, communications, data_storage, cloud_infrastructure, software, hardware_supply, consulting, other |
| is_critical | Bool | Yes | Whether this is a critical ICT dependency |
| is_deleted | Bool | Yes | Soft delete flag (default false) |
| created_at | DateTime | Yes | Auto-set |

### Vendor (extended fields)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| is_critical_ict | Bool | No | Flagged as critical ICT provider |
| risk_level | Enum | No | Cached from latest assessment: low, medium, high, critical |
| website | String(500) | No | Vendor website |
| category | Enum | No | hardware, software, saas, consulting, telecom, cloud, managed_services, other |

## API Endpoints

### Vendor Contracts

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/vendors/:id/contracts | admin | Create contract |
| GET | /api/v1/vendors/:id/contracts | technician+ | List vendor contracts |
| GET | /api/v1/vendors/:id/contracts/:cid | technician+ | Get contract detail |
| PUT | /api/v1/vendors/:id/contracts/:cid | admin | Update contract |
| DELETE | /api/v1/vendors/:id/contracts/:cid | admin | Delete contract |

### Vendor Contract Documents

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/vendors/:id/contracts/:cid/documents | admin | Upload document |
| GET | /api/v1/vendors/:id/contracts/:cid/documents | technician+ | List documents |
| GET | /api/v1/vendors/:id/contracts/:cid/documents/:did/download | technician+ | Download document |
| DELETE | /api/v1/vendors/:id/contracts/:cid/documents/:did | admin | Soft-delete document |

### Vendor Risk Assessments

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/vendors/:id/assessments | admin | Create risk assessment |
| GET | /api/v1/vendors/:id/assessments | technician+ | List vendor assessments |
| GET | /api/v1/vendors/:id/assessments/:aid | technician+ | Get assessment detail |

### Vendor Dependencies

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/vendors/:id/dependencies | admin | Add dependency mapping |
| GET | /api/v1/vendors/:id/dependencies | technician+ | List vendor dependencies |
| PUT | /api/v1/vendors/:id/dependencies/:did | admin | Update dependency |
| DELETE | /api/v1/vendors/:id/dependencies/:did | admin | Remove dependency |

### Vendor Risk Overview

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/vendors/:id/risk-profile | technician+ | Full risk profile (latest assessment, contracts, dependencies, incidents, linked risks) |
| GET | /api/v1/vendors/supply-chain-dashboard | technician+ | Supply chain risk dashboard |
| GET | /api/v1/vendors/concentration-risk | admin | Concentration risk analysis |
| POST | /api/v1/vendors/risk-export | admin | Export vendor risk data (PDF/CSV) |

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `app.py` | Register new vendor sub-routers | Add include_router for contracts, assessments, dependencies |
| `procurement_bc/vendor/domain/entities.py` | Extend Vendor entity | Add is_critical_ict, risk_level, website, category fields |
| `procurement_bc/vendor/infrastructure/models.py` | Extend VendorModel | Add new columns |
| `alembic/versions/` | New migration | New tables + Vendor column additions |
| `core/celery.py` | Register periodic tasks | Contract renewal reminders, concentration risk check |
| `notification_bc` | New event types | CONTRACT_RENEWAL_REMINDER, CONCENTRATION_RISK_ALERT |
| `web/app/src/router.tsx` | Add vendor detail route | /vendors/:id page |
| `web/app/src/pages/admin/VendorListPage.tsx` | Extend with risk indicators | Show risk level badge, link to detail |
| `web/app/src/locales/` | i18n translations | EN + ES |
| `web/app/src/types/index.ts` | TypeScript interfaces | VendorContract, VendorAssessment, VendorDependency types |
| `risk_bc` | Cross-BC query | Vendor detail page shows risks linked to this vendor (via RiskLinkType.VENDOR). Add port or query. |
| `incident_bc` | Cross-BC query | Vendor detail page shows incidents linked to this vendor. Add "incidents by vendor_id" query. |

## Definition of Done

- [ ] VendorContract entity with CRUD, status lifecycle, state machine, security clauses
- [ ] VendorContract auto-expiry Celery task (daily, transitions active→expired when end_date < today)
- [ ] VendorContractDocument entity with MinIO upload/download/soft-delete
- [ ] VendorRiskAssessment entity with structured questionnaire and auto-scoring
- [ ] VendorDependency entity with business function mapping and criticality flag
- [ ] All entities use soft delete (`is_deleted` flag)
- [ ] Vendor entity extended with category, website, is_critical_ict, cached risk_level
- [ ] Risk level escalation rule: critical ICT vendors without security clauses → risk_level = critical
- [ ] Contract renewal reminder Celery task (60/30/7 days)
- [ ] Concentration risk detection Celery task
- [ ] Stale assessment detection Celery task (VENDOR_ASSESSMENT_OVERDUE notification)
- [ ] Vendor risk profile endpoint (aggregated view with linked risks from risk_bc)
- [ ] Supply chain dashboard endpoint
- [ ] PDF/CSV export for vendor risk data
- [ ] Frontend: Vendor detail page with tabs (contracts, assessments, dependencies, incidents, risks)
- [ ] Frontend: Contract CRUD UI with document upload
- [ ] Frontend: Risk assessment form
- [ ] Frontend: Dependency mapping UI
- [ ] Frontend: Supply chain dashboard
- [ ] Frontend: Risk level badges on vendor list
- [ ] i18n: EN + ES translations
- [ ] Unit tests for all command/query handlers
- [ ] Integration tests for all endpoints
- [ ] All tests passing (unit + integration)

## Open Questions

None — scope derived from NIS2/DORA regulatory requirements and existing vendor foundation.

## Resolved Decisions

1. **Same BC:** Extend `procurement_bc/vendor` rather than creating a new BC. Contracts, assessments, and dependencies are intrinsic to vendor management, not a separate domain.
2. **Risk assessment is a snapshot:** Each assessment is an immutable record. New assessments replace the cached risk_level on the vendor. History preserved by keeping all assessments.
3. **Security clauses as JSON:** Flexible structure allows adding new clause types without schema migration. Frontend renders as a checklist.
4. **Concentration risk threshold:** 40% is the initial configurable default. Can be made per-company later.
5. **Vendor category:** Added to Vendor entity directly (not a separate entity) to keep it simple. Enum-based, extensible.
6. **Export reuse:** PDF/CSV export reuses existing `report_bc` infrastructure (WeasyPrint + MinIO).
7. **Performance metrics derived:** Vendor performance (incident count, avg resolution) is a query-time calculation from incident_bc data, not stored redundantly.
8. **Contract state machine — auto-expiry + flexible transitions:** Celery daily task auto-expires contracts past end_date. Expired contracts can be reactivated (renewal). Terminated contracts can return to draft (renegotiation).
9. **Risk scoring — assessment + criticality escalation:** risk_level = latest assessment score, automatically escalated to critical if vendor is critical ICT provider without security clauses. No complex composite formula.
10. **Contract documents in v1:** File uploads stored in MinIO (same infrastructure as reports). Upload/download/delete per contract.
11. **All entities use soft delete:** `is_deleted` flag on VendorContract, VendorRiskAssessment, VendorDependency, VendorContractDocument. No physical deletion.
12. **Vendor detail shows linked risks:** Cross-BC query to risk_bc for risks linked to vendor via RiskLinkType.VENDOR.
13. **Stale assessment alerts:** Celery daily task checks vendors whose latest assessment next_review_date < today, sends VENDOR_ASSESSMENT_OVERDUE notification to admins.
