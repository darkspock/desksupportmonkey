# Tasks: F2 - Event Emission from Request Commands

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Event Factory

### T1.1: Create RequestEventFactory
- **File:** `src/notification_bc/notification/application/services/event_factory.py` (NEW)
- 6 static methods, one per event type
- Each builds DomainEvent with correct event_type, company_id, actor_id, payload, title, body
- Payload always includes: request_id, created_by, assigned_to
- Title/body follow templates from requirements

---

## Phase 2: EventBus Initialization

### T2.1: Create get_event_bus dependency
- **File:** `adapters/http/api/dependencies.py` (NEW or add to existing)
- Module-level EventBus singleton
- `get_event_bus()` function returning the singleton
- Register NotificationSubscriber on the EventBus

### T2.2: Register subscriber in EventBus
- The NotificationSubscriber is a callable that receives (event, db)
- It internally creates TargetResolver (with UserRepository(db)) and NotificationRepository(db)
- Register once at module import time

---

## Phase 3: Router Integration

### T3.1: Emit event in create_request endpoint
- **File:** `adapters/http/api/requests/routers.py` (MODIFY)
- Add EventBus dependency to create_request endpoint
- After handler.handle() succeeds, build event via RequestEventFactory.request_created()
- Call event_bus.publish(event, db)

### T3.2: Emit event in change_status endpoint
- Same file
- Capture old_status before command, new_status after
- Build event via RequestEventFactory.status_changed()

### T3.3: Emit event in change_priority endpoint
- Same file
- Capture old_priority before, new_priority after
- Build event via RequestEventFactory.priority_changed()

### T3.4: Emit event in assign_request endpoint
- Same file
- Build event via RequestEventFactory.request_assigned()

### T3.5: Emit event in add_comment endpoint
- Same file
- Build event via RequestEventFactory.comment_added()

### T3.6: Emit event in add_note endpoint
- Same file
- Build event via RequestEventFactory.note_added()

---

## Phase 4: Tests

### T4.1: Unit tests - RequestEventFactory
- **File:** `tests/unit/notification_bc/notification/application/services/test_event_factory.py` (NEW)
- Each factory method returns correct event_type
- Payload contains required fields
- Title and body match expected format

### T4.2: Integration tests - Event emission
- **File:** `tests/unit/notification_bc/notification/application/services/test_event_emission.py` (NEW)
- Mock EventBus, verify publish() called after each command
- Verify event has correct structure
- Verify no publish on command failure

---

## Phase 5: Verification

### T5.1: Run all tests
### T5.2: Manual verification
1. Create request → verify notification created for technicians
2. Change status → verify notification for request creator
3. Add comment → verify notification for request creator + assigned tech
4. Add note → verify notification for assigned tech only

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Factory | T1.1 | 1 | -- |
| 2. Init | T2.1-T2.2 | 1 | -- |
| 3. Routers | T3.1-T3.6 | -- | 1 (requests/routers.py) |
| 4. Tests | T4.1-T4.2 | 2 | -- |
| 5. Verification | T5.1-T5.2 | -- | -- |
