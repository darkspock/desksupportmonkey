# Tasks: F1 — Priority Scoring

## Implementation Tasks

### 1. Department Priority Weight — Domain
- [x] Edit `src/company_bc/department/domain/entities.py`
  - Add `priority_weight: int` field (default 0)
  - Add validation: must be in range -1 to +2

### 2. Department Priority Weight — Infrastructure
- [x] Edit `src/company_bc/department/infrastructure/models.py`
  - Add `priority_weight: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")`
- [x] Edit `src/company_bc/department/infrastructure/repository.py`
  - Update `_to_entity()` and `_to_model()` to include `priority_weight`

### 3. Department Priority Weight — Migration
- [x] Create `alembic/versions/g2b3c4d5e6f7_add_department_priority_weight.py`
  - Add `priority_weight` column (`INTEGER NOT NULL DEFAULT 0`) to `departments` table

### 4. Department Priority Weight — Command
- [x] Edit `src/company_bc/department/application/commands/update_department.py`
  - Add `priority_weight: Optional[int] = None` to `UpdateDepartmentCommand`
  - Apply if provided, validate range -1 to +2

### 5. Department Priority Weight — API
- [x] Edit `adapters/http/api/departments/schemas.py`
  - Add `priority_weight: Optional[int] = Field(None, ge=-1, le=2)` to update schema
  - Add `priority_weight: int` to response schemas
- [x] Edit `adapters/http/api/departments/routers.py`
  - Pass `priority_weight` to update command
  - Include `priority_weight` in responses

### 6. Priority Scorer Service
- [x] Create `src/request_bc/request/application/services/priority_scorer.py`
  - Class `PriorityScorer` with method `compute(request_type, subtype, department_priority_weight, user_role)`
  - Weight tables implemented
  - Score mapping: `>=4 → urgent, >=3 → high, >=2 → medium, <=1 → low`

### 7. Integrate Scorer into Request Creation
- [x] Edit `src/request_bc/request/application/commands/create_request.py`
  - Import and instantiate `PriorityScorer`
  - Add `department_priority_weight: int = 0` and `user_role: str = "employee"` to command
  - Call scorer instead of `DEFAULT_PRIORITY[type]`
  - Store scoring breakdown in `request.data["priority_scoring"]`
- [x] Edit `adapters/http/api/requests/routers.py`
  - Look up dept priority weight and pass to `CreateRequestCommand`
  - Pass `user_role` from authenticated user

### 8. Unit Tests — Priority Scorer
- [x] Create `tests/unit/request_bc/request/application/services/test_priority_scorer.py`
  - 11 tests covering all scoring scenarios and boundary values

### 9. Unit Tests — Department Priority Weight
- [x] Edit `tests/unit/company_bc/department/application/commands/test_commands.py`
  - Test: update department with valid priority_weight (0, 1, 2, -1) → stored
  - Test: update department with out-of-range weight (3, -2) → validation error
  - Test: update department without priority_weight → field unchanged

### 10. Unit Tests — Scored Request Creation
- [x] Edit `tests/unit/request_bc/request/application/commands/test_commands.py`
  - Test: create request → priority comes from scorer, not DEFAULT_PRIORITY
  - Test: scoring breakdown stored in request.data.priority_scoring
  - Test: create request without department_id → scorer uses weight 0

### 11. Integration Tests
- [x] Edit `tests/integration/test_departments_endpoints.py`
  - Test: PUT /departments/{id} with priority_weight → updated in response
  - Test: GET /departments → priority_weight in list response
- [x] Edit `tests/integration/test_requests_endpoints.py`
  - Test: POST /requests → priority is scored (not hardcoded default)
  - Test: priority_scoring breakdown in response data

### 12. Verification
- [x] `make test` passes
- [ ] `make lint` passes
- [ ] Migration applies cleanly
