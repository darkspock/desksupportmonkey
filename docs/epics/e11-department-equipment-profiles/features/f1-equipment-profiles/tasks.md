# Tasks: F1 — Equipment Profile CRUD

## Implementation Tasks

### 1. Domain Entities
- [x] Create `EquipmentProfile` entity in `src/company_bc/equipment_profile/domain/entities.py`
  - Fields: `id`, `company_id`, `department_id`, `role` (UserRole), `is_active`, `created_at`, `updated_at`
- [x] Create `EquipmentProfileItem` value object
  - Fields: `id`, `profile_id`, `asset_type` (AssetType), `quantity` (default 1), `preferred_brand`, `preferred_model`, `min_ram_gb`, `min_storage_gb`

### 2. Infrastructure
- [x] Create `EquipmentProfileModel` and `EquipmentProfileItemModel` in `src/company_bc/equipment_profile/infrastructure/models.py`
  - Unique partial index: `(company_id, department_id, role) WHERE is_active = true`
  - Items FK: `profile_id` → `equipment_profiles.id` (CASCADE delete)
- [x] Create migration for both tables

### 3. Authorization Helper
- [x] Create `can_manage_department(user, department_id, db) -> bool` utility
  - Returns `True` if `role >= ADMIN` OR `user.id == department.manager_user_id`
  - Reusable across F1 endpoints

### 4. Commands
- [x] `CreateEquipmentProfile(company_id, department_id, role, items[], performed_by)` — validates one-active policy
- [x] `UpdateEquipmentProfile(profile_id, company_id, items[], performed_by)` — replaces items
- [x] `ActivateEquipmentProfile(profile_id, company_id, performed_by)` — deactivates conflicting profile
- [x] `DeactivateEquipmentProfile(profile_id, company_id, performed_by)`
- [x] `DeleteEquipmentProfile(profile_id, company_id, performed_by)`

### 5. Queries
- [x] `ListEquipmentProfiles(company_id, department_id?, role?, is_active?)` — paginated, includes items
- [x] `GetEquipmentProfile(profile_id, company_id)` — detail with items

### 6. API Endpoints
- [x] `POST /api/v1/equipment-profiles` — create with items
- [x] `GET /api/v1/equipment-profiles` — list (filters: department_id, role, is_active)
- [x] `GET /api/v1/equipment-profiles/{id}` — detail with items
- [x] `PUT /api/v1/equipment-profiles/{id}` — update items
- [x] `POST /api/v1/equipment-profiles/{id}/activate`
- [x] `POST /api/v1/equipment-profiles/{id}/deactivate`
- [x] `DELETE /api/v1/equipment-profiles/{id}`
- [x] All endpoints use dual-check authorization (admin OR department manager)

### 7. Unit Tests
- [x] `tests/unit/company_bc/equipment_profile/application/commands/test_create.py`
- [x] `tests/unit/company_bc/equipment_profile/application/commands/test_update.py`
- [x] `tests/unit/company_bc/equipment_profile/application/commands/test_activate.py`
- [x] `tests/unit/company_bc/equipment_profile/application/commands/test_delete.py`
  - Cover: one-active-profile enforcement, item validation, permission checks, tenant isolation

### 8. Integration Tests
- [x] `tests/integration/test_equipment_profiles_endpoints.py`
  - CRUD happy path, permission failures, tenant isolation, one-active-profile conflict

### 9. Verification
- [x] Lint passes
- [x] New tests pass
- [x] Full unit suite passes — 616 passed
- [x] Full integration suite passes — 149 passed (1 pre-existing failure unrelated to F1)

### 10. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F1 status to Done
