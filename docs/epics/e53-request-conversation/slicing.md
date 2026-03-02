# Epic Slicing: E53 — Request Conversation & Email Notifications

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-03-02
**Total Features:** 3

## Slicing Rationale

The epic has three distinct capabilities that map cleanly to vertical slices:

1. **Waiting status** — Backend domain change (enum, transitions, SLA pause, auto-transition) + minimal frontend (status badge, filter). Delivers standalone value: technicians can track which requests are blocked on employees, and SLA stops ticking unfairly. No dependency on email or conversation UI.

2. **Email notifications** — Backend-only (EmailSubscriber, Celery task, HTML templates). Depends on F1 because one email variant fires on `waiting_for_employee` status change. Independent of F3 (conversation UX).

3. **Conversation UX** — Frontend-only (chat bubbles, waiting banner, status dialog with message). Depends on F1 because the waiting banner needs the status to exist. Independent of F2 (email).

No foundation feature is needed because F1 already delivers user value (it's not a "setup-only" feature). F2 and F3 are parallel branches — they can be built in any order after F1.

## Dependency Graph

```
F1: Waiting Status (no dependencies)
    │
    ├── F2: Email Notifications
    │
    └── F3: Conversation UX
```

## Features Summary

| # | Feature | Dependencies | Status | Value Delivered | Complexity |
|---|---------|--------------|--------|-----------------|------------|
| F1 | Waiting Status | None | Done | Technicians can set "waiting for employee", SLA pauses, auto-transition on comment | M |
| F2 | Email Notifications | F1 | Done | Email sent on comment/status change with deep link | M |
| F3 | Conversation UX | F1 | Done | Chat bubbles, waiting banner, status dialog with message | S |

## Recommended Order

1. **F1: Waiting Status** — Must be first. Adds the domain enum, transitions, SLA tracking fields, auto-transition logic, migration, and basic UI (status badge + filter). Everything else depends on this.
2. **F2: Email Notifications** — Highest business impact after F1. Without email, employees still won't know the technician needs info.
3. **F3: Conversation UX** — Polish layer. Improves the experience but the system is functional without it.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F1 → F2, F1 → F3)
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F1 is both foundation and value)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F2 depends on F1's event payload:** The `REQUEST_STATUS_CHANGED` event must include the new status value in the payload for F2's EmailSubscriber to filter on `waiting_for_employee`. This is already the case (the existing `RequestEventFactory.status_changed` includes `new_status` in the payload).
- **F3's status dialog with message (US-09)** creates a comment AND changes status in a single action. This touches the comment API (F1 scope). To avoid overlap, F1 owns the backend logic for "change status with optional comment" and F3 only adds the frontend dialog that calls it.
