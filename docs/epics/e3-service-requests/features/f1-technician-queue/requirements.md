# Requirements: F1 - Technician Queue + Assignment

**Epic:** [E3 - Service Requests](../../requirements.md)
**Depends on:** F0 (Request CRUD + State Machine)
**Date:** 2026-02-15

---

## Overview

Deliver the technician's primary workspace: a filterable, sortable, paginated queue of requests, plus the ability to claim/assign requests to specific technicians.

---

## Requirements

### R1: List Requests (Queue)
- `GET /api/v1/requests` lists all requests for the company
- Default sort: priority desc (urgent first), then created_at asc (oldest first within same priority)
- Priority sorting uses numeric mapping: urgent=4, high=3, medium=2, low=1
- Pagination with page and page_size (default 20, max 100)
- Only technician+ role can access

### R2: Filters
- Filter by status (exact match)
- Filter by type (exact match)
- Filter by priority (exact match)
- Filter by assigned_to:
  - Specific user_id
  - `me` — requests assigned to current technician
  - `none` — unassigned requests
- All filters are optional and combinable

### R3: Search
- Search by title or description (partial match, case-insensitive)
- Uses ILIKE pattern matching (same as asset search)

### R4: Assign/Claim Request
- `PATCH /api/v1/requests/{id}/assign` assigns request to a technician
- Body: `{ "user_id": "..." }` — the technician to assign to
- Technician can self-assign (claim) by passing their own user_id
- Only technician+ can assign
- Assignment recorded as RequestEvent (type=assigned)
- A request can be reassigned to a different technician at any time

### R5: Multi-tenancy
- All list queries filtered by company_id
- Assignment validates that the target technician belongs to the same company
