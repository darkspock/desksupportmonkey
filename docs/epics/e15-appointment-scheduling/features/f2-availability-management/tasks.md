# Tasks: F2 — Availability Management

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 8
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Commands | 1 | M |
| Queries | 1 | M |
| HTTP — Schemas + Dependencies | 1 | S |
| HTTP — Router + App | 1 | M |
| Unit tests | 1 | S |
| Integration tests | 1 | S |
| Verification | 1 | S |

---

## Phase 1: Commands

### 1. Create availability command handlers
- [x] Create `src/appointment_bc/appointment/application/commands/set_availability.py`
  - `@dataclass SetAvailabilityCommand(Command)`: `technician_id`, `company_id`, `windows: list[AvailabilityWindowInput]`
  - `@dataclass AvailabilityWindowInput`: `day_of_week: int`, `start_time: time`, `end_time: time` (plain dataclass, not Command)
  - `SetAvailabilityCommandHandler(CommandHandler[SetAvailabilityCommand])`:
    - `__init__(self, availability_repo: TechnicianAvailabilityRepositoryInterface)`
    - `handle()` → None:
      1. Create `TechnicianAvailability.create()` for each window input
      2. Call `availability_repo.save_all(technician_id, company_id, entities)`
- [x] Create `src/appointment_bc/appointment/application/commands/add_override.py`
  - `@dataclass AddOverrideCommand(Command)`: `override_id`, `company_id`, `technician_id`, `target_date: date`, `is_available: bool`, `start_time: Optional[time]`, `end_time: Optional[time]`, `reason: Optional[str]`
  - `AddOverrideCommandHandler(CommandHandler[AddOverrideCommand])`:
    - `__init__(self, override_repo: AvailabilityOverrideRepositoryInterface)`
    - `handle()` → None:
      1. `AvailabilityOverride.create(...)` with `id=command.override_id`
      2. `override_repo.save(entity)`
- [x] Create `src/appointment_bc/appointment/application/commands/delete_override.py`
  - `@dataclass DeleteOverrideCommand(Command)`: `override_id`, `company_id`
  - `DeleteOverrideCommandHandler(CommandHandler[DeleteOverrideCommand])`:
    - `__init__(self, override_repo: AvailabilityOverrideRepositoryInterface)`
    - `handle()` → None:
      1. `deleted = override_repo.delete(override_id, company_id)`
      2. If not deleted → raise `OverrideNotFoundError`
  - `OverrideNotFoundError(Exception)` with message

---

## Phase 2: Queries

### 2. Create availability query handlers
- [x] Create `src/appointment_bc/appointment/application/queries/get_availability.py`
  - `@dataclass GetAvailabilityQuery(Query)`: `technician_id`, `company_id`
  - `GetAvailabilityQueryHandler(QueryHandler[GetAvailabilityQuery, list[TechnicianAvailability]])`:
    - `__init__(self, availability_repo: TechnicianAvailabilityRepositoryInterface)`
    - `handle()` → `list[TechnicianAvailability]`: `availability_repo.find_by_technician(technician_id, company_id)`
- [x] Create `src/appointment_bc/appointment/application/queries/list_overrides.py`
  - `@dataclass ListOverridesQuery(Query)`: `technician_id`, `company_id`, `date_from: date`, `date_to: date`
  - `ListOverridesQueryHandler(QueryHandler[ListOverridesQuery, list[AvailabilityOverride]])`:
    - `__init__(self, override_repo: AvailabilityOverrideRepositoryInterface)`
    - `handle()` → `list[AvailabilityOverride]`: `override_repo.find_by_technician_date_range(...)`
- [x] Create `src/appointment_bc/appointment/application/queries/get_available_slots.py`
  - `@dataclass GetAvailableSlotsQuery(Query)`: `technician_id`, `company_id`, `target_date: date`, `duration_minutes: int`
  - `GetAvailableSlotsQueryHandler(QueryHandler[GetAvailableSlotsQuery, list[TimeSlot]])`:
    - `__init__(self, availability_repo, override_repo, appointment_repo)`
    - `handle()` → `list[TimeSlot]`:
      1. `recurring = availability_repo.find_by_technician_day(technician_id, company_id, target_date.weekday())`
      2. `overrides = override_repo.find_by_technician_date(technician_id, company_id, target_date)`
      3. `appointments = appointment_repo.find_by_technician_date_range(technician_id, company_id, start_of_day, end_of_day)`
      4. Return `AvailabilityService.compute_available_slots(target_date, duration_minutes, recurring, overrides, appointments)`

---

## Phase 3: HTTP — Schemas + Dependencies

### 3. Create schemas and dependencies
- [x] Create `adapters/http/api/availability/__init__.py` (empty)
- [x] Create `adapters/http/api/availability/schemas.py`
  - `AvailabilityWindowSchema(BaseModel)`: `day_of_week: int` (ge=0, le=6), `start_time: time`, `end_time: time`
  - `SetAvailabilityRequest(BaseModel)`: `windows: list[AvailabilityWindowSchema]`
  - `AvailabilityWindowResponse(BaseModel)`: `id`, `day_of_week`, `start_time`, `end_time`
  - `OverrideCreateRequest(BaseModel)`: `date: date`, `is_available: bool`, `start_time: Optional[time]`, `end_time: Optional[time]`, `reason: Optional[str]`
  - `OverrideResponse(BaseModel)`: `id`, `date`, `is_available`, `start_time?`, `end_time?`, `reason?`, `created_at`, `updated_at`
  - `SlotResponse(BaseModel)`: `start: time`, `end: time`
  - `SlotsQueryResponse(BaseModel)`: `date: date`, `technician_id: str`, `duration_minutes: int`, `slots: list[SlotResponse]`
- [x] Create `adapters/http/api/availability/dependencies.py`
  - `get_availability_repo(db=Depends(get_db)) -> TechnicianAvailabilityRepository`
  - `get_override_repo(db=Depends(get_db)) -> AvailabilityOverrideRepository`

---

## Phase 4: HTTP — Router + App Registration

### 4. Create router and register in app
- [x] Create `adapters/http/api/availability/routers.py`
  - `router = APIRouter(prefix="/api/v1/availability", tags=["availability"])`
  - Helper `_check_self_or_admin(current_user, technician_id)` — raises 403 if non-admin accessing another technician
  - **PUT** `/technicians/{technician_id}` — Set recurring schedule
  - **GET** `/technicians/{technician_id}` — Get recurring schedule
  - **POST** `/technicians/{technician_id}/overrides` — Add override
  - **GET** `/technicians/{technician_id}/overrides` — List overrides
  - **DELETE** `/overrides/{override_id}` — Delete override
  - **GET** `/technicians/{technician_id}/slots` — Get available slots
- [x] Edit `app.py`
  - Add `from adapters.http.api.availability.routers import router as availability_router`
  - Add `app.include_router(availability_router)`

---

## Phase 5: Unit Tests

### 5. Create unit tests for commands and queries
- [x] Create `tests/unit/appointment_bc/appointment/application/commands/test_availability.py`
  - `test_set_availability_saves_all` — creates and saves windows
  - `test_set_availability_validates_windows` — invalid day_of_week → ValueError
  - `test_set_availability_empty_windows` — empty list saves correctly
  - `test_add_override_block` — creates block override
  - `test_add_override_extra` — creates extra availability override with times
  - `test_add_override_validates_times` — is_available=True without times → ValueError
  - `test_delete_override_succeeds` — repo.delete returns True
  - `test_delete_override_not_found_raises` — repo.delete returns False → OverrideNotFoundError
- [x] Create `tests/unit/appointment_bc/appointment/application/queries/test_slots.py`
  - `test_get_availability_returns_windows` — returns technician's schedule
  - `test_list_overrides_returns_filtered` — returns date-range filtered
  - `test_get_available_slots_integrates_service` — verifies all repos called and service invoked

---

## Phase 6: Integration Tests

### 6. Create integration tests
- [x] Create `tests/integration/test_availability_endpoints.py`
  - `test_set_availability_200` — PUT recurring schedule returns saved windows
  - `test_get_availability_200` — GET returns previously set schedule
  - `test_add_override_201` — POST block override
  - `test_list_overrides_200` — GET overrides with date range
  - `test_delete_override_200` — DELETE override
  - `test_delete_override_404` — DELETE non-existent returns 404
  - `test_get_available_slots_200` — GET computed slots
  - `test_technician_self_only_403` — non-admin technician cannot manage another's availability

---

## Phase 7: Verification

### 7. Verify
- [x] Lint passes: `make lint` (no new errors in appointment_bc)
- [x] Unit tests pass: `make test` (919 passed)
- [ ] Integration tests pass: `make test-integration`
- [x] All `__init__.py` files present

---

## Execution Order

**Batch 1 (Parallel):** Tasks 1 + 2 (commands + queries — independent)
**Batch 2 (Parallel):** Tasks 3 + 4 (schemas/deps + router — can be parallelized)
**Batch 3 (Parallel):** Tasks 5 + 6 (unit tests + integration tests)
**Batch 4:** Task 7 (verification)

## Final Checklist

- [x] All tasks completed
- [x] 3 command handlers
- [x] 3 query handlers
- [x] 6 API endpoints
- [x] ~10 unit tests (11 actual)
- [x] ~8 integration tests (8 actual)
- [x] All tests passing
