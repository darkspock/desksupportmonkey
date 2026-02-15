# Tasks: F1 - Technician Queue + Assignment

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Infrastructure Layer

### T1.1: Implement RequestRepository.find_all()
- **File:** `src/request_bc/request/infrastructure/repository.py` (MODIFY)
- Add find_all() with filters: search, status, type, priority, assigned_to
- Search: ILIKE on title + description
- assigned_to: handle "none" (IS NULL), specific user_id
- Sort: priority desc (CASE expression), created_at asc
- Pagination: offset + limit
- Count: select count from subquery

---

## Phase 2: Application Layer

### T2.1: ListRequestsQuery + Handler
- **File:** `src/request_bc/request/application/queries/list_requests.py` (NEW)
- Query dataclass with: company_id, page, page_size, search, status, type, priority, assigned_to
- Handler calls repo.find_all()

### T2.2: AssignRequestCommand + Handler
- **File:** `src/request_bc/request/application/commands/assign_request.py` (NEW)
- Command: request_id, company_id, user_id, performed_by
- Handler: find request -> RequestNotFoundError, validate user -> UserNotFoundError/UserInactiveError, assign, save, create event, return
- Import and use UserRepository for user validation

---

## Phase 3: HTTP Layer

### T3.1: Add list + assign schemas
- **File:** `adapters/http/api/requests/schemas.py` (MODIFY)
- Add AssignRequestRequest (user_id)
- Add RequestListItemResponse (condensed response for list view)

### T3.2: Add list + assign endpoints to router
- **File:** `adapters/http/api/requests/routers.py` (MODIFY)
- GET /api/v1/requests — list with all query params, translate "me" -> current_user.id
- PATCH /api/v1/requests/{request_id}/assign — assign to technician
- Both require_role(UserRole.TECHNICIAN)
- Error mapping: RequestNotFoundError->404, UserNotFoundError->404, UserInactiveError->409

---

## Phase 4: Tests

### T4.1: Unit tests - ListRequestsQuery
- **File:** `tests/unit/request_bc/request/application/queries/test_queries.py` (MODIFY)
- List: returns paginated results
- List: passes filter params to repo

### T4.2: Unit tests - AssignRequestCommand
- **File:** `tests/unit/request_bc/request/application/commands/test_assign.py` (NEW)
- Assign: success, creates event
- Assign: request not found
- Assign: user not found
- Assign: user inactive
- Reassign: updates assigned_to

---

## Phase 5: Verification

### T5.1: Run all tests
### T5.2: Manual verification
1. List requests (empty queue) -> empty data with pagination meta
2. Create several requests, list -> verify sorted by priority desc, created_at asc
3. Filter by status=submitted -> only submitted requests
4. Filter assigned_to=none -> only unassigned
5. Search by title -> partial match
6. Assign request -> verify event recorded
7. Filter assigned_to=me -> only my assigned requests
8. Reassign request -> verify new assignment

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Infrastructure | T1.1 | -- | 1 (repository.py) |
| 2. Application | T2.1-T2.2 | 2 | -- |
| 3. HTTP | T3.1-T3.2 | -- | 2 (schemas, routers) |
| 4. Tests | T4.1-T4.2 | 1 | 1 (test_queries) |
| 5. Verification | T5.1-T5.2 | -- | -- |
