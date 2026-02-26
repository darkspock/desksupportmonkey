# E49 — Asset Checkout & Custody Management

## Problem Statement

When a technician assigns an asset to an employee, three things happen simultaneously that should be separate concerns:

1. **Responsibility assignment** — the asset is now "for" this employee
2. **Physical location change** — the asset auto-moves to "Empleado" location
3. **Physical delivery** — assumed instant, with no record

In reality:
- An asset can be assigned to someone but still sitting in a warehouse being configured
- There is no proof that the employee physically received the equipment
- When an employee is terminated and claims "I never received that laptop", there is zero evidence
- When a device is returned, there is no record of its condition — it goes straight back to stock
- GDPR requires data sanitization before reassignment, but nothing enforces this

## Goals

1. **Decouple assignment from location** — assigning an asset should not auto-move its physical location
2. **Create a custody chain** — explicit checkout/checkin records that prove who had what, when
3. **Employee acceptance** — the employee must confirm they received the equipment (legal evidence)
4. **Condition tracking on return** — record the state of the device when returned, determining its next lifecycle step
5. **GDPR sanitization enforcement** — returned assets go through mandatory maintenance before re-entering stock

## Non-Goals

- Digital signature pad (drawing with mouse/finger) — acceptance confirmation is sufficient for now
- Asset reservation system (booking assets in advance)
- Self-service checkout (employee picks up from a locker/kiosk)
- Bulk checkout (assign multiple devices at once — Phase 2)
- Transfer checkout (direct employee-to-employee — require checkin + new checkout)

---

## Domain Concepts

### AssetCheckout (New Entity)

A `Checkout` represents a period of physical custody. One asset can have many checkouts over its lifetime, but only one active (open) checkout at a time.

| Field | Type | Description |
|---|---|---|
| `id` | ULID | Primary key |
| `company_id` | FK | Tenant isolation |
| `asset_id` | FK → assets | The asset being checked out |
| `user_id` | FK → users | Employee receiving the asset |
| `checked_out_by` | FK → users | Technician who performed the handover |
| `checked_out_at` | datetime | When the handover happened |
| `condition_out` | enum | Condition at checkout: `new`, `good`, `fair`, `damaged` |
| `condition_out_notes` | text? | Optional description of condition at checkout |
| `notes_out` | text | Notes at checkout (accessories included, etc.) |
| `accepted_at` | datetime? | When the employee confirmed receipt (**the legal proof**) |
| `checked_in_at` | datetime? | When the asset was returned (null = active custody) |
| `checked_in_by` | FK? → users | Technician who received the return |
| `condition_in` | enum? | Condition at return: `good`, `fair`, `damaged`, `unusable` |
| `condition_in_notes` | text? | Optional description of condition at return |
| `notes_in` | text? | Notes at return |
| `cancelled_at` | datetime? | When the checkout was cancelled (null = not cancelled) |
| `cancelled_by` | FK? → users | Technician who cancelled the checkout |
| `cancel_reason` | text? | Reason for cancellation |
| `created_at` | datetime | Record creation |

**Invariants:**
- Only one open checkout per asset (where `checked_in_at IS NULL`)
- Cannot checkout an asset that is not `ASSIGNED` or `IN_STOCK` (see "Direct Checkout" below)
- Cannot checkin an asset that has no open checkout
- Cannot checkin a checkout that has been cancelled
- `accepted_at` can only be set by the assigned employee (self-service)

### Checkout Cancellation

A checkout can be **cancelled** by a technician (e.g., checked out to the wrong person). Cancelled checkouts:
- Status: `CANCELLED` (new status, derived from `cancelled_at IS NOT NULL`)
- Fields: `cancelled_at` (datetime), `cancelled_by` (FK → users), `cancel_reason` (text, optional)
- Cancelled checkouts are preserved for audit trail — never deleted
- Cancelling restores the asset to its pre-checkout state (`ASSIGNED` or `IN_STOCK`)
- Cannot cancel a checkout that has already been checked in

### Direct Checkout (Without Prior Assignment)

A technician can checkout an asset directly from `IN_STOCK` status — the system auto-assigns it to the employee. This combines assign + checkout into a single operation for common workflows (e.g., handing a laptop to a new hire).

- Asset must be `IN_STOCK` or already `ASSIGNED` to the target employee
- If `IN_STOCK`: system performs auto-assign (sets `assigned_to`, status → `ASSIGNED`) then creates checkout
- If `ASSIGNED` to a different employee: rejected (must unassign first)

### AssetCondition (New Enum)

```
NEW         — brand new, never used
GOOD        — normal wear, fully functional
FAIR        — visible wear, functional
DAMAGED     — physical damage, may need repair
UNUSABLE    — non-functional, candidate for decommission
```

---

## Revised Asset Lifecycle

### Current (Broken)

```
IN_STOCK ──assign──► ASSIGNED (location auto-moves to "Empleado")
                         │
                     unassign
                         │
                         ▼
                     IN_STOCK (location auto-moves to "Almacén")
```

### Proposed

```
IN_STOCK ──assign──► ASSIGNED ──checkout──► ASSIGNED (with open checkout)
    ▲                    ▲                       │
    │                    │                   checkin / cancel
    │                    │                       │
    │                cancel                      ▼
    │             (restores to              IN_REPAIR
    │              pre-checkout)          (auto maintenance task
    │                                     for GDPR sanitization)
    │                                            │
    │                                  task completed (auto)
    │                                            │
    └────────────────────────────────────────────┘

Direct checkout shortcut:
IN_STOCK ──checkout──► ASSIGNED (auto-assign + open checkout)
```

**Key changes:**
1. `assign` — sets `ASSIGNED` status, sets `assigned_to`. **Does NOT move location.**
2. `checkout` — creates `AssetCheckout` record. Accepts `IN_STOCK` assets (auto-assigns) or `ASSIGNED` assets. Location managed independently.
3. `checkin` — closes the checkout. Asset goes to `IN_REPAIR`. Auto-creates a GDPR sanitization maintenance task.
4. `cancel` — voids a checkout. Asset returns to pre-checkout state. Record kept for audit.
5. Maintenance task completion — **automatically** transitions asset to `IN_STOCK` (event-driven).
6. `unassign` — only allowed if there is no open checkout (can't unassign if employee still has it physically).

### Condition-Based Return Flow

| `condition_in` | Asset next status | Action |
|---|---|---|
| `good` / `fair` | `IN_REPAIR` | Standard GDPR sanitization task |
| `damaged` | `IN_REPAIR` | GDPR sanitization + repair task |
| `unusable` | `DECOMMISSIONED` | GDPR wipe only, no repair |

---

## Employee Acceptance Flow

1. Technician performs checkout → email sent to employee
2. Employee clicks link → sees asset details (brand, model, serial, condition)
3. Employee clicks "Confirm Receipt" → `accepted_at` is set
4. If employee does not confirm within X days → reminder emails (configurable)

The `accepted_at` timestamp is the legal proof that the employee acknowledged receiving the equipment.

**No acceptance required to complete checkout** — the checkout is valid from the technician's side. Acceptance is additional evidence. An asset can be checked in even without employee acceptance (e.g., employee is unresponsive).

### Acceptance Timeout Configuration

The reminder period is configurable at the **company settings** level:
- Setting: `checkout_acceptance_reminder_days` (default: 3 days)
- Stored in the existing company settings infrastructure
- Admin can change it from company settings page
- Celery periodic task checks for unaccepted checkouts older than the configured period and sends reminders

---

## GDPR Sanitization (Auto-Maintenance)

When a checkin is performed:

1. Asset status changes to `IN_REPAIR`
2. A maintenance record is **automatically created** with:
   - Title: "GDPR Sanitization — {asset brand} {asset model}"
   - Template: Company-configurable "GDPR Sanitization" template (seeded by default)
   - Checklist items (default):
     - [ ] Factory reset / disk wipe
     - [ ] Remove MDM/enrollment profile
     - [ ] Deauthorize software licenses
     - [ ] Remove from employee's account
     - [ ] Verify no personal data remains
     - [ ] Compliance sign-off
3. When the maintenance record is completed → asset **automatically** transitions to `IN_STOCK` (event-driven: `MaintenanceCompleted` event triggers `AssetStatusChanged` command)

**Default maintenance template** seeded at company creation, editable by admin.

### Maintenance → IN_STOCK Automation

When a GDPR sanitization maintenance task is completed:
1. `MaintenanceCompleted` domain event is emitted
2. Event handler checks if the maintenance was created by a checkout (linked via `checkout_id` or tag)
3. If yes, automatically transitions the asset from `IN_REPAIR` → `IN_STOCK`
4. This is a new event handler — does not exist in the current codebase

---

## Changes to Existing Code

### assign_asset.py
- **Remove** auto-move to "Empleado" location
- **Remove** `location_changed` event emission
- Keep everything else (status change, assigned event)

### unassign_asset.py
- **Add guard**: reject if there is an open checkout (`checked_in_at IS NULL`)
- **Remove** auto-move to "Almacén" location
- **Remove** `location_changed` event emission
- Keep everything else

### SystemLocation enum
- **Remove** `EMPLOYEE` — no longer needed as a system location. Assets at an employee's possession are tracked via the open checkout, not via location.
- Keep `IN_TRANSIT` and `MAIN_WAREHOUSE`

---

## API Endpoints

### Checkout/Checkin

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/assets/{id}/checkout` | TECHNICIAN | Create checkout (handover to employee). Accepts IN_STOCK (auto-assigns) or ASSIGNED assets. |
| POST | `/assets/{id}/checkin` | TECHNICIAN | Return asset (close checkout) |
| POST | `/assets/{id}/checkout/cancel` | TECHNICIAN | Cancel a checkout (mistake correction) |
| POST | `/assets/{id}/checkout/accept` | EMPLOYEE | Employee confirms receipt |
| GET | `/assets/{id}/checkouts` | TECHNICIAN | Checkout history for an asset |
| GET | `/assets/{id}/checkout/current` | ANY | Current open checkout (if any) |
| GET | `/checkouts` | TECHNICIAN | Global list of all open checkouts company-wide (filterable by status, user, asset) |

### Checkout Request Body
```json
{
  "user_id": "...",
  "condition_out": "good",
  "notes_out": "Includes charger and carrying case"
}
```

### Checkin Request Body
```json
{
  "condition_in": "damaged",
  "notes_in": "Cracked screen, missing charger"
}
```

### Accept (Employee)
No body needed — uses current authenticated user. Returns 403 if the user is not the checkout recipient.

---

## Frontend

### Asset Detail Page
- New "Custody" tab showing:
  - Current checkout status (who has it, since when, accepted or pending)
  - Checkout/Checkin buttons for technicians
  - Checkout history table
- Assignment section no longer shows location change

### Employee Portal ("My Equipment")
- Pending acceptance banner: "You have equipment pending confirmation"
- "Confirm Receipt" button
- List of currently checked-out equipment

### Email Notification
- On checkout: email to employee with asset details + link to accept
- Reminder if not accepted within configurable period

---

## Data Model

### New Table: `asset_checkouts`

```sql
CREATE TABLE asset_checkouts (
    id                VARCHAR(26) PRIMARY KEY,
    company_id        VARCHAR(26) NOT NULL REFERENCES companies(id),
    asset_id          VARCHAR(26) NOT NULL REFERENCES assets(id),
    user_id           VARCHAR(26) NOT NULL REFERENCES users(id),
    checked_out_by    VARCHAR(26) NOT NULL REFERENCES users(id),
    checked_out_at    TIMESTAMP NOT NULL DEFAULT now(),
    condition_out     VARCHAR(20) NOT NULL,
    condition_out_notes TEXT,
    notes_out         TEXT,
    accepted_at       TIMESTAMP,
    checked_in_at     TIMESTAMP,
    checked_in_by     VARCHAR(26) REFERENCES users(id),
    condition_in      VARCHAR(20),
    condition_in_notes TEXT,
    notes_in          TEXT,
    cancelled_at      TIMESTAMP,
    cancelled_by      VARCHAR(26) REFERENCES users(id),
    cancel_reason     TEXT,
    created_at        TIMESTAMP DEFAULT now(),
    updated_at        TIMESTAMP
);

CREATE INDEX ix_asset_checkouts_asset ON asset_checkouts(asset_id);
CREATE INDEX ix_asset_checkouts_user ON asset_checkouts(user_id);
CREATE INDEX ix_asset_checkouts_company ON asset_checkouts(company_id);
CREATE UNIQUE INDEX uq_asset_checkouts_active ON asset_checkouts(asset_id)
    WHERE checked_in_at IS NULL AND cancelled_at IS NULL;
```

The partial unique index `uq_asset_checkouts_active` enforces the "one open checkout per asset" invariant at the database level.

### Migration: Modify existing data

- Seed a default "GDPR Sanitization" maintenance template per company
- Remove `EMPLOYEE` system location (migrate existing assets at that location to `MAIN_WAREHOUSE`)
- Assets currently `ASSIGNED` with location = "Empleado" → keep `ASSIGNED`, set location to null or last known physical location

---

## Events (Audit Trail)

| Event Type | When | Data |
|---|---|---|
| `checked_out` | Checkout created | `{ user_id, checked_out_by, condition_out }` |
| `checkout_accepted` | Employee confirms | `{ user_id, accepted_at }` |
| `checked_in` | Asset returned | `{ checked_in_by, condition_in, maintenance_id }` |
| `checkout_cancelled` | Checkout voided | `{ cancelled_by, cancel_reason }` |
| `maintenance_completed_auto_stock` | GDPR task done | `{ asset_id, maintenance_id }` |

---

## Testing

### Unit Tests
- Checkout: ASSIGNED or IN_STOCK assets only, only one open checkout, condition required
- Checkout from IN_STOCK: auto-assigns then creates checkout
- Checkin: closes checkout, creates maintenance task, condition determines status
- Accept: only by the assigned employee, only on open unaccepted checkout
- Cancel: sets cancelled_at/by, restores asset to pre-checkout state, audit preserved
- Cancel guards: can't cancel checked-in or already cancelled checkout
- Unassign guard: blocked when open checkout exists
- Assign: no longer moves location
- Maintenance completion: auto-transitions asset to IN_STOCK

### Integration Tests
- Full flow: assign → checkout → accept → checkin → maintenance created → complete maintenance → IN_STOCK
- Direct checkout: IN_STOCK → checkout (auto-assign) → accept → checkin
- Cancel flow: checkout → cancel → asset restored
- GDPR template seeding on company creation
- Partial unique index enforcement (double checkout rejected, cancelled checkouts don't block new ones)
- Employee acceptance via authenticated endpoint
- Global checkouts endpoint: list, filter by status/user

---

## Feature Slicing

| # | Feature | Scope |
|---|---|---|
| F0 | Domain + Infrastructure | Entity, enum, model, migration, repository, seed GDPR template |
| F1 | Checkout/Checkin/Cancel commands | Create checkout (incl. direct from IN_STOCK), checkin, cancel, accept + auto-maintenance on checkin |
| F2 | Refactor assign/unassign | Remove auto-location move, add unassign guard |
| F3 | Maintenance → IN_STOCK automation | Event handler for maintenance completion auto-transitioning asset to IN_STOCK |
| F4 | HTTP layer | Endpoints (incl. cancel, global checkouts list), schemas, dependencies |
| F5 | Employee acceptance | Email notification, accept endpoint, acceptance timeout config in company settings, reminder Celery task |
| F6 | Frontend — Asset Detail | Custody tab, checkout/checkin/cancel buttons, history |
| F7 | Frontend — My Equipment | Pending acceptance, confirm receipt |
| F8 | Frontend — Dashboard widget | Open checkouts / pending acceptances widget |
| F9 | Tests | Unit + integration |
