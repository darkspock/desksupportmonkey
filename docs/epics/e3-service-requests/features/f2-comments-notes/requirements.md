# Requirements: F2 - Comments + Internal Notes

**Epic:** [E3 - Service Requests](../../requirements.md)
**Depends on:** F0 (Request CRUD + State Machine)
**Date:** 2026-02-15

---

## Overview

Deliver public comments (visible to employees and technicians) and private internal notes (visible only to technicians) on service requests. This is the communication layer between employees and IT staff.

---

## Requirements

### R1: Comments
- `POST /api/v1/requests/{id}/comments` adds a public comment
- `GET /api/v1/requests/{id}/comments` lists all comments for a request
- Comment fields: body (required, non-empty)
- Comments are ordered by created_at ascending (oldest first)
- Comment records author_id and timestamp
- Adding a comment creates a RequestEvent (type=comment_added)

### R2: Comment Access Control
- Employees can only comment on their own requests
- Technicians can comment on any request in their company
- Employee tries to comment on another's request -> 404

### R3: Internal Notes
- `POST /api/v1/requests/{id}/notes` adds an internal note
- `GET /api/v1/requests/{id}/notes` lists all internal notes
- Note fields: body (required, non-empty)
- Notes are ordered by created_at ascending
- Note records author_id and timestamp
- Adding a note creates a RequestEvent (type=note_added)

### R4: Note Access Control
- Only technician+ role can create and view internal notes
- Notes are NEVER visible to employees
- Separate table ensures no accidental exposure

### R5: Multi-tenancy
- Comments and notes inherit company scope from the parent request
- Verify request belongs to user's company before allowing comment/note operations
