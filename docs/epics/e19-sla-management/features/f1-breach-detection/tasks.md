# Tasks: F1 — Breach Detection

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Add first_response_at to ServiceRequest entity | S | Domain |
| 2 | Add first_response_at to ServiceRequestModel + migration | S | Infra |
| 3 | Set first_response_at in ChangeRequestStatusCommand handler | S | App |
| 4 | Application: RecordSlaBreachCommand + handler | S | App |
| 5 | Application: GetRequestSlaStatusQuery + handler | M | App |
| 6 | Celery: check_sla_breaches periodic task | L | Task |
| 7 | Register Celery beat schedule + import | S | Task |
| 8 | HTTP: SLA status endpoint for request | S | HTTP |
| 9 | Add SLA EventTypes to notification enum | S | Domain |
| 10 | Unit tests: breach detection logic | M | Test |
| 11 | Unit tests: GetRequestSlaStatus query | M | Test |
| 12 | Unit tests: RecordSlaBreachCommand | S | Test |
| 13 | Frontend: SLA status badge on request detail | M | FE |
| 14 | i18n: SLA status translations EN/ES | S | FE |

## Detailed Tasks

### Task 1: Add first_response_at to ServiceRequest entity
- **File:** `src/request_bc/request/domain/entities.py`
- **What:** Add `first_response_at: datetime | None` field (default None). Add `record_first_response()` method that sets it once.
- [x] Done

### Task 2: Add first_response_at to ServiceRequestModel + migration
- **Files:** `src/request_bc/request/infrastructure/models.py`, new Alembic migration
- **What:** Add `first_response_at` column (nullable DateTime) to `service_requests` table. Update `_to_entity()` and `_to_model()`.
- [x] Done

### Task 3: Set first_response_at in ChangeRequestStatusCommand handler
- **File:** `src/request_bc/request/application/commands/change_request_status.py`
- **What:** When status changes from SUBMITTED to any later status (IN_REVIEW, IN_PROGRESS, etc.) and first_response_at is None, call `request.record_first_response()`.
- [x] Done

### Task 4: RecordSlaBreachCommand + handler
- **File:** `src/sla_bc/sla/application/commands/record_breach.py`
- **What:** Internal command used by Celery task. Creates SlaBreachRecord. Checks has_breach_of_type to avoid duplicates.
- [x] Done

### Task 5: GetRequestSlaStatusQuery + handler
- **File:** `src/sla_bc/sla/application/queries/get_request_sla.py`
- **What:** Given request_id, finds applicable policy, calculates response/resolution elapsed times, returns SlaStatusDto with on_track/warning/breached status.
- [x] Done

### Task 6: Celery check_sla_breaches periodic task
- **File:** `core/tasks/sla.py`
- **What:** Task runs every 5 minutes. For each company with active policies, gets open requests, matches policies, detects warnings/breaches, records new breach records. Must be idempotent.
- [x] Done

### Task 7: Register Celery beat schedule + import
- **Files:** `core/celery.py`, `core/tasks/__init__.py`
- **What:** Add check-sla-breaches to beat_schedule (every 5 minutes). Import sla module in __init__.py.
- [x] Done

### Task 8: HTTP SLA status endpoint
- **File:** `adapters/http/api/sla/routers.py`
- **What:** GET /api/v1/sla/requests/{request_id}/status — returns SLA status for a request (technician+)
- [x] Done

### Task 9: Add SLA EventTypes to notification enum
- **File:** `src/notification_bc/notification/domain/enums.py`
- **What:** Add SLA_WARNING, SLA_RESPONSE_BREACHED, SLA_RESOLUTION_BREACHED to EventType enum
- [x] Done

### Task 10: Unit tests — breach detection logic
- **File:** `tests/unit/sla_bc/sla/test_breach_detection.py`
- **What:** Test the Celery task logic: breach detection, warning thresholds, idempotency, policy matching
- [x] Done

### Task 11: Unit tests — GetRequestSlaStatus query
- **File:** `tests/unit/sla_bc/sla/application/queries/test_get_request_sla.py`
- **What:** Test SLA status calculation: on_track, warning, breached, met, no policy
- [x] Done

### Task 12: Unit tests — RecordSlaBreachCommand
- **File:** `tests/unit/sla_bc/sla/application/commands/test_record_breach.py`
- **What:** Test breach recording, duplicate prevention
- [x] Done

### Task 13: Frontend: SLA status badge on request detail
- **File:** `web/app/src/pages/technician/RequestDetailPage.tsx`
- **What:** Fetch SLA status via API and display badge (on_track/warning/breached) with time remaining
- [x] Done

### Task 14: i18n: SLA status translations EN/ES
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** Add page.sla.status_*, page.sla.response_*, page.sla.resolution_* keys
- [x] Done
