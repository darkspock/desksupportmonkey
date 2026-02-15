# Requirements: F1 - Asset Assignment + My Equipment

**Epic:** [E2 - Asset Inventory](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Enable technicians to assign/unassign assets to employees, with automatic status transitions and event recording. Provide employees with a "My Equipment" view of their assigned assets.

---

## Requirements

### R1: Assign Asset
- PATCH /api/v1/assets/{id}/assign assigns asset to a user
- Request body: user_id (required)
- Asset must be in `in_stock` status to assign
- Target user must exist in same company and be active
- On assign: status -> `assigned`, assigned_to -> user_id, department_id -> user's department
- Creates `assigned` event with user_id and assigned_by

### R2: Unassign Asset
- PATCH /api/v1/assets/{id}/unassign removes assignment
- Asset must be in `assigned` status
- On unassign: status -> `in_stock`, assigned_to -> null, department_id -> null
- Creates `unassigned` event

### R3: Assignment Validation
- Cannot assign asset that is `in_repair` or `decommissioned`
- Cannot assign to deactivated user
- Cannot assign to user in different company (tenant isolation)
- Only technician+ role

### R4: My Equipment (Employee)
- GET /api/v1/my/equipment returns all assets assigned to current user
- Any authenticated user can access (employee+)
- Only shows assets with status `assigned`
- Response includes type, brand, model, serial_number, assigned date (from event)

### R5: Event Recording
- Assign creates event: type=assigned, data={user_id, assigned_by, department_id}
- Unassign creates event: type=unassigned, data={previous_user_id, unassigned_by}
