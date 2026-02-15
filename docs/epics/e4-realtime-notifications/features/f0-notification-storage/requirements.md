# Requirements: F0 - Notification Entity + Storage + Endpoints

**Epic:** [E4 - Real-time & Notifications](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Deliver the Notification entity, repository, SQLAlchemy model, migration, and REST endpoints for listing and managing notifications. This is the persistence and API foundation for the entire E4 epic.

---

## Requirements

### R1: Notification Entity
- Notification has: id, user_id, company_id, event_type, title, body, data (JSON), is_read, created_at
- All fields except is_read and data are required
- Default is_read = false
- Notifications are created programmatically (not via HTTP endpoint)

### R2: EventType Enum
- Event types: `request.created`, `request.status_changed`, `request.assigned`, `request.priority_changed`, `request.comment_added`, `request.note_added`
- Stored as string in the database

### R3: NotificationRepository
- `save(notification)` — persist a new notification
- `save_batch(notifications)` — bulk insert multiple notifications
- `find_by_user(user_id, page, page_size, is_read)` — paginated list with optional filter
- `count_unread(user_id)` — count unread notifications for a user
- `mark_read(notification_id, user_id)` — mark single notification as read
- `mark_all_read(user_id)` — mark all unread as read for a user

### R4: List Notifications Endpoint
- `GET /api/v1/my/notifications` — any authenticated user
- Paginated with page and page_size
- Optional filter: `is_read` (true/false, defaults to all)
- Sorted by created_at desc (newest first)
- Response includes notifications array + meta with page, page_size, total, unread_count

### R5: Mark Single as Read
- `PATCH /api/v1/my/notifications/{id}/read` — any authenticated user
- Only the notification owner can mark it
- Non-existent or other user's notification returns 404
- Already-read notification is a no-op (returns 200)

### R6: Mark All as Read
- `PATCH /api/v1/my/notifications/read-all` — any authenticated user
- Marks all unread notifications for the current user as read
- Returns the count of notifications that were marked as read

---

## Acceptance Criteria

- [ ] Notification entity with all fields and validation
- [ ] NotificationModel with proper indexes
- [ ] Alembic migration creates notifications table
- [ ] List notifications endpoint with pagination, filter, unread_count
- [ ] Mark single notification as read
- [ ] Mark all notifications as read
- [ ] Unit tests for entity, commands, queries
