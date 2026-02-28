# Solution Design: Change Dashboard (F3)

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-28
**Complexity:** M

## Architecture Overview

Pure read-only dashboard. No new entities, no new domain logic. Adds a dashboard query handler that aggregates ChangeRequest data using SQL counts/filters, a GET endpoint, and a frontend page.

## Existing Patterns Referenced

- `src/vulnerability_bc/vulnerability/application/queries/vulnerability_dashboard.py` — dashboard query handler
- `adapters/http/api/vulnerabilities/routers.py` — dashboard endpoint (`@router.get("/dashboard")`)
- `web/app/src/pages/admin/SupplyChainDashboardPage.tsx` — frontend dashboard page

## Components

### 1. Repository — Add Dashboard Query Method

**File:** `src/change_bc/change_request/domain/repository.py`

Add abstract method:
```python
@abstractmethod
def get_dashboard_data(
    self, company_id: str
) -> dict: ...
```

**File:** `src/change_bc/change_request/infrastructure/repository.py`

Implement `get_dashboard_data` that returns a dict with:
- `status_counts`: dict[str, int] — count per status (all 8)
- `type_counts`: dict[str, int] — count per type (3)
- `upcoming_scheduled`: list[ChangeRequestModel] — status=scheduled, planned_date in next 30 days, ordered by planned_date ASC, limit 20
- `recently_implemented`: list of dicts — status=implemented or closed with implemented_at in last 30 days, ordered by implemented_at DESC, limit 20. Includes LEFT JOIN to PIR for outcome.
- `rolled_back_90_days`: int — count of rolled_back in last 90 days
- `scheduled_this_week`: int — count with status=scheduled and planned_date within current week

### 2. Application Layer — Dashboard Query Handler

**File:** `src/change_bc/change_request/application/queries/change_dashboard.py`

```python
@dataclass
class UpcomingChangeDto:
    id: str
    title: str
    change_type: str
    planned_date: Optional[datetime]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]

@dataclass
class RecentImplementedDto:
    id: str
    title: str
    change_type: str
    implemented_at: Optional[datetime]
    pir_outcome: Optional[str]

@dataclass
class ChangeDashboardDto:
    total_open: int
    pending_approval: int
    in_progress: int
    implemented: int
    scheduled_this_week: int
    status_counts: dict[str, int]
    type_counts: dict[str, int]
    upcoming_scheduled: list[UpcomingChangeDto]
    recently_implemented: list[RecentImplementedDto]
    rolled_back_90_days: int

@dataclass
class ChangeDashboardQuery(Query):
    company_id: str

class ChangeDashboardQueryHandler(QueryHandler[ChangeDashboardQuery, ChangeDashboardDto]):
    def __init__(self, change_repo, user_name_resolver=None):
        ...
    def handle(self, query) -> ChangeDashboardDto:
        ...
```

### 3. HTTP Layer

**File:** `adapters/http/api/changes/routers.py`

Add `GET /dashboard` endpoint BEFORE `/{change_id}` routes. Admin-only via `require_role(UserRole.ADMIN)`.

**File:** `adapters/http/api/changes/schemas.py`

Add Pydantic response schemas mirroring DTOs.

### 4. Frontend

**File:** `web/app/src/pages/admin/ChangeDashboardPage.tsx`

Standard dashboard page with:
- Summary stat cards (5)
- Status distribution horizontal bar chart
- Type distribution horizontal bar chart
- Upcoming scheduled changes table
- Recently implemented changes table
- Rolled back alert card (conditional)

**File:** `web/app/src/router.tsx` — Add `/changes/dashboard` route before `/changes/:id`
**File:** `web/app/src/config/navSections.ts` — Add nav entry
**Files:** `web/app/src/locales/en.ts`, `es.ts` — i18n keys

## Data Flow

```
Frontend → GET /api/v1/changes/dashboard
  → ChangeDashboardQueryHandler.handle()
    → change_repo.get_dashboard_data(company_id)
    → user_name_resolver (for assigned_to names)
  → Return ChangeDashboardDto → Pydantic response → JSON
```
