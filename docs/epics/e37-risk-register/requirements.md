# Epic E37: Risk Register

**Date:** 2026-02-23
**Priority:** High
**Status:** In Progress
**Bounded Context:** `risk_bc`

## Business Alignment

**Objective:** Provide organizations with a structured risk management capability that satisfies NIS2 Article 21 requirements for risk analysis and enables proactive identification, assessment, and mitigation of operational, cyber, compliance, and third-party risks.

**KPI Targets:**
- 100% of identified risks have assigned owners and mitigation plans
- Risk review cadence compliance > 90% (no overdue reviews)
- Mean time to mitigation < 30 days for High/Critical risks
- Complete audit trail for all risk assessments and decisions

**Evidence:** NIS2 Article 21(2)(a) mandates "policies on risk analysis and information system security." Regulatory auditors expect a living risk register with documented assessments and mitigation tracking.

## Problem Statement

**Current situation:** The platform manages security incidents (E36) but has no structured mechanism to track, assess, and mitigate organizational risks proactively. Risk identification happens reactively after incidents occur.

| Pain Point | Impact |
|-----------|--------|
| No central risk repository | Risks tracked in spreadsheets or not at all |
| No scoring methodology | Inconsistent risk prioritization |
| No mitigation tracking | Risk owners don't know what they're responsible for |
| No review cadence | Risks go stale without periodic reassessment |
| No audit trail | Cannot demonstrate risk management to auditors |
| No dashboard | Management lacks visibility into risk posture |

**Who is affected:**
- **Admins/Risk Managers:** Need to create, assess, and track risks
- **Technicians:** Assigned as mitigation owners, need to track their tasks
- **Management/Auditors:** Need dashboards and reports for compliance evidence

## Proposed Solution

A new `risk_bc` bounded context implementing a full risk register with:
1. Risk entries with categorization and cross-references to assets, departments, and vendors
2. 5x5 likelihood-impact scoring matrix with automatic risk level calculation
3. Mitigation plans with owner assignment, target dates, and status tracking
4. Risk treatment options (mitigate, accept, transfer, avoid)
5. Configurable review cadence with overdue alerts
6. Risk dashboard with heat map and trend visualization
7. Risk history audit trail
8. PDF/CSV export for board reporting

### User Stories

**US1:** As an admin, I can create a risk entry with title, description, and category, so I can document identified risks in a central register.

**US2:** As an admin, I can assess a risk by setting likelihood and impact scores (1-5), so the system auto-calculates the risk level (Low/Medium/High/Critical).

**US3:** As an admin, I can link a risk to assets, departments, and vendors, so I can track which organizational resources are exposed.

**US4:** As an admin, I can create a mitigation plan for a risk with description, owner, target date, and status, so risk treatment is tracked.

**US5:** As an admin, I can set the risk treatment option (mitigate, accept, transfer, avoid), so the chosen approach is documented.

**US6:** As an admin, I can configure a review cadence for each risk (monthly, quarterly, annually), so risks are periodically reassessed.

**US7:** As a technician (mitigation owner), I can view risks assigned to me and update mitigation plan status, so I can track my responsibilities.

**US8:** As an admin, I can view a risk dashboard with heat map, trend chart, and summary statistics, so management has visibility into risk posture.

**US9:** As an admin, I can view the full history of a risk (score changes, review decisions, status updates), so there is an audit trail.

**US10:** As an admin, I can export the risk register as PDF or CSV, so I can share it with auditors and board members.

**US11:** As an admin, I receive alerts when a risk review is overdue, so no risk goes stale.

## Entities & States

### Risk

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | Tenant isolation |
| title | String(200) | Yes | Risk title |
| description | Text | Yes | Detailed description |
| category | Enum | Yes | operational, cyber, compliance, third_party |
| likelihood | Int(1-5) | No | Likelihood score (Very Low to Very High) |
| impact | Int(1-5) | No | Impact score (Very Low to Very High) |
| risk_level | Enum | No | Auto-calculated: low, medium, high, critical |
| treatment | Enum | No | mitigate, accept, transfer, avoid |
| review_cadence | Enum | No | monthly, quarterly, annually |
| next_review_at | DateTime | No | Next review deadline |
| status | Enum | Yes | open, under_review, mitigated, accepted, closed |
| owner_id | ULID | No | Risk owner (user) |
| created_by | ULID | Yes | Creator |
| created_at | DateTime | Yes | Auto-set |
| updated_at | DateTime | Yes | Auto-updated |

### Risk Level Calculation (5x5 Matrix)

| | Impact 1 | Impact 2 | Impact 3 | Impact 4 | Impact 5 |
|---|---|---|---|---|---|
| **Likelihood 5** | Medium | High | High | Critical | Critical |
| **Likelihood 4** | Medium | Medium | High | High | Critical |
| **Likelihood 3** | Low | Medium | Medium | High | High |
| **Likelihood 2** | Low | Low | Medium | Medium | High |
| **Likelihood 1** | Low | Low | Low | Medium | Medium |

### MitigationPlan

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| risk_id | ULID | Yes | FK to risk |
| description | Text | Yes | What needs to be done |
| owner_id | ULID | No | Assigned user |
| target_date | Date | No | Expected completion |
| status | Enum | Yes | open, in_progress, completed, cancelled |
| created_at | DateTime | Yes | Auto-set |
| updated_at | DateTime | Yes | Auto-updated |

### RiskLink

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| risk_id | ULID | Yes | FK to risk |
| link_type | Enum | Yes | asset, department, vendor |
| link_id | ULID | Yes | ID of linked entity |
| created_at | DateTime | Yes | Auto-set |

### RiskHistory

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| risk_id | ULID | Yes | FK to risk |
| event_type | String | Yes | Event type (score_change, status_change, review_completed, etc.) |
| description | Text | Yes | Human-readable description |
| actor_id | ULID | Yes | Who made the change |
| metadata_json | JSON | No | Structured event data |
| created_at | DateTime | Yes | Auto-set |

### Risk Status State Machine

```
open → under_review → mitigated → closed
  │         │             │
  │         └─── open ────┘  (re-open after review)
  │
  └── accepted → closed
```

Valid transitions:
- open → under_review, accepted, closed
- under_review → open, mitigated, accepted, closed
- mitigated → open, closed (can reopen if mitigation fails)
- accepted → open, closed (can reopen if risk landscape changes)
- closed → open (can reopen)

## Use Cases

**UC1: Create Risk**
- Actor: Admin
- Steps: Fill form → Validate → Save → Add history entry → Return risk

**UC2: Assess Risk (Score)**
- Actor: Admin
- Precondition: Risk exists
- Steps: Set likelihood + impact → Auto-calculate risk_level → Save → Add history entry

**UC3: Set Treatment**
- Actor: Admin
- Steps: Select treatment option → Save → Add history entry

**UC4: Add Mitigation Plan**
- Actor: Admin
- Steps: Create plan with description, owner, target date → Save

**UC5: Update Mitigation Status**
- Actor: Technician+ (if owner) or Admin
- Steps: Change mitigation status → Save → Add history entry

**UC6: Link Risk to Entity**
- Actor: Admin
- Steps: Select entity type + ID → Create link → Save

**UC7: Review Risk**
- Actor: Admin
- Steps: Change status to under_review → Reassess scores → Update next_review_at → Add history

**UC8: Export Risk Register**
- Actor: Admin
- Steps: Generate PDF/CSV with all risks, scores, mitigations → Download

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `app.py` | Register risk router | Add include_router |
| `core/celery.py` | Register risk tasks | Add beat schedule for review reminders |
| `core/tasks/__init__.py` | Import risk tasks | Add import |
| `notification_bc` | Risk review overdue alerts | Add RISK_REVIEW_OVERDUE event type |
| `web/app/src/router.tsx` | Add risk routes | New pages |
| `web/app/src/components/layout/Sidebar.tsx` | Add sidebar entries | Under Security section |
| `web/app/src/locales/` | i18n translations | EN + ES |
| `web/app/src/types/index.ts` | TypeScript interfaces | Risk types |

## API Endpoints

### Risk CRUD

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/risks | admin | Create risk |
| GET | /api/v1/risks | technician+ | List risks (paginated, filterable) |
| GET | /api/v1/risks/:id | technician+ | Get risk detail |
| PUT | /api/v1/risks/:id | admin | Update risk |
| DELETE | /api/v1/risks/:id | admin | Delete risk |

### Risk Assessment

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/risks/:id/assess | admin | Set likelihood + impact scores |
| POST | /api/v1/risks/:id/treatment | admin | Set treatment option |
| POST | /api/v1/risks/:id/status | admin | Change risk status |

### Mitigation Plans

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/risks/:id/mitigations | admin | Add mitigation plan |
| PUT | /api/v1/risks/:id/mitigations/:mid | technician+ | Update mitigation (owner or admin) |
| DELETE | /api/v1/risks/:id/mitigations/:mid | admin | Delete mitigation plan |

### Risk Links

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/risks/:id/links | admin | Link risk to entity |
| DELETE | /api/v1/risks/:id/links/:lid | admin | Remove link |

### Risk History & Dashboard

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/risks/:id/history | technician+ | Get risk history |
| GET | /api/v1/risks/dashboard | technician+ | Get dashboard stats |
| POST | /api/v1/risks/export | admin | Export risk register (PDF/CSV) |

## Definition of Done

- [ ] `risk_bc` bounded context created with domain entities, enums, exceptions
- [ ] Risk CRUD endpoints working with pagination and filters
- [ ] 5x5 risk scoring matrix with auto-level calculation
- [ ] Mitigation plan CRUD with owner assignment
- [ ] Risk links to assets, departments, vendors
- [ ] Risk status state machine with valid transitions
- [ ] Risk history audit trail for all changes
- [ ] Review cadence with next_review_at calculation
- [ ] Celery task for overdue review alerts
- [ ] Risk dashboard endpoint with heat map data, trend, and summary stats
- [ ] PDF/CSV export using existing report infrastructure
- [ ] Frontend: Risk list, detail, create/edit forms
- [ ] Frontend: Risk dashboard with heat map and trend chart
- [ ] Frontend: Sidebar navigation entries
- [ ] i18n: EN + ES translations
- [ ] Unit tests for all command/query handlers
- [ ] Integration tests for all endpoints
- [ ] All tests passing (unit + integration)

## Open Questions

None — scope is well-defined from the roadmap description.

## Resolved Decisions

1. **Separate BC:** Risk register is a new `risk_bc` bounded context, not part of `incident_bc`. Risks are organizational concerns broader than security incidents.
2. **Cross-BC links:** Risk links use entity IDs (asset_id, department_id, vendor_id) without foreign keys to maintain BC isolation. Display names resolved at query time.
3. **Risk level calculation:** Deterministic 5x5 matrix, not configurable per company (keeps it simple for v1).
4. **Export reuse:** PDF/CSV export reuses existing `report_bc` infrastructure (WeasyPrint + MinIO).
5. **Review reminders:** Celery beat task checks daily for overdue reviews, creates notification events.
