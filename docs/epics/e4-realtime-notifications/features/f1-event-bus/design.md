# Design: F1 - Event Bus + Target Resolver

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F1 adds the event routing infrastructure to `notification_bc`.

```
NEW FILES:
src/notification_bc/notification/
├── domain/
│   └── events.py                      # DomainEvent dataclass
├── application/
│   └── services/
│       ├── event_bus.py               # EventBus (publish/subscribe)
│       ├── notification_subscriber.py  # Creates Notification records
│       └── target_resolver.py         # Resolves event → target user_ids

MODIFIED FILES: none (subscribers registered in F2 when events are emitted)
```

---

## DomainEvent (Value Object)

```python
@dataclass(frozen=True)
class DomainEvent:
    event_type: str          # e.g., "request.status_changed"
    company_id: str          # For scoping
    actor_id: str            # Who triggered it (excluded from notifications)
    payload: dict            # Event-specific data
    title: str               # Human-readable: "Request #ABC updated"
    body: str                # Human-readable: "Status changed to in_progress"
    timestamp: datetime      # When it happened
```

The payload carries context needed for target resolution:
- `request_id`, `created_by`, `assigned_to` (for all request events)
- `old_status`, `new_status` (for status changes)
- `old_priority`, `new_priority` (for priority changes)

---

## EventBus

```python
class EventBus:
    def __init__(self):
        self._subscribers: list[Callable] = []

    def subscribe(self, subscriber: Callable):
        self._subscribers.append(subscriber)

    def publish(self, event: DomainEvent, db: Session):
        for subscriber in self._subscribers:
            subscriber(event, db)
```

- Subscribers receive `(event, db)` — the db session allows them to persist data
- Synchronous — all subscribers run before the HTTP response is returned
- Singleton instance created at app startup and injected via FastAPI dependency

---

## TargetResolver

```python
class TargetResolver:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    def resolve(self, event: DomainEvent) -> list[str]:
        # Dispatch to specific resolver by event_type
        # Always excludes actor_id from results
        # Returns deduplicated list of user_ids
```

### Resolution Rules

| Event Type | Targets | Data Needed |
|---|---|---|
| `request.created` | All active technicians in company | company_id |
| `request.status_changed` | created_by + assigned_to | payload.created_by, payload.assigned_to |
| `request.assigned` | assigned_to | payload.assigned_to |
| `request.priority_changed` | assigned_to (if any) | payload.assigned_to |
| `request.comment_added` | created_by + assigned_to | payload.created_by, payload.assigned_to |
| `request.note_added` | assigned_to | payload.assigned_to |

For `request.created`, the TargetResolver needs a new repository method: `UserRepository.find_technicians_by_company(company_id)` which returns all active users with role >= TECHNICIAN.

---

## NotificationSubscriber

```python
class NotificationSubscriber:
    def __init__(self, target_resolver: TargetResolver, notification_repo: NotificationRepositoryInterface):
        self.target_resolver = target_resolver
        self.notification_repo = notification_repo

    def __call__(self, event: DomainEvent, db: Session):
        target_ids = self.target_resolver.resolve(event)
        if not target_ids:
            return
        notifications = [
            Notification.create(
                user_id=uid,
                company_id=event.company_id,
                event_type=event.event_type,
                title=event.title,
                body=event.body,
                data=event.payload,
            )
            for uid in target_ids
        ]
        self.notification_repo.save_batch(notifications)
```

---

## New UserRepository Method

Add `find_technicians_by_company(company_id)` to UserRepository:
- Returns all active users in the company with role in (TECHNICIAN, ADMIN, SUPER_ADMIN)
- Returns list of user IDs (not full entities — we only need IDs for targeting)
