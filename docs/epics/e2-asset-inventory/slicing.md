# Slicing: E2 - Asset Inventory

**Epic:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-02-15

---

## Feature Breakdown

| Feature | Description | User Stories | Complexity |
|---|---|---|---|
| **F0** | Asset CRUD + Event Sourcing | US-001, US-002, US-004 | High |
| **F1** | Asset Assignment + My Equipment | US-003, US-007 | Medium |
| **F2** | Search, Filters + CSV Import | US-005, US-006 | Medium |

---

## F0: Asset CRUD + Event Sourcing

**Scope:** Core asset entity, types/statuses with state machine, CRUD endpoints, event sourcing infrastructure.

**Why F0:** Everything else depends on Asset existing. Event sourcing must be baked in from the start — retrofitting it later would mean missing events for early assets.

**Includes:**
- Asset entity with type, status, state machine
- AssetEvent entity (append-only)
- AssetRepository with event recording
- Create, update, change status commands (each records events)
- List assets, get asset detail, get asset history queries
- HTTP router for CRUD + status change + history
- Alembic migration (assets + asset_events tables)

**Endpoints:**
- `POST /api/v1/assets` — create asset (technician+)
- `GET /api/v1/assets` — list assets with basic pagination (technician+)
- `GET /api/v1/assets/{id}` — get asset detail (technician+)
- `PUT /api/v1/assets/{id}` — update asset metadata (technician+)
- `PATCH /api/v1/assets/{id}/status` — change status (technician+)
- `GET /api/v1/assets/{id}/history` — get event history (technician+)

---

## F1: Asset Assignment + My Equipment

**Scope:** Assign/unassign assets to employees, status transitions for assignment, employee "My Equipment" view.

**Why F1:** Assignment is the primary business operation — it connects assets to people. My Equipment is the employee-facing feature.

**Depends on:** F0 (Asset entity and events must exist)

**Includes:**
- Assign/unassign commands with validation (user active, asset in correct status)
- Assignment events (assigned, unassigned)
- Auto-sync department_id from user on assign
- My Equipment query (assets assigned to current user)
- HTTP endpoints for assign/unassign + my equipment router

**Endpoints:**
- `PATCH /api/v1/assets/{id}/assign` — assign to employee (technician+)
- `PATCH /api/v1/assets/{id}/unassign` — remove assignment (technician+)
- `GET /api/v1/my/equipment` — my assigned assets (employee+)

---

## F2: Search, Filters + CSV Import

**Scope:** Advanced search/filter capabilities and bulk CSV import.

**Why F2:** Search/filters enhance the list endpoint from F0. CSV import is a convenience feature for initial data load.

**Depends on:** F0 (basic list exists), F1 (assigned_to filter needs assignment)

**Includes:**
- Extended list query with: search (serial, brand, model), filters (type, status, department, assigned_to), sorting
- CSV import command with row-level validation and error reporting
- Import endpoint with file upload

**Endpoints:**
- `GET /api/v1/assets` — enhanced with search, filters, sort (extends F0)
- `POST /api/v1/assets/import` — CSV bulk import (technician+)

---

## Dependency Graph

```
F0: Asset CRUD + Event Sourcing
 │
 ├── F1: Assignment + My Equipment
 │
 └── F2: Search, Filters + CSV Import
```

F1 and F2 both depend on F0 but are independent of each other. However, F2's filter by `assigned_to` is more meaningful after F1 implements assignment, so sequential order is recommended.

---

## Implementation Order

1. **F0** — Asset CRUD + Event Sourcing (foundation)
2. **F1** — Asset Assignment + My Equipment (primary business logic)
3. **F2** — Search, Filters + CSV Import (enhancement)
