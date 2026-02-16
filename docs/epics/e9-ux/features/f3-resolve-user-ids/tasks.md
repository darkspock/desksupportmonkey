# Tasks: F3 - Resolve User IDs to Names

**Feature:** Resolve User IDs to Names
**Date:** 2026-02-16

---

## Summary

Multiple pages display raw user IDs (ULIDs) instead of human-readable names/emails. Affected areas:
- Request detail page: `assigned_to` and `created_by` fields
- Request queue list: `assigned_to` column
- Internal notes: `author_id` shown as raw ID

**Approach:** Enrich the backend response to include `assigned_to_email` and `created_by_email` fields alongside the IDs, resolving them via the UserRepository. This avoids N+1 on the frontend.

---

## Phase 1: Backend

### T1.1: Enrich request responses with user emails
- **Files:** `adapters/http/api/requests/routers.py`, `adapters/http/api/requests/schemas.py`
- Add `assigned_to_email` and `created_by_email` optional fields to `RequestResponse` and `RequestListItemResponse`
- In `_to_response` and list endpoint, resolve user IDs to emails via `UserRepository`
- For notes/comments, the `author_email` field may already exist on comments; check and add to notes if missing

## Phase 2: Frontend

### T2.1: Display emails instead of IDs
- **Files:** `web/app/src/pages/technician/RequestDetailPage.tsx`, `web/app/src/pages/technician/RequestQueuePage.tsx`
- Use `assigned_to_email` / `created_by_email` from response
- Fallback to ID if email not available
- Notes: use `author_email` instead of `author_id`

## Phase 3: Verification

### T3.1: Manual E2E test
- [ ] Request detail shows email/name for assigned_to
- [ ] Request detail shows email/name for created_by
- [ ] Request queue shows email/name in assigned column
- [ ] Internal notes show author email instead of ID
