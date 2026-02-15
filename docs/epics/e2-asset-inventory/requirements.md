# Epic E2: Asset Inventory

**Type:** Epic
**Status:** Pending Validation
**Created:** 2026-02-15
**Priority:** High
**Depends on:** E1 (Company Management)

---

## Business Alignment

**Objective:** Enable IT technicians to manage a full inventory of company assets (laptops, monitors, peripherals, etc.), assign them to employees, and maintain a complete audit trail of every change via event sourcing.

This epic delivers the core asset management capability. Without E2, the platform has no business value beyond user management. Assets are the primary data object for service requests (E3), reports (E6), and the admin dashboard (E5).

---

## Problem Statement

### Current Situation
E0+E1 delivered authentication, RBAC, company management, departments, and user management. But:
- No asset tracking capability
- No way for technicians to manage hardware inventory
- No assignment of equipment to employees
- No audit trail for asset lifecycle
- Employees cannot see what equipment they have

### What E2 Delivers
A complete asset inventory system where:
- Technicians register, update, and manage assets
- Assets are assigned/unassigned to employees
- Every change is recorded as an append-only event (event sourcing)
- Employees can view their assigned equipment ("My Equipment")
- Technicians can search, filter, and bulk-import assets via CSV

---

## Proposed Solution

### US-E2-001: Asset CRUD (Technician)
**As a** technician
**I want** to register and manage assets in our company inventory
**So that** we have an accurate record of all company equipment

**Acceptance Criteria:**
- [ ] `POST /api/v1/assets` creates an asset with: type, brand, model, serial_number, purchase_date, warranty_expiration, notes
- [ ] `GET /api/v1/assets` lists assets with pagination, filtering, and search
- [ ] `GET /api/v1/assets/{id}` returns asset details including current assignment and event history
- [ ] `PUT /api/v1/assets/{id}` updates asset metadata (brand, model, notes, warranty dates)
- [ ] Only technician+ role can create/update assets
- [ ] Assets are scoped by company_id (multi-tenancy)
- [ ] Serial number must be unique within a company
- [ ] Asset is created in `in_stock` status by default

### US-E2-002: Asset Types and Statuses
**As a** technician
**I want** assets to have standardized types and statuses
**So that** I can categorize and track them consistently

**Acceptance Criteria:**
- [ ] Asset types: `laptop`, `monitor`, `keyboard`, `mouse`, `headset`, `docking_station`, `other`
- [ ] Asset statuses: `in_stock`, `assigned`, `in_repair`, `decommissioned`
- [ ] Status transitions are validated:
  - `in_stock` -> `assigned`, `in_repair`, `decommissioned`
  - `assigned` -> `in_stock` (via unassignment), `in_repair`, `decommissioned`
  - `in_repair` -> `in_stock`, `decommissioned`
  - `decommissioned` -> (terminal, no transitions out)
- [ ] Invalid transitions return 409

### US-E2-003: Asset Assignment
**As a** technician
**I want** to assign and unassign assets to employees
**So that** we track who has what equipment

**Acceptance Criteria:**
- [ ] `PATCH /api/v1/assets/{id}/assign` assigns asset to an employee (user_id, optionally department_id)
- [ ] `PATCH /api/v1/assets/{id}/unassign` removes current assignment
- [ ] Assignment changes status from `in_stock` to `assigned`
- [ ] Unassignment changes status from `assigned` to `in_stock`
- [ ] Cannot assign an asset that is `in_repair` or `decommissioned`
- [ ] Cannot assign to a deactivated user
- [ ] Assignment records who assigned it and when (via event)
- [ ] Only technician+ role can assign/unassign

### US-E2-004: Asset Event History (Event Sourcing)
**As a** technician
**I want** a complete audit trail of every change to an asset
**So that** I can trace the full lifecycle of any piece of equipment

**Acceptance Criteria:**
- [ ] Every mutation creates an append-only event in `asset_events` table
- [ ] Event types: `created`, `updated`, `assigned`, `unassigned`, `status_changed`, `note_added`
- [ ] Each event records: asset_id, event_type, data (JSON), performed_by (user_id), timestamp
- [ ] `GET /api/v1/assets/{id}/history` returns all events for an asset ordered by timestamp
- [ ] Events are never updated or deleted (append-only)
- [ ] Current asset state can be derived from events (but is also stored in the asset table for read performance)

### US-E2-005: Asset Search and Filters
**As a** technician
**I want** to search and filter the asset inventory
**So that** I can quickly find specific equipment

**Acceptance Criteria:**
- [ ] Search by: serial_number, brand, model (partial match)
- [ ] Filter by: type, status, department_id, assigned_to (user_id)
- [ ] Filter unassigned assets: `assigned_to=none`
- [ ] Pagination with page and page_size
- [ ] Sort by: created_at, purchase_date, warranty_expiration (default: created_at desc)
- [ ] Only technician+ role can access full inventory

### US-E2-006: CSV Bulk Import
**As a** technician
**I want** to import multiple assets at once via CSV
**So that** I can quickly onboard existing inventory

**Acceptance Criteria:**
- [ ] `POST /api/v1/assets/import` accepts a CSV file upload
- [ ] CSV columns: type, brand, model, serial_number, purchase_date, warranty_expiration, notes
- [ ] Validates each row: required fields, valid type, unique serial_number
- [ ] Returns summary: total rows, successful imports, failed rows with error details
- [ ] Duplicate serial numbers (within CSV or existing) are reported but don't block other rows
- [ ] Only technician+ role can import
- [ ] Max file size: 1MB (reasonable limit for inventory CSV)

### US-E2-007: My Equipment (Employee)
**As an** employee
**I want** to see all assets currently assigned to me
**So that** I know what company equipment I'm responsible for

**Acceptance Criteria:**
- [ ] `GET /api/v1/my/equipment` returns all assets assigned to the current user
- [ ] Response includes: type, brand, model, serial_number, assigned_at date
- [ ] Any authenticated user can access (employee+ role)
- [ ] Only shows assets in `assigned` status
- [ ] Scoped by company_id (multi-tenancy)

---

## Entities

| Entity | Description | New in E2? |
|---|---|---|
| `Asset` | Equipment tracked in inventory | New |
| `AssetEvent` | Append-only event for audit trail | New |

### Asset Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `company_id` | ULID | FK to Company, NOT NULL, indexed |
| `type` | enum | laptop, monitor, keyboard, mouse, headset, docking_station, other |
| `brand` | string(255) | NOT NULL |
| `model` | string(255) | NOT NULL |
| `serial_number` | string(255) | NOT NULL, unique within company |
| `status` | enum | in_stock, assigned, in_repair, decommissioned |
| `assigned_to` | ULID | FK to User, nullable, indexed |
| `department_id` | ULID | FK to Department, nullable, indexed |
| `purchase_date` | date | nullable |
| `warranty_expiration` | date | nullable |
| `notes` | text | nullable |
| `created_at` | datetime | Auto |
| `updated_at` | datetime | Auto |

**Constraint:** UNIQUE(company_id, serial_number)

### AssetEvent Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `asset_id` | ULID | FK to Asset, NOT NULL, indexed |
| `event_type` | string(50) | created, updated, assigned, unassigned, status_changed, note_added |
| `data` | JSON | Event-specific payload |
| `performed_by` | ULID | FK to User, NOT NULL |
| `created_at` | datetime | Auto, NOT NULL |

**No updated_at** — events are immutable.

---

## Use Cases

### UC-E2-001: Register Asset
**Actor:** Technician
**Preconditions:** Authenticated as technician+ in an active company

**Main Flow:**
1. Technician provides asset metadata (type, brand, model, serial_number, etc.)
2. System validates serial_number is unique within company
3. System creates Asset record (status=in_stock)
4. System creates AssetEvent (type=created)
5. Returns created asset

**Alternative Flows:**
- A1: Serial number already exists -> 409 "Asset with this serial number already exists"

### UC-E2-002: Assign Asset
**Actor:** Technician
**Preconditions:** Asset exists, status is `in_stock`

**Main Flow:**
1. Technician provides user_id to assign asset to
2. System validates user exists in same company and is active
3. System updates asset: assigned_to=user_id, status=assigned
4. System creates AssetEvent (type=assigned, data={user_id, assigned_by})
5. Returns updated asset

**Alternative Flows:**
- A1: Asset not in `in_stock` status -> 409 "Asset must be in stock to assign"
- A2: User not found in company -> 404 "User not found"
- A3: User is deactivated -> 409 "Cannot assign to inactive user"

### UC-E2-003: Bulk Import Assets
**Actor:** Technician
**Preconditions:** Authenticated as technician+

**Main Flow:**
1. Technician uploads CSV file
2. System parses CSV, validates each row
3. For each valid row: creates Asset + AssetEvent
4. Returns import summary with successes and failures

**Alternative Flows:**
- A1: Invalid CSV format -> 422 "Invalid CSV format"
- A2: Row has missing required fields -> included in failure details
- A3: Duplicate serial number -> included in failure details

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `models_registry.py` | Add AssetModel, AssetEventModel | Update imports |
| `app.py` | Register asset router, my-equipment router | Update router includes |
| Alembic | New migration for assets + asset_events tables | Generate migration |

---

## Bounded Context

```
src/asset_bc/
├── asset/
│   ├── domain/
│   │   ├── entities.py         # Asset, AssetEvent entities
│   │   ├── enums.py            # AssetType, AssetStatus enums + transitions
│   │   └── repository.py       # AssetRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_asset.py
│   │   │   ├── update_asset.py
│   │   │   ├── assign_asset.py
│   │   │   ├── unassign_asset.py
│   │   │   ├── change_asset_status.py
│   │   │   └── import_assets.py
│   │   └── queries/
│   │       ├── list_assets.py
│   │       ├── get_asset.py
│   │       ├── get_asset_history.py
│   │       └── my_equipment.py
│   └── infrastructure/
│       ├── models.py           # AssetModel, AssetEventModel
│       └── repository.py       # AssetRepository

adapters/http/api/
├── assets/
│   ├── routers.py              # Asset CRUD + assign/unassign + import (technician)
│   └── schemas.py
├── my/
│   ├── routers.py              # My Equipment (employee)
│   └── schemas.py
```

---

## Definition of Done

- [ ] Technician can create, view, update assets via API
- [ ] Asset types and statuses are enforced with valid transitions
- [ ] Technician can assign/unassign assets to employees
- [ ] Every asset mutation creates an append-only event
- [ ] Asset history endpoint returns full audit trail
- [ ] Search and filter work across all criteria
- [ ] CSV bulk import works with error reporting
- [ ] Employees can view their assigned equipment
- [ ] All endpoints respect RBAC (technician+ for inventory, employee+ for my equipment)
- [ ] All queries scoped by company_id
- [ ] Alembic migration creates tables and indexes
- [ ] Unit tests for domain entities, business rules, and state machine
- [ ] API tests for all endpoints

---

## Open Questions

1. **Asset decommission:** Should decommissioned assets be hidden from default list views, or shown with a visual indicator? Recommend: shown but filterable (like department soft delete).
2. **CSV import atomicity:** Should the import be all-or-nothing (transaction), or process each row independently? Recommend: independent rows so one bad row doesn't block the rest.
3. **Asset-department link:** When assigning to a user, should asset.department_id auto-update to the user's department? Recommend: yes, auto-sync for convenience.
