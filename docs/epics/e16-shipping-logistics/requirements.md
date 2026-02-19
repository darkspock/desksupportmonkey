# Requirements: E16 - Shipping & Logistics

**Type:** Epic
**Status:** Validated
**Created:** 2026-02-18
**Author:** AI
**Priority:** Medium
**Depends on:** E2 (Asset Inventory), E3 (Service Requests), E14 (Procurement & Budget)

---

## Business Alignment

**Objective:** Enable IT teams to ship equipment to employees (home, office, or vendor for repair), track shipments from dispatch to delivery, manage return logistics, and maintain full audit trail of where equipment is at any given time.

**KPI Targets:**
- 100% of asset movements have a traceable shipment record
- Average shipment resolution time visible per carrier and destination type
- Return rate and turnaround time tracked per vendor (repair shipments)
- Zero lost-in-transit assets due to missing tracking information

**Evidence:**
- Remote/hybrid work requires shipping equipment to employee homes (laptops, peripherals, monitors)
- Repair workflows (E3) currently have no way to track when equipment is sent to a vendor and when it comes back
- New equipment from POs (E14) needs delivery tracking to the employee or office
- IT managers need visibility into assets that are "in transit" vs "in stock" vs "assigned"
- E22 (Onboarding/Offboarding) will depend on this for automated equipment delivery workflows

---

## Problem Statement

### Current Situation
When a technician ships equipment to an employee or sends an asset for repair, there is no structured way to record the shipment, track its status, or confirm delivery. The asset status jumps directly from one state to another with no visibility into the transit period. Delivery addresses are not stored anywhere in the system — technicians rely on email threads or external tools.

### Pain Points
1. **No transit visibility** — Assets go from "in stock" to "assigned" with no record of the shipping step. If a package is lost, there is no audit trail.
2. **No address management** — Employee delivery addresses (home, office) are not stored in the system. Technicians copy-paste addresses from emails or spreadsheets.
3. **No return tracking** — When equipment is sent for repair or an employee returns equipment, there is no structured way to track the inbound shipment.
4. **No carrier information** — Tracking numbers, carrier names, and estimated delivery dates are scattered across emails and notes fields.
5. **No shipment history** — When an asset has been shipped multiple times (initial delivery, repair, replacement), there is no consolidated view of its shipment history.

### Impact if Not Solved
- Lost equipment with no traceability, leading to financial losses and audit failures
- Manual email-based coordination for every shipment, wasting technician time
- No data for optimizing carrier selection or identifying problematic routes
- E22 (Onboarding/Offboarding) cannot automate equipment delivery without structured shipment management

---

## Goals

1. **Structured shipment lifecycle** — Create, dispatch, track, deliver, and return shipments with full state machine and audit trail
2. **Reusable address book** — Store and reuse delivery addresses for employees and offices, eliminating manual address lookup
3. **Carrier tracking** — Record carrier name, tracking number, and tracking URL for every shipment
4. **Bidirectional flow** — Support both outbound shipments (to employee/office/vendor) and inbound returns (from employee/vendor)
5. **Asset linkage** — Every shipment links to the assets being shipped, providing a complete movement history per asset
6. **Request and PO linkage** — Shipments can optionally link to a service request (repair) or purchase order (new equipment delivery)
7. **Notification flow** — Notify employees when their equipment is shipped, delivered, or when a return is expected

---

## Validation Decisions (Closed)

1. **Carrier integration scope.** Decided: Store carrier name, tracking number, and tracking URL as text fields. No real-time API integration with carriers (FedEx, UPS, DHL). Technicians manually enter tracking info and update status. Real-time carrier API integration is a future enhancement, not MVP.

2. **Asset status extension.** Decided: Do NOT add new statuses to `AssetStatus` enum. The shipment lifecycle is managed entirely within `shipping_bc`. Assets remain in their current status (e.g., `IN_STOCK`, `IN_REPAIR`) and are updated only at terminal shipment events (e.g., outbound delivery confirmed → mark asset as `ASSIGNED`; repair return delivered → mark asset as `IN_STOCK`). This follows E14's pattern where PO lifecycle is independent from asset statuses.

3. **Address model.** Decided: Create a `ShippingAddress` entity within `shipping_bc` that stores structured addresses (street, city, state, zip, country) linked to a company. Addresses are reusable — an employee's home address can be saved and reused for future shipments. This entity will also serve E22's needs.

4. **Shipment direction.** Decided: A single `Shipment` entity with a `direction` field (`outbound` | `inbound`) and a `destination_type` field (`employee_home` | `office` | `vendor`) handles all cases. No separate entities for outbound vs inbound.

5. **Return workflow.** Decided: Returns are modeled as a new `inbound` shipment linked to the original `outbound` shipment via `return_for_shipment_id`. This allows independent lifecycle tracking for each direction while maintaining the relationship.

6. **Multi-asset shipments.** Decided: A single shipment can contain multiple assets (e.g., laptop + monitor + peripherals for onboarding). The relationship is many-to-many via a `shipment_items` table.

---

## Non-Goals (This Epic)

- Real-time carrier API integration (webhook-based tracking updates from FedEx/UPS/DHL)
- Automated shipping label generation or printing
- Shipping cost estimation or rate comparison
- International customs/duties management
- Automated return request workflow for employees (E22 will handle return-on-offboarding)
- Warehouse/location management beyond simple office addresses

---

## User Stories

### US-E16-001: Create Outbound Shipment
**As a** technician, **I want to** create a shipment for one or more assets with a destination address, carrier, and tracking info, **so that** I can record that equipment is being sent to an employee, office, or vendor.

**Acceptance Criteria:**
- [ ] Can select one or more assets to include in the shipment
- [ ] Can choose destination type: employee_home, office, or vendor
- [ ] Can select or create a delivery address
- [ ] Can enter carrier name, tracking number, and tracking URL (all optional at creation)
- [ ] Can optionally link to a service request or purchase order
- [ ] Can add shipment notes
- [ ] Shipment is created in DRAFT status
- [ ] Only assets belonging to the same company can be shipped together
- [ ] An asset already in an active shipment (DRAFT/DISPATCHED/IN_TRANSIT) cannot be added to another shipment

### US-E16-002: Dispatch and Track Shipment
**As a** technician, **I want to** mark a shipment as dispatched and update tracking information, **so that** I can track the shipment's progress from warehouse to destination.

**Acceptance Criteria:**
- [ ] Can transition shipment from DRAFT → DISPATCHED (requires carrier + tracking number)
- [ ] Can update tracking number and tracking URL after dispatch
- [ ] Can mark shipment as IN_TRANSIT (optional intermediate state after dispatch)
- [ ] Can mark shipment as DELIVERED with delivery confirmation date
- [ ] Can mark shipment as FAILED with a failure reason
- [ ] Each status change is recorded with timestamp and performed_by
- [ ] Can add/remove items while shipment is in DRAFT status
- [ ] Items are locked (cannot be modified) after shipment is DISPATCHED

### US-E16-003: Manage Delivery Addresses
**As a** technician, **I want to** save and manage delivery addresses for employees and offices, **so that** I can reuse them for future shipments without re-entering the information.

**Acceptance Criteria:**
- [ ] Can create an address with: label, recipient_name, street_line_1, street_line_2 (optional), city, state, postal_code, country, phone (optional)
- [ ] Can associate an address with a user_id (employee) or mark it as an office address
- [ ] Can list all addresses for the company
- [ ] Can update an existing address
- [ ] Can soft-delete (deactivate) an address
- [ ] Address is auto-suggested when selecting a destination for a known employee

### US-E16-004: Create Return Shipment
**As a** technician, **I want to** create a return shipment for equipment coming back from an employee or vendor, **so that** I can track inbound asset movements.

**Acceptance Criteria:**
- [ ] Can create an inbound shipment linked to an original outbound shipment
- [ ] Can create a standalone inbound shipment (e.g., vendor returning repaired equipment)
- [ ] Return shipment has its own lifecycle (DRAFT → DISPATCHED → IN_TRANSIT → DELIVERED)
- [ ] When a return is delivered, linked assets can be updated (e.g., repair → IN_STOCK)
- [ ] Can record condition notes on return delivery (e.g., "arrived damaged")

### US-E16-005: View Shipment History per Asset
**As a** technician or admin, **I want to** see all shipments associated with an asset, **so that** I can trace the complete movement history of that equipment.

**Acceptance Criteria:**
- [ ] Asset detail page shows a "Shipment History" section
- [ ] Lists all shipments (outbound and inbound) containing this asset
- [ ] Shows shipment status, destination, carrier, dates
- [ ] Sorted by date descending (most recent first)

### US-E16-006: Shipment Notifications
**As an** employee, **I want to** receive notifications when equipment is shipped to me and when I need to return equipment, **so that** I know when to expect deliveries and what actions are needed.

**Acceptance Criteria:**
- [ ] Employee receives notification when a shipment is dispatched to them
- [ ] Employee receives notification when a shipment is marked as delivered
- [ ] Technician receives notification when a return shipment is delivered
- [ ] Technician receives notification when a shipment fails

### US-E16-007: My Shipments (Employee)
**As an** employee, **I want to** see a list of shipments sent to me, **so that** I can track incoming equipment and know when deliveries are expected.

**Acceptance Criteria:**
- [ ] Employee can view a paginated list of shipments where they are the recipient (`recipient_user_id`)
- [ ] Shows shipment status, carrier, tracking number (clickable URL), dispatched/delivered dates
- [ ] Sorted by date descending (most recent first)
- [ ] Accessible via sidebar "My Shipments" link

### US-E16-008: Shipment Dashboard
**As an** admin, **I want to** see a summary of active shipments and recent deliveries on the dashboard, **so that** I can monitor logistics activity at a glance.

**Acceptance Criteria:**
- [ ] Dashboard shows count of active shipments by status (draft, dispatched, in_transit)
- [ ] Dashboard shows recent deliveries (last 7 days)
- [ ] Dashboard shows failed shipments requiring attention

---

## Entities

| Entity | Description | States |
|--------|-------------|--------|
| Shipment | A package of one or more assets being shipped from/to a location | DRAFT, DISPATCHED, IN_TRANSIT, DELIVERED, FAILED, CANCELLED |
| ShipmentItem | Links a shipment to a specific asset | (no states, junction table) |
| ShippingAddress | A reusable delivery address linked to a company | (no states, soft-delete via is_active) |

### State Machine: Shipment

```
                ┌──────────┐
                │  DRAFT   │
                └────┬─────┘
                     │ dispatch (requires carrier + tracking)
                     ▼
              ┌──────────────┐
              │  DISPATCHED  │
              └──┬───────┬───┘
                 │       │
      in_transit │       │ deliver (shortcut for local/same-day)
                 ▼       │
          ┌────────────┐ │
          │ IN_TRANSIT  │ │
          └──┬──────┬──┘ │
             │      │    │
     deliver │ fail │    │
             ▼      ▼    ▼
      ┌──────────┐ ┌────────┐
      │ DELIVERED│ │ FAILED │
      └──────────┘ └────────┘

  Any non-terminal state → CANCELLED (with reason)
```

### State Transitions

| From | To | Trigger | Conditions | Side Effects |
|------|----|---------|------------|--------------|
| DRAFT | DISPATCHED | dispatch | carrier + tracking_number required | Set dispatched_at, notify recipient |
| DRAFT | CANCELLED | cancel | reason required | — |
| DISPATCHED | IN_TRANSIT | mark_in_transit | — | Update tracking info |
| DISPATCHED | DELIVERED | deliver | — | Set delivered_at, update linked assets, notify recipient |
| DISPATCHED | FAILED | fail | reason required | Notify technician |
| DISPATCHED | CANCELLED | cancel | reason required | — |
| IN_TRANSIT | DELIVERED | deliver | — | Set delivered_at, update linked assets, notify recipient |
| IN_TRANSIT | FAILED | fail | reason required | Notify technician |
| IN_TRANSIT | CANCELLED | cancel | reason required | — |

### CRUD Operations

| Entity | Create | Read | Update | Delete | List | Filter | Search |
|--------|--------|------|--------|--------|------|--------|--------|
| Shipment | POST | GET by id | PATCH (tracking, notes) | — (cancel instead) | GET paginated | status, direction, destination_type, asset_id, request_id, po_id | — |
| ShipmentItem | via Shipment create | via Shipment detail | — | — | via Shipment detail | — | — |
| ShippingAddress | POST | GET by id | PUT | soft-delete (deactivate) | GET paginated | user_id, is_office, is_active | — |

### Inverse Operations

| Action | Inverse | Notes |
|--------|---------|-------|
| Dispatch shipment | Cancel shipment | Cancellation requires reason |
| Deliver shipment | Create return shipment | Return is a new inbound shipment |
| Fail shipment | Re-dispatch (create new shipment) | Failed shipments are terminal |

---

## Use Cases

### UC-001: Create and Dispatch Outbound Shipment

**Actor:** Technician
**Preconditions:** Assets exist and belong to the technician's company. Destination address exists or is created inline.
**Postconditions:** Shipment record created with linked assets. If dispatched, recipient notified.

**Main Flow:**
1. Technician navigates to Shipments page and clicks "New Shipment"
2. Selects direction: Outbound
3. Selects destination type: employee_home / office / vendor
4. Selects or creates destination address
5. Selects one or more assets to ship
6. Optionally links a service request or purchase order
7. Enters carrier, tracking number, tracking URL (optional at draft)
8. Adds notes (optional)
9. Saves as DRAFT
10. Clicks "Dispatch" — validates carrier + tracking number are present
11. Shipment moves to DISPATCHED, dispatched_at is recorded
12. Notification sent to recipient (employee or vendor contact)

**Alternative Flows:**
- 7a. Technician saves as DRAFT without carrier info (will add later before dispatch)
- 10a. Carrier or tracking number missing → validation error, remains DRAFT

**Error Scenarios:**
- Asset does not belong to company → 403
- Address does not belong to company → 403
- Invalid state transition → 409

### UC-002: Record Delivery

**Actor:** Technician
**Preconditions:** Shipment is in DISPATCHED or IN_TRANSIT status.
**Postconditions:** Shipment marked DELIVERED. Linked assets updated if applicable.

**Main Flow:**
1. Technician opens shipment detail
2. Clicks "Mark Delivered"
3. Optionally adds delivery notes
4. System records delivered_at timestamp
5. If outbound to employee_home: linked assets are marked as ASSIGNED to the destination employee
6. If inbound (return from repair): linked assets are marked as IN_STOCK
7. Notification sent to relevant party

**Alternative Flows:**
- 5a. Outbound to vendor (repair): assets remain in IN_REPAIR status — the repair return will be a separate inbound shipment
- 5b. Outbound to office: assets remain in IN_STOCK (just relocated)

**Error Scenarios:**
- Shipment already delivered or cancelled → 409

### UC-003: Create Return Shipment

**Actor:** Technician
**Preconditions:** Original outbound shipment exists (DELIVERED or any status).
**Postconditions:** Inbound shipment created, linked to original outbound shipment.

**Main Flow:**
1. Technician opens an existing outbound shipment
2. Clicks "Create Return"
3. System pre-fills: direction=inbound, assets from original shipment, origin=original destination address
4. Technician enters return destination (warehouse/office address)
5. Enters carrier and tracking info (optional at draft)
6. Saves as DRAFT
7. Return shipment follows its own lifecycle independently

**Alternative Flows:**
- 3a. Technician can modify assets (partial return) or add different assets

**Error Scenarios:**
- Original shipment not found → 404

### UC-004: Manage Address Book

**Actor:** Technician or Admin
**Preconditions:** User has technician+ role.
**Postconditions:** Address created/updated/deactivated.

**Main Flow:**
1. Technician navigates to Addresses page or creates address inline during shipment creation
2. Enters: label, recipient_name, street lines, city, state, postal_code, country, phone
3. Optionally links to a user_id (employee's personal address) or marks as office address
4. Saves address
5. Address appears in future shipment destination dropdowns

**Alternative Flows:**
- 2a. Address already exists for this employee → technician selects from existing list
- 4a. Deactivate address → soft-delete, no longer shown in dropdowns

**Error Scenarios:**
- Missing required fields → 422

### UC-005: View Asset Shipment History

**Actor:** Technician or Admin
**Preconditions:** Asset exists.
**Postconditions:** None (read-only).

**Main Flow:**
1. Technician opens asset detail page
2. Scrolls to "Shipment History" section
3. Sees list of all shipments containing this asset (outbound and inbound)
4. Each entry shows: direction, destination, carrier, status, dispatched_at, delivered_at
5. Can click shipment to navigate to shipment detail

### UC-006: Shipment Failure and Resolution

**Actor:** Technician
**Preconditions:** Shipment is in DISPATCHED or IN_TRANSIT status.
**Postconditions:** Shipment marked FAILED. Technician creates new shipment to reattempt.

**Main Flow:**
1. Technician learns shipment has failed (carrier notification, customer report)
2. Opens shipment detail, clicks "Mark Failed"
3. Enters failure reason (required)
4. Shipment moves to FAILED status
5. Notification sent to creating technician
6. Technician creates a new shipment for the same assets to reattempt delivery

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Asset Detail (frontend) | Add "Shipment History" section | Edit AssetDetailPage.tsx |
| Request Detail (frontend) | Show linked shipments if any | Edit RequestDetailPage.tsx |
| Dashboard (frontend) | Add active shipments card | Edit DashboardPage.tsx |
| Notification EventTypes | Add 5 shipment events | Edit enums.py |
| Notification TargetResolver | Add shipment event resolvers | Edit target_resolver.py |
| Sidebar | Add "Shipments" nav item | Edit Sidebar.tsx |
| Router | Add shipment routes | Edit router.tsx |
| i18n | Add ~80 keys per language | Edit en.ts, es.ts |
| app.py | Register shipment + address routers | Edit app.py |

---

## Domain & Data (High-Level)

### New Bounded Context: `shipping_bc`

#### Subdomain: `shipment`

**Entity: `Shipment`**
- `id: str` (ULID)
- `company_id: str` (tenant isolation)
- `direction: ShipmentDirection` — OUTBOUND | INBOUND
- `destination_type: DestinationType` — EMPLOYEE_HOME | OFFICE | VENDOR
- `status: ShipmentStatus` — DRAFT | DISPATCHED | IN_TRANSIT | DELIVERED | FAILED | CANCELLED
- `origin_address_id: str | None` — FK to ShippingAddress (origin)
- `destination_address_id: str` — FK to ShippingAddress (destination)
- `recipient_name: str | None` — display name of recipient
- `carrier: str | None` — carrier name (FedEx, UPS, DHL, etc.)
- `tracking_number: str | None` — carrier tracking code
- `tracking_url: str | None` — URL to carrier tracking page
- `request_id: str | None` — optional link to ServiceRequest
- `po_id: str | None` — optional link to PurchaseOrder
- `return_for_shipment_id: str | None` — for inbound returns, links to original outbound
- `recipient_user_id: str | None` — FK to User (employee receiving the shipment, enables /my/shipments and notification routing)
- `notes: str | None`
- `failure_reason: str | None`
- `cancellation_reason: str | None`
- `created_by: str` — user who created
- `dispatched_at: datetime | None`
- `delivered_at: datetime | None`
- `created_at: datetime`
- `updated_at: datetime`

**Enum: `ShipmentStatus`**
```
DRAFT = "draft"
DISPATCHED = "dispatched"
IN_TRANSIT = "in_transit"
DELIVERED = "delivered"
FAILED = "failed"
CANCELLED = "cancelled"
```

**Enum: `ShipmentDirection`**
```
OUTBOUND = "outbound"
INBOUND = "inbound"
```

**Enum: `DestinationType`**
```
EMPLOYEE_HOME = "employee_home"
OFFICE = "office"
VENDOR = "vendor"
```

**Entity: `ShipmentItem`**
- `id: str` (ULID)
- `shipment_id: str` — FK to Shipment
- `asset_id: str` — FK to Asset
- `notes: str | None` — per-item notes (e.g., condition on return)

#### Subdomain: `address`

**Entity: `ShippingAddress`**
- `id: str` (ULID)
- `company_id: str` (tenant isolation)
- `label: str` — display label (e.g., "Home", "Office NYC", "Vendor Warehouse")
- `recipient_name: str | None`
- `street_line_1: str`
- `street_line_2: str | None`
- `city: str`
- `state: str`
- `postal_code: str`
- `country: str` — ISO 3166-1 alpha-2 (default "US")
- `phone: str | None`
- `user_id: str | None` — FK to User (if employee address)
- `is_office: bool` — true if company office address
- `is_active: bool` — soft-delete
- `created_at: datetime`
- `updated_at: datetime`

### Computed Values (Not Stored)
- `shipment.item_count` — count of ShipmentItems
- `shipment.days_in_transit` — difference between dispatched_at and now (or delivered_at)

### New Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `shipments` | Shipment records | id, company_id, direction, destination_type, status, carrier, tracking_number, ... |
| `shipment_items` | Assets in a shipment | id, shipment_id, asset_id, notes |
| `shipping_addresses` | Reusable delivery addresses | id, company_id, label, street_line_1, city, state, postal_code, country, user_id, is_office |

### Events
- `shipment.created` — Shipment created (draft)
- `shipment.dispatched` — Shipment dispatched (carrier + tracking assigned)
- `shipment.delivered` — Shipment delivered to destination
- `shipment.failed` — Shipment failed (lost, damaged, returned to sender)
- `shipment.cancelled` — Shipment cancelled (notify recipient if already dispatched)

### Dashboard Extensions
- **Active Shipments card** — count by status (draft, dispatched, in_transit)
- **Recent Deliveries** — last 7 days list
- **Failed Shipments** — count requiring attention

---

## API Endpoints (High-Level)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/shipments | technician+ | Create shipment (draft) |
| GET | /api/v1/shipments | technician+ | List shipments (paginated, filtered) |
| GET | /api/v1/shipments/{id} | technician+ | Get shipment detail with items |
| PATCH | /api/v1/shipments/{id} | technician+ | Update tracking info, notes |
| POST | /api/v1/shipments/{id}/dispatch | technician+ | Dispatch shipment |
| POST | /api/v1/shipments/{id}/in-transit | technician+ | Mark in transit |
| POST | /api/v1/shipments/{id}/deliver | technician+ | Mark delivered |
| POST | /api/v1/shipments/{id}/fail | technician+ | Mark failed |
| POST | /api/v1/shipments/{id}/cancel | technician+ | Cancel shipment |
| POST | /api/v1/shipments/{id}/return | technician+ | Create return shipment from existing |
| GET | /api/v1/shipments/by-asset/{asset_id} | technician+ | Shipment history for an asset |
| POST | /api/v1/addresses | technician+ | Create address |
| GET | /api/v1/addresses | technician+ | List addresses |
| GET | /api/v1/addresses/{id} | technician+ | Get address detail |
| PUT | /api/v1/addresses/{id} | technician+ | Update address |
| DELETE | /api/v1/addresses/{id} | technician+ | Deactivate address |
| GET | /api/v1/addresses/by-user/{user_id} | technician+ | Get addresses for a user |
| GET | /api/v1/my/shipments | any auth | Employee's own shipments |
| PATCH | /api/v1/shipments/{id}/items | technician+ | Add/remove items (DRAFT only) |
| GET | /api/v1/dashboard/shipments | admin+ | Shipment summary for dashboard |

---

## Technical Constraints

- All shipment queries must be scoped by `company_id` (multi-tenant isolation)
- ShipmentItem references to assets must validate same `company_id` ownership
- Carrier and tracking_number are required for dispatch transition (not for draft creation)
- `return_for_shipment_id` must reference a shipment in the same company
- ShippingAddress is soft-deleted (is_active=false) — never hard-deleted since historical shipments reference it
- Asset status changes on delivery are informational side effects — the shipment state machine is the source of truth for logistics, not the asset status
- An asset cannot be in more than one active shipment (DRAFT, DISPATCHED, or IN_TRANSIT) simultaneously. Enforced at creation and item addition.
- ShipmentItems can be added/removed only while shipment is in DRAFT status. After DISPATCHED, items are locked.
- Maximum 20 items per shipment (practical limit to prevent abuse)
- Tracking URL is stored as-is (no validation) — the frontend will render it as a clickable link

---

## Definition of Done

- [ ] `shipping_bc` bounded context created with domain entities, enums, repositories
- [ ] 3 database migrations (shipments, shipment_items, shipping_addresses)
- [ ] Shipment state machine with all valid transitions
- [ ] 20 API endpoints (11 shipment + 7 address + 1 my/shipments + 1 dashboard)
- [ ] 5 notification event types registered
- [ ] Notification delivery for dispatch, delivery, failure events
- [ ] Asset detail page shows shipment history
- [ ] Request detail page shows linked shipments
- [ ] Dashboard shows active shipments card
- [ ] Shipment list page with filters (status, direction, destination type)
- [ ] Shipment detail page with status timeline and items
- [ ] Address management page
- [ ] New shipment form with asset selection and address picker
- [ ] 3 routes + 2 sidebar nav items
- [ ] ~80 i18n keys per language (EN + ES)
- [ ] Unit tests for all command/query handlers (~25 tests)
- [ ] Integration tests for all endpoints (~20 tests)
- [ ] TypeScript compiles, build succeeds
- [ ] All existing tests continue passing

---

## Time Constraints

**Deadline:** None (medium priority)
**Type:** Feature development
**Dependencies:** E2 (Asset), E3 (Service Requests), E14 (Procurement) — all Done
**Calendar Conflicts:** None

---

## Open Questions

1. ~~Should we add IN_TRANSIT to AssetStatus?~~ → Decided: No. Shipment status is managed in `shipping_bc`. Asset status updated only at terminal events.

2. ~~Should addresses be a separate bounded context?~~ → Decided: No. Keep in `shipping_bc` for now. If E22 needs shared addresses, extract later.

3. ~~Should employees be able to create return shipments?~~ → Decided: No. Only technicians create shipments. Employees receive notifications only. Employee-initiated returns will be part of E22.

4. ~~Multi-carrier support per shipment?~~ → Decided: No. One carrier per shipment. If a shipment is transferred between carriers, create a new shipment.

5. ~~Should we track shipping costs?~~ → Decided: Not in this epic. Shipping costs can be tracked via PO items (E14) if needed. May add a `cost_cents` field in a future iteration.
