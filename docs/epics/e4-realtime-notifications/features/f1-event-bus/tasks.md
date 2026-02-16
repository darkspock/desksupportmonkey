# Tasks: F1 - Event Bus + Target Resolver

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Create DomainEvent value object ✅
- **File:** `src/notification_bc/notification/domain/events.py` (NEW)
- Frozen dataclass: event_type, company_id, actor_id, payload (dict), title, body, timestamp
- Factory method `create()` that sets timestamp to now

---

## Phase 2: Application Services

### T2.1: Create EventBus service ✅
- **File:** `src/notification_bc/notification/application/services/event_bus.py` (NEW)
- subscribe(callback) — registers a subscriber
- publish(event, db) — calls all subscribers with (event, db)
- Subscribers are callables that take (DomainEvent, Session)

### T2.2: Create TargetResolver service ✅
- **File:** `src/notification_bc/notification/application/services/target_resolver.py` (NEW)
- resolve(event) → list[str] of target user_ids
- Dispatch by event_type to specific methods
- Always exclude actor_id from results
- Deduplicate with set()
- For `request.created`: call user_repo.find_technician_ids_by_company(company_id)
- For others: extract created_by and/or assigned_to from payload

### T2.3: Create NotificationSubscriber ✅
- **File:** `src/notification_bc/notification/application/services/notification_subscriber.py` (NEW)
- Callable that receives (event, db)
- Uses TargetResolver to get targets
- Creates Notification entities for each target
- Calls notification_repo.save_batch()
- No-op if no targets

### T2.4: Create __init__.py for services ✅
- `src/notification_bc/notification/application/services/__init__.py`

---

## Phase 3: UserRepository Extension

### T3.1: Add find_technician_ids_by_company to UserRepositoryInterface ✅
- **File:** `src/auth_bc/user/domain/repository.py` (MODIFY)
- New abstract method: find_technician_ids_by_company(company_id) → list[str]

### T3.2: Implement in UserRepository ✅
- **File:** `src/auth_bc/user/infrastructure/repository.py` (MODIFY)
- Select user IDs where company_id matches, role in (technician, admin, super_admin), is_active=True

---

## Phase 4: Tests

### T4.1: Unit tests - DomainEvent ✅
- **File:** `tests/unit/notification_bc/notification/domain/test_events.py` (NEW)
- Create event with all fields
- Frozen (immutable)

### T4.2: Unit tests - EventBus ✅
- **File:** `tests/unit/notification_bc/notification/application/services/test_event_bus.py` (NEW)
- Publish with no subscribers — no error
- Publish with one subscriber — subscriber called
- Publish with multiple subscribers — all called
- Subscriber receives event and db

### T4.3: Unit tests - TargetResolver ✅
- **File:** `tests/unit/notification_bc/notification/application/services/test_target_resolver.py` (NEW)
- request.created → all technicians in company
- request.status_changed → created_by + assigned_to, minus actor
- request.assigned → assigned_to, minus actor
- request.priority_changed → assigned_to, minus actor
- request.comment_added → created_by + assigned_to, minus author
- request.note_added → assigned_to, minus author
- Actor always excluded
- No duplicates
- Empty targets when assigned_to is None

### T4.4: Unit tests - NotificationSubscriber ✅
- **File:** `tests/unit/notification_bc/notification/application/services/test_notification_subscriber.py` (NEW)
- Creates notifications for all targets
- No-op when no targets
- Calls save_batch with correct notification list

---

## Phase 5: Verification

### T5.1: Run all tests ✅
### T5.2: Verify event bus can be instantiated and subscribers registered ✅

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1 | 1 | -- |
| 2. Services | T2.1-T2.4 | 3 + init | -- |
| 3. UserRepo | T3.1-T3.2 | -- | 2 (user repo interface + impl) |
| 4. Tests | T4.1-T4.4 | 4 | -- |
| 5. Verification | T5.1-T5.2 | -- | -- |
