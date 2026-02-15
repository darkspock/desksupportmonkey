# Tasks: F2 - Comments + Internal Notes

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Infrastructure Layer

### T1.1: Implement comment/note repository methods
- **File:** `src/request_bc/request/infrastructure/repository.py` (MODIFY)
- save_comment(): insert + flush + refresh + convert
- find_comments(): select where request_id, order by created_at asc
- save_note(): same pattern
- find_notes(): same pattern
- _comment_to_entity() and _note_to_entity() converters

---

## Phase 2: Application Layer

### T2.1: AddCommentCommand + Handler
- **File:** `src/request_bc/request/application/commands/add_comment.py` (NEW)
- Command: request_id, company_id, author_id, body
- Handler: find request -> RequestNotFoundError, create comment, save, create event, return

### T2.2: AddNoteCommand + Handler
- **File:** `src/request_bc/request/application/commands/add_note.py` (NEW)
- Command: request_id, company_id, author_id, body
- Handler: find request -> RequestNotFoundError, create note, save, create event, return

### T2.3: ListCommentsQuery + Handler
- **File:** `src/request_bc/request/application/queries/list_comments.py` (NEW)
- Query: request_id, company_id
- Handler: find request -> RequestNotFoundError, return find_comments()

### T2.4: ListNotesQuery + Handler
- **File:** `src/request_bc/request/application/queries/list_notes.py` (NEW)
- Query: request_id, company_id
- Handler: find request -> RequestNotFoundError, return find_notes()

---

## Phase 3: HTTP Layer

### T3.1: Add comment/note schemas
- **File:** `adapters/http/api/requests/schemas.py` (MODIFY)
- AddCommentRequest (body: str, min_length=1)
- CommentResponse (id, request_id, author_id, body, created_at)
- NoteResponse (id, request_id, author_id, body, created_at)

### T3.2: Add comment/note endpoints to router
- **File:** `adapters/http/api/requests/routers.py` (MODIFY)
- POST /{request_id}/comments — add comment (employee own / technician+)
- GET /{request_id}/comments — list comments (employee own / technician+)
- POST /{request_id}/notes — add note (technician+)
- GET /{request_id}/notes — list notes (technician+)
- Employee access control helper: verify request ownership for comment endpoints

---

## Phase 4: Tests

### T4.1: Unit tests - AddCommentCommand
- **File:** `tests/unit/request_bc/request/application/commands/test_comments.py` (NEW)
- Add comment: success, creates event
- Add comment: request not found
- Add comment: empty body raises ValueError (from entity)

### T4.2: Unit tests - AddNoteCommand
- **File:** `tests/unit/request_bc/request/application/commands/test_notes.py` (NEW)
- Add note: success, creates event
- Add note: request not found
- Add note: empty body raises ValueError

### T4.3: Unit tests - ListCommentsQuery + ListNotesQuery
- **File:** `tests/unit/request_bc/request/application/queries/test_queries.py` (MODIFY)
- List comments: success, returns ordered
- List comments: request not found
- List notes: success, returns ordered
- List notes: request not found

---

## Phase 5: Verification

### T5.1: Run all tests
### T5.2: Manual verification
1. Add comment to own request (as employee) -> 201
2. Add comment to other's request (as employee) -> 404
3. Add comment to any request (as technician) -> 201
4. List comments -> verify ordered by created_at asc
5. Add internal note (as technician) -> 201
6. Add internal note (as employee) -> 403
7. List notes (as technician) -> success
8. List notes (as employee) -> 403

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Infrastructure | T1.1 | -- | 1 (repository.py) |
| 2. Application | T2.1-T2.4 | 4 | -- |
| 3. HTTP | T3.1-T3.2 | -- | 2 (schemas, routers) |
| 4. Tests | T4.1-T4.3 | 2 | 1 (test_queries) |
| 5. Verification | T5.1-T5.2 | -- | -- |
