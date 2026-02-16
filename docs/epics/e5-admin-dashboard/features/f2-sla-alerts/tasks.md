# Tasks: F2 - SLA Breach Alerts

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: SLA Constants + Repository Method

### Task 1.1: Define SLA threshold constants ✅
**File:** `adapters/http/api/dashboard/routers.py` (or a constants section at the top)
- Define `SLA_THRESHOLDS_HOURS` dict mapping priority → hours threshold

### Task 1.2: Add SLA query method to RequestRepositoryInterface ✅
**File:** `src/request_bc/request/domain/repository.py`
- Add abstract method:
  - `find_open_requests_with_age(company_id: str) -> list[dict]`
  - Returns: id, title, type, priority, status, assigned_to, created_at, hours_open

### Task 1.3: Implement SLA query in RequestRepository ✅
**File:** `src/request_bc/request/infrastructure/repository.py`
- Query all open requests (status IN submitted, in_review, in_progress)
- Calculate hours_open = EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600
- Return list of dicts sorted by hours_open DESC

---

## Phase 2: Dashboard Endpoint

### Task 2.1: Add SLA alert endpoint to dashboard router ✅
**File:** `adapters/http/api/dashboard/routers.py`

**Endpoint: GET /alerts/sla**
- Call find_open_requests_with_age(company_id)
- For each result, add sla_threshold_hours from SLA_THRESHOLDS_HOURS[priority]
- Add breached = hours_open > sla_threshold_hours
- Return list[SlaAlertItem]

---

## Phase 3: Tests

### Task 3.1: Unit tests for SLA query method ✅
**File:** `tests/unit/request_bc/request/infrastructure/test_dashboard_queries.py` (append to F0 test file)
- Test find_open_requests_with_age returns only open requests
- Test find_open_requests_with_age excludes resolved/rejected
- Test hours_open calculation is correct
- Mock DB session

### Task 3.2: Unit tests for SLA alert endpoint ✅
**File:** `tests/unit/adapters/http/api/dashboard/test_sla_endpoints.py` (NEW)
- Test GET /alerts/sla returns correct shape
- Test breached flag is true when hours_open > threshold
- Test breached flag is false when within SLA
- Test SLA thresholds match expected values
- Test requires admin role
- Mock repository

---

## Phase 4: Verify

- Run `python -m pytest tests/ -v` — all tests pass
- Verify all 7 dashboard endpoints work correctly
- Run full test suite to confirm no regressions
