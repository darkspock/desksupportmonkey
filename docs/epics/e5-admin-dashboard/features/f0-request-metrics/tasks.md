# Tasks: F0 - Request Metrics + Dashboard Router

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Repository Aggregate Methods

### Task 1.1: Add aggregate methods to RequestRepositoryInterface
**File:** `src/request_bc/request/domain/repository.py`
- Add abstract methods:
  - `count_by_status(company_id: str) -> dict[str, int]`
  - `count_by_type(company_id: str) -> dict[str, int]`
  - `count_by_priority(company_id: str) -> dict[str, int]`
  - `avg_resolution_time(company_id: str, from_date: date | None, to_date: date | None) -> float | None`
  - `avg_resolution_time_by_technician(company_id: str, from_date: date | None, to_date: date | None) -> list[dict]`
  - `count_by_period(company_id: str, bucket: str, from_date: date, to_date: date) -> list[dict]`

### Task 1.2: Implement aggregate methods in RequestRepository
**File:** `src/request_bc/request/infrastructure/repository.py`
- `count_by_status`: SELECT status, COUNT(*) GROUP BY status. Return dict with all statuses (default 0).
- `count_by_type`: SELECT type, COUNT(*) GROUP BY type. Return dict with all types (default 0).
- `count_by_priority`: SELECT priority, COUNT(*) GROUP BY priority. Return dict with all priorities (default 0).
- `avg_resolution_time`: AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600) WHERE resolved_at IS NOT NULL. Optional date filters on resolved_at.
- `avg_resolution_time_by_technician`: Same as above but GROUP BY assigned_to WHERE assigned_to IS NOT NULL. Return list of dicts with technician_id, avg_hours, resolved_count.
- `count_by_period`: Use `func.date_trunc(bucket, created_at)` for PostgreSQL. GROUP BY period, type. Return list of dicts with period, type, count.

---

## Phase 2: Dashboard Schemas

### Task 2.1: Create dashboard response schemas
**File:** `adapters/http/api/dashboard/schemas.py` (NEW)
- `RequestStatusCounts` — counts for each of the 5 statuses
- `RequestTypeCounts` — counts for each of the 3 types
- `RequestPriorityCounts` — counts for each of the 4 priorities
- `RequestSummaryResponse` — by_status, by_type, by_priority, total_open, total_resolved
- `TechnicianResolutionTime` — technician_id, avg_hours, resolved_count
- `ResolutionTimeResponse` — avg_hours (float | None), by_technician (list)
- `TrendBucketTypeCounts` — counts per request type
- `TrendBucket` — period (str), total (int), by_type
- `RequestTrendResponse` — bucket, from_date, to_date, data (list of TrendBucket)
- Also define schemas for F1/F2 endpoints (asset summary, warranty alert, aging alert, SLA alert) to keep everything in one file

### Task 2.2: Create dashboard __init__.py
**File:** `adapters/http/api/dashboard/__init__.py` (NEW)

---

## Phase 3: Dashboard Router

### Task 3.1: Create dashboard router with 3 request endpoints
**File:** `adapters/http/api/dashboard/routers.py` (NEW)
- Router prefix: `/api/v1/dashboard`
- All endpoints depend on `require_role(UserRole.ADMIN)`

**Endpoint 1: GET /requests/summary**
- Instantiate RequestRepository(db)
- Call count_by_status, count_by_type, count_by_priority
- Calculate total_open = submitted + in_review + in_progress
- Calculate total_resolved from status counts
- Return RequestSummaryResponse

**Endpoint 2: GET /requests/resolution-time**
- Query params: from_date (optional date), to_date (optional date)
- Call avg_resolution_time and avg_resolution_time_by_technician
- Return ResolutionTimeResponse

**Endpoint 3: GET /requests/trend**
- Query params: bucket (day|week|month, default "day"), from_date (optional), to_date (optional)
- Default date range: last 30 days
- Call count_by_period
- Transform raw data into TrendBucket list (aggregate type counts per period)
- Return RequestTrendResponse

### Task 3.2: Register dashboard router in app.py
**File:** `app.py`
- Import dashboard router
- `application.include_router(dashboard_router)`

---

## Phase 4: Tests

### Task 4.1: Unit tests for request aggregate methods
**File:** `tests/unit/request_bc/request/infrastructure/test_dashboard_queries.py` (NEW)
- Test count_by_status returns dict with all statuses, defaults to 0
- Test count_by_type returns dict with all types, defaults to 0
- Test count_by_priority returns dict with all priorities, defaults to 0
- Test avg_resolution_time returns float hours for resolved requests
- Test avg_resolution_time returns None when no resolved requests
- Test avg_resolution_time with date filter
- Test avg_resolution_time_by_technician groups correctly
- Test count_by_period returns bucketed data
- All tests mock the DB session and execute results

### Task 4.2: Unit tests for dashboard endpoints
**File:** `tests/unit/adapters/http/api/dashboard/test_request_endpoints.py` (NEW)
- Test GET /requests/summary returns correct shape
- Test GET /requests/resolution-time returns correct shape
- Test GET /requests/resolution-time with date params
- Test GET /requests/trend returns correct shape
- Test GET /requests/trend with bucket param
- Test all endpoints require admin role (403 for employee/technician)
- Mock repositories in all tests

---

## Phase 5: Verify

- Run `python -m pytest tests/ -v` — all tests pass
- Verify no regressions in existing tests
