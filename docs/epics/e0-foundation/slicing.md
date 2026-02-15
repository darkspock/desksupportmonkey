# Epic Slicing: E0 - Foundation

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-15
**Total Features:** 3

---

## Slicing Rationale

E0 is sliced into 3 vertical features following a natural dependency chain: first make the app boot (F0), then add authentication (F1), then wire up async infrastructure (F2). Each feature is deployable on its own and adds testable value.

---

## Dependency Graph

```
F0: Bootstrapping
 │
 ├── F1: Authentication & Authorization
 │
 └── F2: Async Infrastructure (Celery + MinIO)
```

F1 and F2 both depend on F0 but are independent of each other. They can be built in parallel or sequentially.

---

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity |
|---|---|---|---|---|
| F0 | Bootstrapping | None | App boots, DB works, API responds, response standards | M |
| F1 | Authentication & Authorization | F0 | Magic link login, JWT, RBAC, multi-tenancy, super admin bootstrap | L |
| F2 | Async Infrastructure | F0 | Celery worker runs, MinIO stores files, magic link cleanup task | S |

---

## Recommended Order

1. **F0: Bootstrapping** - Must be first. Everything depends on a running app.
2. **F1: Authentication & Authorization** - Core of E0. Without auth, no other epic can start.
3. **F2: Async Infrastructure** - Can be done last. No epic depends on Celery/MinIO until E6 (Reports).

---

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

---

## Risk Notes

- F1 is the largest feature. If it feels too big during implementation, the magic link flow (US-002, US-003) and RBAC/multi-tenancy (US-004, US-005) could be split further. But for now they're tightly coupled (RBAC needs JWT, JWT comes from magic link).
