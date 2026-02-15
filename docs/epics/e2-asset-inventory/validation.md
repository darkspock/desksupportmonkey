# Validation: E2 - Asset Inventory

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Codebase Alignment Check

### Existing Patterns to Follow

| Pattern | Source | Apply to E2 |
|---|---|---|
| Entity as dataclass | `src/company_bc/company/domain/entities.py` | Asset, AssetEvent entities |
| Repository interface (ABC) | `src/company_bc/company/domain/repository.py` | AssetRepositoryInterface |
| Enum with transitions | `src/company_bc/company/domain/enums.py` | AssetType, AssetStatus with VALID_TRANSITIONS |
| ULIDMixin + TimestampMixin | `core/mixins.py` | AssetModel |
| ULIDMixin only (no updated_at) | `src/auth_bc/magic_link/infrastructure/models.py` | AssetEventModel (immutable) |
| Command + Handler pattern | `src/company_bc/company/application/commands/` | All asset commands |
| Query + Handler pattern | `src/company_bc/company/application/queries/` | All asset queries |
| Router with DI | `adapters/http/api/departments/routers.py` | Asset routes using `current_user` directly (not tenant context vars) |
| Pydantic schemas | `adapters/http/api/companies/schemas.py` | Asset request/response schemas |
| Pagination with PaginationMeta | `adapters/http/schemas/responses.py` | List endpoints |
| Error mapping in router | `adapters/http/api/companies/routers.py` | Domain errors -> HTTP errors |

### Existing Infrastructure to Reuse

| Component | Location | Usage in E2 |
|---|---|---|
| `get_db` | `core/database.py` | DB session dependency |
| `require_role()` | `adapters/http/api/auth/dependencies.py` | `require_role(UserRole.TECHNICIAN)` for most endpoints |
| `get_current_user` | `adapters/http/api/auth/dependencies.py` | For `my/equipment` endpoint |
| `UserRepository` | `src/auth_bc/user/infrastructure/repository.py` | Validate user exists on assignment |
| `models_registry.py` | `core/models_registry.py` | Register AssetModel, AssetEventModel |

### Key Decision: Use `current_user` Not Tenant Context

From E1-F2 implementation: `contextvars.ContextVar` doesn't reliably propagate across threads in uvicorn. All routers must use `current_user.company_id` and `current_user.id` directly from dependency injection.

---

## Dependency Check

### Required from E1 (All Exist)
- [x] Company model with status — `src/company_bc/company/infrastructure/models.py`
- [x] User model with department_id — `src/auth_bc/user/infrastructure/models.py`
- [x] Department model — `src/company_bc/department/infrastructure/models.py`
- [x] UserRepository.find_by_id_and_company() — `src/auth_bc/user/infrastructure/repository.py`
- [x] RBAC with technician role — `adapters/http/api/auth/dependencies.py`

### New Bounded Context
- `asset_bc` is entirely new — no existing code to conflict with
- ForeignKey references: companies.id, users.id, departments.id (all exist)

---

## Scope Validation

### In Scope (from roadmap)
- [x] Asset CRUD (technician)
- [x] Asset types, statuses, serial numbers
- [x] Asset assignment/unassignment to employees
- [x] Asset event sourcing (append-only history log)
- [x] Asset search and filters
- [x] CSV bulk import
- [x] "My Equipment" view (employee)

### Not in Scope (deferred to later epics)
- Asset-to-request linking (E3)
- Warranty expiration alerts (E5)
- Asset inventory report PDF (E6)
- Asset dashboard metrics (E5)

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Event sourcing adds complexity | Keep dual-write: mutable Asset table for reads + append-only events for audit. Don't derive state from events (CQRS read model is the Asset table itself) |
| CSV import could be slow for large files | Process rows sequentially in a single request. 1MB limit keeps it manageable. If needed later, move to Celery task |
| JSON data column in events varies by type | Use typed Python dicts with clear schemas per event_type. Validate at domain layer |
| Asset-department auto-sync on assign | Keep it simple: copy user's department_id to asset on assign |

---

## Estimated Complexity

| Area | Items | Complexity |
|---|---|---|
| Domain entities | 2 (Asset, AssetEvent) + 2 enums | Medium |
| Repository | 1 interface + 1 implementation | Medium |
| Commands | 6 (create, update, assign, unassign, status change, import) | High |
| Queries | 4 (list, get, history, my equipment) | Medium |
| HTTP routes | 2 routers (assets, my) + schemas | Medium |
| Migration | 1 (2 tables) | Low |
| Tests | ~50 unit tests | Medium |

**Overall:** Medium-High. The event sourcing pattern and CSV import add complexity beyond standard CRUD.

---

## Validation Result

**Status:** APPROVED - Ready for slicing

All E1 dependencies are in place. The `asset_bc` bounded context is isolated. Follow established patterns from E1 (entities, repos, commands, routers). Use `current_user` pattern in routers (not tenant context vars).
