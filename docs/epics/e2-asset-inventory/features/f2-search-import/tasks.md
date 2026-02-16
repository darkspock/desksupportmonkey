# Tasks: F2 - Search, Filters + CSV Import

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Extended Search/Filter/Sort

### T1.1: Extend AssetRepositoryInterface ✅
- **File:** `src/asset_bc/asset/domain/repository.py` (MODIFY)
- Update find_all signature with: search, type, status, department_id, assigned_to, sort_by, sort_order

### T1.2: Implement extended find_all in AssetRepository ✅
- **File:** `src/asset_bc/asset/infrastructure/repository.py` (MODIFY)
- Add search (OR across serial_number, brand, model with ILIKE)
- Add filters (type, status, department_id, assigned_to including "none")
- Add sorting with validation (only allowed columns)

### T1.3: Extend ListAssetsQuery ✅
- **File:** `src/asset_bc/asset/application/queries/list_assets.py` (MODIFY)
- Add all filter/search/sort params to query dataclass and handler

### T1.4: Extend asset router list endpoint ✅
- **File:** `adapters/http/api/assets/routers.py` (MODIFY)
- Add query parameters: search, type, status, department_id, assigned_to, sort_by, sort_order

---

## Phase 2: CSV Import

### T2.1: Create ImportAssetsCommand + Handler ✅
- **File:** `src/asset_bc/asset/application/commands/import_assets.py` (NEW)
- Parse CSV, validate headers
- Validate each row, collect errors
- Create Asset + AssetEvent for valid rows
- Track seen serial numbers to detect intra-CSV duplicates
- Return ImportResult(total, successful, failed)
- Define ImportResult, ImportRowError dataclasses

### T2.2: Add import schemas ✅
- **File:** `adapters/http/api/assets/schemas.py` (MODIFY)
- Add ImportRowErrorResponse, ImportResponse

### T2.3: Add import endpoint ✅
- **File:** `adapters/http/api/assets/routers.py` (MODIFY)
- POST /api/v1/assets/import — accepts UploadFile, reads content, calls handler

---

## Phase 3: Tests

### T3.1: Unit tests - Extended list query ✅
- **File:** `tests/unit/asset_bc/asset/application/queries/test_queries.py` (MODIFY)
- Test list with search param
- Test list with type filter
- Test list with sort_by and sort_order

### T3.2: Unit tests - Import command ✅
- **File:** `tests/unit/asset_bc/asset/application/commands/test_import.py` (NEW)
- Success: all rows valid
- Partial: some rows fail validation
- Duplicate serial in CSV
- Duplicate serial in DB
- Missing required fields
- Invalid type enum
- Invalid date format

---

## Phase 4: Verification

### T4.1: Run all tests ✅
### T4.2: Manual verification ✅
1. List with search param -> partial match works
2. List with type filter -> only matching type
3. List with status filter -> only matching status
4. List with assigned_to=none -> only unassigned
5. List with sort_by=purchase_date&sort_order=asc -> correct order
6. Import valid CSV -> all rows imported
7. Import CSV with errors -> partial success with error details
8. Import CSV with duplicate serial -> reported in failures

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Search/Filter | T1.1-T1.4 | — | 4 (repo interface, repo, query, router) |
| 2. CSV Import | T2.1-T2.3 | 1 | 2 (schemas, router) |
| 3. Tests | T3.1-T3.2 | 1 | 1 (query tests) |
| 4. Verification | T4.1-T4.2 | — | — |
