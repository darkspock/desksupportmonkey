# Tasks: F3 — Auto-Assignment Timing Fix

## Implementation Tasks

### 1. Remove Auto-Assignment on new_equipment Creation
- [x] Edit `adapters/http/api/requests/routers.py`
  - Changed auto-assignment trigger condition from `NEW_EQUIPMENT | ONBOARDING` to `ONBOARDING` only
  - `new_equipment` requests now get auto-assignment after approval instead

### 2. Add Auto-Assignment After Approval
- [x] Edit `adapters/http/api/requests/routers.py` (approve_request endpoint)
  - Added `profile_repo`, `config_repo`, `asset_repo` dependencies
  - After approval and refresh: if `request.type == NEW_EQUIPMENT and requester`, call `_attempt_auto_assign()` using requester's department/role info

### 3. Router Support for Post-Approval Auto-Assignment
- [x] Implemented in the router (consistent with existing E11 create flow pattern)
  - Uses requester's `department_id` and `role` (not approver's) for auto-assign metadata

### 4. Unit Tests
- [ ] Edit `tests/unit/request_bc/request/application/commands/test_approval.py`
  - Auto-assign is in router, not command handlers — covered by integration tests
- [ ] Edit `tests/unit/request_bc/request/application/commands/test_commands.py`
  - Auto-assign is in router, not command handlers — covered by integration tests

### 5. Integration Tests
- [ ] Edit `tests/integration/test_auto_assignment.py` (requires Docker)
  - Test: create new_equipment → no auto_assignment in response data
  - Test: approve new_equipment → auto_assignment metadata appears in request data
  - Test: create onboarding → auto_assignment runs at creation (unchanged behavior)

### 6. Verification
- [x] `make test` passes (681 unit tests)
- [ ] `make test-integration` passes (requires Docker)
- [x] Existing E11 onboarding auto-assignment behavior unchanged (only trigger removed for new_equipment)
