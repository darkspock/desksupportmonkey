# Tasks: F2 — Procurement Config

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 11
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Commands | 1 | S |
| Application - Queries | 1 | S |
| HTTP - Schemas + Deps | 2 | S |
| HTTP - Router | 1 | S |
| Config | 1 | S |
| Frontend | 1 | M |
| Tests - Unit | 1 | S |
| Tests - Integration | 1 | S |
| Verification | 1 | S |

---

## Phase 1: Application Layer

### 1. SaveProcurementConfigCommand + handler
- [x] Create `src/procurement_bc/budget/application/commands/save_config.py`
  - `SaveProcurementConfigCommand(Command)`: company_id, enforcement_mode, approval_threshold_cents, po_number_prefix, fiscal_year_start_month, currency, auto_create_assets, performed_by
  - Handler validates:
    - enforcement_mode in ("warn", "strict")
    - approval_threshold_cents >= 0
    - fiscal_year_start_month in range 1-12
    - po_number_prefix non-empty, len <= 10
    - currency is 3-char string
  - Upsert: find existing by company_id -> update or create new

### 2. GetProcurementConfigQuery + handler
- [x] Create `src/procurement_bc/budget/application/queries/get_config.py`
  - `GetProcurementConfigQuery(Query)`: company_id
  - Handler: find by company_id, return entity or default config (warn, 0 threshold, "PO" prefix, month 1, "USD", false)

---

## Phase 2: HTTP Layer

### 3. Procurement config schemas
- [x] Create `adapters/http/api/settings/procurement_schemas.py`
  - `ProcurementConfigUpdateRequest`: enforcement_mode (pattern "warn|strict"), approval_threshold_cents (ge=0), po_number_prefix (1-10), fiscal_year_start_month (1-12), currency (3 chars), auto_create_assets (bool)
  - `ProcurementConfigResponse`: all fields including id?, company_id, timestamps

### 4. Procurement config dependencies
- [x] Create `adapters/http/api/settings/procurement_dependencies.py`
  - `get_procurement_config_repo(db) -> CompanyProcurementConfigRepository`

### 5. Procurement config router
- [x] Create `adapters/http/api/settings/procurement_routers.py`
  - `PUT /api/v1/settings/procurement` — save config (admin)
  - `GET /api/v1/settings/procurement` — get config (admin)
  - Exception handling for validation errors
  - Response format: `{"data": {...}}`

---

## Phase 3: Configuration

### 6. Register procurement settings router
- [x] Edit `app.py`
  - Import and include procurement settings router with prefix `/api/v1/settings/procurement`

---

## Phase 4: Frontend

### 7. Procurement settings frontend
- [x] Add `CompanyProcurementConfig` interface to `web/app/src/types/index.ts`
  - id?, company_id, enforcement_mode, approval_threshold_cents, po_number_prefix, fiscal_year_start_month, currency, auto_create_assets, created_at?, updated_at?
- [x] Create `web/app/src/pages/admin/ProcurementSettingsPage.tsx`
  - Enforcement mode: dropdown (Warn / Strict)
  - Approval threshold: number input (display in whole units, convert to/from cents)
  - PO number prefix: text input
  - Fiscal year start month: dropdown (January through December)
  - Currency: text input (ISO 4217, e.g., USD)
  - Auto-create assets on receipt: toggle
  - Save button -> PUT, load on mount -> GET
  - Follow AssignmentAISettingsPage pattern
- [x] Edit `web/app/src/router.tsx` — add `/settings/procurement` route (admin)
- [x] Edit `web/app/src/components/layout/Sidebar.tsx` — add "Procurement Settings" nav item (admin)
- [x] Edit `web/app/src/locales/en.ts` — add ~30 procurement config keys
- [x] Edit `web/app/src/locales/es.ts` — add ~30 procurement config keys

---

## Phase 5: Tests

### 8. Unit tests
- [x] Create `tests/unit/procurement_bc/budget/application/commands/test_save_config.py`
  - Save new config -> creates
  - Save existing config -> updates
  - Invalid enforcement_mode -> error
  - Invalid fiscal_year_start_month (0, 13) -> error
  - Invalid threshold (negative) -> error
  - Empty prefix -> error
  - Invalid currency -> error
- [x] Create `tests/unit/procurement_bc/budget/application/queries/test_get_config.py`
  - Config exists -> returns it
  - Config not found -> returns defaults
- 9 unit tests

### 9. Integration tests
- [x] Create `tests/integration/test_procurement_config_endpoints.py`
  - PUT save config -> 200
  - PUT updates existing -> 200
  - PUT with invalid mode -> 422
  - GET config -> returns defaults
  - GET after save -> returns saved
  - Non-admin access -> 403 (technician, employee)
- 8 integration tests

---

## Phase 6: Verification

### 10. Verify
- [x] Lint passes: `make lint`
- [x] Unit tests pass: `make test` — 785 passed
- [ ] Integration tests pass: `make test-integration`
- [x] Frontend builds: `cd web/app && npm run build`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`

---

## Dependency Graph

```
Command (1) + Query (2) — depend on F0 config entity/repo
  └── Schemas (3) + Deps (4) — depend on entity types
        └── Router (5) — depends on schemas + deps + command + query
              └── Config (6) — depends on router
                    └── Frontend (7) — depends on API
                          └── Tests (8-9) — after all code
```

## Execution Order

**Batch 1 (Parallel):** Tasks 1-2 (command + query)
**Batch 2 (Parallel):** Tasks 3-4 (schemas + deps)
**Batch 3:** Task 5 (router)
**Batch 4:** Task 6 (config)
**Batch 5:** Task 7 (frontend)
**Batch 6 (Parallel):** Tasks 8-9 (tests)
**Batch 7:** Task 10 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing
- [x] mypy passes
- [x] Frontend builds
- [x] PUT + GET endpoints working
- [x] Settings page renders and saves correctly
