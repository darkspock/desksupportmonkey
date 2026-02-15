# Slicing: E5 - Admin Dashboard

**Epic:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-02-15

---

## Feature Breakdown

| Feature | Description | User Stories | Complexity |
|---|---|---|---|
| **F0** | Request Metrics + Dashboard Router | US-E5-001, US-E5-002, US-E5-004 | Medium-High |
| **F1** | Asset Metrics + Alert Endpoints | US-E5-003, US-E5-005, US-E5-006 | Medium |
| **F2** | SLA Breach Alerts | US-E5-007 | Low-Medium |

---

## F0: Request Metrics + Dashboard Router

**Scope:** Dashboard router setup, request summary metrics, resolution time analytics, request trend data.

**Why F0:** The dashboard router and request metrics are the highest-value deliverables. Request summary and resolution time give admins immediate visibility into workload and performance. The trend endpoint provides time-series data for pattern identification. Establishing the router in F0 lets subsequent features just add endpoints.

**Includes:**
- `adapters/http/api/dashboard/routers.py` — dashboard router with admin-only access
- `adapters/http/api/dashboard/schemas.py` — all response schemas (including for F1/F2)
- Request aggregate methods in `RequestRepository`:
  - `count_by_status(company_id)` — counts per status
  - `count_by_type(company_id)` — counts per type
  - `count_by_priority(company_id)` — counts per priority
  - `avg_resolution_time(company_id, from_date?, to_date?)` — overall average hours
  - `avg_resolution_time_by_technician(company_id, from_date?, to_date?)` — per assigned_to
  - `count_by_period(company_id, bucket, from_date, to_date)` — time-series data
- Register dashboard router in `app.py`
- Unit tests for all aggregate methods
- Unit tests for 3 endpoints

**Endpoints:**
- `GET /api/v1/dashboard/requests/summary`
- `GET /api/v1/dashboard/requests/resolution-time`
- `GET /api/v1/dashboard/requests/trend`

---

## F1: Asset Metrics + Alert Endpoints

**Scope:** Asset summary metrics, warranty expiration alerts, aging asset alerts.

**Why F1:** Asset metrics complement request metrics for a complete dashboard view. Warranty and aging alerts are proactive — they help admins take action before problems occur. These are natural groupings since they all query the AssetModel.

**Depends on:** F0 (dashboard router and schemas must exist)

**Includes:**
- Asset aggregate methods in `AssetRepository`:
  - `count_by_status(company_id)` — counts per status
  - `count_by_type(company_id)` — counts per type
  - `find_expiring_warranties(company_id, days)` — assets with warranty expiring within N days
  - `find_aging_assets(company_id, years)` — assets older than N years
- 3 dashboard endpoints for asset metrics and alerts
- Unit tests for all aggregate methods
- Unit tests for 3 endpoints

**Endpoints:**
- `GET /api/v1/dashboard/assets/summary`
- `GET /api/v1/dashboard/alerts/warranty`
- `GET /api/v1/dashboard/alerts/aging`

---

## F2: SLA Breach Alerts

**Scope:** SLA breach detection endpoint with priority-based thresholds.

**Why F2:** SLA alerts require calculating hours_open in real-time for all open requests, then comparing against priority-based thresholds. This is separated from F0 because it's a distinct concept (operational alerts vs. metrics) and has its own data shape (request details + SLA comparison).

**Depends on:** F0 (dashboard router must exist)

**Includes:**
- SLA threshold constants
- Request method in `RequestRepository`:
  - `find_sla_breaches(company_id)` — open requests exceeding their priority SLA threshold
- 1 dashboard endpoint for SLA alerts
- Unit tests for breach detection logic
- Unit tests for endpoint

**Endpoints:**
- `GET /api/v1/dashboard/alerts/sla`

---

## Dependency Graph

```
F0: Request Metrics + Dashboard Router
 ├── F1: Asset Metrics + Alert Endpoints
 └── F2: SLA Breach Alerts
```

F1 and F2 are independent of each other but both depend on F0 (the dashboard router and schema foundation). They can be implemented in either order or even in parallel.

---

## Implementation Order

1. **F0** — Dashboard router, request summary, resolution time, trend data
2. **F1** — Asset summary, warranty alerts, aging alerts
3. **F2** — SLA breach alerts

---

## Migration Strategy

**No migration needed.** E5 is a purely read-only query layer over existing tables (assets, service_requests). All aggregate queries use SQL functions (COUNT, AVG, date_trunc) against existing columns.
