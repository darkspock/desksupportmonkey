# Tasks: F0 — Department Managers

## Implementation Tasks

### 1. Domain Changes
- [x] Add `manager_user_id: Optional[str]` to `Department` entity in `src/company_bc/department/domain/entities.py`
- [x] Add `manager_user_id` column to `DepartmentModel` (FK to `users.id`, nullable, SET NULL on delete)
- [x] Create migration: `ALTER TABLE departments ADD COLUMN manager_user_id VARCHAR(26) REFERENCES users(id) ON DELETE SET NULL`

### 2. Commands
- [x] Create `AssignDepartmentManager` command + handler in `src/company_bc/department/application/commands/assign_manager.py`
  - Validates: department exists, user exists, same company, user is active
  - Sets `department.manager_user_id = user_id`
- [x] Create `RemoveDepartmentManager` command + handler in `src/company_bc/department/application/commands/remove_manager.py`
  - Sets `department.manager_user_id = None`

### 3. Query Updates
- [x] Update `get_department` query to include `manager_user_id`, `manager_email`, `manager_name`
- [x] Update `list_departments` query to include manager info

### 4. API Endpoints
- [x] Add `PUT /api/v1/departments/{id}/manager` — body: `{ user_id: str }` — Admin only
- [x] Add `DELETE /api/v1/departments/{id}/manager` — Admin only
- [x] Update department response schemas to include manager fields

### 5. Unit Tests
- [x] `tests/unit/company_bc/department/application/commands/test_manager.py`
  - test_assign_manager_success
  - test_assign_manager_department_not_found
  - test_assign_manager_user_not_found
  - test_assign_manager_cross_company_rejected
  - test_assign_manager_user_inactive_rejected
  - test_remove_manager_success
  - test_remove_manager_no_current_manager (idempotent)

### 6. Integration Tests
- [x] Add manager tests to `tests/integration/test_departments_endpoints.py`
  - test_assign_manager_admin_success
  - test_remove_manager_admin_success
  - test_assign_manager_forbidden_employee

### 7. Verification
- [x] Lint passes
- [x] New tests pass
- [x] Full unit suite passes (`make test`) — 604 passed
- [x] Full integration suite passes (`make test-integration`) — 139 passed (1 pre-existing failure unrelated to F0)

### 8. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F0 status to Done
