# Tasks: F3 - My Requests (Employee)

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Infrastructure Layer

### T1.1: Implement RequestRepository.find_by_created_by()
- **File:** `src/request_bc/request/infrastructure/repository.py` (MODIFY)
- Filter by user_id + company_id
- Optional status filter
- Sort by created_at desc
- Pagination: offset + limit + count

---

## Phase 2: Application Layer

### T2.1: MyRequestsQuery + Handler
- **File:** `src/request_bc/request/application/queries/my_requests.py` (NEW)
- Query: user_id, company_id, page, page_size, status
- Handler: calls repo.find_by_created_by()

---

## Phase 3: HTTP Layer

### T3.1: Add MyRequestResponse schema
- **File:** `adapters/http/api/my/schemas.py` (MODIFY)
- MyRequestResponse: id, type, title, status, priority, assigned_to, created_at, updated_at

### T3.2: Add my_requests endpoint to My router
- **File:** `adapters/http/api/my/routers.py` (MODIFY)
- GET /api/v1/my/requests — list my requests
- Uses get_current_user (any authenticated user)
- Query params: page, page_size, status
- Returns paginated response with PaginationMeta

---

## Phase 4: Tests

### T4.1: Unit tests - MyRequestsQuery
- **File:** `tests/unit/request_bc/request/application/queries/test_queries.py` (MODIFY)
- My requests: returns paginated results
- My requests: passes status filter to repo

---

## Phase 5: Verification

### T5.1: Run all tests
### T5.2: Manual verification
1. List my requests (as employee with requests) -> paginated results
2. List my requests (as employee with no requests) -> empty
3. Filter by status=submitted -> only submitted
4. Verify pagination meta (page, page_size, total)
5. Verify sort: newest first

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Infrastructure | T1.1 | -- | 1 (repository.py) |
| 2. Application | T2.1 | 1 | -- |
| 3. HTTP | T3.1-T3.2 | -- | 2 (my/schemas, my/routers) |
| 4. Tests | T4.1 | -- | 1 (test_queries) |
| 5. Verification | T5.1-T5.2 | -- | -- |
