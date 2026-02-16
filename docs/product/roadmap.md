# DeskSupportMonkey - Roadmap

## Epic Overview

| # | Epic | Description | Priority | Status |
|---|---|---|---|---|
| E0 | Foundation | Project setup, DB, auth, multi-tenancy base | Critical | Done |
| E1 | Company Management | Super admin: create companies, assign admins, manage domains | Critical | Done |
| E2 | Asset Inventory | Asset CRUD, assignment, history (event sourcing), CSV import | High | Done |
| E3 | Service Requests | Employee portal, request state machine, technician queue, comments | High | Done |
| E4 | Real-time & Notifications | WebSockets, in-app notifications, pub/sub events | Medium | Done |
| E5 | Admin Dashboard | Metrics, charts, alerts, user management | Medium | Done |
| E6 | Report Generation | Celery async tasks, PDF generation, MinIO storage | Medium | Done |
| E7 | Frontend | React app, routing, layouts, pages for all modules | High | Done |
| E8 | Seed Data & Demo | Demo data, demo script, Docker Compose polish | Low | Done |
| E9 | UX Improvements | Invite users, departments edit, frontend quality uplift, and reliability hardening | Medium | Done |
| E10 | Asset QR & Barcodes | QR codes and barcodes on asset detail page with print functionality for physical labels | Medium | Done |

---

## Dependency Graph

```
E0: Foundation
 │
 ├── E1: Company Management
 │    │
 │    ├── E2: Asset Inventory
 │    │    │
 │    │    └── E6: Report Generation
 │    │
 │    ├── E3: Service Requests
 │    │    │
 │    │    └── E4: Real-time & Notifications
 │    │
 │    └── E5: Admin Dashboard (depends on E2 + E3)
 │
 └── E7: Frontend (parallel, depends on API endpoints from E1-E6)

E8: Seed Data & Demo (after all others)

E10: Asset QR & Barcodes (depends on E2 + E7)
```

---

## Epic Details

### E0: Foundation
- Project scaffolding (FastAPI app, folder structure, base classes)
- PostgreSQL + Alembic setup
- Redis connection
- Magic link authentication (request link, verify token, JWT)
- RBAC middleware (super_admin, admin, technician, employee)
- Multi-tenancy base (company_id scoping in repositories)
- Health check endpoint
- CORS, error handling, API response format

### E1: Company Management
- Company CRUD (super admin only)
- Company email domains configuration
- Company statuses (active, suspended, deactivated)
- Department CRUD (company admin)
- User auto-creation on first magic link login
- User role management (company admin promotes/demotes)
- User deactivation

### E2: Asset Inventory
- Asset CRUD (technician)
- Asset types, statuses, serial numbers
- Asset assignment/unassignment to employees
- Asset event sourcing (append-only history log)
- Asset search and filters
- CSV bulk import
- "My Equipment" view (employee)

### E3: Service Requests
- Request creation (employee): incident, new equipment, onboarding
- Request state machine: submitted -> in_review -> in_progress -> resolved/rejected
- Automatic priority based on type
- Technician queue (claim/self-assign)
- Comments (employee + technician)
- Internal notes (technician only)
- "My Requests" view (employee)

### E4: Real-time & Notifications
- WebSocket endpoint (per user, JWT auth)
- Domain events on state changes
- Pub/sub: route events to subscribers (notifier, audit)
- In-app notification storage and read/unread
- Push events: request status changed, comment added, report ready

### E5: Admin Dashboard
- Open requests summary (by type, priority, status)
- Average resolution time (overall + per technician)
- Assets by status (chart data)
- Requests over time (chart data)
- Warranty expiration alerts
- Aging asset alerts
- SLA breach alerts (hardcoded thresholds)
- User management (list, promote, deactivate)

### E6: Report Generation
- Celery task for async PDF generation
- Jinja2 HTML templates -> WeasyPrint PDF
- Upload to MinIO (S3-compatible)
- Report record (pending -> completed/failed)
- Signed URL for download (1h expiry)
- Report types: asset inventory, request summary, technician performance
- Max 3 retries, 5 min timeout

### E7: Frontend
- React + TypeScript + Vite setup
- Routing by role (employee, technician, admin, super admin)
- Auth flow (magic link request, verify, JWT storage)
- Employee portal: my equipment, submit request, my requests
- Technician panel: request queue, inventory management
- Admin dashboard: metrics, alerts, user management
- Super admin: company management
- WebSocket integration for real-time updates
- Responsive design (desktop + tablet)

### E8: Seed Data & Demo
- Seed script: 2-3 companies, users per role, assets, requests in various states
- Demo walkthrough script (documentation)
- Docker Compose verified end-to-end
- .env.example with defaults

### E9: UX Improvements
- Invite users by email from Users page (admin sends magic link)
- Departments page: add edit/rename functionality
- Asset detail page: proper formatted event history instead of raw JSON
- Resolve user IDs to names/emails across request views, dashboard, and notes
- Asset assignment UI (assign/unassign from asset detail page)
- Standardize date format to YYYY/MM/DD across all pages (11 instances)
- Confirmation dialogs for destructive actions (delete, deactivate, status changes)
- Toast notifications for silent mutations (mark-read, toggle active, status change, delete)
- Empty state CTAs (MyEquipmentPage)
- i18n: Spanish and English with language selector in header
- Asset edit and status change from detail page
- Request priority change from detail page
- User department assignment from Users page
- Dashboard: warranty alerts, aging alerts, request trend chart
- Company edit (name, domains) from Companies page
- Auth refresh with stronger visual hierarchy and branded login experience
- Login uses root README branding image source (`web/site/logo.png`)
- Lightweight design-system foundation (tokens + shared form/action primitives)
- Improved responsive app shell for tablet/mobile navigation
- Accessibility polish (keyboard/focus/labels/tooltips)
- Unified loading/empty/error and mutation feedback patterns

### E10: Asset QR Codes & Barcodes
- QR code on asset detail page encoding full URL to asset (scan-to-access)
- Code 128 barcode encoding asset ID (ULID) for physical identification
- Print button: opens clean print view with QR, barcode, brand, model, serial number
- Auth redirect flow: unauthenticated QR scans redirect to login, then back to asset
- i18n support for all labels (English and Spanish)

---

## Recommended Implementation Order

| Phase | Epics | Outcome |
|---|---|---|
| **Phase 1** | E0 + E1 | App boots, auth works, companies exist, users can log in |
| **Phase 2** | E2 + E3 | Core business: assets and requests fully functional (API) |
| **Phase 3** | E4 + E5 + E6 | Real-time, dashboard, reports (API complete) |
| **Phase 4** | E7 | Frontend for everything |
| **Phase 5** | E8 | Demo-ready with seed data |

Note: E7 (Frontend) can start in parallel with Phase 2 once E0+E1 APIs are stable.
