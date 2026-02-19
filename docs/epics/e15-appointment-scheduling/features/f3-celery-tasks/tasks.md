# Tasks: F3 — Celery Tasks: Reminders & No-Show Detection

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 5
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Notification enum | 1 | S |
| Celery tasks | 1 | M |
| Beat schedule + exports | 1 | S |
| Unit tests | 1 | S |
| Verification | 1 | S |

---

## Phase 1: Notification Enum

### 1. Add reminder EventType
- [x] Edit `src/notification_bc/notification/domain/enums.py`
  - Add `APPOINTMENT_REMINDER = "appointment.reminder"`

---

## Phase 2: Celery Tasks

### 2. Create appointment tasks
- [x] Create `core/tasks/appointments.py`
  - `send_appointment_reminders()`: 24h + 1h reminders with idempotency flags
  - `detect_no_shows()`: auto NO_SHOW detection with 2h grace period

---

## Phase 3: Beat Schedule + Exports

### 3. Register in Beat schedule and exports
- [x] Edit `core/celery.py` — 2 Beat schedule entries (every 15min, every 30min)
- [x] Edit `core/tasks/__init__.py` — export both tasks

---

## Phase 4: Unit Tests

### 4. Create unit tests
- [x] Create `tests/unit/core/tasks/test_appointments.py`
  - `test_send_24h_reminders` — 24h window, creates 2 notifications, marks sent
  - `test_send_1h_reminders` — 1h window, marks reminder_1h_sent
  - `test_no_reminders_when_none_found` — no saves
  - `test_detect_no_shows` — marks NO_SHOW, creates notification
  - `test_detect_no_shows_none_found` — no saves

---

## Phase 5: Verification

### 5. Verify
- [x] Lint passes: `make lint` (no new errors in appointment_bc)
- [x] Unit tests pass: `make test` (924 passed)
- [x] EventType count test updated (20)

---

## Final Checklist

- [x] 2 Celery tasks created
- [x] 2 Beat schedule entries added
- [x] 1 new EventType value
- [x] 5 unit tests
- [x] All tests passing
