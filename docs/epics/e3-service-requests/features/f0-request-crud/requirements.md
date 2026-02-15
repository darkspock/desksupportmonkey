# Requirements: F0 - Request CRUD + State Machine

**Epic:** [E3 - Service Requests](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Deliver the core ServiceRequest entity with types, statuses (state machine), priorities (auto-assigned), CRUD endpoints, and the event sourcing infrastructure. Also create the migration for all 4 E3 tables (service_requests, request_events, request_comments, request_notes).

---

## Requirements

### R1: ServiceRequest Entity
- ServiceRequest has: id, company_id, created_by, assigned_to, type, title, description, status, priority, data (JSON), resolved_at, created_at, updated_at
- Title is required (non-empty, max 255 chars)
- Description is required (non-empty)
- Default status is `submitted`
- Priority is auto-assigned based on type

### R2: Request Types
- Enum values: `incident`, `new_equipment`, `onboarding`
- Type is required on creation and immutable after
- Type-specific data stored in JSON `data` field:
  - `incident`: optional `asset_id`
  - `new_equipment`: optional `equipment_type`
  - `onboarding`: optional `employee_name`, `start_date`, `department_id`

### R3: Request Status State Machine
- Statuses: `submitted`, `in_review`, `in_progress`, `resolved`, `rejected`
- Valid transitions:
  - `submitted` -> `in_review`
  - `in_review` -> `in_progress`
  - `in_review` -> `rejected`
  - `in_progress` -> `resolved`
  - `in_progress` -> `in_review`
- Invalid transitions return error
- `resolved` and `rejected` are terminal states
- When transitioning to `resolved` or `rejected`, set `resolved_at` timestamp

### R4: Request Priority
- Priority levels: `low`, `medium`, `high`, `urgent`
- Default priority by type: incident=high, onboarding=medium, new_equipment=low
- Priority can be overridden by technician via dedicated endpoint
- Priority stored as string enum, sorted by numeric mapping (urgent=4, high=3, medium=2, low=1)

### R5: Request Event Sourcing
- Every request mutation creates a RequestEvent record
- Event types: `created`, `status_changed`, `priority_changed`, `assigned`, `comment_added`, `note_added`
- Each event stores: request_id, event_type, data (JSON), performed_by, created_at
- Events are immutable (never updated or deleted)

### R6: Auto-Assignment Side Effect
- When a technician changes status to `in_review` and the request is unassigned, auto-assign to the acting technician
- This is an application-level side effect in the change_status command handler

### R7: CRUD Endpoints
- `POST /api/v1/requests` — create request (employee+)
- `GET /api/v1/requests/{id}` — get request detail (employee own / technician+ any)
- `PATCH /api/v1/requests/{id}/status` — change status (technician+)
- `PATCH /api/v1/requests/{id}/priority` — change priority (technician+)

### R8: Employee Access Control
- Employees can only view their own requests (filter by created_by = current user)
- Technicians can view any request in their company
- If an employee tries to access another user's request, return 404 (not 403)

### R9: Multi-tenancy
- All request queries filtered by company_id
- Request detail returns 404 for requests in other companies

### R10: Migration (All E3 Tables)
- Single migration creates all 4 tables: service_requests, request_events, request_comments, request_notes
- Indexes: `(company_id, status)`, `(company_id, created_by)`, `(company_id, assigned_to)` on service_requests
- Index on `request_id` for request_events, request_comments, request_notes
