# Design: F2 — Availability Management

**Feature:** Technician availability CRUD — recurring weekly schedule, date-specific overrides, and available slot computation endpoint.
**Depends on:** F0 (entities, repos, AvailabilityService already exist)

## Overview

F2 wraps the F0 domain layer (TechnicianAvailability, AvailabilityOverride, AvailabilityService) with application-layer commands/queries and HTTP endpoints. No new domain entities or migrations are needed — everything builds on the F0 foundation.

## Application Layer

### Commands

#### SetAvailabilityCommand
- **Purpose:** Replace all recurring weekly windows for a technician (upsert pattern)
- **Fields:** `technician_id`, `company_id`, `windows: list[AvailabilityWindowInput]`
  - `AvailabilityWindowInput`: `day_of_week`, `start_time`, `end_time`
- **Handler:**
  1. Create `TechnicianAvailability.create()` for each window (validates day_of_week and start < end)
  2. Call `availability_repo.save_all(technician_id, company_id, windows)`
- **Returns:** None (CQRS)

#### AddOverrideCommand
- **Purpose:** Add a date-specific override (block or extra availability)
- **Fields:** `override_id` (pre-generated), `company_id`, `technician_id`, `target_date`, `is_available`, `start_time?`, `end_time?`, `reason?`
- **Handler:**
  1. Create `AvailabilityOverride.create()` (validates time rules)
  2. Save via `override_repo.save(override)`
- **Returns:** None (CQRS)

#### DeleteOverrideCommand
- **Purpose:** Remove a date-specific override
- **Fields:** `override_id`, `company_id`
- **Handler:**
  1. Call `override_repo.delete(override_id, company_id)`
  2. If not found → raise `OverrideNotFoundError`
- **Returns:** None (CQRS)

### Queries

#### GetAvailabilityQuery
- **Purpose:** Get a technician's recurring weekly schedule
- **Fields:** `technician_id`, `company_id`
- **Handler:** Calls `availability_repo.find_by_technician(technician_id, company_id)`
- **Returns:** `list[TechnicianAvailability]`

#### ListOverridesQuery
- **Purpose:** Get overrides for a technician in a date range
- **Fields:** `technician_id`, `company_id`, `date_from`, `date_to`
- **Handler:** Calls `override_repo.find_by_technician_date_range(...)`
- **Returns:** `list[AvailabilityOverride]`

#### GetAvailableSlotsQuery
- **Purpose:** Compute available booking slots for a technician on a date
- **Fields:** `technician_id`, `company_id`, `target_date`, `duration_minutes`
- **Handler:**
  1. Fetch recurring windows for target_date's weekday
  2. Fetch overrides for target_date
  3. Fetch existing CONFIRMED appointments for target_date
  4. Call `AvailabilityService.compute_available_slots(...)`
- **Returns:** `list[TimeSlot]`

## HTTP Layer

### Router: `/api/v1/availability`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| PUT | `/technicians/{technician_id}` | technician+ (self) or admin | Set recurring weekly schedule |
| GET | `/technicians/{technician_id}` | technician+ (self) or admin | Get recurring schedule |
| POST | `/technicians/{technician_id}/overrides` | technician+ (self) or admin | Add override |
| GET | `/technicians/{technician_id}/overrides` | technician+ (self) or admin | List overrides (date range) |
| DELETE | `/overrides/{override_id}` | technician+ (self) or admin | Delete override |
| GET | `/technicians/{technician_id}/slots` | any authenticated | Get available slots for a date |

### Access Control
- Technicians can only manage their own availability (enforce `technician_id == current_user.id`)
- Admins can manage any technician's availability
- Anyone authenticated can query available slots (needed for employee booking flow)

### Schemas

**AvailabilityWindowSchema:** `day_of_week` (0-6), `start_time` (HH:MM), `end_time` (HH:MM)
**SetAvailabilityRequest:** `windows: list[AvailabilityWindowSchema]`
**AvailabilityResponse:** `id`, `day_of_week`, `start_time`, `end_time`
**OverrideCreateRequest:** `date`, `is_available`, `start_time?`, `end_time?`, `reason?`
**OverrideResponse:** `id`, `date`, `is_available`, `start_time?`, `end_time?`, `reason?`, timestamps
**SlotResponse:** `start`, `end`
**SlotsResponse:** `date`, `technician_id`, `duration_minutes`, `slots: list[SlotResponse]`

### Dependencies

**get_availability_repo:** `TechnicianAvailabilityRepository(db)`
**get_override_repo:** `AvailabilityOverrideRepository(db)`
**get_appointment_repo:** reuse from appointments dependencies

## File Structure

```
src/appointment_bc/appointment/application/
├── commands/
│   ├── set_availability.py          # SetAvailabilityCommand + handler
│   ├── add_override.py              # AddOverrideCommand + handler
│   └── delete_override.py           # DeleteOverrideCommand + handler
├── queries/
│   ├── get_availability.py          # GetAvailabilityQuery + handler
│   ├── list_overrides.py            # ListOverridesQuery + handler
│   └── get_available_slots.py       # GetAvailableSlotsQuery + handler

adapters/http/api/availability/
├── __init__.py
├── schemas.py
├── dependencies.py
└── routers.py

tests/unit/appointment_bc/appointment/application/
├── commands/test_availability.py    # set, add override, delete override tests
├── queries/test_slots.py            # get availability, list overrides, available slots tests

tests/integration/
└── test_availability_endpoints.py   # all 6 endpoints
```

## Test Strategy

### Unit Tests (~10)
- `test_set_availability_replaces_all` — saves all windows
- `test_set_availability_validates_windows` — invalid day_of_week raises ValueError
- `test_add_override_block` — creates block override
- `test_add_override_extra` — creates extra availability
- `test_add_override_validates_times` — is_available=True without times raises ValueError
- `test_delete_override_succeeds` — deletes and returns
- `test_delete_override_not_found_raises` — OverrideNotFoundError
- `test_get_availability_returns_windows` — returns technician's schedule
- `test_list_overrides_returns_filtered` — returns date-range filtered overrides
- `test_get_available_slots_calls_service` — integrates all repos + service

### Integration Tests (~8)
- `test_set_availability_200` — PUT recurring schedule
- `test_get_availability_200` — GET recurring schedule
- `test_add_override_201` — POST block override
- `test_list_overrides_200` — GET overrides with date range
- `test_delete_override_200` — DELETE override
- `test_delete_override_404` — not found
- `test_get_available_slots_200` — GET computed slots
- `test_technician_self_only` — non-admin cannot manage other technician's availability
