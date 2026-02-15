# Requirements: F0 - Asset CRUD + Event Sourcing

**Epic:** [E2 - Asset Inventory](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Deliver the core Asset entity with types, statuses (state machine), CRUD endpoints, and the event sourcing infrastructure that records every mutation as an append-only event.

---

## Requirements

### R1: Asset Entity
- Asset has: id, company_id, type, brand, model, serial_number, status, assigned_to, department_id, purchase_date, warranty_expiration, notes, created_at, updated_at
- Serial number is unique within a company
- Default status is `in_stock`

### R2: Asset Types
- Enum values: `laptop`, `monitor`, `keyboard`, `mouse`, `headset`, `docking_station`, `other`
- Type is required on creation and immutable after

### R3: Asset Status State Machine
- Statuses: `in_stock`, `assigned`, `in_repair`, `decommissioned`
- Valid transitions:
  - `in_stock` -> `in_repair`, `decommissioned`
  - `assigned` -> `in_repair`, `decommissioned`
  - `in_repair` -> `in_stock`, `decommissioned`
  - `decommissioned` -> (terminal)
- Note: `in_stock` -> `assigned` and `assigned` -> `in_stock` are handled by assign/unassign commands in F1, not the generic status change endpoint
- Invalid transitions return error

### R4: Asset Event Sourcing
- Every asset mutation creates an AssetEvent record
- Event types: `created`, `updated`, `status_changed`  (F1 adds `assigned`, `unassigned`)
- Each event stores: asset_id, event_type, data (JSON), performed_by (user_id), created_at
- Events are immutable (never updated or deleted)
- Event history endpoint returns all events for an asset

### R5: CRUD Endpoints
- POST /api/v1/assets — create (technician+)
- GET /api/v1/assets — list with pagination (technician+)
- GET /api/v1/assets/{id} — detail (technician+)
- PUT /api/v1/assets/{id} — update metadata (technician+)
- PATCH /api/v1/assets/{id}/status — change status (technician+)
- GET /api/v1/assets/{id}/history — event history (technician+)

### R6: Validation Rules
- brand, model, serial_number are required (non-empty strings)
- type must be a valid AssetType enum value
- serial_number unique within company (case-insensitive)
- purchase_date and warranty_expiration are optional dates
- Status change validates against state machine

### R7: Multi-tenancy
- All asset queries filtered by company_id
- Asset detail returns 404 for assets in other companies
