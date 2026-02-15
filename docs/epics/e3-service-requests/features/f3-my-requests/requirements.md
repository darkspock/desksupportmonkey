# Requirements: F3 - My Requests (Employee)

**Epic:** [E3 - Service Requests](../../requirements.md)
**Depends on:** F0 (Request CRUD), F1 (list/filter pattern to reuse)
**Date:** 2026-02-15

---

## Overview

Deliver an employee-facing view of their own submitted requests. A simple read-only query on top of F0's data, following the list/filter pattern established in F1.

---

## Requirements

### R1: My Requests Endpoint
- `GET /api/v1/my/requests` lists all requests created by the current user
- Any authenticated user (employee+) can access
- Extends the existing `/api/v1/my/` router (alongside My Equipment)

### R2: Response Fields
- Response includes: id, type, title, status, priority, assigned_to, created_at, updated_at

### R3: Pagination
- Pagination with page and page_size (default 20, max 100)
- Default sort: created_at desc (newest first)

### R4: Filter
- Filter by status (optional, exact match)

### R5: Multi-tenancy
- Queries scoped by company_id (from current_user)
- Only returns requests where created_by = current_user.id
