# Tasks: F1 - Company Status + Auth Integration

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Add valid transitions to CompanyStatus enum ✅
- **File:** `src/company_bc/company/domain/enums.py` (MODIFY)
- Add `VALID_TRANSITIONS` dict mapping each status to its allowed target statuses
- DEACTIVATED maps to empty list (terminal state)

### T1.2: Add change_status() to Company entity ✅
- **File:** `src/company_bc/company/domain/entities.py` (MODIFY)
- Add `change_status(new_status: CompanyStatus)` method
- Validates: same status → raise `InvalidStatusTransitionError("Company is already {status}")`
- Validates: invalid transition → raise `InvalidStatusTransitionError("Cannot transition from '{current}' to '{target}'")`
- Updates `status` and syncs `is_active = (new_status == CompanyStatus.ACTIVE)`
- Define `InvalidStatusTransitionError` exception class

---

## Phase 2: Application Layer

### T2.1: Create UpdateCompanyStatusCommand + Handler ✅
- **File:** `src/company_bc/company/application/commands/update_company_status.py` (NEW)
- Command: `company_id: str`, `new_status: str`
- Handler:
  1. Find company → raise `CompanyNotFoundError` if not found
  2. Convert `new_status` string to `CompanyStatus` enum → raise ValueError if invalid
  3. Call `company.change_status(new_status)` (domain validation)
  4. Save company via repo
  5. Log status change at INFO level
  6. Return company

---

## Phase 3: Auth Integration

### T3.1: Extend CompanyLookupService with status-aware lookup ✅
- **File:** `src/auth_bc/company_lookup/domain/service.py` (MODIFY)
- Add abstract method: `find_company_by_email_domain(email) -> Optional[tuple[str, bool]]` (company_id, is_active)
- **File:** `src/auth_bc/company_lookup/infrastructure/service.py` (MODIFY)
- Implement: query CompanyEmailDomainModel + join CompanyModel, return (company_id, is_active) or None

### T3.2: Update CreateMagicLinkCommand for company status ✅
- **File:** `src/auth_bc/magic_link/application/commands/create_magic_link.py` (MODIFY)
- Use new `find_company_by_email_domain()` method
- If None → raise `InvalidEmailDomainError` (domain not found)
- If found but `is_active == False` → raise new `CompanyRestrictedError`
- Define `CompanyRestrictedError` in this file

### T3.3: Update VerifyMagicLinkCommand for company status ✅
- **File:** `src/auth_bc/magic_link/application/commands/verify_magic_link.py` (MODIFY)
- Use new `find_company_by_email_domain()` method
- If None → raise `InvalidTokenError` (domain somehow not found — shouldn't happen if magic link was created)
- If found but `is_active == False` → raise `CompanyRestrictedError`
- Define or import `CompanyRestrictedError`

### T3.4: Update get_current_user dependency for company status ✅
- **File:** `adapters/http/api/auth/dependencies.py` (MODIFY)
- After user `is_active` check, before `set_tenant()`:
- If `user.company_id` is not None:
  - Load company from CompanyRepository
  - If company exists and `company.status != CompanyStatus.ACTIVE`:
    - Raise HTTPException(403, "Company access is currently restricted")
- Super admins with no company_id skip this check

### T3.5: Update auth router for CompanyRestrictedError ✅
- **File:** `adapters/http/api/auth/routers.py` (MODIFY)
- Catch `CompanyRestrictedError` in magic-link and verify endpoints
- Return 403 "Company access is currently restricted"

---

## Phase 4: HTTP Layer

### T4.1: Add status schemas ✅
- **File:** `adapters/http/api/companies/schemas.py` (MODIFY)
- Add `UpdateCompanyStatusRequest(BaseModel)`: `status: str` with validation against valid values

### T4.2: Add status endpoint to company router ✅
- **File:** `adapters/http/api/companies/routers.py` (MODIFY)
- `PATCH /api/v1/companies/{company_id}/status`
- Depends: `require_role(UserRole.SUPER_ADMIN)`, `get_db`
- Instantiate `UpdateCompanyStatusCommandHandler` with `CompanyRepository`
- Map errors:
  - `CompanyNotFoundError` → 404
  - `InvalidStatusTransitionError` → 409
  - `ValueError` (bad status string) → 422

---

## Phase 5: Tests

### T5.1: Unit tests - Company status transitions ✅
- **File:** `tests/unit/company_bc/company/domain/test_status_transitions.py` (NEW)
- Test active → suspended → OK
- Test active → deactivated → OK
- Test suspended → active → OK
- Test suspended → deactivated → OK
- Test deactivated → active → InvalidStatusTransitionError
- Test deactivated → suspended → InvalidStatusTransitionError
- Test same status → InvalidStatusTransitionError
- Test is_active syncs correctly

### T5.2: Unit tests - UpdateCompanyStatusCommand ✅
- **File:** `tests/unit/company_bc/company/application/commands/test_update_company_status.py` (NEW)
- Test successful status change
- Test company not found → CompanyNotFoundError
- Test invalid transition → InvalidStatusTransitionError
- Test invalid status string → ValueError

### T5.3: Unit tests - Auth integration ✅
- **File:** `tests/unit/auth_bc/test_company_status_auth.py` (NEW)
- Test magic link request with suspended company → CompanyRestrictedError
- Test magic link request with deactivated company → CompanyRestrictedError
- Test magic link verify with suspended company → CompanyRestrictedError
- Test get_current_user with suspended company → 403

### T5.4: Regression tests ✅
- Run all existing auth tests to ensure no regressions
- Especially: magic link creation, verification, /me endpoint

---

## Phase 6: Verification

### T6.1: Run all tests ✅
- `make test` — all tests pass

### T6.2: Manual verification ✅
1. Create a company (via F0 endpoint)
2. Login with a user from that company (magic link flow)
3. Verify `/me` works
4. Suspend company via PATCH
5. Verify `/me` returns 403
6. Verify magic link request returns 403
7. Reactivate company
8. Verify `/me` works again
9. Deactivate company
10. Verify cannot reactivate (409)

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.2 | — | 2 (enums.py, entities.py) |
| 2. Application | T2.1 | 1 | — |
| 3. Auth Integration | T3.1-T3.5 | — | 5 (lookup service/interface, create/verify commands, dependencies, router) |
| 4. HTTP | T4.1-T4.2 | — | 2 (schemas, router) |
| 5. Tests | T5.1-T5.4 | 3 new | — |
| 6. Verification | T6.1-T6.2 | — | — |
