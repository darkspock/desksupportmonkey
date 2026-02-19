# Design: F3 — Celery Tasks: Reminders & No-Show Detection

**Feature:** Two Celery Beat scheduled tasks for appointment reminders and auto no-show detection.
**Depends on:** F1 (appointment entities, repos, notification events)

## Overview

F3 adds two background tasks using Celery Beat:
1. **send_appointment_reminders** — sends 24h and 1h reminders for upcoming CONFIRMED appointments
2. **detect_no_shows** — marks CONFIRMED appointments as NO_SHOW 2h after scheduled end

Both tasks use the existing `find_needing_reminder()`, `find_confirmed_before()` repository methods and `mark_reminder_sent()`, `mark_no_show()` entity methods from F0.

## New EventType Values

Add to `src/notification_bc/notification/domain/enums.py`:
- `APPOINTMENT_REMINDER = "appointment.reminder"`

## Task 1: send_appointment_reminders

**Schedule:** Every 15 minutes via Celery Beat
**Logic:**
1. Compute 24h window: `(now + 24h, now + 24h + 15min)`
2. Query `find_needing_reminder("24h", window_start, window_end)` — CONFIRMED appointments in that window with `reminder_24h_sent=False`
3. For each: create Notification for both technician and employee, call `mark_reminder_sent("24h")`, save
4. Repeat for 1h window: `(now + 1h, now + 1h + 15min)`
5. Commit all changes

**Idempotency:** `reminder_24h_sent` and `reminder_1h_sent` flags prevent duplicate sends.

## Task 2: detect_no_shows

**Schedule:** Every 30 minutes via Celery Beat
**Logic:**
1. Compute cutoff: `now - 2h` (appointments that ended 2+ hours ago)
2. Query `find_confirmed_before(cutoff)` — CONFIRMED appointments where `scheduled_end < cutoff`
3. For each: call `mark_no_show()`, save, create Notification
4. Commit

**Idempotency:** Only CONFIRMED status appointments match; after `mark_no_show()` they become NO_SHOW and won't match again.

## Notification Pattern

Uses direct `Notification.create()` + `NotificationRepository.save()` pattern (same as report task), NOT the EventBus (which requires a FastAPI request context).

## Files

| File | Action |
|------|--------|
| `core/tasks/appointments.py` | Create — 2 tasks |
| `core/tasks/__init__.py` | Edit — export new tasks |
| `core/celery.py` | Edit — add 2 Beat schedule entries |
| `src/notification_bc/notification/domain/enums.py` | Edit — add APPOINTMENT_REMINDER |
| `tests/unit/core/tasks/test_appointments.py` | Create — unit tests |
