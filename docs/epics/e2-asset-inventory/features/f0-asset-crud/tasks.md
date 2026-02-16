# Tasks: F0 - Asset CRUD + Event Sourcing

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Create AssetType and AssetStatus enums ✅
- **File:** `src/asset_bc/asset/domain/enums.py` (NEW)
- AssetType: laptop, monitor, keyboard, mouse, headset, docking_station, other
- AssetStatus: in_stock, assigned, in_repair, decommissioned
- VALID_TRANSITIONS map (excludes in_stock<->assigned, handled by F1)
- InvalidStatusTransitionError class

### T1.2: Create Asset entity ✅
- **File:** `src/asset_bc/asset/domain/entities.py` (NEW)
- Dataclass with all fields from design
- `create()`: validates brand, model, serial_number not empty, generates ULID, status=in_stock
- `update()`: updates brand, model, notes, purchase_date, warranty_expiration (all optional)
- `change_status()`: validates transition, updates status, clears assigned_to if decommissioned

### T1.3: Create AssetEvent entity ✅
- Same file as T1.2 or separate
- Dataclass: id, asset_id, event_type, data (dict), performed_by, created_at
- `create()`: generates ULID

### T1.4: Create AssetRepositoryInterface ✅
- **File:** `src/asset_bc/asset/domain/repository.py` (NEW)
- ABC: save, find_by_id(id, company_id), find_by_serial_number(sn, company_id), find_all(company_id, page, page_size), save_event, find_events(asset_id)

### T1.5: Create __init__.py files ✅
- `src/asset_bc/__init__.py`
- `src/asset_bc/asset/__init__.py`
- `src/asset_bc/asset/domain/__init__.py`
- `src/asset_bc/asset/application/__init__.py`
- `src/asset_bc/asset/application/commands/__init__.py`
- `src/asset_bc/asset/application/queries/__init__.py`
- `src/asset_bc/asset/infrastructure/__init__.py`
- `adapters/http/api/assets/__init__.py`

---

## Phase 2: Infrastructure Layer

### T2.1: Create AssetModel ✅
- **File:** `src/asset_bc/asset/infrastructure/models.py` (NEW)
- AssetModel(ULIDMixin, TimestampMixin, Base): all columns from design
- UniqueConstraint("company_id", "serial_number")

### T2.2: Create AssetEventModel ✅
- Same file
- AssetEventModel(ULIDMixin, Base): asset_id, event_type, data (JSON), performed_by, created_at
- No TimestampMixin (no updated_at)

### T2.3: Update models_registry.py ✅
- Add imports for AssetModel, AssetEventModel

### T2.4: Create Alembic migration ✅
- `alembic revision --autogenerate -m "add_assets_and_asset_events"`
- Verify: assets table with indexes and unique constraint, asset_events table
- Test upgrade + downgrade

### T2.5: Implement AssetRepository ✅
- **File:** `src/asset_bc/asset/infrastructure/repository.py` (NEW)
- save(): upsert pattern
- find_by_id(): filter by id + company_id
- find_by_serial_number(): case-insensitive, within company
- find_all(): pagination (basic for now, extended in F2)
- save_event(): insert event
- find_events(): ordered by created_at asc
- _to_entity() and _event_to_entity() conversions

---

## Phase 3: Application Layer

### T3.1: CreateAssetCommand + Handler ✅
- **File:** `src/asset_bc/asset/application/commands/create_asset.py` (NEW)
- Command: company_id, type, brand, model, serial_number, purchase_date, warranty_expiration, notes, performed_by
- Handler: validate serial unique -> SerialNumberExistsError, create entity, save, create event, return
- Define SerialNumberExistsError

### T3.2: UpdateAssetCommand + Handler ✅
- **File:** `src/asset_bc/asset/application/commands/update_asset.py` (NEW)
- Command: asset_id, company_id, brand, model, notes, purchase_date, warranty_expiration, performed_by
- Handler: find -> AssetNotFoundError, collect changes, update, save, create event with changed fields, return
- Define AssetNotFoundError

### T3.3: ChangeAssetStatusCommand + Handler ✅
- **File:** `src/asset_bc/asset/application/commands/change_asset_status.py` (NEW)
- Command: asset_id, company_id, new_status, performed_by
- Handler: find -> AssetNotFoundError, change_status (validates transitions), save, create event, return
- If decommissioned and was assigned: also create unassigned event

### T3.4: ListAssetsQuery + Handler ✅
- **File:** `src/asset_bc/asset/application/queries/list_assets.py` (NEW)
- Query: company_id, page, page_size
- Handler: calls repo.find_all()

### T3.5: GetAssetQuery + Handler ✅
- **File:** `src/asset_bc/asset/application/queries/get_asset.py` (NEW)
- Query: asset_id, company_id
- Handler: find -> AssetNotFoundError, return

### T3.6: GetAssetHistoryQuery + Handler ✅
- **File:** `src/asset_bc/asset/application/queries/get_asset_history.py` (NEW)
- Query: asset_id, company_id
- Handler: verify asset exists -> AssetNotFoundError, get events, return

---

## Phase 4: HTTP Layer

### T4.1: Create asset schemas ✅
- **File:** `adapters/http/api/assets/schemas.py` (NEW)
- CreateAssetRequest, UpdateAssetRequest, ChangeStatusRequest
- AssetResponse, AssetEventResponse

### T4.2: Create asset router ✅
- **File:** `adapters/http/api/assets/routers.py` (NEW)
- POST /api/v1/assets -> create_asset
- GET /api/v1/assets -> list_assets
- GET /api/v1/assets/{id} -> get_asset
- PUT /api/v1/assets/{id} -> update_asset
- PATCH /api/v1/assets/{id}/status -> change_status
- GET /api/v1/assets/{id}/history -> get_history
- All require_role(UserRole.TECHNICIAN)
- Use current_user.company_id and current_user.id directly

### T4.3: Register router in app.py ✅

---

## Phase 5: Tests

### T5.1: Unit tests - Asset entity ✅
- **File:** `tests/unit/asset_bc/asset/domain/test_entities.py` (NEW)
- Create with valid data
- Create with empty brand/model/serial raises
- Update fields
- Status change valid transitions
- Status change invalid raises
- Decommission clears assigned_to

### T5.2: Unit tests - AssetEvent entity ✅
- Create event with data

### T5.3: Unit tests - Asset commands ✅
- **File:** `tests/unit/asset_bc/asset/application/commands/test_commands.py` (NEW)
- Create: success, duplicate serial
- Update: success, not found, creates event with changes
- Change status: success, not found, invalid transition, decommission clears assignment

### T5.4: Unit tests - Asset queries ✅
- **File:** `tests/unit/asset_bc/asset/application/queries/test_queries.py` (NEW)
- List: returns paginated
- Get: success, not found
- History: success, asset not found

---

## Phase 6: Verification

### T6.1: Run all tests ✅
### T6.2: Run migration ✅
### T6.3: Manual verification ✅
1. Create asset -> verify response
2. List assets -> verify pagination
3. Get asset detail -> verify
4. Update asset metadata -> verify
5. Change status (in_stock -> in_repair) -> verify
6. Change status (in_repair -> in_stock) -> verify
7. Change status invalid -> 409
8. Get history -> verify events
9. Duplicate serial number -> 409

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.5 | 3 + inits | — |
| 2. Infrastructure | T2.1-T2.5 | 2 + migration | 1 (models_registry) |
| 3. Application | T3.1-T3.6 | 6 | — |
| 4. HTTP | T4.1-T4.3 | 2 + init | 1 (app.py) |
| 5. Tests | T5.1-T5.4 | 3 | — |
| 6. Verification | T6.1-T6.3 | — | — |
