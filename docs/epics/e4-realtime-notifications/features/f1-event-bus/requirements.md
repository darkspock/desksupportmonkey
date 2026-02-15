# Requirements: F1 - Event Bus + Target Resolver

**Epic:** [E4 - Real-time & Notifications](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Deliver the domain event bus (pub/sub), the target resolver (who receives notifications), and the notification subscriber (creates Notification records when events are published). This is the core routing layer that connects event producers to notification storage.

---

## Requirements

### R1: DomainEvent Value Object
- DomainEvent is a dataclass (not persisted): event_type, company_id, actor_id, payload (dict), title, body, timestamp
- target_user_ids is resolved by TargetResolver, not set by the producer
- Immutable after creation

### R2: EventBus
- Publish/subscribe pattern
- `publish(event, db)` dispatches to all registered subscribers
- Subscribers are registered at startup
- Synchronous dispatch (same request context)
- EventBus is a singleton injectable dependency

### R3: TargetResolver
- Given an event_type and context (request data), resolves which user_ids should be notified
- Rules per event type:
  - `request.created` → all active technicians in the company
  - `request.status_changed` → request creator + assigned technician (excluding actor)
  - `request.assigned` → the assigned technician (excluding actor)
  - `request.priority_changed` → assigned technician (if any, excluding actor)
  - `request.comment_added` → request creator + assigned technician (excluding author)
  - `request.note_added` → assigned technician (excluding author, technician-only)
- Actor is NEVER included in target list
- Duplicate user_ids are removed

### R4: NotificationSubscriber
- Receives domain events from the event bus
- For each target user_id, creates a Notification record
- Uses NotificationRepository.save_batch() for bulk creation
- If no targets, does nothing (no-op)

---

## Acceptance Criteria

- [ ] DomainEvent dataclass with all fields
- [ ] EventBus with publish/subscribe working
- [ ] TargetResolver correctly resolves all 6 event types
- [ ] Actor excluded from all notifications
- [ ] NotificationSubscriber creates notifications for all targets
- [ ] Bulk insert for multiple targets
- [ ] Unit tests for event bus, target resolver, notification subscriber
