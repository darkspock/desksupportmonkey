# Validation: E3 - Service Requests

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Codebase Alignment Check

### Existing Patterns to Follow

| Pattern | Source | Apply to E3 |
|---|---|---|
| Entity as dataclass | `src/asset_bc/asset/domain/entities.py` | ServiceRequest, RequestComment, RequestNote, RequestEvent |
| Repository interface (ABC) | `src/asset_bc/asset/domain/repository.py` | RequestRepositoryInterface |
| Enum with transitions | `src/asset_bc/asset/domain/enums.py` | RequestType, RequestStatus, RequestPriority with VALID_TRANSITIONS |
| ULIDMixin + TimestampMixin | `core/mixins.py` | ServiceRequestModel |
| ULIDMixin only (no updated_at) | `src/auth_bc/magic_link/infrastructure/models.py` | RequestCommentModel, RequestNoteModel, RequestEventModel (immutable) |
| Command + Handler pattern | `src/asset_bc/asset/application/commands/create_asset.py` | All request commands |
| Query + Handler pattern | `src/asset_bc/asset/application/queries/list_assets.py` | All request queries |
| Router with DI | `adapters/http/api/assets/routers.py` | Request routes using `current_user` directly |
| Pydantic schemas | `adapters/http/api/assets/schemas.py` | Request/comment/note schemas |
| Pagination with PaginationMeta | `adapters/http/schemas/responses.py` | List endpoints |
| Error mapping in router | `adapters/http/api/assets/routers.py` | Domain errors → HTTP errors |
| Append-only events | `src/asset_bc/asset/domain/entities.py` (AssetEvent) | RequestEvent (same immutable pattern) |
| My router extension | `adapters/http/api/my/routers.py` | Add My Requests alongside My Equipment |

### Existing Infrastructure to Reuse

| Component | Location | Usage in E3 |
|---|---|---|
| `get_db` | `core/database.py` | DB session dependency |
| `require_role()` | `adapters/http/api/auth/dependencies.py` | `require_role(UserRole.TECHNICIAN)` for queue, `require_role(UserRole.EMPLOYEE)` for creation |
| `get_current_user` | `adapters/http/api/auth/dependencies.py` | For My Requests, comment authoring |
| `UserRepository` | `src/auth_bc/user/infrastructure/repository.py` | Validate assigned technician exists |
| `AssetRepository` | `src/asset_bc/asset/infrastructure/repository.py` | Validate asset_id on incident requests (optional) |
| `models_registry.py` | `core/models_registry.py` | Register all 4 new models |
| `PaginationMeta` | `adapters/http/schemas/responses.py` | Paginated list responses |
| SQLAlchemy v2 notation | All models | `mapped_column()`, `Mapped[]`, `select()` |

### Key Decision: Use `current_user` Not Tenant Context

From E1-F2 / E2 implementation: `contextvars.ContextVar` doesn't reliably propagate across threads in uvicorn. All routers must use `current_user.company_id` and `current_user.id` directly from dependency injection.

### Key Decision: Store Type-Specific Data in JSON

For incident (asset_id), new_equipment (equipment_type), and onboarding (employee_name, start_date, department_id), store in a `data` JSON column on ServiceRequest. This keeps the entity generic and avoids coupling request_bc to asset_bc via foreign keys.

---

## Dependency Check

### Required from E0 (All Exist)

- [x] FastAPI app with router registration — `app.py`
- [x] Base model classes (ULIDMixin, TimestampMixin) — `core/mixins.py`
- [x] Database session dependency (get_db) — `core/database.py`
- [x] JWT authentication — `core/jwt.py`
- [x] RBAC with role hierarchy — `adapters/http/api/auth/dependencies.py`
- [x] Error handler middleware — `adapters/http/middleware/error_handler.py`

### Required from E1 (All Exist)

- [x] Company model with status — `src/company_bc/company/infrastructure/models.py`
- [x] User model with company_id, department_id — `src/auth_bc/user/infrastructure/models.py`
- [x] UserRepository.find_by_id_and_company() — `src/auth_bc/user/infrastructure/repository.py`
- [x] UserRole enum (EMPLOYEE, TECHNICIAN, ADMIN, SUPER_ADMIN) — `src/auth_bc/user/domain/enums.py`
- [x] Department model — `src/company_bc/department/infrastructure/models.py`

### Required from E2 (All Exist)

- [x] Asset model — `src/asset_bc/asset/infrastructure/models.py`
- [x] AssetRepository.find_by_id(asset_id, company_id) — `src/asset_bc/asset/infrastructure/repository.py`
- [x] AssetEvent pattern (append-only events) — to replicate for RequestEvent
- [x] My router — `adapters/http/api/my/routers.py` (to extend with My Requests)

### New Bounded Context

- `request_bc` is entirely new — no existing code to conflict with
- ForeignKey references: companies.id, users.id (all exist)
- No FK to assets table (asset_id stored in JSON data field — loose coupling)

---

## Scope Validation

### In Scope (from roadmap)

- [x] Request creation (employee): incident, new_equipment, onboarding
- [x] Request state machine: submitted → in_review → in_progress → resolved/rejected
- [x] Automatic priority based on type
- [x] Technician queue (claim/self-assign)
- [x] Comments (employee + technician)
- [x] Internal notes (technician only)
- [x] "My Requests" view (employee)

### Not in Scope (deferred to later epics)

- Real-time notifications on status change (E4)
- WebSocket push on new comments (E4)
- Request metrics and resolution time analytics (E5)
- Request summary PDF reports (E6)
- Frontend UI for requests (E7)

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| State machine adds complexity | Follow same pattern as AssetStatus transitions (dict-based VALID_TRANSITIONS). Keep it in the domain entity |
| Comment visibility (employee vs technician) | Separate tables (RequestComment vs RequestNote) — simpler than a visibility flag on a shared table |
| Employee access control on requests | Employee can only see own requests (filter by created_by). Technician sees all in company. Enforce in query/router layer |
| Request-asset coupling | Store asset_id in JSON data field, not FK. Keeps request_bc independent of asset_bc |
| Priority ordering in queue | Use numeric priority mapping (urgent=4, high=3, medium=2, low=1) for ORDER BY. Store enum string, sort by mapped value |
| 4 new tables in one migration | All tables are independent (only FK to existing tables). Single migration is fine |

---

## Observations

### 1. Auto-assignment on status change
When a technician moves a request to `in_review`, if the request is unassigned, the system should auto-assign it to the acting technician. This should be handled in the `change_status` command handler, not in the domain entity (it's an application-level side effect).

### 2. Employee request visibility
The `GET /api/v1/requests/{id}` endpoint must check: if the current user is an employee, they can only see their own requests. If technician+, they can see any request in their company. This is a router-level check, not a domain concern.

### 3. Comment vs Note — separate entities, separate endpoints
Using separate tables (RequestComment, RequestNote) instead of a single table with a `visibility` flag is cleaner:
- No risk of accidentally exposing internal notes to employees
- Simpler queries (no WHERE clause on visibility)
- Follows YAGNI — no need for flexible visibility in v1

### 4. Request events vs comments/notes
RequestEvent tracks system-level mutations (status_changed, assigned, priority_changed). Comments and notes are user-generated content — different concerns. Keeping them in separate tables is correct.

### 5. Resolved_at timestamp
Setting `resolved_at` when status changes to `resolved` or `rejected` is useful for resolution time metrics in E5. This should be set in the domain entity's `change_status` method.

---

## Estimated Complexity

| Area | Items | Complexity |
|---|---|---|
| Domain entities | 4 (ServiceRequest, RequestComment, RequestNote, RequestEvent) + 3 enums | Medium |
| Repository | 1 interface + 1 implementation (many query methods) | Medium-High |
| Commands | 6 (create, change_status, change_priority, assign, add_comment, add_note) | High |
| Queries | 5 (list, get, list_comments, list_notes, my_requests) | Medium |
| HTTP routes | 2 routers (requests, extend my) + schemas | Medium |
| Migration | 1 (4 tables) | Low |
| Tests | ~60 unit tests | Medium |

**Overall:** High. The state machine, multi-entity interactions (request + comments + notes + events), and access control rules make this the most complex epic so far.

---

## Validation Result

**Status:** APPROVED — Ready for slicing

All E0, E1, and E2 dependencies are in place. The `request_bc` bounded context is isolated. Follow established patterns from E2 (entities, repos, commands, events, routers). Use `current_user` pattern in routers. Store type-specific data in JSON field. Use separate tables for comments and notes.
