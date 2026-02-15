# Epic E5: Admin Dashboard

**Type:** Epic
**Status:** Pending Validation
**Created:** 2026-02-15
**Priority:** Medium
**Depends on:** E2 (Asset Inventory), E3 (Service Requests)

---

## Business Alignment

**Objective:** Provide company admins and technicians with a dashboard featuring key operational metrics, visual chart data, and proactive alerts so they can monitor IT operations, identify bottlenecks, and act on urgent issues without manually querying data.

E0-E4 built the complete operational backend: auth, companies, assets, service requests, and notifications. But managers have no way to get a high-level view of IT operations — no summary metrics, no trend data, no alerts for warranty expirations or SLA breaches. E5 delivers the data layer that the frontend dashboard (E7) will visualize.

---

## Problem Statement

### Current Situation
E0-E4 delivered full CRUD and operational workflows. But:
- No summary of open requests by type, priority, or status
- No average resolution time metrics (overall or per technician)
- No asset status breakdown for capacity planning
- No request volume trends over time
- No proactive alerts for expiring warranties
- No aging asset alerts (old equipment that should be replaced)
- No SLA breach detection (requests open too long)
- User management exists (E1) but is not part of a unified admin view

### What E5 Delivers
A dashboard API that provides:
- Request summary metrics (counts by type, priority, status)
- Resolution time analytics (average overall, per technician)
- Asset metrics (counts by status, type)
- Request trend data (volume over time, bucketed by day/week/month)
- Warranty expiration alerts (assets expiring within N days)
- Aging asset alerts (assets older than N years)
- SLA breach alerts (requests open longer than threshold)
- Unified access via admin-only dashboard endpoints

---

## Proposed Solution

### US-E5-001: Request Summary Metrics
**As an** admin
**I want** to see a summary of all open requests by type, priority, and status
**So that** I can understand the current workload

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/requests/summary` returns request counts
- [ ] Breakdown by status (submitted, in_review, in_progress, resolved, rejected)
- [ ] Breakdown by type (incident, new_equipment, onboarding)
- [ ] Breakdown by priority (low, medium, high, urgent)
- [ ] Total open count (submitted + in_review + in_progress)
- [ ] Total resolved count
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E5-002: Resolution Time Analytics
**As an** admin
**I want** to see average resolution time for requests
**So that** I can measure team performance and identify bottlenecks

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/requests/resolution-time` returns resolution metrics
- [ ] Average resolution time overall (in hours)
- [ ] Average resolution time per technician (assigned_to)
- [ ] Only considers resolved/rejected requests (those with resolved_at)
- [ ] Resolution time = resolved_at - created_at
- [ ] Optional filter by date range (from_date, to_date)
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E5-003: Asset Status Metrics
**As an** admin
**I want** to see a breakdown of assets by status and type
**So that** I can plan inventory and replacements

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/assets/summary` returns asset counts
- [ ] Breakdown by status (in_stock, assigned, in_repair, decommissioned)
- [ ] Breakdown by type
- [ ] Total count
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E5-004: Requests Over Time
**As an** admin
**I want** to see request volume trends over time
**So that** I can identify patterns and plan staffing

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/requests/trend` returns time-series data
- [ ] Bucketed by day (default), week, or month (query param `bucket`)
- [ ] Each bucket: period label, total count, breakdown by type
- [ ] Default last 30 days, configurable via from_date/to_date
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E5-005: Warranty Expiration Alerts
**As an** admin
**I want** to see assets with warranties expiring soon
**So that** I can renew warranties or plan replacements before coverage lapses

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/alerts/warranty` returns assets with expiring warranties
- [ ] Default threshold: 30 days from now
- [ ] Configurable via query param `days` (1-365)
- [ ] Only active assets (not decommissioned)
- [ ] Response includes: asset id, brand, model, serial_number, warranty_expiration, assigned_to, days_remaining
- [ ] Sorted by warranty_expiration asc (soonest first)
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E5-006: Aging Asset Alerts
**As an** admin
**I want** to see assets that are aging beyond a threshold
**So that** I can plan replacement cycles

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/alerts/aging` returns old assets
- [ ] Default threshold: 3 years from purchase_date
- [ ] Configurable via query param `years` (1-10)
- [ ] Only active assets (not decommissioned)
- [ ] Response includes: asset id, brand, model, serial_number, purchase_date, age_years, assigned_to
- [ ] Sorted by purchase_date asc (oldest first)
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

### US-E5-007: SLA Breach Alerts
**As an** admin
**I want** to see requests that have been open longer than SLA thresholds
**So that** I can escalate overdue requests

**Acceptance Criteria:**
- [ ] `GET /api/v1/dashboard/alerts/sla` returns overdue requests
- [ ] Hardcoded SLA thresholds by priority:
  - urgent: 4 hours
  - high: 24 hours (1 day)
  - medium: 72 hours (3 days)
  - low: 168 hours (7 days)
- [ ] Only open requests (submitted, in_review, in_progress)
- [ ] Response includes: request id, title, type, priority, status, assigned_to, created_at, hours_open, sla_threshold_hours, breached (boolean)
- [ ] Sorted by hours_open desc (most overdue first)
- [ ] Only admin+ role can access
- [ ] Scoped by company_id

---

## Entities

No new domain entities. E5 is purely a read/query layer over existing data from E2 (assets) and E3 (requests). All metrics are computed at query time via SQL aggregations.

---

## Use Cases

### UC-E5-001: Admin Reviews Dashboard
**Actor:** Admin
**Preconditions:** Logged in with admin+ role

**Main Flow:**
1. Admin opens dashboard
2. System returns request summary, resolution metrics, asset summary
3. Admin reviews metrics, identifies bottlenecks
4. Admin checks alerts for warranty expirations, aging assets, SLA breaches
5. Admin takes action on flagged items

### UC-E5-002: Admin Monitors SLA Compliance
**Actor:** Admin
**Preconditions:** Open requests exist

**Main Flow:**
1. Admin views SLA breach alerts
2. System calculates hours_open for each open request
3. System compares against priority-based SLA thresholds
4. Admin sees list of breached requests sorted by severity
5. Admin escalates or reassigns overdue requests

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `app.py` | Register dashboard router | Update router includes |
| `src/asset_bc/asset/infrastructure/repository.py` | May need new aggregate query methods | Add methods if needed |
| `src/request_bc/request/infrastructure/repository.py` | May need new aggregate query methods | Add methods if needed |
| No migration needed | Queries over existing tables | None |

---

## Bounded Context

E5 does NOT create a new bounded context. Dashboard queries read across existing bounded contexts (asset_bc, request_bc, auth_bc). The dashboard is an adapter-layer concern — a read-only API that aggregates data.

```
adapters/http/api/dashboard/
├── __init__.py
├── routers.py              # All dashboard endpoints (admin+ only)
└── schemas.py              # Response schemas

src/asset_bc/asset/
├── infrastructure/
│   └── repository.py       # Add aggregate query methods (count_by_status, find_expiring_warranties, etc.)

src/request_bc/request/
├── infrastructure/
│   └── repository.py       # Add aggregate query methods (count_by_status, avg_resolution_time, etc.)
```

---

## Technical Decisions

### 1. No New Bounded Context
Dashboard is a cross-cutting read model. Creating a separate dashboard_bc would require duplicating entity definitions. Instead, add aggregate query methods to existing repositories and build the HTTP layer in adapters.

### 2. Query Methods in Repositories (Not Raw SQL in Routers)
Aggregate queries live in existing repositories as new methods. This keeps SQL out of the router layer and makes queries testable.

### 3. Hardcoded SLA Thresholds
SLA thresholds are hardcoded constants, not configurable per company. This keeps v1 simple. Can be moved to company settings later.

### 4. No Caching for v1
Dashboard queries run live against the database. For v1, this is acceptable given expected data volumes. Redis caching can be added later if needed.

### 5. Resolution Time in Hours
Resolution time is calculated as `(resolved_at - created_at)` in hours (float). Displayed as hours for consistency. Frontend can convert to human-readable format.

---

## Definition of Done

- [ ] Request summary endpoint with counts by status, type, priority
- [ ] Resolution time analytics overall and per technician
- [ ] Asset summary with counts by status and type
- [ ] Request trend data bucketed by day/week/month
- [ ] Warranty expiration alerts with configurable threshold
- [ ] Aging asset alerts with configurable threshold
- [ ] SLA breach alerts with hardcoded priority thresholds
- [ ] All endpoints admin+ only, scoped by company_id
- [ ] No new migration required
- [ ] Unit tests for all aggregate query methods
- [ ] Unit tests for all dashboard endpoints

---

## Open Questions

1. **SLA thresholds per company?** **Recommend:** No for v1. Hardcode. Add company_settings table later if needed.
2. **Cache dashboard responses?** **Recommend:** No for v1. Live queries. Add Redis TTL caching if performance becomes an issue.
3. **Include resolved requests in summary?** **Recommend:** Yes — show total resolved alongside open counts for context.
4. **Technician performance ranking?** **Recommend:** Not in v1. Resolution time per technician is sufficient. Ranking/leaderboard is a future feature.
5. **Date range for all metrics?** **Recommend:** Optional from_date/to_date on resolution time and trend. Summary and alerts are always "current state".
