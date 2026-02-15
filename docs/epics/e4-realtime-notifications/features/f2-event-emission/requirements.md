# Requirements: F2 - Event Emission from Request Commands

**Epic:** [E4 - Real-time & Notifications](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Integrate the event bus into the existing request routers so that every request mutation (create, status change, priority change, assign, comment, note) emits a domain event. This connects the request_bc as event producer to the notification_bc as event consumer.

---

## Requirements

### R1: Event Emission After Command Success
- Events are emitted in the router layer AFTER the command handler succeeds
- If the command fails (exception), no event is emitted
- Events are emitted within the same DB transaction (before commit)

### R2: Event Bus Initialization
- EventBus singleton is created at app startup
- NotificationSubscriber is registered as a subscriber
- EventBus is available as a FastAPI dependency

### R3: Events Emitted Per Command

| Command | Event Type | Title Template | Body Template |
|---|---|---|---|
| create_request | request.created | "New {type} request" | "{title}" |
| change_status | request.status_changed | "Request updated" | "Status changed from {old} to {new}" |
| change_priority | request.priority_changed | "Priority changed" | "Priority changed from {old} to {new}" |
| assign_request | request.assigned | "Request assigned" | "Assigned to {technician}" |
| add_comment | request.comment_added | "New comment" | "Comment on: {request_title}" |
| add_note | request.note_added | "New internal note" | "Note on: {request_title}" |

### R4: Event Payload
Each event payload includes:
- `request_id` (always)
- `created_by` (always — the request creator, for target resolution)
- `assigned_to` (always — current assignee, for target resolution)
- Additional context fields per event type (old_status, new_status, etc.)

---

## Acceptance Criteria

- [ ] EventBus initialized at startup with NotificationSubscriber
- [ ] All 6 request command routers emit domain events
- [ ] Events contain correct titles, bodies, and payloads
- [ ] Notifications created for correct targets after each command
- [ ] No event emitted on command failure
- [ ] Integration tests verify end-to-end: command → event → notification
