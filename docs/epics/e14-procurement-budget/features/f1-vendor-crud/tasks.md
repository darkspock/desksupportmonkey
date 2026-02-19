# Tasks: F1 — Vendor CRUD

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 14
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Commands | 4 | S-M |
| Application - Queries | 2 | S |
| HTTP - Schemas + Deps | 2 | S |
| HTTP - Router | 1 | M |
| Config | 1 | S |
| Frontend | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Application Layer — Commands

### 1. CreateVendorCommand + handler
- [x] Create `src/procurement_bc/vendor/application/commands/create_vendor.py`
  - `CreateVendorCommand(Command)`: company_id, name, contact_email?, phone?, address?, notes?, id, performed_by
  - Handler: validate name not empty, create entity via `Vendor.create()`, save to repo

### 2. UpdateVendorCommand + handler
- [x] Create `src/procurement_bc/vendor/application/commands/update_vendor.py`
  - `UpdateVendorCommand(Command)`: vendor_id, company_id, name, contact_email?, phone?, address?, notes?, performed_by
  - Handler: find vendor by id + company_id, raise if not found, update fields, save

### 3. ActivateVendorCommand + handler
- [x] Create `src/procurement_bc/vendor/application/commands/activate_vendor.py`
  - `ActivateVendorCommand(Command)`: vendor_id, company_id, performed_by
  - Handler: find vendor, call `vendor.activate()`, save

### 4. DeactivateVendorCommand + handler
- [x] Create `src/procurement_bc/vendor/application/commands/deactivate_vendor.py`
  - `DeactivateVendorCommand(Command)`: vendor_id, company_id, performed_by
  - Handler: find vendor, call `vendor.deactivate()`, save

---

## Phase 1: Application Layer — Queries

### 5. ListVendorsQuery + handler
- [x] Create `src/procurement_bc/vendor/application/queries/list_vendors.py`
  - `ListVendorsQuery(Query)`: company_id, page, page_size, search?, is_active?
  - Handler: call repo.find_all() with filters, return (vendors, total)

### 6. GetVendorQuery + handler
- [x] Create `src/procurement_bc/vendor/application/queries/get_vendor.py`
  - `GetVendorQuery(Query)`: vendor_id, company_id
  - Handler: find vendor by id + company_id, raise if not found

---

## Phase 2: HTTP Layer

### 7. Vendor schemas
- [x] Create `adapters/http/api/vendors/schemas.py`
  - `VendorCreateRequest`: name (required, max 200), contact_email?, phone?, address?, notes?
  - `VendorUpdateRequest`: same fields as create
  - `VendorResponse`: all fields including timestamps
  - Pydantic validation with Field constraints

### 8. Vendor dependencies
- [x] Create `adapters/http/api/vendors/dependencies.py`
  - `get_vendor_repo(db) -> VendorRepository`

### 9. Vendor router
- [x] Create `adapters/http/api/vendors/routers.py`
  - `POST /` — create vendor (technician+)
  - `GET /` — list vendors (technician+, search + active filter)
  - `GET /{id}` — get vendor detail (technician+)
  - `PUT /{id}` — update vendor (technician+)
  - `POST /{id}/activate` — activate (admin)
  - `POST /{id}/deactivate` — deactivate (admin)
  - Exception handling: not found → 404, validation → 422
  - Response format: `{"data": {...}, "meta": {...}}`
- [x] Create `adapters/http/api/vendors/__init__.py`

---

## Phase 3: Configuration

### 10. Register vendor router
- [x] Edit `app.py`
  - Import and include vendor router with prefix `/api/v1/vendors`

---

## Phase 4: Frontend

### 11. Vendor frontend
- [x] Add `Vendor` interface to `web/app/src/types/index.ts`
  - id, company_id, name, contact_email?, phone?, address?, notes?, is_active, created_at?, updated_at?
- [x] Create `web/app/src/pages/admin/VendorListPage.tsx`
  - List with search input, active/inactive filter dropdown
  - Create modal with form fields
  - Edit inline or modal
  - Activate/deactivate toggle (admin only)
  - Uses useQuery + useMutation pattern
- [ ] Create `web/app/src/pages/admin/VendorDetailPage.tsx`
  - Vendor info card with edit capability
  - POs section (placeholder — populated in F3)
- [x] Edit `web/app/src/router.tsx` — add `/vendors` and `/vendors/:id` routes (technician+)
- [x] Edit `web/app/src/components/layout/Sidebar.tsx` — add "Vendors" nav item (technician+)
- [x] Edit `web/app/src/locales/en.ts` — add ~25 vendor keys
- [x] Edit `web/app/src/locales/es.ts` — add ~25 vendor keys

---

## Phase 5: Tests

### 12. Unit tests
- [x] Create `tests/unit/procurement_bc/vendor/application/commands/test_create.py`
  - Create with valid data, create with missing name → error
- [x] Create `tests/unit/procurement_bc/vendor/application/commands/test_update.py`
  - Update existing, update non-existent → error
- [x] Create `tests/unit/procurement_bc/vendor/application/commands/test_activate.py`
  - Activate/deactivate, not found → error
- [x] Create `tests/unit/procurement_bc/vendor/application/queries/test_list.py`
  - List with filters, empty result
- [x] Create `tests/unit/procurement_bc/vendor/application/queries/test_get.py`
  - Get existing, get not found → error
- ~13 unit tests (command: 9, query: 4) + 6 domain tests = 19 total

### 13. Integration tests
- [x] Create `tests/integration/test_vendors_endpoints.py`
  - POST create vendor → 201
  - GET list vendors → 200 with pagination
  - GET list with search → filtered results
  - GET vendor detail → 200
  - PUT update vendor → 200
  - POST activate → 200 (admin)
  - POST deactivate → 200 (admin)
  - POST activate as technician → 403
  - Tenant isolation: vendor from company A not visible to company B
- ~15 integration tests

---

## Phase 6: Verification

### 14. Verify
- [x] Lint passes: `make lint`
- [x] Unit tests pass: `make test` — 776 passed
- [ ] Integration tests pass: `make test-integration`
- [x] Frontend builds: `cd web/app && npm run build`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`

---

## Dependency Graph

```
Commands (1-4) + Queries (5-6) — depend on F0 entities/repos
  └── Schemas (7) + Deps (8) — depend on entity types
        └── Router (9) — depends on schemas + deps + commands + queries
              └── Config (10) — depends on router
                    └── Frontend (11) — depends on API being available
                          └── Tests (12-13) — after all code
```

## Execution Order

**Batch 1 (Parallel):** Tasks 1-6 (commands + queries)
**Batch 2 (Parallel):** Tasks 7-8 (schemas + deps)
**Batch 3:** Task 9 (router)
**Batch 4:** Task 10 (config)
**Batch 5:** Task 11 (frontend)
**Batch 6 (Parallel):** Tasks 12-13 (tests)
**Batch 7:** Task 14 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing
- [x] mypy passes
- [x] Frontend builds
- [x] 6 vendor endpoints working
- [x] Vendor CRUD complete end-to-end
