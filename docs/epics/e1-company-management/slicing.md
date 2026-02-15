# Epic Slicing: E1 - Company Management

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-15
**Total Features:** 3

---

## Slicing Rationale

E1 is sliced into 3 features following a dependency chain: first create companies with email domains (F0), then add status management and auth integration (F1), then departments and user management (F2). Each feature adds testable, deployable value.

---

## Dependency Graph

```
F0: Company CRUD + Email Domains
 │
 ├── F1: Company Status + Auth Integration
 │
 └── F2: Departments + User Management
```

F1 and F2 both depend on F0 but are independent of each other.

---

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity |
|---|---|---|---|---|
| F0 | Company CRUD + Email Domains | E0 | Companies exist, domain matching works, initial admin assigned | M |
| F1 | Company Status + Auth Integration | F0 | Company lifecycle, auth respects status, security enforcement | M |
| F2 | Departments + User Management | F0 | Full org structure, admin manages users and departments | L |

---

## Recommended Order

1. **F0: Company CRUD + Email Domains** — Must be first. Real domain matching replaces E0 stub.
2. **F1: Company Status + Auth Integration** — Security layer. Blocks suspended/deactivated companies.
3. **F2: Departments + User Management** — Org structure. Admin can manage their company.

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

- F0 modifies the existing auth flow (CompanyLookupService) — requires regression tests on magic link flow.
- F1 adds company status check to `get_current_user` — cross-cutting change affecting every authenticated endpoint.
- F2 is the largest feature (departments + users) but all patterns are straightforward CRUD.
