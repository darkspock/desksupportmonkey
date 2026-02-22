# Tasks: F4 - Plan Enforcement (Simplified)

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F3](../f3-admin-billing-ui/tasks.md)
**Date:** 2026-02-22
**Revised:** 2026-02-23 — Scope reduced per product decision: check on login + adding employees only.

---

## Revised Scope

Instead of adding guards to all write endpoints, enforcement is limited to two targeted checks:
1. **Block login** for suspended companies (magic link verify, password login, Google OAuth, Microsoft OAuth)
2. **Block adding employees** when the plan user limit is reached (invite, import confirm, quick create)

---

## Phase 1: Login Suspension Check

### T1.1: _check_billing_not_suspended helper
- [x] **File:** `adapters/http/api/auth/routers.py` (MODIFY)
- Added `_check_billing_not_suspended(user, db)` helper:
  - Returns early if no user, no company_id, or `OPEN_SOURCE_MODE=True`
  - Returns early if company is `complimentary`
  - Raises `HTTP 402 "account_suspended"` if `billing_status == SUSPENDED`

### T1.2: Call check in verify_magic_link
- [x] **File:** `adapters/http/api/auth/routers.py` (MODIFY)
- Called after decoding JWT and fetching user

### T1.3: Call check in password_login
- [x] **File:** `adapters/http/api/auth/routers.py` (MODIFY)
- Added JWT decode + user fetch + billing check after successful login

### T1.4: Call check in google_oauth_login
- [x] **File:** `adapters/http/api/auth/routers.py` (MODIFY)
- Added `db` and `user_repo` dependencies; billing check after service returns token

### T1.5: Call check in microsoft_oauth_login
- [x] **File:** `adapters/http/api/auth/routers.py` (MODIFY)
- Added `db` and `user_repo` dependencies; billing check after service returns token

---

## Phase 2: User Limit Check on Employee Add

### T2.1: _check_user_limit_not_reached helper
- [x] **File:** `adapters/http/api/users/routers.py` (MODIFY)
- Added `_check_user_limit_not_reached(company_id, company_repo)` helper:
  - Returns early if `OPEN_SOURCE_MODE=True` or company is `complimentary`
  - Uses `PlanGate.get_user_limit(company.plan)` — returns `None` for unlimited
  - Uses `company_repo.count_users(company_id)` for current count
  - Raises `HTTP 402 "plan_limit_reached"` if `count >= limit`

### T2.2: Call check in invite_user
- [x] **File:** `adapters/http/api/users/routers.py` (MODIFY)

### T2.3: Call check in import_users_confirm
- [x] **File:** `adapters/http/api/users/routers.py` (MODIFY)

### T2.4: Call check in quick_create_employee
- [x] **File:** `adapters/http/api/users/routers.py` (MODIFY)

---

## Phase 3: Fix Unit Tests

### T3.1: Update Google OAuth success test
- [x] **File:** `tests/unit/auth_bc/test_google_oauth_endpoint.py` (MODIFY)
- Added `get_user_repo` override; mock service now returns real JWT (so `decode_token` succeeds)

### T3.2: Update Microsoft OAuth success test
- [x] **File:** `tests/unit/auth_bc/test_microsoft_oauth_endpoint.py` (MODIFY)
- Same fix as T3.1 for Microsoft endpoint

---

## Phase 4: Verification

### T4.1: Run linter
- [x] `make lint` — only 4 pre-existing errors (OAuth stub types), no new errors

### T4.2: Run unit tests
- [x] `make test` — 1184 passed

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Login check | T1.1-T1.5 | — | 1 modified (auth/routers.py) |
| 2. User limit check | T2.1-T2.4 | — | 1 modified (users/routers.py) |
| 3. Tests | T3.1-T3.2 | — | 2 modified (OAuth unit tests) |
| 4. Verification | T4.1-T4.2 | — | — |
