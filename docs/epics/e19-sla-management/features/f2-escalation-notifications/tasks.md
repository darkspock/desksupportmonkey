# Tasks: F2 — Escalation & Notifications

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | TargetResolver: add SLA event mappings | S | Domain |
| 2 | Celery task: send breach notifications to admins | S | Task |
| 3 | Celery task: auto-escalate priority on breach | S | Task |
| 4 | Unit tests: TargetResolver SLA events | S | Test |
| 5 | Unit tests: escalation logic | S | Test |

## Detailed Tasks

### Task 1: TargetResolver SLA event mappings
- **File:** `src/notification_bc/notification/application/services/target_resolver.py`
- **What:** Add resolver methods for SLA_WARNING (assigned technician), SLA_RESPONSE_BREACHED (technician + admins), SLA_RESOLUTION_BREACHED (technician + admins)
- [x] Done

### Task 2: Celery task: send breach notifications to admins
- **File:** `core/tasks/sla.py`
- **What:** On SLA_RESPONSE_BREACHED and SLA_RESOLUTION_BREACHED, also send notifications to all company admins
- [x] Done

### Task 3: Celery task: auto-escalate priority on breach
- **File:** `core/tasks/sla.py`
- **What:** When escalate_on_breach is True and a response breach occurs, bump the request's priority if not already urgent
- [x] Done

### Task 4: Unit tests — TargetResolver SLA events
- **File:** `tests/unit/notification_bc/notification/application/test_target_resolver.py`
- **What:** Test target resolution for SLA_WARNING, SLA_RESPONSE_BREACHED, SLA_RESOLUTION_BREACHED
- [x] Done

### Task 5: Unit tests — escalation logic
- **File:** `tests/unit/sla_bc/sla/test_escalation.py`
- **What:** Test priority escalation on breach with escalate_on_breach flag
- [x] Done
