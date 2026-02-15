# Design: F2 - Event Emission from Request Commands

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F2 modifies existing request routers to emit domain events after successful command execution.

```
NEW FILES:
src/notification_bc/notification/application/services/event_factory.py  # Build DomainEvent for each command

MODIFIED FILES:
adapters/http/api/requests/routers.py   # Emit events after each command
app.py                                   # Initialize EventBus + register subscribers
```

---

## Event Factory

A helper that builds DomainEvent instances from request data:

```python
class RequestEventFactory:
    @staticmethod
    def request_created(request: ServiceRequest, actor_id: str) -> DomainEvent:
        ...

    @staticmethod
    def status_changed(request: ServiceRequest, old_status: str, new_status: str, actor_id: str) -> DomainEvent:
        ...

    @staticmethod
    def priority_changed(request: ServiceRequest, old_priority: str, new_priority: str, actor_id: str) -> DomainEvent:
        ...

    @staticmethod
    def request_assigned(request: ServiceRequest, actor_id: str) -> DomainEvent:
        ...

    @staticmethod
    def comment_added(request: ServiceRequest, actor_id: str) -> DomainEvent:
        ...

    @staticmethod
    def note_added(request: ServiceRequest, actor_id: str) -> DomainEvent:
        ...
```

Each method returns a `DomainEvent` with the correct event_type, payload, title, and body.

---

## EventBus Initialization

In `app.py`:

```python
from src.notification_bc.notification.application.services.event_bus import EventBus
from src.notification_bc.notification.application.services.notification_subscriber import NotificationSubscriber
from src.notification_bc.notification.application.services.target_resolver import TargetResolver

# Create singleton
event_bus = EventBus()

# Register subscribers (at startup)
# NotificationSubscriber needs TargetResolver and NotificationRepo — created per-request via DI
```

---

## EventBus as FastAPI Dependency

The EventBus is a singleton, but the NotificationSubscriber needs per-request dependencies (db session, repos). Two approaches:

**Approach A (Recommended): Pass db to publish()**
The EventBus passes the db session to subscribers. Subscribers create their own repos from the session.

```python
# In router
event_bus.publish(event, db)

# In subscriber
def __call__(self, event, db):
    repo = NotificationRepository(db)
    resolver = TargetResolver(UserRepository(db))
    # ... create notifications
```

**Approach B:** Pre-configure subscriber with factory callables. More complex, not needed for v1.

---

## Router Modifications

Each endpoint in `adapters/http/api/requests/routers.py` gets an event emission block after the command succeeds:

```python
@router.post("/")
def create_request(..., event_bus: EventBus = Depends(get_event_bus)):
    # ... existing command execution ...
    request = handler.handle(command)

    # Emit event
    event = RequestEventFactory.request_created(request, actor_id=current_user.id)
    event_bus.publish(event, db)

    return {"data": ...}
```

The `get_event_bus` dependency returns the singleton EventBus instance.

---

## get_event_bus Dependency

```python
# In a new file or in app.py
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    return _event_bus
```

Alternatively, attach to `app.state.event_bus` and retrieve via `request.app.state.event_bus`.
