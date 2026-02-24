# Epic Slicing: E29 — Audit Trail & Compliance Evidence

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Total Features:** 4

## Slicing Rationale

E29 is a large epic spanning 5 entities, 18 API endpoints, 4 Celery tasks, middleware integration, and multiple frontend pages. The natural slicing follows distinct business capabilities:

1. **Audit capture** is the foundational capability — all other features depend on audit data existing.
2. **Audit UI + export + compliance tagging** form a cohesive admin workflow for viewing and leveraging audit data.
3. **GDPR operations** are a separate regulatory workflow (export + anonymization) that only needs audit data to exist.
4. **Retention + integrity** are operational/governance concerns that can be layered on independently.

Each feature delivers independent user value and can be deployed separately. The foundation (F0) runs silently — it starts capturing audit data for all plans so that when Enterprise features (F1-F3) are activated, historical data is available.

## Dependency Graph

```
Feature 0: Audit Foundation
    │
    ├── Feature 1: Audit UI, Export & Compliance
    │
    ├── Feature 2: GDPR Operations
    │
    └── Feature 3: Retention & Integrity
```

All features depend only on F0. F1, F2, and F3 are independent of each other and can be implemented in parallel or any order.

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| F0 | Audit Foundation | None | All write ops captured in centralized audit log with hash integrity | M | Done |
| F1 | Audit UI, Export & Compliance | F0 | Admins can view, search, filter, export audit log; tag with compliance controls; super admin cross-company view | L | Done |
| F2 | GDPR Operations | F0 | Admins can fulfill GDPR data export and anonymization requests | M | Done |
| F3 | Retention & Integrity | F0 | Admins can configure retention policies; verify audit log integrity | S | Done |

## Recommended Order

1. **Feature 0: Audit Foundation** — Must be first. Establishes the `audit_bc` bounded context, AuditEntry entity, middleware, MCP capture, and database. Once deployed, audit data starts accumulating silently for all plans.
2. **Feature 1: Audit UI, Export & Compliance** — Highest admin value. Unlocks the audit log UI, export functionality, and compliance tagging. Includes super admin cross-company view.
3. **Feature 2: GDPR Operations** — Regulatory compliance. Enables GDPR Article 15 (right of access) and Article 17 (right to erasure) workflows.
4. **Feature 3: Retention & Integrity** — Governance layer. Adds data lifecycle management and tamper detection verification.

## Entity Ownership

| Entity | Owner Feature | Used By |
|--------|--------------|---------|
| AuditEntry | F0 | F1, F2, F3 |
| AuditEntryTag | F1 | — |
| ComplianceControl | F1 | — |
| GdprRequest | F2 | — |
| RetentionPolicy | F3 | — |

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (all point to F0)
- [x] Each feature independently deployable
- [x] Vertical slices (each has domain + infra + app + http + frontend)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F0 is invisible to users** — It captures data silently. While it delivers infrastructure value, there's no UI feedback. Consider deploying F0 and F1 close together so admins see results quickly.
- **F1 is the largest feature** — Includes audit UI, export, compliance controls, tagging, and super admin view. Could be further split if needed, but the compliance control catalog and tagging are tightly coupled to the audit UI, so splitting would create overlapping scope.
- **F2 modifies the User entity** — Adding `is_anonymized` to User requires cross-BC coordination. This is isolated to F2 to minimize risk.
