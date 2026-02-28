# Epic E38: Asset Criticality & CMDB

**Date:** 2026-02-26
**Priority:** Medium
**Status:** Pending
**Bounded Context:** `asset_bc` (extends existing `asset` subdomain)

## Business Alignment

**Objective:** Extend the asset inventory with criticality classification, business impact analysis, and Configuration Item (CI) relationship mapping — satisfying NIS2 Article 21(2)(i) asset management requirements, NIS2 Article 21(2)(c) business continuity planning, and enabling criticality-based SLA escalation for incidents affecting critical infrastructure.

**KPI Targets:**
- 100% of critical/high-criticality assets have BIA data (impact score, RTO, RPO)
- 0 orphan critical assets (all critical assets have at least one CI relationship)
- Mean time to identify downstream impact of a critical asset failure < 5 minutes (via dependency graph)
- Criticality-based SLA escalation applied to 100% of incidents linked to critical assets

**Evidence:**
- NIS2 Article 21(2)(i): "human resources security, access control policies and asset management" — requires asset classification and management proportionate to risk
- NIS2 Article 21(2)(c): "business continuity, such as backup management and disaster recovery, and crisis management" — requires understanding which assets are critical for business operations and their recovery priorities
- DORA Article 5-6: "ICT risk management framework" — requires identification and classification of ICT assets supporting critical functions
- ISO 27001 Annex A.5.9: "Inventory of information and other associated assets" — requires asset classification scheme

## Problem Statement

**Current situation:** The platform has a mature asset inventory (E2) with CRUD, assignment, event sourcing, locations (E45), custom fields (E30), and configurable types (E47). However, all assets are treated equally — there is no way to distinguish a critical production server from a spare keyboard. This creates blind spots in incident response and business continuity planning.

| Pain Point | Impact | Regulatory Gap |
|-----------|--------|----------------|
| No asset criticality classification | Cannot prioritize incident response by asset importance | NIS2 Art. 21(2)(i) requires proportionate asset management |
| No business impact analysis per asset | Unknown impact of asset failure on business operations | NIS2 Art. 21(2)(c) requires business continuity planning |
| No dependency mapping between assets | Cannot trace cascading failures (switch failure → all connected devices) | DORA Art. 5 requires identification of ICT assets supporting critical functions |
| No RTO/RPO per asset | Recovery priorities unknown during incidents | NIS2 Art. 21(2)(c) requires disaster recovery planning |
| No criticality-based SLA escalation | Critical asset incidents get same response time as non-critical | Operational risk: slow response to critical failures |
| No CMDB dashboard | No visibility into infrastructure topology and health | Operational gap: no choke-point identification |

**Who is affected:**
- **Admins:** Need to classify assets by criticality and define recovery targets
- **Technicians:** Need to know which assets are critical during incident response and see dependency chains
- **Management/Auditors:** Need CMDB reports for NIS2/DORA compliance evidence, business continuity plans
- **Employees:** Indirectly benefit from faster incident resolution for critical assets

## Existing Foundation

E38 builds on top of what already exists:

| Component | Status | Source |
|-----------|--------|--------|
| Asset CRUD (create, list, get, update, status change) | Done | E2 |
| Asset domain entity (type, brand, model, serial, status) | Done | E2 |
| Asset event sourcing (append-only audit history) | Done | E2 |
| Asset locations (system + custom, movement tracking) | Done | E45 |
| Asset custom fields (JSON, per-company definitions) | Done | E30 |
| Configurable asset types (admin-defined, per-company) | Done | E47 |
| Asset assignment to users with department tracking | Done | E2, E11 |
| RiskLink entity (links risks to assets via link_type=asset) | Done | E37 |
| Incident-asset linking (affected systems) | Done | E36 |
| SLA policies (response/resolution targets by priority) | Done | E19 |
| Vendor dependencies (ICT provider mapping) | Done | E25 |

## Proposed Solution

Extend the `asset_bc/asset` subdomain with new fields, a new CI relationship entity, and a CMDB dashboard:

### 1. Asset Criticality Classification

Add a `criticality` field to the Asset entity with four levels: Critical, High, Medium, Low. Default is `null` (unclassified). Admins and technicians can set/change criticality from the asset detail page.

**Criticality definitions:**
- **Critical:** Asset supports essential business services. Failure causes immediate business disruption. Examples: production database server, core network switch, domain controller.
- **High:** Asset supports important business functions. Failure causes significant impact within hours. Examples: application server, backup system, VPN concentrator.
- **Medium:** Asset supports business operations. Failure causes moderate impact within days. Examples: department printer, secondary workstation, monitoring server.
- **Low:** Asset has minimal business impact. Failure causes inconvenience. Examples: spare equipment, personal peripherals, test devices.

### 2. Business Impact Analysis (BIA)

Per-asset BIA data stored as fields on the Asset entity:
- `impact_score` (1-10): Business impact severity if asset becomes unavailable. 1 = negligible, 10 = catastrophic.
- `rto_minutes` (Recovery Time Objective): Maximum acceptable downtime in minutes before business impact becomes unacceptable.
- `rpo_minutes` (Recovery Point Objective): Maximum acceptable data loss in minutes (for data-bearing assets).
- `bia_justification` (text): Free-text explanation of why this criticality and impact score were assigned.
- `bia_reviewed_at` (datetime): When BIA was last reviewed.
- `bia_reviewed_by` (user_id): Who last reviewed BIA.

BIA is optional but encouraged for Critical/High assets. The CMDB dashboard shows an "overdue reviews" table listing assets whose BIA review is older than 6 months — no Celery task or push notifications for BIA reviews.

### 3. Configuration Item (CI) Relationships

A new `CIRelationship` entity maps directional relationships between assets:

**Relationship types:**
- `runs_on`: Software/service runs on hardware (e.g., App Server runs_on Physical Server)
- `depends_on`: Asset requires another to function (e.g., App depends_on Database Server)
- `connected_to`: Network or physical connection (e.g., Workstation connected_to Switch)
- `part_of`: Component is part of a larger system (e.g., RAM Module part_of Server)
- `backs_up`: Asset provides backup/redundancy (e.g., Backup Server backs_up Primary Server)

**Directionality:** Relationships have a `source_asset_id` and `target_asset_id`. The source is the dependent, the target is the dependency. Example: "App Server (source) depends_on (type) Database Server (target)".

**Constraints:**
- Both assets must belong to the same company
- No self-referencing (source != target)
- No duplicate relationships (same source, target, and type)
- Decommissioned assets cannot be added as targets (but existing relationships are preserved for history)
- Optional `description` field for relationship notes (editable after creation via PATCH)

**Delete strategy:** Hard delete. The audit trail is preserved in AssetEvent (`ci_relationship_deleted` event). Once deleted, the relationship row is removed from the database.

### 4. Impact Propagation

When querying dependencies, the system can trace upstream and downstream chains:
- **Downstream impact (what breaks if this asset fails):** Follow all relationships where this asset is the target (other assets depend on it). Recursive traversal up to configurable depth (default: 5 levels).
- **Upstream dependencies (what this asset needs to work):** Follow all relationships where this asset is the source. Shows all dependencies.
- **Impact radius:** Count of unique assets in the downstream chain, grouped by criticality level.

This is a **read-only query** — no automatic state changes. Useful for incident impact assessment.

### 5. Affected Assets on Service Requests

When a technician picks up a service request, the request detail page shows the requester's assigned assets. The technician can mark one or more assets as "affected" — these are stored in the request's existing `data` JSON field as `data.affected_asset_ids: string[]`. No migration or entity change needed on the request side.

This enables criticality-based SLA escalation: when SLA targets are calculated, the system looks up the affected assets from `data.affected_asset_ids` and checks their criticality level.

### 6. Criticality-Based SLA Escalation

Integrate with the SLA BC to adjust response/resolution targets based on asset criticality:
- When a service request has affected assets (stored in `data.affected_asset_ids`), the system looks up their criticality.
- If any affected asset has criticality = CRITICAL, the SLA priority is escalated by one level (e.g., Medium → High priority SLA targets apply).
- When any affected asset has criticality = HIGH and the request priority is LOW, escalate to MEDIUM.
- Escalation is logged in the request audit trail.
- Admin can disable criticality-based escalation per company (opt-in by default).

**Implementation:** The SLA check query already receives the request's priority. The escalation hook reads `data.affected_asset_ids`, fetches asset criticality, and adjusts the effective priority used for SLA target lookup. This is a read-time adjustment — the request's actual priority field is not modified.

### 7. CMDB Dashboard

A new dashboard page showing infrastructure topology health:

**Summary cards:**
- Total assets by criticality level (Critical / High / Medium / Low / Unclassified)
- Orphan critical assets (criticality=Critical but zero CI relationships — data quality alert)
- Average BIA coverage for Critical/High assets (% with impact_score + RTO set)
- Total CI relationships

**Tables/Charts:**
- Most-depended-upon assets (top 10 by incoming relationship count) — infrastructure choke points
- Assets with highest impact scores and their downstream counts
- Recent BIA reviews (last 30 days) and overdue reviews
- CI relationships by type (bar chart)

### User Stories

**US1:** As an admin, I can set the criticality level of an asset (Critical/High/Medium/Low), so I can classify assets by business importance for NIS2 compliance.

**US2:** As an admin, I can record Business Impact Analysis data (impact score, RTO, RPO, justification) for an asset, so recovery priorities are documented for business continuity planning.

**US3:** As a technician, I can create a CI relationship between two assets (e.g., "App Server depends_on Database Server"), so infrastructure dependencies are mapped.

**US4:** As a technician, I can view the dependency graph for an asset (upstream dependencies and downstream impact), so I can assess the blast radius of an incident.

**US5:** As a technician, when viewing a service request, I can see the requester's assigned assets and mark which ones are affected, so the request is linked to specific assets for impact analysis.

**US6:** As a technician, when I view a service request linked to a critical asset, the SLA targets reflect the escalated priority, so critical asset incidents get faster response.

**US7:** As an admin, I can view the CMDB dashboard with criticality distribution, orphan alerts, and choke-point analysis, so I can maintain infrastructure topology health.

**US8:** As a technician, I can see an asset's criticality badge and BIA summary on the asset detail page, so I immediately know its business importance during incident response.

**US9:** As an admin, I can list and filter assets by criticality level, so I can quickly find all critical infrastructure assets for compliance audits.

**US10:** As a technician, I can edit the description of an existing CI relationship, so I can update notes without deleting and recreating the relationship.

## Entities

| Entity | Description | New/Extend |
|--------|-------------|------------|
| Asset | Add criticality, BIA fields | Extend |
| CIRelationship | Directional relationship between two assets | New |
| AssetEvent | Audit trail for criticality/BIA changes | Extend (new event types) |

### Entity: Asset (Extended Fields)

New fields added to existing Asset entity:
- `criticality: Optional[AssetCriticality]` — enum: CRITICAL, HIGH, MEDIUM, LOW. Default: null (unclassified).
- `impact_score: Optional[int]` — 1-10 scale. Nullable.
- `rto_minutes: Optional[int]` — Recovery Time Objective. Nullable.
- `rpo_minutes: Optional[int]` — Recovery Point Objective. Nullable.
- `bia_justification: Optional[str]` — Free text. Nullable.
- `bia_reviewed_at: Optional[datetime]` — Last BIA review timestamp. Nullable.
- `bia_reviewed_by: Optional[str]` — User ID of reviewer. Nullable.

### Entity: CIRelationship (New)

| Field | Type | Description |
|-------|------|-------------|
| id | str (ULID) | Primary key |
| company_id | str | Multi-tenancy scope |
| source_asset_id | str | The dependent asset (FK → assets) |
| target_asset_id | str | The dependency asset (FK → assets) |
| relationship_type | CIRelationshipType | Enum: runs_on, depends_on, connected_to, part_of, backs_up |
| description | Optional[str] | Notes about this relationship |
| created_at | Optional[datetime] | Auto-set |
| created_by | str | User ID who created the relationship |

**Constraints:**
- UNIQUE(source_asset_id, target_asset_id, relationship_type)
- source_asset_id != target_asset_id
- Both assets must belong to same company_id

### New Enums

**AssetCriticality:**
```
CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"
```

**CIRelationshipType:**
```
RUNS_ON = "runs_on"
DEPENDS_ON = "depends_on"
CONNECTED_TO = "connected_to"
PART_OF = "part_of"
BACKS_UP = "backs_up"
```

### New Event Types (AssetEvent)

- `criticality_set` — Criticality level changed. Data: `{old_criticality, new_criticality}`
- `bia_updated` — BIA fields changed. Data: `{impact_score, rto_minutes, rpo_minutes, justification}`
- `ci_relationship_created` — CI relationship added. Data: `{relationship_id, target_asset_id, type}`
- `ci_relationship_deleted` — CI relationship removed. Data: `{relationship_id, target_asset_id, type}`

## Use Cases

### UC-001: Set Asset Criticality

**Actor:** Admin or Technician
**Preconditions:** Asset exists and is not decommissioned
**Postconditions:** Criticality field updated, event recorded

**Main Flow:**
1. User navigates to asset detail page
2. Clicks "Set Criticality" button
3. Selects criticality level from dropdown (Critical/High/Medium/Low)
4. System saves criticality, records AssetEvent `criticality_set`
5. Asset detail page shows criticality badge

**Alternative Flows:**
- User clears criticality (sets to null/unclassified)

**Error Scenarios:**
- Asset not found → 404
- Asset is decommissioned → 422 "Cannot modify decommissioned asset"

### UC-002: Record BIA Data

**Actor:** Admin
**Preconditions:** Asset exists and is not decommissioned
**Postconditions:** BIA fields updated, event recorded, review timestamp set

**Main Flow:**
1. User navigates to asset detail page
2. Opens BIA section
3. Enters impact_score (1-10), RTO (minutes), RPO (minutes), justification
4. System saves fields, sets bia_reviewed_at = now, bia_reviewed_by = current user
5. Records AssetEvent `bia_updated`

**Validation:**
- impact_score must be 1-10
- rto_minutes must be > 0
- rpo_minutes must be >= 0

**Error Scenarios:**
- Invalid impact_score (out of range) → 422
- Asset not found → 404

### UC-003: Create CI Relationship

**Actor:** Technician or Admin
**Preconditions:** Both assets exist, belong to same company, neither is the same asset
**Postconditions:** Relationship created, events recorded on both assets

**Main Flow:**
1. User navigates to asset detail page → "Dependencies" tab
2. Clicks "Add Relationship"
3. Selects relationship type from dropdown
4. Searches and selects target asset
5. Optionally adds description
6. System validates constraints, creates relationship
7. Records AssetEvent on source asset `ci_relationship_created`

**Alternative Flows:**
- Create relationship from "reverse" direction (from target asset, choosing source)

**Error Scenarios:**
- Target asset not found → 404
- Same asset as source and target → 422 "Self-referencing not allowed"
- Duplicate relationship → 409 "Relationship already exists"
- Target asset is decommissioned → 422 "Cannot create relationship to decommissioned asset"

### UC-004: View Dependency Graph

**Actor:** Technician or Admin
**Preconditions:** Asset exists
**Postconditions:** None (read-only)

**Main Flow:**
1. User navigates to asset detail page → "Dependencies" tab
2. System shows two sections:
   - **Upstream dependencies:** Assets this one depends on (source relationships)
   - **Downstream impact:** Assets that depend on this one (target relationships)
3. Each section shows relationship type, asset name/serial, criticality badge
4. Impact radius summary: count of downstream assets by criticality level

### UC-005: View CMDB Dashboard

**Actor:** Admin
**Preconditions:** None
**Postconditions:** None (read-only)

**Main Flow:**
1. User navigates to CMDB Dashboard via sidebar
2. System loads dashboard data:
   - Criticality distribution (card per level)
   - Orphan critical assets count
   - BIA coverage percentage
   - Most-depended-upon assets table
   - Overdue BIA reviews table
3. Data refreshes on page load (no caching)

### UC-006: Mark Affected Assets on Request

**Actor:** Technician
**Preconditions:** Service request exists, requester has assigned assets
**Postconditions:** Affected asset IDs stored in request's `data.affected_asset_ids`

**Main Flow:**
1. Technician opens request detail page
2. System shows the requester's assigned assets (fetched from asset_bc by `assigned_to = request.created_by`)
3. Technician checks one or more assets as "affected"
4. System saves `data.affected_asset_ids = ["asset1", "asset2"]` on the request
5. Affected assets appear as badges/links on the request detail page

**Alternative Flows:**
- Technician unchecks an asset (removes from affected list)
- Request has no assigned assets for requester → section shows "No assets assigned to requester"

**Error Scenarios:**
- Asset not found → skip silently (may have been decommissioned)

### UC-007: SLA Escalation Check

**Actor:** System (automatic)
**Preconditions:** Service request exists, SLA policy configured, affected assets marked
**Postconditions:** Effective SLA priority may differ from request priority

**Main Flow:**
1. When SLA targets are calculated for a request, system reads `data.affected_asset_ids`
2. System fetches criticality for each affected asset
3. If any affected asset has criticality = CRITICAL, effective priority escalates one level
4. If any affected asset has criticality = HIGH and request priority is LOW, escalate to MEDIUM
5. Escalated priority is used for SLA target lookup only — request priority field unchanged
6. SLA response indicates whether escalation was applied

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Asset entity/model | Add 7 new nullable fields | Migration: add columns with defaults |
| Asset detail page (frontend) | Add criticality badge, BIA section, dependencies tab | Extend existing page |
| Asset list page (frontend) | Add criticality filter and column | Extend existing page |
| Request detail page (frontend) | Add "Affected Assets" section showing requester's assets with checkboxes | Extend existing page |
| SLA query handler | Read data.affected_asset_ids, fetch criticality, adjust effective priority | Modify get_request_sla query |
| Dashboard (admin) | No impact — separate CMDB dashboard page | New page |
| Asset CSV import | Optionally support criticality column | Minor extension |
| MCP server asset tools | Expose criticality field in responses | Update existing tool |
| Risk BC | No changes — existing RiskLink already supports asset linking | No action |
| Incident BC | No changes — incidents already link to assets | No action |

## Definition of Done

- [ ] Asset criticality field (CRITICAL/HIGH/MEDIUM/LOW) settable from asset detail
- [ ] BIA fields (impact_score, RTO, RPO, justification) recordable per asset
- [ ] BIA review tracking (reviewed_at, reviewed_by) auto-set on save
- [ ] CIRelationship CRUD: create, list, update (description), delete (hard) between assets
- [ ] Relationship type enum: runs_on, depends_on, connected_to, part_of, backs_up
- [ ] Constraint enforcement: no self-reference, no duplicates, same company
- [ ] Upstream/downstream dependency queries with configurable depth
- [ ] Impact radius calculation (downstream count by criticality)
- [ ] Affected assets on requests: technician marks affected assets from requester's equipment (stored in data.affected_asset_ids)
- [ ] Criticality-based SLA escalation (Critical→+1, High+Low→Medium) using affected_asset_ids
- [ ] CMDB dashboard: criticality distribution, orphans, BIA coverage, choke points
- [ ] Asset detail: criticality badge, BIA section, dependencies tab
- [ ] Asset list: criticality filter + column
- [ ] Event sourcing: criticality_set, bia_updated, ci_relationship_created/deleted events
- [ ] Migration: new fields on assets table + new ci_relationships table
- [ ] Unit tests for all commands, queries, and domain logic
- [ ] Integration tests for all new endpoints
- [ ] i18n EN/ES for all new UI strings
- [ ] TypeScript types updated

## Time Constraints

**Deadline:** N/A
**Type:** None
**Calendar Conflicts:** None

## Open Questions

None — all validation questions resolved:
- **SLA escalation / request-asset link:** Technician marks affected assets from requester's equipment, stored in `data.affected_asset_ids` JSON field. No request_bc entity change needed.
- **BIA review reminders:** Dashboard-only (overdue reviews table). No Celery task.
- **CIRelationship delete:** Hard delete. Audit trail in AssetEvent.
- **CIRelationship update:** Description editable via PATCH endpoint.
