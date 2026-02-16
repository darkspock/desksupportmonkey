# Tasks: F1 - Asset Metrics + Alert Endpoints

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Repository Aggregate Methods

### Task 1.1: Add aggregate methods to AssetRepositoryInterface ✅
**File:** `src/asset_bc/asset/domain/repository.py`
- Add abstract methods:
  - `count_by_status(company_id: str) -> dict[str, int]`
  - `count_by_type(company_id: str) -> dict[str, int]`
  - `find_expiring_warranties(company_id: str, days: int) -> list[dict]`
  - `find_aging_assets(company_id: str, years: int) -> list[dict]`

### Task 1.2: Implement aggregate methods in AssetRepository ✅
**File:** `src/asset_bc/asset/infrastructure/repository.py`
- `count_by_status`: GROUP BY status, return dict with all 4 AssetStatus values defaulting to 0
- `count_by_type`: GROUP BY type, return dict with all 7 AssetType values defaulting to 0
- `find_expiring_warranties`: Filter active assets with warranty_expiration between now and now+N days. Return list of dicts with id, brand, model, serial_number, warranty_expiration, assigned_to, days_remaining. Sorted by warranty_expiration ASC.
- `find_aging_assets`: Filter active assets with purchase_date older than N years. Return list of dicts with id, brand, model, serial_number, purchase_date, age_years, assigned_to. Sorted by purchase_date ASC.

---

## Phase 2: Dashboard Endpoints

### Task 2.1: Add asset and alert endpoints to dashboard router ✅
**File:** `adapters/http/api/dashboard/routers.py`

**Endpoint 1: GET /assets/summary**
- Instantiate AssetRepository(db)
- Call count_by_status and count_by_type
- Calculate total = sum of all status counts
- Return AssetSummaryResponse

**Endpoint 2: GET /alerts/warranty**
- Query param: days (int, default 30, ge=1, le=365)
- Call find_expiring_warranties(company_id, days)
- Return list[WarrantyAlertItem]

**Endpoint 3: GET /alerts/aging**
- Query param: years (int, default 3, ge=1, le=10)
- Call find_aging_assets(company_id, years)
- Return list[AgingAlertItem]

---

## Phase 3: Tests

### Task 3.1: Unit tests for asset aggregate methods ✅
**File:** `tests/unit/asset_bc/asset/infrastructure/test_dashboard_queries.py` (NEW)
- Test count_by_status returns all statuses with defaults
- Test count_by_type returns all types with defaults
- Test find_expiring_warranties filters correctly
- Test find_expiring_warranties excludes decommissioned
- Test find_aging_assets filters correctly
- Test find_aging_assets excludes decommissioned
- Mock DB session

### Task 3.2: Unit tests for dashboard asset/alert endpoints ✅
**File:** `tests/unit/adapters/http/api/dashboard/test_asset_endpoints.py` (NEW)
- Test GET /assets/summary returns correct shape
- Test GET /alerts/warranty returns list with correct fields
- Test GET /alerts/warranty with custom days param
- Test GET /alerts/aging returns list with correct fields
- Test GET /alerts/aging with custom years param
- Test all endpoints require admin role
- Mock repositories

---

## Phase 4: Verify

- Run `python -m pytest tests/ -v` — all tests pass
- Verify no regressions
