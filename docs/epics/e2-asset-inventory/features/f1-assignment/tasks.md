# Tasks: F1 - Asset Assignment + My Equipment

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Extend Asset entity ✅
- **File:** `src/asset_bc/asset/domain/entities.py` (MODIFY)
- Add `assign(user_id, department_id)` method: validates status is in_stock, sets fields
- Add `unassign()` method: validates status is assigned, clears fields
- Add `InvalidAssignmentError` class

### T1.2: Extend AssetRepositoryInterface ✅
- **File:** `src/asset_bc/asset/domain/repository.py` (MODIFY)
- Add: `find_by_assigned_to(user_id: str, company_id: str) -> list[Asset]`

---

## Phase 2: Infrastructure Layer

### T2.1: Extend AssetRepository ✅
- **File:** `src/asset_bc/asset/infrastructure/repository.py` (MODIFY)
- Add `find_by_assigned_to()`: filter by assigned_to + company_id, status=assigned

---

## Phase 3: Application Layer

### T3.1: AssignAssetCommand + Handler ✅
- **File:** `src/asset_bc/asset/application/commands/assign_asset.py` (NEW)
- Command: asset_id, company_id, user_id, performed_by
- Handler: find asset, find user (via UserRepository), validate active, assign, save, create event
- Errors: AssetNotFoundError, UserNotFoundError, UserInactiveError, InvalidAssignmentError

### T3.2: UnassignAssetCommand + Handler ✅
- **File:** `src/asset_bc/asset/application/commands/unassign_asset.py` (NEW)
- Command: asset_id, company_id, performed_by
- Handler: find asset, unassign, save, create event
- Errors: AssetNotFoundError, InvalidAssignmentError

### T3.3: MyEquipmentQuery + Handler ✅
- **File:** `src/asset_bc/asset/application/queries/my_equipment.py` (NEW)
- Query: user_id, company_id
- Handler: calls repo.find_by_assigned_to()

---

## Phase 4: HTTP Layer

### T4.1: Add assign/unassign to asset router ✅
- **File:** `adapters/http/api/assets/routers.py` (MODIFY)
- PATCH /{id}/assign — request body: AssignAssetRequest(user_id)
- PATCH /{id}/unassign — no body

### T4.2: Create my equipment schemas ✅
- **File:** `adapters/http/api/my/schemas.py` (NEW)
- MyEquipmentResponse: id, type, brand, model, serial_number, created_at

### T4.3: Create my equipment router ✅
- **File:** `adapters/http/api/my/routers.py` (NEW)
- GET /api/v1/my/equipment — uses get_current_user (not require_role)

### T4.4: Register my router in app.py ✅

---

## Phase 5: Tests

### T5.1: Unit tests - Asset assign/unassign ✅
- **File:** `tests/unit/asset_bc/asset/domain/test_entities.py` (MODIFY)
- Assign: success, wrong status raises
- Unassign: success, not assigned raises

### T5.2: Unit tests - Assignment commands ✅
- **File:** `tests/unit/asset_bc/asset/application/commands/test_assignment.py` (NEW)
- Assign: success, asset not found, user not found, user inactive, wrong status
- Unassign: success, asset not found, not assigned

### T5.3: Unit tests - My equipment query ✅
- **File:** `tests/unit/asset_bc/asset/application/queries/test_queries.py` (MODIFY)
- Returns user's assigned assets

---

## Phase 6: Verification

### T6.1: Run all tests ✅
### T6.2: Manual verification ✅
1. Assign asset to employee -> verify status changes to assigned
2. Get asset detail -> verify assigned_to populated
3. Get asset history -> verify assigned event
4. My equipment -> verify employee sees their asset
5. Unassign -> verify status back to in_stock
6. Assign to inactive user -> 409
7. Assign non-in_stock asset -> 409

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.2 | — | 2 (entity, repo interface) |
| 2. Infrastructure | T2.1 | — | 1 (repo) |
| 3. Application | T3.1-T3.3 | 3 | — |
| 4. HTTP | T4.1-T4.4 | 2 + init | 2 (asset router, app.py) |
| 5. Tests | T5.1-T5.3 | 1 | 2 (entity tests, query tests) |
| 6. Verification | T6.1-T6.2 | — | — |
