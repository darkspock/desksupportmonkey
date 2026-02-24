# Epic Slicing: E19 — SLA Management

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Total Features:** 4

## Slicing Rationale

E19 introduces a new bounded context (`sla_bc`) with 2 entities (SlaPolicy, SlaBreachRecord), a Celery periodic task for breach detection, notification integration, compliance reporting, and admin management UI. The scope requires slicing into vertical features.

Slicing follows **vertical slices by user value**:
- **F0** establishes the foundation (BC, entities, policy CRUD, admin pages) — admins can define SLA policies
- **F1** adds automated breach detection (Celery task, breach records, first_response_at tracking) — system monitors compliance
- **F2** adds escalation and notifications — managers are alerted on breaches
- **F3** adds compliance dashboard and reports — admins can measure and report on SLA performance

Each feature is independently deployable and delivers standalone user value.

## Dependency Graph

```
Feature 0: SLA Policies
    │
    ├── Feature 1: Breach Detection
    │       │
    │       ├── Feature 2: Escalation & Notifications
    │       │
    │       └── Feature 3: Compliance Dashboard & Reports
    │
    └── (F1 depends on F0)
```

F2 and F3 both depend on F1. No circular dependencies.

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | SLA Policies | None | Admin creates/manages SLA policies with response/resolution targets per priority | M | Done |
| 1 | Breach Detection | F0 | Celery task detects SLA breaches, records them, SLA status on request detail | L | Done |
| 2 | Escalation & Notifications | F1 | Warning/breach notifications to technicians and admins, auto-escalation | M | Done |
| 3 | Compliance Dashboard & Reports | F1 | SLA compliance dashboard with metrics, trend charts, and PDF report | M | Done |

## Recommended Order

1. **Feature 0: SLA Policies** — Must be first. Creates the BC, DB tables, policy CRUD endpoints, and admin management page. No automated processing yet.
2. **Feature 1: Breach Detection** — Adds `first_response_at` to requests, Celery periodic task, breach record persistence, and SLA status display on request detail pages.
3. **Feature 2: Escalation & Notifications** — Extends breach detection with notification events and auto-escalation rules.
4. **Feature 3: Compliance Dashboard & Reports** — Adds dashboard queries, compliance metrics page, and SLA compliance report type.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- F1 requires modifying the `request_bc` to add `first_response_at` field — this is a cross-BC dependency. Minimize by adding only the field and setting it in the existing ChangeRequestStatusCommand handler.
- Celery beat task must be idempotent — never create duplicate breach records for the same request+breach_type.
- Policy matching must handle the priority+type specificity correctly: type-specific policy overrides priority-only default.
- Plan gate (`sla` feature key) must be enforced on all SLA endpoints.
