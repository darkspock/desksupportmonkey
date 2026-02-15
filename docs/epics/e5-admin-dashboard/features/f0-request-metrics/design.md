# Design: F0 - Request Metrics + Dashboard Router

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture

E5 does not create a new bounded context. The dashboard is an adapter-layer concern — a read-only API that aggregates data from existing bounded contexts.

```
adapters/http/api/dashboard/
├── __init__.py
├── routers.py              # All dashboard endpoints (admin+ only)
└── schemas.py              # Response schemas for all E5 endpoints
```

---

## Repository Methods (Added to RequestRepository)

### count_by_status(company_id) -> dict[str, int]
```sql
SELECT status, COUNT(*) FROM service_requests WHERE company_id = ? GROUP BY status
```

### count_by_type(company_id) -> dict[str, int]
```sql
SELECT type, COUNT(*) FROM service_requests WHERE company_id = ? GROUP BY type
```

### count_by_priority(company_id) -> dict[str, int]
```sql
SELECT priority, COUNT(*) FROM service_requests WHERE company_id = ? GROUP BY priority
```

### avg_resolution_time(company_id, from_date?, to_date?) -> float | None
```sql
SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600)
FROM service_requests
WHERE company_id = ? AND resolved_at IS NOT NULL
  [AND resolved_at >= from_date]
  [AND resolved_at <= to_date]
```

### avg_resolution_time_by_technician(company_id, from_date?, to_date?) -> list[dict]
```sql
SELECT assigned_to, AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600) as avg_hours, COUNT(*) as resolved_count
FROM service_requests
WHERE company_id = ? AND resolved_at IS NOT NULL AND assigned_to IS NOT NULL
  [AND resolved_at >= from_date]
  [AND resolved_at <= to_date]
GROUP BY assigned_to
```

### count_by_period(company_id, bucket, from_date, to_date) -> list[dict]
```sql
SELECT date_trunc(bucket, created_at) as period, type, COUNT(*)
FROM service_requests
WHERE company_id = ? AND created_at >= from_date AND created_at <= to_date
GROUP BY period, type
ORDER BY period ASC
```

---

## Schemas

### RequestSummaryResponse
```python
class StatusCounts(BaseModel):
    submitted: int
    in_review: int
    in_progress: int
    resolved: int
    rejected: int

class TypeCounts(BaseModel):
    incident: int
    new_equipment: int
    onboarding: int

class PriorityCounts(BaseModel):
    low: int
    medium: int
    high: int
    urgent: int

class RequestSummaryResponse(BaseModel):
    by_status: StatusCounts
    by_type: TypeCounts
    by_priority: PriorityCounts
    total_open: int
    total_resolved: int
```

### ResolutionTimeResponse
```python
class TechnicianResolution(BaseModel):
    technician_id: str
    avg_hours: float
    resolved_count: int

class ResolutionTimeResponse(BaseModel):
    avg_hours: float | None
    by_technician: list[TechnicianResolution]
```

### RequestTrendResponse
```python
class TrendBucketType(BaseModel):
    incident: int
    new_equipment: int
    onboarding: int

class TrendBucket(BaseModel):
    period: str
    total: int
    by_type: TrendBucketType

class RequestTrendResponse(BaseModel):
    bucket: str
    from_date: str
    to_date: str
    data: list[TrendBucket]
```

---

## Router

All endpoints under `APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])`.

Each endpoint:
1. Depends on `require_role(UserRole.ADMIN)` for authorization
2. Instantiates the relevant repository with the DB session
3. Calls aggregate methods
4. Returns Pydantic response

---

## Design Decisions

### 1. No Command/Query Handlers
Dashboard endpoints are simple read operations — they don't fit the CQRS command/query handler pattern used for domain mutations. The router directly calls repository aggregate methods.

### 2. All Schemas in One File
All E5 response schemas live in `adapters/http/api/dashboard/schemas.py`. This keeps F1 and F2 simple — they just add endpoints to the existing router and use schemas already defined.

### 3. date_trunc for PostgreSQL
The trend endpoint uses `func.date_trunc()` which is PostgreSQL-specific. The project uses PostgreSQL exclusively (docker-compose.yml), so this is acceptable.

### 4. Resolution Time Precision
Resolution time is returned as a float in hours (e.g., 24.5 hours). Frontend can convert to human-readable format.
