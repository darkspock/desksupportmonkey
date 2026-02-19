# Tasks: F2 — Address Management

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 9
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Commands (3) | 1 | S |
| Application - Queries (3) | 1 | S |
| HTTP - Schemas | 1 | S |
| HTTP - Dependencies | 1 | S |
| HTTP - Router | 1 | S |
| HTTP - App Registration | 1 | S |
| Tests - Unit Commands | 1 | S |
| Tests - Unit Queries | 1 | S |
| Tests - Integration | 1 | M |

---

## Phase 1: Application Layer — Commands

### 1. Create address commands
- [x] Create `src/shipping_bc/address/application/commands/create_address.py`
  - `CreateAddressCommand(Command)`: company_id, label, street_line_1, city, state, postal_code, country (default "US"), optional: street_line_2, recipient_name, phone, user_id, is_office
  - Handler: creates `ShippingAddress.create(...)`, saves via repo, returns address ID
- [x] Create `src/shipping_bc/address/application/commands/update_address.py`
  - `UpdateAddressCommand(Command)`: address_id, company_id, + all optional fields (label, street_line_1, etc.)
  - Handler: loads address (raise ValueError if not found), calls `address.update(...)` with non-None fields, saves
- [x] Create `src/shipping_bc/address/application/commands/deactivate_address.py`
  - `DeactivateAddressCommand(Command)`: address_id, company_id
  - Handler: loads address (raise ValueError if not found), calls `address.deactivate()`, saves

---

## Phase 2: Application Layer — Queries

### 2. Create address queries
- [x] Create `src/shipping_bc/address/application/queries/list_addresses.py`
  - `ListAddressesQuery(Query)`: company_id, page, page_size, optional: user_id, is_office, is_active (default True)
  - Handler: delegates to `address_repo.find_all(...)`, returns tuple(list, count)
- [x] Create `src/shipping_bc/address/application/queries/get_address.py`
  - `GetAddressQuery(Query)`: address_id, company_id
  - Handler: `find_by_id()`, raise ValueError if not found
- [x] Create `src/shipping_bc/address/application/queries/addresses_by_user.py`
  - `AddressesByUserQuery(Query)`: user_id, company_id
  - Handler: delegates to `address_repo.find_by_user_id(...)`, returns list

---

## Phase 3: HTTP Layer

### 3. Create address schemas
- [x] Create `adapters/http/api/addresses/__init__.py`
- [x] Create `adapters/http/api/addresses/schemas.py`
  - `AddressCreateRequest(BaseModel)`: label, street_line_1, city, state, postal_code, country (default "US"), optional: street_line_2, recipient_name, phone, user_id, is_office (default False)
  - `AddressUpdateRequest(BaseModel)`: all fields optional
  - `AddressResponse(BaseModel)`: id, company_id, label, street_line_1, street_line_2, city, state, postal_code, country, recipient_name, phone, user_id, is_office, is_active, created_at, updated_at

### 4. Create address dependencies
- [x] Create `adapters/http/api/addresses/dependencies.py`
  - `get_address_repo(db)` → `ShippingAddressRepository(db)`

### 5. Create addresses router
- [x] Create `adapters/http/api/addresses/routers.py`
  - 6 endpoints:
    - `POST /` — create address (201)
    - `GET /` — list addresses with filters (user_id, is_office, is_active)
    - `GET /{id}` — get address detail
    - `PUT /{id}` — update address
    - `DELETE /{id}` — deactivate (soft-delete, returns 200)
    - `GET /by-user/{user_id}` — addresses for user
  - Error handling: ValueError → 404 (not found) or 422 (validation)
  - Response wrapping follows existing patterns (data envelope or direct)

### 6. Register addresses router
- [x] Edit `app.py`
  - Import and include `addresses_router`

---

## Phase 4: Tests

### 7. Unit tests — Commands
- [x] Create `tests/unit/shipping_bc/address/application/__init__.py`
- [x] Create `tests/unit/shipping_bc/address/application/commands/__init__.py`
- [x] Create `tests/unit/shipping_bc/address/application/commands/test_commands.py`
  - `test_create_address_saves` — valid data → address saved with ULID
  - `test_create_address_defaults_country` — no country → "US"
  - `test_update_address_modifies_fields` — only non-None fields updated
  - `test_update_not_found_raises` — address not found → ValueError
  - `test_deactivate_sets_inactive` — is_active = False
  - `test_deactivate_not_found_raises` — address not found → ValueError

### 8. Unit tests — Queries
- [x] Create `tests/unit/shipping_bc/address/application/queries/__init__.py`
- [x] Create `tests/unit/shipping_bc/address/application/queries/test_queries.py`
  - `test_list_returns_paginated` — returns tuple(list, count)
  - `test_list_defaults_active_only` — is_active=True default
  - `test_get_returns_address` — found
  - `test_get_not_found_raises` — raises ValueError
  - `test_by_user_returns_addresses` — filtered by user_id

### 9. Integration tests
- [x] Create `tests/integration/test_addresses_endpoints.py`
  - `test_create_address_returns_201`
  - `test_list_addresses_returns_200`
  - `test_get_address_returns_200`
  - `test_update_address_returns_200`
  - `test_deactivate_address_returns_200`
  - `test_addresses_by_user_returns_200`
  - `test_deactivated_not_in_list` — deactivated address not in default list
  - `test_deactivated_still_accessible_by_id` — GET by ID still works

---

## Dependency Graph

```
Commands (1) — uses F0 entities + repos
  └── Queries (2) — uses F0 repos
        └── Schemas (3)
              └── Dependencies (4)
                    └── Router (5)
                          └── App Registration (6)
                                └── Unit Tests Commands (7) + Queries (8)
                                      └── Integration Tests (9)
```

## Execution Order

**Batch 1 (Parallel):** Tasks 1 + 2 (commands + queries)
**Batch 2 (Parallel):** Tasks 3 + 4 (schemas + dependencies)
**Batch 3:** Task 5 (router)
**Batch 4:** Task 6 (app registration)
**Batch 5 (Parallel):** Tasks 7 + 8 (unit tests)
**Batch 6:** Task 9 (integration tests)

## Final Checklist

- [x] All tasks completed
- [x] 3 command handlers (create, update, deactivate)
- [x] 3 query handlers (list, get, by_user)
- [x] 6 API endpoints
- [x] ~11 unit tests (11 actual)
- [x] ~8 integration tests (8 actual)
- [x] All tests passing (988 unit + 8 integration)
