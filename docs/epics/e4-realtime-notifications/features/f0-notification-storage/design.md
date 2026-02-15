# Design: F0 - Notification Entity + Storage + Endpoints

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F0 introduces the `notification_bc` bounded context with the Notification entity, repository, and REST endpoints.

```
NEW FILES:
src/notification_bc/
├── notification/
│   ├── domain/
│   │   ├── entities.py           # Notification
│   │   ├── enums.py              # EventType
│   │   └── repository.py         # NotificationRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_notification.py
│   │   │   ├── mark_read.py
│   │   │   └── mark_all_read.py
│   │   └── queries/
│   │       └── list_notifications.py
│   └── infrastructure/
│       ├── models.py             # NotificationModel
│       └── repository.py         # NotificationRepository

MODIFIED FILES:
core/models_registry.py           # Add NotificationModel
adapters/http/api/my/routers.py   # Add notification endpoints
adapters/http/api/my/schemas.py   # Add notification schemas
```

---

## Entity Design

### Notification (dataclass)

```python
@dataclass
class Notification:
    id: str
    user_id: str
    company_id: str
    event_type: str
    title: str
    body: str
    data: dict
    is_read: bool
    created_at: Optional[datetime]

    @staticmethod
    def create(user_id, company_id, event_type, title, body, data=None) -> "Notification":
        # Generate ULID, set is_read=False, created_at=None (DB sets it)
```

### NotificationModel (SQLAlchemy)

```python
class NotificationModel(ULIDMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(String(26), index=True)
    company_id: Mapped[str] = mapped_column(String(26))
    event_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )
```

No `updated_at` — is_read is flipped via direct UPDATE, not entity-level save.

---

## Repository Design

### NotificationRepository

- `save(notification)` — add single record
- `save_batch(notifications)` — `session.add_all()` for bulk insert
- `find_by_user(user_id, page, page_size, is_read)` — select + optional where is_read + order by created_at desc + offset/limit
- `count_unread(user_id)` — `select(func.count()).where(user_id, is_read=False)`
- `mark_read(notification_id, user_id)` — `update(NotificationModel).where(id, user_id).values(is_read=True)`
- `mark_all_read(user_id)` — `update(NotificationModel).where(user_id, is_read=False).values(is_read=True)` — returns rowcount

---

## HTTP Endpoints

### GET /api/v1/my/notifications

Query params: page (default 1), page_size (default 20), is_read (optional bool)

Response:
```json
{
  "data": [
    {
      "id": "01HXYZ...",
      "event_type": "request.status_changed",
      "title": "Request updated",
      "body": "Status changed to in_progress",
      "data": {"request_id": "...", "old_status": "in_review", "new_status": "in_progress"},
      "is_read": false,
      "created_at": "2026-02-15T10:30:00Z"
    }
  ],
  "meta": {"page": 1, "page_size": 20, "total": 42, "unread_count": 7}
}
```

### PATCH /api/v1/my/notifications/{id}/read

Response: `{"data": {"id": "...", "is_read": true}}`

### PATCH /api/v1/my/notifications/read-all

Response: `{"data": {"marked_count": 5}}`
