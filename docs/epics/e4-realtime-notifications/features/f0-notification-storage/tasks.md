# Tasks: F0 - Notification Entity + Storage + Endpoints

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Create EventType enum
- **File:** `src/notification_bc/notification/domain/enums.py` (NEW)
- String enum with values: request.created, request.status_changed, request.assigned, request.priority_changed, request.comment_added, request.note_added

### T1.2: Create Notification entity
- **File:** `src/notification_bc/notification/domain/entities.py` (NEW)
- Dataclass with all fields from design
- `create()`: generates ULID, sets is_read=False, validates title/body not empty

### T1.3: Create NotificationRepositoryInterface
- **File:** `src/notification_bc/notification/domain/repository.py` (NEW)
- ABC with methods: save, save_batch, find_by_user, count_unread, mark_read, mark_all_read

### T1.4: Create __init__.py files
- `src/notification_bc/__init__.py`
- `src/notification_bc/notification/__init__.py`
- `src/notification_bc/notification/domain/__init__.py`
- `src/notification_bc/notification/application/__init__.py`
- `src/notification_bc/notification/application/commands/__init__.py`
- `src/notification_bc/notification/application/queries/__init__.py`
- `src/notification_bc/notification/infrastructure/__init__.py`

---

## Phase 2: Infrastructure Layer

### T2.1: Create NotificationModel
- **File:** `src/notification_bc/notification/infrastructure/models.py` (NEW)
- NotificationModel(ULIDMixin, Base) with all columns
- Composite index on (user_id, is_read, created_at)
- No TimestampMixin (no updated_at)
- created_at as mapped_column with server_default=func.now()

### T2.2: Update models_registry.py
- Add import for NotificationModel

### T2.3: Create NotificationRepository
- **File:** `src/notification_bc/notification/infrastructure/repository.py` (NEW)
- Implement all interface methods
- save: add + flush + refresh
- save_batch: add_all + flush
- find_by_user: select + where + optional is_read filter + order_by + offset/limit
- count_unread: select count where is_read=False
- mark_read: update statement where id + user_id, return success boolean
- mark_all_read: update statement where user_id + is_read=False, return rowcount

### T2.4: Create Alembic migration
- `alembic revision --autogenerate -m "add_notifications_table"`
- Verify: notifications table with all columns, indexes
- Test upgrade + downgrade

---

## Phase 3: Application Layer

### T3.1: CreateNotificationCommand + Handler
- **File:** `src/notification_bc/notification/application/commands/create_notification.py` (NEW)
- Command: user_id, company_id, event_type, title, body, data
- Handler: create entity, save via repo, return notification
- This is an internal command (used by event subscribers, not HTTP)

### T3.2: MarkReadCommand + Handler
- **File:** `src/notification_bc/notification/application/commands/mark_read.py` (NEW)
- Command: notification_id, user_id
- Handler: call repo.mark_read, if not found raise NotificationNotFoundError

### T3.3: MarkAllReadCommand + Handler
- **File:** `src/notification_bc/notification/application/commands/mark_all_read.py` (NEW)
- Command: user_id
- Handler: call repo.mark_all_read, return marked_count

### T3.4: ListNotificationsQuery + Handler
- **File:** `src/notification_bc/notification/application/queries/list_notifications.py` (NEW)
- Query: user_id, page, page_size, is_read (optional)
- Handler: call repo.find_by_user for page, call repo.count_unread for badge count, return (notifications, total, unread_count)

---

## Phase 4: HTTP Layer

### T4.1: Add notification schemas
- **File:** `adapters/http/api/my/schemas.py` (MODIFY)
- NotificationResponse: id, event_type, title, body, data, is_read, created_at
- NotificationListMeta: page, page_size, total, unread_count

### T4.2: Add notification endpoints to my router
- **File:** `adapters/http/api/my/routers.py` (MODIFY)
- GET /api/v1/my/notifications → list with pagination, filter, unread_count
- PATCH /api/v1/my/notifications/{notification_id}/read → mark single as read
- PATCH /api/v1/my/notifications/read-all → mark all as read
- All require authenticated user (get_current_user)
- Error mapping: NotificationNotFoundError → 404

---

## Phase 5: Tests

### T5.1: Unit tests - Notification entity
- **File:** `tests/unit/notification_bc/notification/domain/test_entities.py` (NEW)
- Create with valid data
- Create with empty title raises ValueError
- Create with empty body raises ValueError
- Default is_read = False

### T5.2: Unit tests - Commands
- **File:** `tests/unit/notification_bc/notification/application/commands/test_commands.py` (NEW)
- CreateNotification: success
- MarkRead: success, not found raises error
- MarkAllRead: success, returns count

### T5.3: Unit tests - Queries
- **File:** `tests/unit/notification_bc/notification/application/queries/test_queries.py` (NEW)
- ListNotifications: returns paginated with unread_count
- ListNotifications with is_read filter

---

## Phase 6: Verification

### T6.1: Run all tests
### T6.2: Run migration
### T6.3: Manual verification
1. Seed a notification directly in DB
2. GET /api/v1/my/notifications → verify response format with unread_count
3. PATCH /api/v1/my/notifications/{id}/read → verify is_read=true
4. PATCH /api/v1/my/notifications/read-all → verify count returned

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.4 | 3 + inits | -- |
| 2. Infrastructure | T2.1-T2.4 | 2 + migration | 1 (models_registry) |
| 3. Application | T3.1-T3.4 | 4 | -- |
| 4. HTTP | T4.1-T4.2 | -- | 2 (my/routers, my/schemas) |
| 5. Tests | T5.1-T5.3 | 3 | -- |
| 6. Verification | T6.1-T6.3 | -- | -- |
