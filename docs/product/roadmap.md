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
| E11 | Department Equipment Profiles | Department managers, role-based equipment profiles (e.g., Tech → Linux 32GB, Design → MacBook Pro, Heads → MacBook Air), and automatic asset assignment by department and role | High | Pending |
| E12 | Request Typification & Approval | Structured request categories (repair, new equipment, configuration, etc.), sub-types for new equipment (computer, mobile, etc.), priority scoring based on department and role, and approval workflow for new equipment requests | High | Pending |
| E13 | AI Request Classification | AI-powered automatic classification of service requests — infers category, sub-type, and priority from user description, overriding user-submitted values when the AI assessment is more accurate | Medium | Pending |
| E14 | Procurement & Budget | Purchase order management, goods receipt tracking, department budget allocation, and expense control per department with spending reports | High | Pending |
| E15 | Appointment Scheduling | Schedule and manage support appointments between technicians and employees — calendar view, time slot availability, booking, reminders, and rescheduling | Medium | Pending |
| E16 | Shipping & Logistics | Ship equipment to employee home, other offices, or vendor for repair — shipment tracking, delivery addresses, carrier integration, return management, and shipment status notifications | Medium | Pending |
| E17 | Scheduled Maintenance | Recurring and one-off maintenance plans for assets — maintenance templates, calendar integration, technician assignment, completion tracking, and overdue alerts | Medium | Pending |
| E18 | Knowledge Base & Self-Service | Built-in wiki with TipTap WYSIWYG editor — articles, FAQs, categorized solutions, version history, native links to assets/tickets/users, full-text search (PostgreSQL tsvector), AI-suggested articles on ticket creation for deflection, and self-service portal for employees | High | Pending |
| E19 | SLA Management | Configurable SLA policies per priority and category — response/resolution time targets, automatic escalation rules, breach notifications to managers, and SLA compliance reports | High | Pending |
| E20 | Asset Lifecycle & Warranties | Asset depreciation tracking, end-of-life planning, renewal/refresh cycles, lease vs purchase tracking, warranty management with vendor contacts, and warranty claim workflow | Medium | Pending |
| E21 | Software License Management | Track software licenses per user and department — seat compliance (used vs purchased), renewal alerts, cost allocation per department, and license audit reports | Medium | Pending |
| E22 | Employee Onboarding/Offboarding | Automated workflows for new hires (equipment pack based on department + role from E11) and departures (return checklist, account deactivation, asset recovery tracking) | High | Pending |
| E23 | Multi-channel Intake | Email-to-ticket conversion, Slack/Teams integration for creating and tracking requests, and chatbot for guided ticket creation without entering the app | Medium | Pending |
| E24 | SSO & Directory Sync | SAML/OIDC single sign-on for corporate login, LDAP/Active Directory synchronization of users, departments, and roles with automatic provisioning | High | Pending |
| E25 | Vendor Management | Vendor directory with contacts and contracts, vendor SLA tracking, incident history per vendor, warranty claim routing, and vendor performance reports | Medium | Pending |
| E26 | Observability with SigNoz | OpenTelemetry instrumentation for FastAPI, SQLAlchemy, Celery, and Redis — self-hosted SigNoz for distributed tracing, metrics, logs, error tracking, and performance dashboards | Medium | Pending |
| E27 | Surveys & Feedback | CSAT surveys after ticket resolution (star rating + comment), decision polls for purchase planning (connects with E14), onboarding feedback after equipment delivery (connects with E22), and satisfaction metrics per technician, department, and category | Medium | Pending |
| E28 | Mobile / PWA | Progressive Web App for technicians and employees — QR scanning with camera, ticket updates from the field, push notifications, offline support, and responsive mobile-first UI | High | Pending |
| E29 | Audit Trail & Compliance | Complete audit log of all user actions (who did what, when), GDPR data export and deletion requests, compliance reports, and data retention policies per company | High | Pending |
| E30 | Custom Fields | Admin-defined custom fields for assets, tickets, and companies — text, number, date, dropdown, and multi-select types with validation rules and visibility per role | High | Pending |
| E31 | Workflow Automations | Rule engine for if-then automations — auto-assign tickets by category, auto-escalate after SLA threshold, notify manager on critical priority, auto-close resolved tickets after X days, and trigger actions on asset status changes | High | Pending |
| E32 | Asset Discovery | Automatic network device discovery — agent-based and agentless scanning, sync discovered devices with asset inventory, detect new/removed devices, and scheduled discovery scans | Medium | Pending |
| E33 | Change Management (ITIL) | Change request workflow — request, risk assessment, CAB approval board, scheduled implementation, rollback plan, post-implementation review, and change calendar integration | Medium | Pending |
| E34 | Feature Voting & Roadmap | In-app feature request board — users submit and upvote ideas, admin reviews and prioritizes, public roadmap view with status (planned, in progress, shipped), and vote-based priority scoring for product decisions | Low | Pending |

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
