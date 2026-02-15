# F1: Asset Metrics + Alert Endpoints

**Epic:** E5 - Admin Dashboard
**Feature:** F1
**Status:** Pending
**Depends on:** F0
**Date:** 2026-02-15

---

## User Stories

### US-E5-003: Asset Status Metrics
**As an** admin, **I want** to see a breakdown of assets by status and type **so that** I can plan inventory and replacements.

### US-E5-005: Warranty Expiration Alerts
**As an** admin, **I want** to see assets with warranties expiring soon **so that** I can renew warranties or plan replacements before coverage lapses.

### US-E5-006: Aging Asset Alerts
**As an** admin, **I want** to see assets that are aging beyond a threshold **so that** I can plan replacement cycles.

---

## Acceptance Criteria

### Asset Summary (`GET /api/v1/dashboard/assets/summary`)
- [ ] Returns counts by status (in_stock, assigned, in_repair, decommissioned)
- [ ] Returns counts by type (laptop, monitor, keyboard, mouse, headset, docking_station, other)
- [ ] Returns total count
- [ ] Admin+ role only
- [ ] Scoped by company_id

### Warranty Alerts (`GET /api/v1/dashboard/alerts/warranty`)
- [ ] Returns assets with warranty expiring within N days
- [ ] Default threshold: 30 days
- [ ] Configurable via query param `days` (1-365)
- [ ] Only active assets (not decommissioned)
- [ ] Response includes: id, brand, model, serial_number, warranty_expiration, assigned_to, days_remaining
- [ ] Sorted by warranty_expiration asc (soonest first)
- [ ] Admin+ role only
- [ ] Scoped by company_id

### Aging Alerts (`GET /api/v1/dashboard/alerts/aging`)
- [ ] Returns assets older than N years from purchase_date
- [ ] Default threshold: 3 years
- [ ] Configurable via query param `years` (1-10)
- [ ] Only active assets (not decommissioned)
- [ ] Response includes: id, brand, model, serial_number, purchase_date, age_years, assigned_to
- [ ] Sorted by purchase_date asc (oldest first)
- [ ] Admin+ role only
- [ ] Scoped by company_id

---

## Dependencies

- F0 must be complete (dashboard router and schemas exist)
- `AssetModel` exists with status, type, warranty_expiration, purchase_date fields
- `AssetStatus.DECOMMISSIONED` enum value exists for exclusion filter
