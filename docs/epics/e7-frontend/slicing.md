# E7: Frontend - Feature Slicing

**Date:** 2026-02-16

---

## Features

| # | Feature | Description | Depends | Status |
|---|---------|-------------|---------|--------|
| F0 | Project Setup | Vite + React + TS + Tailwind + routing + API client + auth context | - | Done |
| F1 | Auth Flow | Magic link request, verify, JWT storage, protected routes | F0 | Done |
| F2 | Layout & Navigation | App shell, sidebar, header, role-based menus, notification badge | F1 | Done |
| F3 | Employee Views | My Equipment, Submit Request, My Requests, Request Detail, Notifications | F2 | Done |
| F4 | Technician Views | Request Queue, Request Detail (assign/status/notes), Asset CRUD, CSV Import | F2 | Done |
| F5 | Admin Views | Dashboard (charts + alerts), User Management, Department Management, Reports | F2 | Done |
| F6 | Super Admin Views | Company list, create, edit, status management | F2 | Done |
| F7 | Real-Time | WebSocket connection, live notification badge, toast on new events | F2 | Done |

## Dependency Graph

```
F0 → F1 → F2 → F3 (employee)
                ├── F4 (technician)
                ├── F5 (admin)
                ├── F6 (super admin)
                └── F7 (real-time)
```

F3-F7 can be implemented in parallel after F2.

## Implementation Order

1. F0 + F1 + F2 (foundation — must be sequential)
2. F3 + F4 + F5 + F6 + F7 (parallel, role-specific views)
