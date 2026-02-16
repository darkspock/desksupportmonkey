# Tasks: F2 - Departments + User Management

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Create Department entity ✅
- **File:** `src/company_bc/department/domain/entities.py` (NEW)
- Dataclass: `id`, `company_id`, `name`, `is_active`, `created_at`, `updated_at`
- `create(company_id, name)`: validates name not empty, generates ULID, is_active=True
- `deactivate()`: sets is_active=False
- `update_name(name)`: validates not empty, updates name

### T1.2: Create DepartmentRepositoryInterface ✅
- **File:** `src/company_bc/department/domain/repository.py` (NEW)
- ABC with: `save()`, `find_by_id(id, company_id)`, `find_by_name(name, company_id)`, `find_all(company_id, page, page_size, include_inactive)`, `count_users(department_id)`

### T1.3: Extend User entity with department_id ✅
- **File:** `src/auth_bc/user/domain/entities.py` (MODIFY)
- Add `department_id: Optional[str] = None`
- Add `activate()` method (sets is_active=True)
- Add `assign_department(department_id: Optional[str])` method
- Update `create()` to accept optional `department_id`

### T1.4: Extend UserRepositoryInterface ✅
- **File:** `src/auth_bc/user/domain/repository.py` (MODIFY)
- Add: `find_all_by_company(company_id, page, page_size, role, is_active, department_id, search) -> tuple[list[User], int]`
- Add: `find_by_id_and_company(user_id, company_id) -> Optional[User]`
- Add: `count_by_department(department_id) -> int`

### T1.5: Create __init__.py files ✅
- Create all necessary `__init__.py` files for new packages:
  - `src/company_bc/department/__init__.py`
  - `src/company_bc/department/domain/__init__.py`
  - `src/company_bc/department/application/__init__.py`
  - `src/company_bc/department/application/commands/__init__.py`
  - `src/company_bc/department/application/queries/__init__.py`
  - `src/company_bc/department/infrastructure/__init__.py`
  - `adapters/http/api/departments/__init__.py`
  - `adapters/http/api/users/__init__.py`

---

## Phase 2: Infrastructure Layer

### T2.1: Create DepartmentModel ✅
- **File:** `src/company_bc/department/infrastructure/models.py` (NEW)
- `DepartmentModel(ULIDMixin, TimestampMixin, Base)`:
  - `__tablename__ = "departments"`
  - `company_id`: String(26), FK to companies.id, NOT NULL, indexed
  - `name`: String(255), NOT NULL
  - `is_active`: Boolean, default True, NOT NULL
  - UniqueConstraint("company_id", "name")

### T2.2: Add department_id to UserModel ✅
- **File:** `src/auth_bc/user/infrastructure/models.py` (MODIFY)
- Add `department_id = Column(String(26), ForeignKey("departments.id"), nullable=True, index=True)`

### T2.3: Update models_registry.py ✅
- **File:** `core/models_registry.py` (MODIFY)
- Add import for `DepartmentModel`

### T2.4: Create Alembic migration ✅
- Run `alembic revision --autogenerate -m "add_departments_and_user_department"`
- Verify: creates departments table, adds department_id to users, correct indexes and FK constraints
- Test upgrade + downgrade

### T2.5: Implement DepartmentRepository ✅
- **File:** `src/company_bc/department/infrastructure/repository.py` (NEW)
- Implements DepartmentRepositoryInterface
- `save()`: upsert pattern
- `find_by_id(id, company_id)`: filter by both id AND company_id
- `find_by_name(name, company_id)`: case-insensitive within company
- `find_all()`: pagination, optional include_inactive filter
- `count_users()`: COUNT from users where department_id matches
- `_to_entity()`: model to entity conversion

### T2.6: Extend UserRepository ✅
- **File:** `src/auth_bc/user/infrastructure/repository.py` (MODIFY)
- Add `find_all_by_company()`: query with filters (role, is_active, department_id, search via ilike on email/name), pagination
- Add `find_by_id_and_company()`: filter by id + company_id
- Add `count_by_department()`: COUNT where department_id matches
- Update `save()` to include department_id
- Update `_to_entity()` to include department_id

---

## Phase 3: Application Layer - Departments

### T3.1: CreateDepartmentCommand + Handler ✅
- **File:** `src/company_bc/department/application/commands/create_department.py` (NEW)
- Command: `company_id`, `name`
- Handler: validate name uniqueness → `DepartmentNameExistsError`, create entity, save, return
- Define `DepartmentNameExistsError`

### T3.2: UpdateDepartmentCommand + Handler ✅
- **File:** `src/company_bc/department/application/commands/update_department.py` (NEW)
- Command: `department_id`, `company_id`, `name`
- Handler: find → `DepartmentNotFoundError`, validate name uniqueness (exclude self) → `DepartmentNameExistsError`, update, save, return
- Define `DepartmentNotFoundError`

### T3.3: DeleteDepartmentCommand + Handler ✅
- **File:** `src/company_bc/department/application/commands/delete_department.py` (NEW)
- Command: `department_id`, `company_id`
- Handler: find → `DepartmentNotFoundError`, check user count → `DepartmentHasUsersError`, soft delete, save, return
- Define `DepartmentHasUsersError`

### T3.4: ListDepartmentsQuery + Handler ✅
- **File:** `src/company_bc/department/application/queries/list_departments.py` (NEW)
- Query: `company_id`, `page`, `page_size`, `include_inactive`
- Handler: calls `department_repo.find_all()`

### T3.5: GetDepartmentQuery + Handler ✅
- **File:** `src/company_bc/department/application/queries/get_department.py` (NEW)
- Query: `department_id`, `company_id`
- Handler: find → `DepartmentNotFoundError`, get user_count, return

---

## Phase 4: Application Layer - User Management

### T4.1: ChangeUserRoleCommand + Handler ✅
- **File:** `src/auth_bc/user/application/commands/change_user_role.py` (NEW)
- Command: `user_id`, `company_id`, `current_user_id`, `new_role` (str)
- Handler:
  1. Find user by id + company_id → `UserNotFoundError`
  2. Check user_id != current_user_id → `CannotChangeSelfError`
  3. Validate role is not super_admin → `CannotAssignSuperAdminError`
  4. Convert to UserRole enum → ValueError if invalid
  5. Call user.change_role(), save, return
- Define error classes

### T4.2: DeactivateUserCommand + Handler ✅
- **File:** `src/auth_bc/user/application/commands/deactivate_user.py` (NEW)
- Command: `user_id`, `company_id`, `current_user_id`
- Handler:
  1. Find user → `UserNotFoundError`
  2. Check user_id != current_user_id → `CannotDeactivateSelfError`
  3. Deactivate, save, return

### T4.3: ActivateUserCommand + Handler ✅
- **File:** `src/auth_bc/user/application/commands/activate_user.py` (NEW)
- Command: `user_id`, `company_id`
- Handler: find → `UserNotFoundError`, activate, save, return

### T4.4: AssignDepartmentCommand + Handler ✅
- **File:** `src/auth_bc/user/application/commands/assign_department.py` (NEW)
- Command: `user_id`, `company_id`, `department_id` (nullable)
- Handler:
  1. Find user → `UserNotFoundError`
  2. If department_id:
     a. Find department → `DepartmentNotFoundError`
     b. Validate same company → `DepartmentNotFoundError`
     c. Validate is_active → `DepartmentInactiveError`
  3. Assign department, save, return
- Define `DepartmentInactiveError`

### T4.5: ListUsersQuery + Handler ✅
- **File:** `src/auth_bc/user/application/queries/list_users.py` (NEW)
- Query: `company_id`, `page`, `page_size`, `role`, `is_active`, `department_id`, `search`
- Handler: calls `user_repo.find_all_by_company()`

### T4.6: GetUserDetailQuery + Handler ✅
- **File:** `src/auth_bc/user/application/queries/get_user_detail.py` (NEW)
- Query: `user_id`, `company_id`
- Handler: find by id + company → `UserNotFoundError`

---

## Phase 5: HTTP Layer - Departments

### T5.1: Create department schemas ✅
- **File:** `adapters/http/api/departments/schemas.py` (NEW)
- `CreateDepartmentRequest`: name (str, min 1, max 255)
- `UpdateDepartmentRequest`: name (str, min 1, max 255)
- `DepartmentResponse`: id, company_id, name, is_active, created_at, updated_at
- `DepartmentDetailResponse(DepartmentResponse)`: + user_count

### T5.2: Create department router ✅
- **File:** `adapters/http/api/departments/routers.py` (NEW)
- POST /api/v1/departments → create_department
- GET /api/v1/departments → list_departments
- GET /api/v1/departments/{id} → get_department
- PUT /api/v1/departments/{id} → update_department
- DELETE /api/v1/departments/{id} → delete_department
- All use `require_role(UserRole.ADMIN)`
- Get company_id from `get_tenant_company_id()`
- Map domain errors to HTTP errors

---

## Phase 6: HTTP Layer - Users

### T6.1: Create user management schemas ✅
- **File:** `adapters/http/api/users/schemas.py` (NEW)
- `ChangeRoleRequest`: role (str)
- `AssignDepartmentRequest`: department_id (Optional[str])
- `UserDetailResponse`: id, email, name, role, company_id, department_id, is_active, created_at, updated_at

### T6.2: Create user management router ✅
- **File:** `adapters/http/api/users/routers.py` (NEW)
- GET /api/v1/users → list_users
- GET /api/v1/users/{id} → get_user
- PATCH /api/v1/users/{id}/role → change_role
- PATCH /api/v1/users/{id}/deactivate → deactivate_user
- PATCH /api/v1/users/{id}/activate → activate_user
- PATCH /api/v1/users/{id}/department → assign_department
- All use `require_role(UserRole.ADMIN)`
- Get company_id and current_user_id from tenant context
- Map domain errors to HTTP errors

### T6.3: Register routers in app.py ✅
- **File:** `app.py` (MODIFY)
- Add department and user routers

---

## Phase 7: Tests

### T7.1: Unit tests - Department entity ✅
- **File:** `tests/unit/company_bc/department/domain/test_entities.py` (NEW)
- Test create with valid data
- Test create with empty name → ValueError
- Test deactivate
- Test update_name
- Test update_name with empty → ValueError

### T7.2: Unit tests - Department commands ✅
- **File:** `tests/unit/company_bc/department/application/commands/test_commands.py` (NEW)
- Create: success, duplicate name
- Update: success, not found, duplicate name
- Delete: success, not found, has users

### T7.3: Unit tests - Department queries ✅
- **File:** `tests/unit/company_bc/department/application/queries/test_queries.py` (NEW)
- List: returns paginated
- Get: success, not found

### T7.4: Unit tests - User management commands ✅
- **File:** `tests/unit/auth_bc/user/application/commands/test_user_commands.py` (NEW)
- Change role: success, not found, self, super_admin target
- Deactivate: success, not found, self
- Activate: success, not found
- Assign department: success, null (unassign), department not found, department inactive

### T7.5: Unit tests - User queries ✅
- **File:** `tests/unit/auth_bc/user/application/queries/test_user_queries.py` (NEW)
- List with filters
- Get detail: success, not found

### T7.6: Unit tests - Extended User entity ✅
- **File:** `tests/unit/auth_bc/user/domain/test_entities.py` (MODIFY)
- Add test for activate()
- Add test for assign_department()

---

## Phase 8: Verification

### T8.1: Run all tests ✅
- `make test` — all tests pass

### T8.2: Run migration ✅
- `alembic upgrade head`
- Verify departments table + users.department_id column

### T8.3: Manual verification ✅
1. Login as admin
2. Create department → verify response
3. List departments → verify pagination
4. Update department name → verify
5. List users → verify filters work
6. Change user role → verify
7. Assign user to department → verify
8. Try delete department with users → 409
9. Unassign user from department → verify
10. Delete department → verify soft delete
11. Try access from different company → 404 (tenant isolation)

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.5 | 2 + inits | 2 (user entity, user repo interface) |
| 2. Infrastructure | T2.1-T2.6 | 2 (model, repo) + migration | 3 (user model, models_registry, user repo) |
| 3. App - Depts | T3.1-T3.5 | 5 | — |
| 4. App - Users | T4.1-T4.6 | 6 | — |
| 5. HTTP - Depts | T5.1-T5.2 | 2 + init | — |
| 6. HTTP - Users | T6.1-T6.3 | 2 + init | 1 (app.py) |
| 7. Tests | T7.1-T7.6 | 5 | 1 (existing user entity tests) |
| 8. Verification | T8.1-T8.3 | — | — |
