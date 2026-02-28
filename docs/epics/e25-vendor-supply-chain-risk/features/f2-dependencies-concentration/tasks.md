# Tasks: F2 — Dependencies & Concentration Risk

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-26

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: VendorDependency entity, repository interface | S | Domain |
| 2 | Infrastructure: VendorDependencyModel | S | Infra |
| 3 | Infrastructure: Alembic migration | S | Infra |
| 4 | Infrastructure: VendorDependency repository implementation | M | Infra |
| 5 | Application: CreateDependencyCommand + handler | S | App |
| 6 | Application: UpdateDependencyCommand + handler | S | App |
| 7 | Application: SoftDeleteDependencyCommand + handler | S | App |
| 8 | Application: ListDependenciesQuery + handler | S | App |
| 9 | Application: ConcentrationRiskQuery + handler | M | App |
| 10 | HTTP: dependency schemas | S | HTTP |
| 11 | HTTP: dependency router + dependencies | M | HTTP |
| 12 | HTTP: concentration risk endpoint | S | HTTP |
| 13 | HTTP: Register router in app.py | S | HTTP |
| 14 | Unit tests: domain entity | S | Test |
| 15 | Unit tests: command handlers | S | Test |
| 16 | Unit tests: query handlers + concentration calculation | M | Test |
| 17 | Integration tests: dependency + concentration endpoints | M | Test |
| 18 | Frontend: TypeScript types | S | FE |
| 19 | Frontend: i18n EN/ES translations for dependencies | S | FE |

## Detailed Tasks

### Phase 1: Domain

#### Task 1: VendorDependency entity, repository interface
- **Files:**
  - `src/procurement_bc/vendor/domain/entities.py` (add VendorDependency)
  - `src/procurement_bc/vendor/domain/repository.py` (add VendorDependencyRepositoryInterface)
- **What:**
  - `VendorDependency` entity with `create()` factory, `update()`, `soft_delete()`. Validates service_description non-empty, business_function valid enum.
  - `VendorDependencyRepositoryInterface` ABC: save, find_by_id, find_all_by_vendor (paginated), soft_delete, find_all_critical_by_company (for concentration risk)
  - Exception: `DependencyNotFoundError`
- **Acceptance:** Entity and repo interface defined
- [x] Done

### Phase 2: Infrastructure

#### Task 2: ORM model
- **File:** `src/procurement_bc/vendor/infrastructure/models.py` (add)
- **What:** `VendorDependencyModel` with Mapped[] annotations. is_deleted default false. Indexes: (vendor_id, company_id), (company_id, is_critical).
- **Deps:** Task 1
- **Acceptance:** Model defined with proper indexes
- [x] Done

#### Task 3: Alembic migration
- **File:** `alembic/versions/` (new migration)
- **What:** Create `vendor_dependencies` table with all columns and indexes.
- **Deps:** Task 2
- **Acceptance:** Migration runs up and down cleanly
- [x] Done

#### Task 4: Repository implementation
- **File:** `src/procurement_bc/vendor/infrastructure/repository.py` (extend)
- **What:** Implement `VendorDependencyRepositoryInterface`: save, find_by_id (is_deleted=false), find_all_by_vendor (paginated, is_deleted=false), soft_delete, find_all_critical_by_company (is_critical=true, is_deleted=false, joins vendor for name).
- **Deps:** Tasks 1-3
- **Acceptance:** All methods work
- [x] Done

### Phase 3: Application

#### Task 5: CreateDependencyCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/create_dependency.py`
- **What:** `CreateDependencyCommand(vendor_id, company_id, service_description, business_function, is_critical)`. Handler validates vendor exists, creates dependency, saves.
- **Deps:** Task 4
- **Acceptance:** Dependency created
- [x] Done

#### Task 6: UpdateDependencyCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/update_dependency.py`
- **What:** `UpdateDependencyCommand(dependency_id, vendor_id, company_id, service_description?, business_function?, is_critical?)`. Handler finds, updates, saves.
- **Deps:** Task 4
- **Acceptance:** Updates allowed fields
- [x] Done

#### Task 7: SoftDeleteDependencyCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/soft_delete_dependency.py`
- **What:** `SoftDeleteDependencyCommand(dependency_id, vendor_id, company_id)`. Marks deleted.
- **Deps:** Task 4
- **Acceptance:** Dependency soft-deleted
- [x] Done

#### Task 8: ListDependenciesQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/list_dependencies.py`
- **What:** `ListDependenciesQuery(vendor_id, company_id, page, page_size)`. Returns `tuple[list[DependencyDto], int]`.
- **Deps:** Task 4
- **Acceptance:** Returns paginated list
- [x] Done

#### Task 9: ConcentrationRiskQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/concentration_risk.py`
- **What:** `ConcentrationRiskQuery(company_id)`. Handler: fetch all critical dependencies (is_critical=true, is_deleted=false), group by vendor_id, calculate percentage of total critical dependencies per vendor. Return list of `ConcentrationRiskDto(vendor_id, vendor_name, critical_count, total_critical, percentage, is_above_threshold)` where threshold=40%.
- **Deps:** Task 4
- **Acceptance:** Correct percentage calculation, flags vendors above 40%
- [x] Done

### Phase 4: HTTP

#### Task 10: Dependency schemas
- **File:** `adapters/http/api/vendors/dependency_schemas.py` (new)
- **What:** `CreateDependencyRequest`, `UpdateDependencyRequest`, `DependencyResponse`, `DependencyListResponse`, `ConcentrationRiskResponse`, `ConcentrationRiskItemResponse`.
- **Deps:** Tasks 5-9
- **Acceptance:** All schemas defined
- [x] Done

#### Task 11: Dependency router + dependencies
- **File:** `adapters/http/api/vendors/dependency_router.py` (new), `adapters/http/api/vendors/dependency_dependencies.py` (new)
- **What:** POST create, GET list, PUT update, DELETE soft-delete. Auth: create/update/delete = admin, list = technician+.
- **Deps:** Task 10
- **Acceptance:** All endpoints working
- [x] Done

#### Task 12: Concentration risk endpoint
- **File:** `adapters/http/api/vendors/dependency_router.py` (add endpoint)
- **What:** GET `/api/v1/vendors/concentration-risk`. Admin only. Returns concentration risk analysis.
- **Deps:** Task 11
- **Acceptance:** Returns correct concentration data
- [x] Done

#### Task 13: Register router in app.py
- **File:** `app.py` (extend)
- **What:** Include dependency_router under vendors prefix.
- **Deps:** Task 11
- **Acceptance:** Router registered
- [x] Done

### Phase 5: Tests

#### Task 14: Unit tests — domain entity
- **File:** `tests/unit/procurement_bc/vendor/domain/test_dependency_entities.py` (new)
- **What:** Test VendorDependency.create validation, update, soft_delete.
- **Acceptance:** Domain logic covered
- [x] Done

#### Task 15: Unit tests — command handlers
- **File:** `tests/unit/procurement_bc/vendor/application/commands/test_dependency_commands.py` (new)
- **What:** Test Create, Update, SoftDelete command handlers. Mock repos.
- **Acceptance:** All handlers tested
- [x] Done

#### Task 16: Unit tests — query handlers + concentration
- **File:** `tests/unit/procurement_bc/vendor/application/queries/test_dependency_queries.py` (new)
- **What:** Test ListDependenciesQueryHandler, ConcentrationRiskQueryHandler. Concentration test cases: single vendor 100% (above threshold), two vendors 50/50 (above), three vendors 40/30/30 (at threshold), no critical deps (empty result).
- **Acceptance:** All query handlers tested, concentration edge cases covered
- [x] Done

#### Task 17: Integration tests — dependency + concentration endpoints
- **File:** `tests/integration/test_vendor_dependencies_endpoints.py` (new)
- **What:** Create dependency (201), list (200), update (200), soft delete (204), concentration risk (200). Auth checks. Tenant isolation.
- **Acceptance:** All endpoints tested with real DB
- [x] Done

### Phase 6: Frontend

#### Task 18: TypeScript types
- **File:** `web/app/src/types/index.ts`
- **What:** Add `VendorDependency`, `ConcentrationRiskItem` interfaces.
- **Acceptance:** Types defined
- [x] Done

#### Task 19: i18n EN/ES translations
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** Dependency-related keys: business function names, criticality labels, concentration risk labels, form fields.
- **Acceptance:** All strings translated EN + ES
- [x] Done
