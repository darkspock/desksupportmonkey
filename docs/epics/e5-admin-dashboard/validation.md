# Validation: E5 - Admin Dashboard

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Codebase Alignment Check

### Existing Patterns to Follow

| Pattern | Source | Apply to E5 |
|---|---|---|
| Repository with aggregate queries | `src/asset_bc/asset/infrastructure/repository.py` | Add count_by_status, find_expiring_warranties, etc. |
| SQLAlchemy v2 select() + func | `src/request_bc/request/infrastructure/repository.py` | All aggregate queries use select(), func.count(), etc. |
| Router with DI | `adapters/http/api/requests/routers.py` | Dashboard router with require_role(admin) |
| Pydantic response schemas | `adapters/http/api/my/schemas.py` | Dashboard response schemas |
| require_role() dependency | `adapters/http/api/auth/dependencies.py` | `require_role(UserRole.ADMIN)` for all dashboard endpoints |
| Company-scoped queries | All repositories | All dashboard queries filtered by company_id |

### Existing Infrastructure to Reuse

| Component | Location | Usage in E5 |
|---|---|---|
| `get_db` | `core/database.py` | DB session dependency |
| `require_role(UserRole.ADMIN)` | `adapters/http/api/auth/dependencies.py` | All dashboard endpoints admin+ only |
| `AssetModel` | `src/asset_bc/asset/infrastructure/models.py` | Asset aggregate queries (status, type, warranty_expiration, purchase_date) |
| `ServiceRequestModel` | `src/request_bc/request/infrastructure/models.py` | Request aggregate queries (status, type, priority, resolved_at, created_at) |
| `AssetStatus` enum | `src/asset_bc/asset/domain/enums.py` | 4 statuses: in_stock, assigned, in_repair, decommissioned |
| `RequestStatus` enum | `src/request_bc/request/domain/enums.py` | 5 statuses: submitted, in_review, in_progress, resolved, rejected |
| `RequestType` enum | `src/request_bc/request/domain/enums.py` | 3 types: incident, new_equipment, onboarding |
| `RequestPriority` enum | `src/request_bc/request/domain/enums.py` | 4 priorities: low, medium, high, urgent |
| `AssetType` enum | `src/asset_bc/asset/domain/enums.py` | 7 types: laptop, monitor, keyboard, mouse, headset, docking_station, other |
| SQLAlchemy v2 notation | All models/repos | mapped_column(), Mapped[], select(), func |

### Key Decision: No New Bounded Context

Dashboard is a cross-cutting read model. The `adapters/http/api/dashboard/` layer queries existing repositories directly. No new domain entities, no new migrations. Aggregate query methods are added to existing repositories (`AssetRepository`, `RequestRepository`).

### Key Decision: Query Methods in Repositories

All SQL aggregation lives in repository methods (not raw SQL in routers). This keeps queries testable and consistent with existing patterns. The router calls repository methods and formats responses.

### Key Decision: Hardcoded SLA Thresholds

SLA thresholds are Python constants, not database-configurable. Keeps v1 simple:
- urgent: 4 hours
- high: 24 hours
- medium: 72 hours
- low: 168 hours

---

## Dependency Check

### Required from E0 (All Exist)

- [x] FastAPI app with router registration — `app.py`
- [x] Database session dependency (get_db) — `core/database.py`
- [x] JWT authentication — `core/jwt.py`
- [x] RBAC with require_role() — `adapters/http/api/auth/dependencies.py`
- [x] SQLAlchemy v2 patterns — all models and repositories

### Required from E1 (All Exist)

- [x] User model with company_id and role — `src/auth_bc/user/infrastructure/models.py`
- [x] UserRole enum with ADMIN — `src/auth_bc/user/domain/enums.py`
- [x] require_role(UserRole.ADMIN) dependency — `adapters/http/api/auth/dependencies.py`

### Required from E2 (All Exist)

- [x] AssetModel with status, type, warranty_expiration, purchase_date, assigned_to — `src/asset_bc/asset/infrastructure/models.py`
- [x] AssetRepository with find_all — `src/asset_bc/asset/infrastructure/repository.py`
- [x] AssetStatus (in_stock, assigned, in_repair, decommissioned) — `src/asset_bc/asset/domain/enums.py`
- [x] AssetType (7 types) — `src/asset_bc/asset/domain/enums.py`

### Required from E3 (All Exist)

- [x] ServiceRequestModel with status, type, priority, resolved_at, created_at, assigned_to — `src/request_bc/request/infrastructure/models.py`
- [x] RequestRepository with find_all — `src/request_bc/request/infrastructure/repository.py`
- [x] RequestStatus (5 statuses) — `src/request_bc/request/domain/enums.py`
- [x] RequestType (3 types) — `src/request_bc/request/domain/enums.py`
- [x] RequestPriority (4 priorities) — `src/request_bc/request/domain/enums.py`
- [x] resolved_at field on ServiceRequestModel — exists

### No New Tables

Dashboard queries run entirely against existing tables: `assets`, `service_requests`, `users`. No migration needed.

---

## Scope Validation

### In Scope (from roadmap)

- [x] Request summary metrics (counts by status, type, priority)
- [x] Resolution time analytics (overall and per technician)
- [x] Asset status metrics (counts by status and type)
- [x] Request volume trends over time (bucketed by day/week/month)
- [x] Warranty expiration alerts
- [x] Aging asset alerts
- [x] SLA breach alerts

### Not in Scope (deferred)

- Dashboard caching (Redis TTL — future optimization)
- Configurable SLA thresholds per company (future company_settings table)
- Technician performance ranking/leaderboard
- CSV/PDF export of dashboard data (E6 — Report Generation)
- Frontend visualization (E7 — Frontend)

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Dashboard queries may be slow on large datasets | For v1, live queries are acceptable. Add Redis caching or materialized views later |
| Cross-BC queries in adapters/dashboard | Read-only queries via existing repositories, no domain mutations, no coupling |
| SLA threshold changes require code deploy | Acceptable for v1. Company settings table can be added later |
| Date truncation for trend buckets varies by DB | Use SQLAlchemy `func.date_trunc()` (PostgreSQL). Project uses PostgreSQL exclusively |

---

## Observations

### 1. All Required Fields Exist

The models already have all fields needed for E5 queries:
- `ServiceRequestModel`: status, type, priority, resolved_at, created_at, assigned_to, company_id
- `AssetModel`: status, type, warranty_expiration, purchase_date, assigned_to, company_id

No schema changes or migrations required.

### 2. Repository Method Placement

New aggregate methods go into existing repositories:
- `AssetRepository`: count_by_status, count_by_type, find_expiring_warranties, find_aging_assets
- `RequestRepository`: count_by_status, count_by_type, count_by_priority, avg_resolution_time, avg_resolution_time_by_technician, count_by_period

### 3. Dashboard Router Is an Adapter

The dashboard router in `adapters/http/api/dashboard/routers.py` directly instantiates repositories and calls aggregate methods. No command/query handlers needed — these are simple read operations that don't fit the CQRS pattern (no domain logic, just SQL aggregation).

### 4. User Info for Technician Names

Resolution time per technician returns user_ids. The router may need to resolve user names. The `UserRepository.find_by_id()` exists but fetching N users individually is inefficient. Consider adding a `find_by_ids()` batch method or returning user_ids only (let frontend resolve names).

**Recommendation:** Return user_id + user name in resolution time response. Add `find_by_ids()` to UserRepository if needed, or do a simple join in the query.

---

## Estimated Complexity

| Area | Items | Complexity |
|---|---|---|
| Asset aggregate queries | 4 methods (count_by_status, count_by_type, find_expiring, find_aging) | Medium |
| Request aggregate queries | 6 methods (count_by_status/type/priority, avg_resolution, per_technician, trend) | Medium-High |
| Dashboard router | 7 endpoints | Medium |
| Response schemas | 7 Pydantic models | Low |
| Tests | ~30 unit tests for aggregate methods + ~15 endpoint tests | Medium |
| Migration | None | None |

**Overall:** Medium. All data already exists. The complexity is in writing correct SQL aggregations and formatting time-series data.

---

## Validation Result

**Status:** APPROVED — Ready for slicing

All E0-E4 dependencies are in place. Required fields (warranty_expiration, resolved_at, purchase_date) exist on models. No migration needed. Follow existing patterns for repositories and routers. Admin-only access via require_role(UserRole.ADMIN).
