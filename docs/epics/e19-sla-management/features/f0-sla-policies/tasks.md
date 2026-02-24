# Tasks: F0 — SLA Policies

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: enums | S | Domain |
| 2 | Domain: entities (SlaPolicy, SlaBreachRecord) | M | Domain |
| 3 | Domain: repository interface | S | Domain |
| 4 | Domain: exceptions | S | Domain |
| 5 | Infrastructure: ORM models | M | Infra |
| 6 | Infrastructure: Alembic migration | S | Infra |
| 7 | Infrastructure: repository implementation | M | Infra |
| 8 | Application: CreateSlaPolicyCommand + handler | S | App |
| 9 | Application: UpdateSlaPolicyCommand + handler | S | App |
| 10 | Application: DeactivateSlaPolicyCommand + handler | S | App |
| 11 | Application: ListSlaPoliciesQuery + handler | S | App |
| 12 | Application: GetSlaPolicyQuery + handler | S | App |
| 13 | HTTP: dependencies, schemas | S | HTTP |
| 14 | HTTP: SLA policy routers | M | HTTP |
| 15 | Register router in app.py | S | HTTP |
| 16 | Unit tests: domain entities | M | Test |
| 17 | Unit tests: command handlers | M | Test |
| 18 | Frontend: SLA Policies page (list + create/edit) | M | FE |
| 19 | Frontend: routes + sidebar entry | S | FE |
| 20 | i18n: SLA translations EN/ES | S | FE |

## Detailed Tasks

### Task 1: Enums
- **File:** `src/sla_bc/sla/domain/enums.py`
- **What:** SlaBreachType enum (response_warning, response_breach, resolution_warning, resolution_breach)
- [x] Done

### Task 2: Entities
- **File:** `src/sla_bc/sla/domain/entities.py`
- **What:** SlaPolicy (create, update, deactivate), SlaBreachRecord (create)
- [x] Done

### Task 3: Repository interface
- **File:** `src/sla_bc/sla/domain/repository.py`
- **What:** SlaRepositoryInterface with methods for policies, breaches, and dashboard queries
- [x] Done

### Task 4: Exceptions
- **File:** `src/sla_bc/sla/domain/exceptions.py`
- **What:** SlaPolicyNotFoundError, DuplicateSlaPolicyError, InvalidSlaTargetsError
- [x] Done

### Task 5: ORM models
- **File:** `src/sla_bc/sla/infrastructure/models.py`
- **What:** SlaPolicyModel, SlaBreachRecordModel with Mapped annotations + indexes
- [x] Done

### Task 6: Alembic migration
- **File:** `alembic/versions/a4c5d6e7f8g9_create_sla_tables.py`
- **What:** Create sla_policies and sla_breach_records tables with partial unique index
- [x] Done

### Task 7: Repository implementation
- **File:** `src/sla_bc/sla/infrastructure/repository.py`
- **What:** SlaRepository implementing policy CRUD, breach recording, and dashboard query methods
- [x] Done

### Task 8: CreateSlaPolicyCommand
- **File:** `src/sla_bc/sla/application/commands/create_policy.py`
- **What:** Creates SlaPolicy with validation (response < resolution, no duplicate active policy)
- [x] Done

### Task 9: UpdateSlaPolicyCommand
- **File:** `src/sla_bc/sla/application/commands/update_policy.py`
- **What:** Updates SlaPolicy name, targets, warning threshold, escalation flag
- [x] Done

### Task 10: DeactivateSlaPolicyCommand
- **File:** `src/sla_bc/sla/application/commands/deactivate_policy.py`
- **What:** Soft-deletes policy by setting is_active=False
- [x] Done

### Task 11: ListSlaPoliciesQuery
- **File:** `src/sla_bc/sla/application/queries/list_policies.py`
- **What:** Returns list of policies for company, optionally filtered by is_active
- [x] Done

### Task 12: GetSlaPolicyQuery
- **File:** `src/sla_bc/sla/application/queries/get_policy.py`
- **What:** Returns single policy by ID
- [x] Done

### Task 13: HTTP schemas + dependencies
- **Files:** `adapters/http/api/sla/schemas.py`, `adapters/http/api/sla/dependencies.py`
- **What:** Request/response schemas. get_sla_repo dependency.
- [x] Done

### Task 14: SLA policy routers
- **File:** `adapters/http/api/sla/routers.py`
- **What:** CRUD endpoints for SLA policies (admin only). Plan gate enforcement.
- [x] Done

### Task 15: Register router
- **File:** `app.py`
- **What:** Import and include SLA router
- [x] Done

### Task 16: Unit tests — domain entities
- **File:** `tests/unit/sla_bc/sla/domain/test_entities.py`
- **What:** Test SlaPolicy creation, validation, update, deactivation. SlaBreachRecord creation.
- [x] Done

### Task 17: Unit tests — command handlers
- **File:** `tests/unit/sla_bc/sla/application/commands/`
- **What:** Test create, update, deactivate command handlers
- [x] Done

### Task 18: Frontend: SLA Policies page
- **File:** `web/app/src/pages/technician/SlaPolicesPage.tsx` (NEW)
- **What:** List policies in table, create/edit modal or form, deactivate button. Admin only.
- [x] Done

### Task 19: Routes + sidebar entry
- **Files:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Route /sla/policies (admin). Sidebar entry under Operations.
- [x] Done

### Task 20: i18n translations
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** All page.sla.* keys
- [x] Done
